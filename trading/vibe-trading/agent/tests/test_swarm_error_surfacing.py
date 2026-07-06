"""Regression tests for P04 — a misconfigured LLM provider must surface a
diagnosable error from the swarm read boundaries.

The swarm already captures ``SwarmTask.error`` on disk; the bug was that every
read-side projection hand-maintained a field allowlist that omitted it, so the
caller saw ``status="failed"`` with no reason. These tests drive the *real*
``SwarmRuntime`` / ``SwarmStore`` with an injected worker failure (no network,
no ``.env`` access) and assert the error is BOTH captured AND surfaced.

Pre-fix: ``test_error_captured_*`` passes (capture was never broken);
``test_*_surfaces_error`` FAIL (the swallow). Post-fix: all pass.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import httpx
import pytest
from openai import AuthenticationError

import mcp_server
import src.swarm.runtime as rt
from src.swarm.models import SwarmAgentSpec, SwarmRun, SwarmTask, WorkerResult
from src.swarm.store import SwarmStore
from src.tools.swarm_tool import _format_result


def _run(tmp_path: Path) -> SwarmRun:
    store = SwarmStore(base_dir=tmp_path)
    runtime = rt.SwarmRuntime(store=store)
    agent = SwarmAgentSpec(id="analyst", role="Analyst", system_prompt="x", max_retries=0)
    task = SwarmTask(id="t1", agent_id="analyst", prompt_template="do x")
    run = SwarmRun(
        id="r",
        preset_name="demo",
        created_at="2026-01-01T00:00:00Z",
        agents=[agent],
        tasks=[task],
    )
    store.create_run(run)
    runtime._execute_run(run, threading.Event())
    reloaded = store.load_run(run.id)
    assert reloaded is not None
    return reloaded


@pytest.fixture
def auth_failure(monkeypatch):
    def fake_worker(*a, **k):
        resp = httpx.Response(401, request=httpx.Request("POST", "https://x/v1"))
        exc = AuthenticationError("Error code: 401 - bad key", response=resp, body=None)
        return WorkerResult(
            status="failed",
            summary="",
            error=f"LLM call failed at iteration 0: {exc}",
        )

    monkeypatch.setattr(rt, "run_worker", fake_worker)


def test_error_captured_in_run_json(tmp_path, auth_failure):
    """Capture path must keep working (guards against a future regression)."""
    run = _run(tmp_path)
    assert run.tasks[0].error and "401" in run.tasks[0].error


def test_get_run_result_surfaces_error(tmp_path, auth_failure):
    """get_run_result / get_swarm_status (_run_to_dict) must expose the error."""
    run = _run(tmp_path)
    view = mcp_server._run_to_dict(run)
    assert view.get("error") and "401" in view["error"]
    assert "401" in (view["tasks"][0].get("error") or "")


def test_in_process_tool_surfaces_error(tmp_path, auth_failure):
    """The in-process run_swarm agent tool (_format_result) must expose it too."""
    view = json.loads(_format_result(_run(tmp_path), "demo", {}))
    assert "401" in json.dumps(view)
    assert view.get("error") and "401" in view["error"]


def test_unset_model_runtime_error_surfaces(tmp_path, monkeypatch):
    """A RuntimeError raised above the worker try/except must surface too."""

    def boom(*a, **k):
        raise RuntimeError("LANGCHAIN_MODEL_NAME is not set")

    monkeypatch.setattr(rt, "run_worker", boom)
    run = _run(tmp_path)
    assert "LANGCHAIN_MODEL_NAME" in json.dumps(mcp_server._run_to_dict(run))
