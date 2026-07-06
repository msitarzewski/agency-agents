"""P0-A regression: a DAG with a failed upstream must NOT silently launch
downstream tasks with empty upstream summaries.

Original 5/27 incident: swarm-20260527-183056-2d91b0f2 (investment_committee
preset). risk_officer correctly failed grounding (mock VaR), then portfolio_manager
started 2 ms later with task_summaries['task-risk'] missing — produced a
"decision" with no risk input. This is safety-critical because matt-invest is
wired to a live Questrade account.

Pre-fix: ``test_failed_upstream_blocks_downstream`` FAILS because PM/B runs.
Post-fix: B is marked ``TaskStatus.blocked``, no ``task_started`` for B, and
``task_blocked`` event is emitted.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

import src.swarm.runtime as rt
from src.swarm.models import (
    SwarmAgentSpec,
    SwarmRun,
    SwarmTask,
    TaskStatus,
    WorkerResult,
)
from src.swarm.store import SwarmStore


def _make_run(tmp_path: Path) -> tuple[SwarmStore, rt.SwarmRuntime, SwarmRun]:
    store = SwarmStore(base_dir=tmp_path)
    runtime = rt.SwarmRuntime(store=store)
    agents = [
        SwarmAgentSpec(id="risk", role="risk", system_prompt="x", max_retries=0),
        SwarmAgentSpec(id="pm", role="pm", system_prompt="x", max_retries=0),
    ]
    tasks = [
        SwarmTask(id="task-risk", agent_id="risk", prompt_template="do risk"),
        SwarmTask(
            id="task-pm",
            agent_id="pm",
            prompt_template="do pm",
            depends_on=["task-risk"],
            blocked_by=["task-risk"],
            input_from={"risk": "task-risk"},
        ),
    ]
    run = SwarmRun(
        id="r-p0a",
        preset_name="demo",
        created_at="2026-05-27T18:30:56+00:00",
        agents=agents,
        tasks=tasks,
    )
    store.create_run(run)
    return store, runtime, run


@pytest.fixture
def risk_fails(monkeypatch):
    """Make every worker invocation return status=failed."""

    def fake_worker(agent_spec, task, **kwargs):
        return WorkerResult(
            status="failed",
            summary="",
            error="output contract not met: explicitly fabricated / mock data",
        )

    monkeypatch.setattr(rt, "run_worker", fake_worker)


def test_failed_upstream_blocks_downstream(tmp_path, risk_fails):
    """When task-risk FAILS, task-pm MUST be blocked, not started."""
    store, runtime, run = _make_run(tmp_path)
    runtime._execute_run(run, threading.Event())

    reloaded = store.load_run(run.id)
    assert reloaded is not None

    by_id = {t.id: t for t in reloaded.tasks}
    assert by_id["task-risk"].status == TaskStatus.failed, (
        f"risk should be failed, got {by_id['task-risk'].status}"
    )
    assert by_id["task-pm"].status == TaskStatus.blocked, (
        f"PM must be blocked when risk fails, got {by_id['task-pm'].status} — "
        "this is the 5/27 incident pattern"
    )
    assert by_id["task-pm"].started_at is None, (
        f"PM must NOT have a start timestamp when blocked, got "
        f"{by_id['task-pm'].started_at}"
    )


def test_blocked_downstream_emits_task_blocked_event(tmp_path, risk_fails):
    """Blocked downstream tasks must emit task_blocked, not task_started."""
    store, runtime, run = _make_run(tmp_path)
    runtime._execute_run(run, threading.Event())

    events_file = tmp_path / run.id / "events.jsonl"
    events = [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]

    pm_events = [e for e in events if e.get("task_id") == "task-pm"]
    types = [e["type"] for e in pm_events]
    assert "task_started" not in types, (
        f"PM must never emit task_started when upstream failed; events: {types}"
    )
    assert "task_blocked" in types, (
        f"PM must emit task_blocked when upstream failed; events: {types}"
    )

    blocked_evt = next(e for e in pm_events if e["type"] == "task_blocked")
    assert "task-risk" in blocked_evt.get("data", {}).get("blocked_by", []), (
        f"task_blocked.data.blocked_by must reference upstream task; got {blocked_evt['data']}"
    )
    # CLI live panel (cli/_legacy.py) keys events off agent_id to update the
    # per-agent row — task_blocked without agent_id silently noops the UI.
    assert blocked_evt.get("agent_id") == "pm", (
        f"task_blocked must carry agent_id for CLI live-panel routing; got "
        f"{blocked_evt.get('agent_id')!r}"
    )


def test_run_marked_failed_when_downstream_blocked(tmp_path, risk_fails):
    """The whole run must be RunStatus.failed when any task is blocked."""
    from src.swarm.models import RunStatus

    store, runtime, run = _make_run(tmp_path)
    runtime._execute_run(run, threading.Event())

    reloaded = store.load_run(run.id)
    assert reloaded.status == RunStatus.failed, (
        f"run must be failed when downstream blocked, got {reloaded.status}"
    )
