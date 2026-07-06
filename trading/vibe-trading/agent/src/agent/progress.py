"""Progress emission channel for long-running tools.

Two mechanisms:
  * Tool-level heartbeat: a background timer fires keepalive events every N
    seconds while a tool runs, so the UI never looks frozen. Driven by the
    agent loop, opaque to the tool.
  * Structured progress: tools can opt in via ``emit_progress()`` to publish
    quantified state (stage, current/total, message). Routed back to the
    agent loop's event channel via a thread-local emitter set before the
    tool executes.

Thread model: tools run synchronously inside ``ToolRegistry.execute`` from
worker threads (read batches) or the main loop thread (writes). A
``threading.local`` slot holds the per-thread emitter so structured
progress flows back to the correct AgentLoop instance even when multiple
read-only tools run in parallel.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProgressEvent:
    """Structured progress event emitted by a tool mid-execution.

    Attributes:
        tool: Tool name (filled by the loop, tools don't supply this).
        stage: Short stage label, e.g. ``loading_data`` or ``simulating``.
        current: Current unit count (e.g. page 23 of 100). Optional.
        total: Total unit count. Optional.
        message: Free-form human-readable detail.
        elapsed_s: Seconds since the tool started.
        ts: Wall-clock timestamp.
    """

    tool: str = ""
    stage: str = ""
    current: Optional[int] = None
    total: Optional[int] = None
    message: str = ""
    elapsed_s: float = 0.0
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict for SSE payloads."""
        return {
            "tool": self.tool,
            "stage": self.stage,
            "current": self.current,
            "total": self.total,
            "message": self.message,
            "elapsed_s": round(self.elapsed_s, 2),
            "ts": self.ts,
        }


# Thread-local emitter slot. The agent loop sets ``_local.emit`` to a callable
# before invoking the tool and clears it after, so tools running on the same
# thread can publish structured progress without a circular import.
_local = threading.local()


def _set_emitter(emit: Optional[Callable[[ProgressEvent], None]]) -> None:
    """Install the active progress emitter for the current thread.

    Args:
        emit: Callable that consumes a ``ProgressEvent``. Pass ``None`` to clear.
    """
    if emit is None:
        if hasattr(_local, "emit"):
            del _local.emit
        return
    _local.emit = emit


def _get_emitter() -> Optional[Callable[[ProgressEvent], None]]:
    """Return the active emitter on the current thread, if any."""
    return getattr(_local, "emit", None)


def emit_progress(
    stage: str = "",
    *,
    current: Optional[int] = None,
    total: Optional[int] = None,
    message: str = "",
) -> None:
    """Publish a structured progress event from a tool.

    Silently no-ops when called outside an active tool context (e.g. during
    unit tests that invoke tools directly). Never raises.

    Args:
        stage: Short stage label.
        current: Current unit count.
        total: Total unit count.
        message: Free-form human-readable detail.
    """
    emit = _get_emitter()
    if emit is None:
        return
    try:
        event = ProgressEvent(
            stage=stage,
            current=current,
            total=total,
            message=message,
        )
        emit(event)
    except Exception:
        # Progress emission must never break a tool.
        pass


class HeartbeatTimer:
    """Background thread that emits keepalive ticks while a tool runs.

    Use as a context manager around a single tool invocation:

        with HeartbeatTimer(tool_name="run_backtest", interval=3.0, emit=fn):
            result = registry.execute(...)

    The timer wakes every ``interval`` seconds and calls ``emit`` with a
    dict containing ``tool`` and ``elapsed_s``. Stops cleanly on context
    exit; ``join`` is bounded so a hung emitter can't deadlock the loop.
    """

    def __init__(
        self,
        tool_name: str,
        interval: float,
        emit: Callable[[Dict[str, Any]], None],
    ) -> None:
        """Initialize the heartbeat timer (not started until ``__enter__``).

        Args:
            tool_name: Tool name surfaced in each tick payload.
            interval: Seconds between ticks. Values <0.5 are clamped.
            emit: Callback invoked with each tick payload.
        """
        self._tool_name = tool_name
        requested_interval = float(interval)
        self._interval = max(0.5, requested_interval)
        if requested_interval < 0.5:
            logger.warning(
                "HeartbeatTimer interval %s clamped to 0.5s", interval
            )
        self._emit = emit
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._t0 = 0.0

    def __enter__(self) -> "HeartbeatTimer":
        self._t0 = time.perf_counter()
        self._thread = threading.Thread(
            target=self._run,
            name=f"heartbeat-{self._tool_name}",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        """Tick loop: wait + emit until the stop event fires."""
        while not self._stop_event.wait(self._interval):
            elapsed = time.perf_counter() - self._t0
            try:
                self._emit({"tool": self._tool_name, "elapsed_s": round(elapsed, 2)})
            except Exception:
                # A failing callback must not crash the heartbeat thread.
                pass
