"""Streaming renderer + thinking spinner for the interactive CLI.

Single-agent mode (the only mode demoed in Parcel α): a short-lived
``Rich.Live`` with ``transient=True`` drives the spinner while the model
thinks; tool events and the final answer are emitted as *static* prints so
they persist on screen after the live area is erased. This avoids the
"ghost re-paint" bug that plagued Vibe-Trading's earlier Live-based
dashboards (nanobot lesson, design proposal §3.5).

Swarm mode is a stub: callers should fall through to the legacy Rich Live
dashboard in ``cli/_legacy.py``. The full multi-agent grid lands in Parcel β.

Tool events use the dexter-style ``⏺ Tool Name (args)  duration · summary``
format. Tool names are auto-Title-Cased with a small acronym whitelist.
"""

from __future__ import annotations

import re
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Optional

from rich.console import Console
from rich.live import Live
from rich.text import Text

from cli.theme import Theme, get_console
from cli.utils.format import format_duration
from cli.utils.thinking_verbs import pick_thinking_verb

_PREFIX_RE = re.compile(r"^(get|run|do|fetch|load|build|compute|calc(?:ulate)?)_")

# Canonical acronyms that should render UPPERCASE rather than Title-Case.
# Whitelist (not "len <= 3" heuristic) so common words like "web" stay "Web".
_ACRONYMS: frozenset[str] = frozenset({
    "api", "url", "csv", "json", "yaml", "sql", "tsv", "pdf",
    "ai", "ml", "dcf", "fcf", "roe", "roi", "pe", "pb", "iv",
    "btc", "eth", "usd", "cny", "id",
})


def beautify_tool_name(raw: str) -> str:
    """``get_market_data`` → ``Market Data``. Acronyms in whitelist UPPER."""
    if not raw:
        return raw
    parts = _PREFIX_RE.sub("", raw).split("_")
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        out.append(part.upper() if part.lower() in _ACRONYMS else part.capitalize())
    return " ".join(out) if out else raw


def summarize_args(args: dict | str | None, *, max_len: int = 60) -> str:
    """Compact single-line preview. Prefers query/symbol/url; truncates long."""
    if not args:
        return ""
    if isinstance(args, str):
        return _truncate(args, max_len)
    if not isinstance(args, dict):
        return _truncate(str(args), max_len)
    for priority_key in ("query", "prompt", "url", "symbol", "ticker", "code"):
        if priority_key in args and args[priority_key]:
            return f'"{_truncate(str(args[priority_key]), max_len - 2)}"'
    pieces: list[str] = []
    used = 0
    for k, v in args.items():
        token = f"{k}={_truncate(str(v), 20)}"
        if used + len(token) + 2 > max_len:
            pieces.append("…"); break
        pieces.append(token); used += len(token) + 2
    return ", ".join(pieces)


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    if max_len <= 1:
        return "…"
    return value[: max_len - 1] + "…"


# ---------------------------------------------------------------------------
# ThinkingSpinner
# ---------------------------------------------------------------------------


@dataclass
class _SpinnerState:
    verb: str
    started_at: float
    paused: bool = False
    stopped: bool = False
    extra: str = ""


class ThinkingSpinner:
    """Transient spinner that can be paused/resumed safely.

    ``pause()`` is a context manager: stops the underlying ``Live`` (clearing
    its line), yields so the caller can print a static line, then restarts.
    This is nanobot's pattern and avoids ANSI escape interleaving.
    """

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or get_console()
        self._state = _SpinnerState(
            verb=pick_thinking_verb(), started_at=time.monotonic()
        )
        self._live: Optional[Live] = None
        self._lock = threading.Lock()
        self._tick_thread: Optional[threading.Thread] = None

    def start(self, verb: str | None = None) -> None:
        """Begin rendering. ``verb`` rerolls per turn if not supplied."""
        with self._lock:
            if self._live is not None:
                return
            self._state.verb = verb or pick_thinking_verb()
            self._state.started_at = time.monotonic()
            self._state.paused = False
            self._state.stopped = False
            self._live = Live(self._render(), console=self._console,
                               refresh_per_second=10, transient=True)
            self._live.start(refresh=False)
            self._tick_thread = threading.Thread(target=self._tick, daemon=True)
            self._tick_thread.start()

    def stop(self) -> None:
        """Stop and erase the spinner line."""
        with self._lock:
            self._state.stopped = True
            if self._live is not None:
                try:
                    self._live.stop()
                except Exception:  # noqa: BLE001 — Rich shutdown can race
                    pass
                self._live = None

    def set_extra(self, extra: str) -> None:
        """Update the right-hand suffix (e.g. token / cost preview)."""
        self._state.extra = extra

    @contextmanager
    def pause(self) -> Iterator[None]:
        """Suspend the spinner so the caller can safely ``console.print``."""
        was_running = False
        with self._lock:
            if self._live is not None and not self._state.stopped:
                was_running = True
                self._state.paused = True
                try:
                    self._live.stop()
                except Exception:  # noqa: BLE001
                    pass
                self._live = None
        try:
            yield
        finally:
            if was_running and not self._state.stopped:
                with self._lock:
                    self._state.paused = False
                    self._live = Live(self._render(), console=self._console,
                                       refresh_per_second=10, transient=True)
                    self._live.start(refresh=False)

    def _render(self) -> Text:
        elapsed_ms = int((time.monotonic() - self._state.started_at) * 1000)
        text = Text()
        text.append(" ")
        text.append("●", style=Theme.warning)  # pulse anchor (no emoji)
        text.append("  ")
        text.append(self._state.verb, style=Theme.primary_dim)
        text.append("   ")
        text.append(format_duration(elapsed_ms), style=Theme.muted)
        if self._state.extra:
            text.append("  · ", style=Theme.muted)
            text.append(self._state.extra, style=Theme.muted)
        return text

    def _tick(self) -> None:
        """Refresh duration label every 100 ms."""
        while not self._state.stopped:
            time.sleep(0.1)
            with self._lock:
                if self._live is not None and not self._state.paused:
                    try:
                        self._live.update(self._render(), refresh=True)
                    except Exception:  # noqa: BLE001
                        pass


