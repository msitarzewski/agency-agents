"""Tests for the swarm-run retry path (MCP ``retry_run`` tool + HTTP endpoint).

Retry re-launches a brand-new run with the same preset/variables as a prior
``failed`` / ``cancelled`` / stale run, leaving the original untouched. A
still-``running`` run must be refused so we never fork an active run.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import mcp_server
import src.swarm.runtime as rt
from src.swarm.models import RunStatus, SwarmAgentSpec, SwarmRun, SwarmTask, TaskStatus
from src.swarm.store import SwarmStore
from src.swarm.task_store import TaskStore


def _make_run(run_id: str, status: RunStatus) -> SwarmRun:
    agent = SwarmAgentSpec(id="analyst", role="Analyst", system_prompt="x", timeout_seconds=300)
    task = SwarmTask(id="t1", agent_id="analyst", prompt_template="do x")
    run = SwarmRun(
        id=run_id,
        preset_name="demo",
        created_at=datetime.now(timezone.utc).isoformat(),
        agents=[agent],
        tasks=[task],
        user_vars={"target": "AAPL.US"},
    )
    run.status = status
    return run


def test_retry_run_missing_returns_error(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.retry_run("does-not-exist"))

    assert payload["status"] == "error"
    assert "not found" in payload["error"].lower()


def test_retry_run_rejects_path_shaped_run_id(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.retry_run("../outside/victim"))

    assert payload["status"] == "error"
    assert "run_id" in payload["error"]


def test_retry_run_refuses_running_run(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    run = _make_run("r-running", RunStatus.running)
    store.create_run(run)
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.retry_run("r-running"))

    assert payload["status"] == "error"
    assert "running" in payload["error"].lower()


def test_retry_run_relaunches_failed_run_with_same_preset(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    original = _make_run("r-failed", RunStatus.failed)
    store.create_run(original)
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    captured: dict[str, object] = {}

    def fake_start_run(self, preset_name, variables, **kwargs):
        captured["preset_name"] = preset_name
        captured["variables"] = variables
        new = _make_run("r-retry", RunStatus.running)
        new.preset_name = preset_name
        self._store.create_run(new)
        TaskStore(self._store.run_dir(new.id)).save_task(
            new.tasks[0].model_copy(update={"status": TaskStatus.in_progress})
        )
        return new

    monkeypatch.setattr(rt.SwarmRuntime, "start_run", fake_start_run)

    payload = json.loads(mcp_server.retry_run("r-failed"))

    # Same preset + user_vars carried over from the original run.
    assert captured["preset_name"] == "demo"
    assert captured["variables"] == {"target": "AAPL.US"}
    # A fresh run id is returned, not the original.
    assert payload["run_id"] == "r-retry"
    assert payload["status"] == "running"
