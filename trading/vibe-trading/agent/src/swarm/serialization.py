"""Shared serialization helpers for the swarm read boundaries.

Single source of truth for projecting a :class:`SwarmTask` into the per-task
JSON dict returned by the MCP tools (``run_swarm`` / ``get_swarm_status`` /
``get_run_result``) and the in-process ``run_swarm`` agent tool.

Before this module each boundary hand-maintained its own field allowlist and
all three silently omitted ``SwarmTask.error``: a misconfigured provider
produced ``status="failed"`` with no diagnosable reason anywhere the caller
could see, even though the error was captured on disk (see P04).
"""

from __future__ import annotations

from typing import Any

from src.tools.redaction import redact_internal_paths


def serialize_task(task: Any) -> dict:
    """Project a SwarmTask into its public per-task dict.

    ``error`` and ``iterations`` are always included so a failed or degraded
    task is diagnosable from every read path, not only the on-disk artifacts.
    """
    status = task.status.value if hasattr(task.status, "value") else str(task.status)
    return {
        "id": task.id,
        "agent_id": task.agent_id,
        "status": status,
        "summary": task.summary,
        "iterations": getattr(task, "worker_iterations", 0),
        "error": redact_internal_paths(getattr(task, "error", None)) or None,
        "started_at": getattr(task, "started_at", None),
        "completed_at": getattr(task, "completed_at", None),
        "depends_on": list(getattr(task, "depends_on", []) or []),
        "blocked_by": list(getattr(task, "blocked_by", []) or []),
    }


def run_level_error(run: Any) -> str | None:
    """First failed task's error, for a top-level ``error`` field.

    Returns ``None`` (an explicit null, not an absent key) when no task carries
    an error, so a caller that only reads the top level still gets a signal.
    """
    for task in getattr(run, "tasks", None) or []:
        err = getattr(task, "error", None)
        if err:
            return f"{task.id}/{task.agent_id}: {redact_internal_paths(err)}"
    return None
