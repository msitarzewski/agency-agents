"""Swarm multi-agent system — run state persistence.

File-system-based persistence for SwarmRun. Directory structure:
    .swarm/runs/{run_id}/
    ├── run.json         # SwarmRun state (atomic write)
    ├── events.jsonl     # append-only event log
    ├── tasks/           # task state files
    ├── inboxes/         # agent message inboxes
    └── artifacts/       # agent outputs
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from src.swarm.models import SwarmEvent, SwarmRun
from src.tools.redaction import redact_internal_paths


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _last_event_timestamp(events_file: Path) -> datetime | None:
    """Return the timestamp of the last line in ``events.jsonl``.

    Used by the stale-run reaper. Returns ``None`` when the file is missing,
    empty, or the tail line cannot be parsed — callers treat that as
    "no liveness signal" and skip the run.
    """
    if not events_file.exists():
        return None
    try:
        text = events_file.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except ValueError:
            continue
        return _parse_iso(payload.get("timestamp"))
    return None


def swarm_runs_root() -> Path:
    """Single source of truth for where swarm runs are persisted.

    The swarm store (mcp_server) and the run-dir sandbox allow-list
    (src.tools.path_utils) must agree on this path. They previously each
    derived ``<agent_root>/.swarm/runs`` independently; a packaging layout
    where the two anchors resolved differently silently put every worker
    run_dir outside the allow-list (P03-A). Deriving it here once keeps
    the store location and the allow-list from drifting again.
    """
    return Path(__file__).resolve().parents[2] / ".swarm" / "runs"


_TRANSIENT_WINERRORS = (5, 32)  # ERROR_ACCESS_DENIED, ERROR_SHARING_VIOLATION
_REPLACE_ATTEMPTS = 6
_REPLACE_BACKOFF = (0.025, 0.05, 0.1, 0.2, 0.4)  # seconds; len == attempts - 1


def _is_transient_windows_error(exc: OSError) -> bool:
    """True for the Windows access/sharing race on os.replace.

    ``winerror`` is only set on Windows; ``getattr`` keeps this a hard
    False on POSIX, so the retry path is Windows-only and POSIX behavior
    is unchanged.
    """
    return getattr(exc, "winerror", None) in _TRANSIENT_WINERRORS


def _replace_with_retry(tmp: Path, target: Path) -> None:
    """``os.replace`` retried on the Windows concurrent-access race.

    A reader holding ``target`` open (e.g. ``load_run`` on the poll path)
    makes Windows fail the rename with WinError 5/32. POSIX ``os.replace``
    is atomic and never raises these, so off-Windows this loop runs
    exactly once — no behavior change. Non-transient errors re-raise
    immediately; the last transient error re-raises after the budget.
    """
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(tmp, target)
            return
        except OSError as exc:
            if not _is_transient_windows_error(exc):
                raise
            if attempt == _REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(_REPLACE_BACKOFF[attempt])


class SwarmStore:
    """File-based persistence store for SwarmRun.

    Each run is stored under base_dir/{run_id}/. run.json uses atomic writes
    (write to .tmp then rename) to prevent corruption. events.jsonl is append-only
    and supports offset-based reads for SSE streaming.

    Attributes:
        base_dir: Storage root directory, typically agent/.swarm/runs.
    """

    def __init__(self, base_dir: Path) -> None:
        """Initialize SwarmStore.

        Args:
            base_dir: Storage root directory path.
        """
        self.base_dir = base_dir
        self._write_lock = threading.Lock()

    def run_dir(self, run_id: str) -> Path:
        """Return the directory path for a given run.

        Args:
            run_id: Run identifier.

        Returns:
            Path to the run directory.

        Raises:
            ValueError: If run_id is empty, absolute, or path-shaped.
        """
        candidate = Path(run_id)
        if (
            not run_id.strip()
            or candidate.is_absolute()
            or len(candidate.parts) != 1
            or any(part in {"", ".", ".."} for part in candidate.parts)
            or "/" in run_id
            or "\\" in run_id
        ):
            raise ValueError(f"run_id {run_id!r} must be a bare run directory name")
        return self.base_dir / candidate.name

    def create_run(self, run: SwarmRun) -> Path:
        """Create the directory structure for a new run and write initial state.

        Args:
            run: SwarmRun instance.

        Returns:
            Path to the created run directory.

        Raises:
            FileExistsError: If the run directory already exists.
        """
        rd = self.run_dir(run.id)
        rd.mkdir(parents=True, exist_ok=False)
        (rd / "tasks").mkdir()
        (rd / "inboxes").mkdir()
        (rd / "artifacts").mkdir()
        self._atomic_write(rd / "run.json", run.model_dump_json(indent=2))
        return rd

    def load_run(self, run_id: str) -> SwarmRun | None:
        """Load the state for a given run.

        Args:
            run_id: Run identifier.

        Returns:
            SwarmRun instance, or None if not found.
        """
        run_file = self.run_dir(run_id) / "run.json"
        if not run_file.exists():
            return None
        # The file may be read mid-replace by a concurrent writer; retry a
        # transient read/parse failure before giving up (same race as
        # _replace_with_retry, reader side).
        last: Exception | None = None
        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                return SwarmRun.model_validate_json(run_file.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                last = exc
                if attempt < len(_REPLACE_BACKOFF):
                    time.sleep(_REPLACE_BACKOFF[attempt])
        assert last is not None  # loop body sets `last` or returns
        raise type(last)(redact_internal_paths(str(last))) from None

    def update_run(self, run: SwarmRun) -> None:
        """Atomically update run state.

        Args:
            run: Updated SwarmRun instance.

        Raises:
            FileNotFoundError: If the run directory does not exist.
        """
        rd = self.run_dir(run.id)
        if not rd.exists():
            raise FileNotFoundError(f"Run directory not found: {rd.name}")
        self._atomic_write(rd / "run.json", run.model_dump_json(indent=2))

    def list_runs(self, limit: int = 50) -> list[SwarmRun]:
        """List all runs sorted by created_at descending.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            List of SwarmRun instances.
        """
        if not self.base_dir.exists():
            return []

        runs: list[SwarmRun] = []
        for entry in self.base_dir.iterdir():
            if not entry.is_dir():
                continue
            run_file = entry / "run.json"
            if run_file.exists():
                try:
                    run = SwarmRun.model_validate_json(run_file.read_text(encoding="utf-8"))
                    runs.append(run)
                except (json.JSONDecodeError, ValueError):
                    continue

        runs.sort(key=lambda r: r.created_at, reverse=True)
        return runs[:limit]

    def append_event(self, run_id: str, event: SwarmEvent) -> None:
        """Append an event to events.jsonl.

        Args:
            run_id: Run identifier.
            event: Event to append.

        Raises:
            FileNotFoundError: If the run directory does not exist.
        """
        rd = self.run_dir(run_id)
        if not rd.exists():
            raise FileNotFoundError(f"Run directory not found: {rd.name}")
        events_file = rd / "events.jsonl"
        with self._write_lock:
            with events_file.open("a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

    def read_events(self, run_id: str, after_index: int = 0) -> list[SwarmEvent]:
        """Read the event log with optional offset for SSE incremental streaming.

        Args:
            run_id: Run identifier.
            after_index: Skip the first N events and return from event N+1 onward.

        Returns:
            List of SwarmEvent instances.
        """
        events_file = self.run_dir(run_id) / "events.jsonl"
        if not events_file.exists():
            return []

        events: list[SwarmEvent] = []
        lines = events_file.read_text(encoding="utf-8").strip().splitlines()
        for line in lines[after_index:]:
            stripped = line.strip()
            if stripped:
                events.append(SwarmEvent.model_validate_json(stripped))
        return events

    def hydrate_run(self, run: SwarmRun) -> SwarmRun:
        """Return a copy of ``run`` with live ``tasks/*.json`` merged in.

        ``run.json`` only gets the full snapshot at start and finalize; the
        per-task files are the live source of truth while execution is in
        flight. Readers (MCP / API / agent tool) call this before serializing
        so callers see the actual task progress instead of the stale snapshot.

        Pure function: no disk writes, returns a new ``SwarmRun`` via
        :meth:`pydantic.BaseModel.model_copy`. Falls back to ``run`` unchanged
        when no task files exist.
        """
        from src.swarm.task_store import TaskStore

        tasks_dir = self.run_dir(run.id) / "tasks"
        if not tasks_dir.exists():
            return run
        live = TaskStore(self.run_dir(run.id)).load_all()
        if not live:
            return run
        by_id = {task.id: task for task in live}
        merged = [by_id.get(task.id, task) for task in run.tasks]
        # Surface any task that only exists in the live store (defensive — DAG
        # validation runs at start_run so it shouldn't happen, but a future
        # caller that mutates the task set will not silently drop tasks).
        seen = {task.id for task in merged}
        merged.extend(task for tid, task in by_id.items() if tid not in seen)
        return run.model_copy(update={"tasks": merged})

    def compute_stale_threshold(self, run: SwarmRun) -> float:
        """Per-run silence budget before a ``running`` run looks abandoned.

        With ``HeartbeatTimer`` wrapping ``registry.execute`` in the swarm
        worker, the events.jsonl tail gets a fresh entry every
        ``SWARM_HEARTBEAT_INTERVAL_S`` (default 3s) while a tool call is
        running. Missing ~10 heartbeats in a row means the host has stopped
        making progress — so the natural threshold is ``heartbeat × 10``
        (≈30s by default).

        We clamp the upper bound to ``max(agent.timeout × (retries+1)) + 60s``
        so a misconfigured / disabled heartbeat (e.g. interval set to 10min)
        cannot push detection latency past the run's own retry budget. And
        we hold a 60s lower bound so a very tight heartbeat doesn't false-
        positive on routine sub-second event gaps.

        Returns:
            Seconds of event silence after which the run should be reaped.
        """
        try:
            interval = float(os.getenv("SWARM_HEARTBEAT_INTERVAL_S", "3.0"))
        except ValueError:
            interval = 3.0
        heartbeat_floor = max(60.0, interval * 10.0)

        agent_budgets = [
            max(1, int(agent.timeout_seconds or 300)) * (max(0, int(agent.max_retries)) + 1)
            for agent in run.agents
        ]
        retry_ceiling = (max(agent_budgets) if agent_budgets else 300) + 60

        return float(max(60.0, min(heartbeat_floor, retry_ceiling)))

    def is_run_stale(self, run: SwarmRun, *, now: datetime | None = None) -> bool:
        """Read-only check: is this ``running`` run silent past its threshold?

        Used by both the read paths (return ``is_stale`` to callers without
        writing) and the reaper (only mark failed when this returns True).
        Returns False for any non-running run so callers don't accidentally
        flag completed/cancelled runs.
        """
        from src.swarm.models import RunStatus

        if run.status != RunStatus.running:
            return False
        last_activity = _last_event_timestamp(self.run_dir(run.id) / "events.jsonl")
        last_activity = last_activity or _parse_iso(run.created_at)
        if last_activity is None:
            return False
        now = now or datetime.now(timezone.utc)
        return (now - last_activity).total_seconds() > self.compute_stale_threshold(run)

    def reconcile_run(self, run: SwarmRun, *, write: bool = True) -> SwarmRun:
        """Single source of truth for "what does this run actually look like".

        Three layered transforms, applied in order to ``run``:

        1. **Hydrate**: merge live ``tasks/*.json`` into ``run.tasks`` so
           callers never see the stale start-of-run snapshot.
        2. **Terminal recovery**: if every task is terminal but ``run.status``
           is still ``running``, derive the real run status from the task
           statuses (all completed → ``completed``; any failed → ``failed``;
           else ``cancelled``) and fill ``final_report`` from the last
           completed task's summary. Handles the "host crashed between the
           last layer sync and finalize" case.
        3. **Stale reap**: if the run is still ``running`` past its
           heartbeat-based threshold, mark non-terminal tasks ``failed`` with
           a diagnostic error and the run ``failed``.

        ``write=True`` persists any state change to ``run.json`` /
        ``tasks/*.json`` and appends a recovery event. ``write=False`` returns
        the reconciled view in memory only — used by ``list_runs`` so a
        20-row listing doesn't fire 20 disk writes (the next read of any
        affected row will persist if needed).

        Args:
            run: The ``SwarmRun`` loaded from ``run.json``.
            write: Persist recovered state if it differs from on-disk.

        Returns:
            Reconciled ``SwarmRun`` (a new instance — original is not mutated).
        """
        from src.swarm.models import RunStatus, TaskStatus

        hydrated = self.hydrate_run(run)
        now = datetime.now(timezone.utc)
        terminal_run = {RunStatus.completed, RunStatus.failed, RunStatus.cancelled}
        terminal_task = {TaskStatus.completed, TaskStatus.failed, TaskStatus.cancelled}

        if hydrated.status in terminal_run:
            return hydrated

        all_terminal = bool(hydrated.tasks) and all(t.status in terminal_task for t in hydrated.tasks)
        if all_terminal:
            recovered = self._recover_terminal(hydrated, now=now)
            if write and recovered is not hydrated:
                self._persist_recovery(recovered, kind="run_recovered_terminal", reason="all tasks terminal")
            return recovered

        if self.is_run_stale(hydrated, now=now):
            reaped = self._reap_stale(hydrated, now=now)
            if write and reaped is not hydrated:
                threshold = int(self.compute_stale_threshold(hydrated))
                self._persist_recovery(
                    reaped,
                    kind="run_reaped",
                    reason=f"no event for >{threshold}s; host process likely exited",
                    extra={"stale_seconds": threshold},
                )
            return reaped

        return hydrated

    def _recover_terminal(self, run: SwarmRun, *, now: datetime) -> SwarmRun:
        """Pure: derive a terminal SwarmRun from already-terminal tasks."""
        from src.swarm.models import RunStatus, TaskStatus

        statuses = {t.status for t in run.tasks}
        if statuses <= {TaskStatus.completed}:
            new_status = RunStatus.completed
        elif TaskStatus.failed in statuses:
            new_status = RunStatus.failed
        elif statuses <= {TaskStatus.cancelled, TaskStatus.completed}:
            new_status = RunStatus.cancelled
        else:
            new_status = RunStatus.failed

        final_report = run.final_report
        if new_status == RunStatus.completed and not final_report:
            for task in reversed(run.tasks):
                if task.summary:
                    final_report = task.summary
                    break

        return run.model_copy(
            update={
                "status": new_status,
                "completed_at": run.completed_at or now.isoformat(),
                "final_report": final_report,
            }
        )

    def _reap_stale(self, run: SwarmRun, *, now: datetime) -> SwarmRun:
        """Pure: mark non-terminal tasks failed; derive run status from tasks."""
        from src.swarm.models import TaskStatus

        terminal_task = {TaskStatus.completed, TaskStatus.failed, TaskStatus.cancelled}
        last_event_at = _last_event_timestamp(self.run_dir(run.id) / "events.jsonl")
        threshold = int(self.compute_stale_threshold(run))
        error_msg = (
            f"Run reaped: no event for >{threshold}s "
            f"(last event at {last_event_at.isoformat() if last_event_at else 'never'}); "
            "host process likely exited before completion."
        )

        updated_tasks = []
        for task in run.tasks:
            if task.status in terminal_task:
                updated_tasks.append(task)
            else:
                updated_tasks.append(
                    task.model_copy(
                        update={
                            "status": TaskStatus.failed,
                            "error": error_msg,
                            "completed_at": now.isoformat(),
                        }
                    )
                )

        # Same derivation as terminal recovery — if every task happened to be
        # completed before the host died, the run is completed, not failed.
        post = run.model_copy(update={"tasks": updated_tasks})
        return self._recover_terminal(post, now=now)

    def _persist_recovery(
        self,
        run: SwarmRun,
        *,
        kind: str,
        reason: str,
        extra: dict | None = None,
    ) -> None:
        """Write a reconciled SwarmRun back to disk and append a recovery event.

        Idempotent: when a recovery event of the same kind already exists,
        the disk update still runs (so duplicate readers converge) but no
        second event is appended.
        """
        from src.swarm.task_store import TaskStore

        try:
            task_store = TaskStore(self.run_dir(run.id))
            for task in run.tasks:
                task_store.save_task(task)
            self.update_run(run)
        except Exception:  # pragma: no cover — best-effort sweep
            logger = __import__("logging").getLogger(__name__)
            logger.warning("Failed to persist reconciliation for run %s", run.id, exc_info=True)
            return

        existing = self.read_events(run.id)
        if any(e.type == kind for e in existing):
            return
        try:
            data = {"reason": reason}
            if extra:
                data.update(extra)
            self.append_event(
                run.id,
                SwarmEvent(
                    type=kind,
                    data=data,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
            )
        except Exception:  # pragma: no cover
            pass

    def reap_stale_running_runs(self) -> list[str]:
        """Sweep all run directories and reconcile each one.

        Returns IDs of runs whose status flipped from ``running`` to a
        terminal status — useful for log/telemetry and for the explicit
        ``reap_stale_runs`` MCP tool.
        """
        from src.swarm.models import RunStatus

        if not self.base_dir.exists():
            return []

        reaped: list[str] = []
        for entry in self.base_dir.iterdir():
            if not entry.is_dir():
                continue
            run = self.load_run(entry.name)
            if run is None or run.status != RunStatus.running:
                continue
            reconciled = self.reconcile_run(run, write=True)
            if reconciled.status != RunStatus.running:
                reaped.append(run.id)
        return reaped

    def _atomic_write(self, path: Path, content: str) -> None:
        """Atomically write a file: write to .tmp then rename.

        Args:
            path: Target file path.
            content: File content.
        """
        tmp_path = path.with_suffix(".tmp")
        with self._write_lock:
            tmp_path.write_text(content, encoding="utf-8")
            _replace_with_retry(tmp_path, path)