# ---------------------------------------------------------------------------
# StreamRenderer
# ---------------------------------------------------------------------------


@dataclass
class ToolCall:
    """A single tool invocation observed during a turn."""

    name: str
    args: dict | str | None
    started_at: float = field(default_factory=time.monotonic)
    finished_at: Optional[float] = None
    summary: str = ""

    @property
    def duration_ms(self) -> int | None:
        if self.finished_at is None:
            return None
        return int((self.finished_at - self.started_at) * 1000)


class StreamRenderer:
    """Drives the streaming display for a single agent turn.

    Mode ``"single"`` is the focus of Parcel α. Mode ``"swarm"`` is a stub
    — callers should detect it and route to ``_legacy`` swarm rendering.
    """

    def __init__(self, *, mode: str = "single",
                  console: Console | None = None) -> None:
        if mode not in {"single", "swarm"}:
            raise ValueError(f"unknown StreamRenderer mode: {mode!r}")
        self._mode = mode
        self._console = console or get_console()
        self._spinner: Optional[ThinkingSpinner] = None
        self._active_calls: dict[str, ToolCall] = {}

    @property
    def mode(self) -> str:
        return self._mode

    @contextmanager
    def turn(self, *, verb: str | None = None) -> Iterator["StreamRenderer"]:
        """Context manager wrapping one agent turn. Manages spinner lifecycle."""
        if self._mode == "swarm":
            yield self
            return
        self._spinner = ThinkingSpinner(self._console)
        self._spinner.start(verb=verb)
        try:
            yield self
        finally:
            if self._spinner is not None:
                self._spinner.stop()
                self._spinner = None
            self._active_calls.clear()

    def on_tool_start(self, name: str, args: dict | str | None) -> None:
        """Record a tool call start. Line emitted only when call finishes."""
        self._active_calls[name] = ToolCall(name=name, args=args)

    def on_tool_end(self, name: str, *, summary: str = "") -> None:
        """Mark a tool call finished and emit its static line."""
        call = self._active_calls.pop(name, None)
        if call is None:
            call = ToolCall(name=name, args=None,
                             finished_at=time.monotonic(), summary=summary)
        else:
            call.finished_at = time.monotonic()
            call.summary = summary
        self._print_tool_line(call)

    def _print_tool_line(self, call: ToolCall) -> None:
        line = Text()
        line.append("●", style=Theme.success)
        line.append("  ")
        line.append(beautify_tool_name(call.name), style=Theme.label)
        args_preview = summarize_args(
            call.args if isinstance(call.args, (dict, str)) else None
        )
        if args_preview:
            line.append(" ")
            line.append(f"({args_preview})", style=Theme.muted)
        # Right-pad so the duration column aligns at column 60.
        pad_to = 60
        current_len = len(line.plain)
        line.append(" " * max(2, pad_to - current_len))
        if call.duration_ms is not None:
            line.append(format_duration(call.duration_ms), style=Theme.muted)
        if call.summary:
            line.append(" · ", style=Theme.muted)
            line.append(call.summary, style=Theme.muted)
        self._emit_static(line)

    def _emit_static(self, renderable) -> None:  # type: ignore[no-untyped-def]
        """Print a static line, pausing the spinner if running."""
        if self._spinner is not None:
            with self._spinner.pause():
                self._console.print(renderable)
        else:
            self._console.print(renderable)

    def print_answer(self, body: str) -> None:
        """Print the assistant's final answer, prefixed with the brand marker."""
        if self._spinner is not None:
            self._spinner.stop()
            self._spinner = None
        lines = body.splitlines() or [""]
        head = Text()
        head.append("● ", style=Theme.primary)
        head.append(lines[0])
        self._console.print(head)
        for line in lines[1:]:
            self._console.print(Text("  " + line))
        self._console.print()

    def print_footer(self, *, run_id: str, tool_count: int,
                      duration_ms: int | float | None,
                      token_count: int | None, cost: float | None) -> None:
        """``/show <id> · N tool calls · 4.1s · 1.2k tokens · $0.003``."""
        from cli.utils.format import abbreviate_num, format_tokens

        line = Text("  ")
        line.append(f"/show {run_id}", style=Theme.info)
        line.append("  ·  ", style=Theme.muted)
        line.append(
            f"{tool_count} tool call{'s' if tool_count != 1 else ''}",
            style=Theme.muted,
        )
        line.append("  ·  ", style=Theme.muted)
        line.append(format_duration(duration_ms), style=Theme.muted)
        if token_count is not None:
            line.append("  ·  ", style=Theme.muted)
            line.append(format_tokens(token_count), style=Theme.muted)
        if cost is not None:
            line.append("  ·  ", style=Theme.muted)
            line.append(abbreviate_num(cost, currency="$"), style=Theme.muted)
        self._console.print(line)
        self._console.print()


__all__ = [
    "StreamRenderer",
    "ThinkingSpinner",
    "ToolCall",
    "beautify_tool_name",
    "summarize_args",
]
