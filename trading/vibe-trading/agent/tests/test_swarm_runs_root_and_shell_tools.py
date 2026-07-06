"""Regression tests for P03-A (run-root / store single source of truth) and
P03-B (MCP swarm wrapper must thread include_shell_tools; the filtered
registry must not silently drop a requested tool).

P03-A: the swarm store location and the run-dir sandbox allow-list were each
derived independently as ``<agent_root>/.swarm/runs``. A packaging layout
where the two anchors resolved differently put every worker run_dir outside
the allow-list with no error. They now share ``swarm_runs_root()``.

P03-B: ``mcp_server.run_swarm`` called ``start_run`` without
``include_shell_tools``, so stdio MCP swarm workers silently lost ``bash`` and
could not execute their own scripts.
"""

from __future__ import annotations

import logging
import threading

from src.swarm.models import SwarmAgentSpec, SwarmRun, SwarmTask, WorkerResult
from src.swarm.store import SwarmStore, swarm_runs_root
from src.tools import build_filtered_registry, path_utils
import src.swarm.runtime as rt


# ---- P03-A: single source of truth -----------------------------------------
def test_swarm_runs_root_is_an_allowed_run_root():
    """Whatever swarm_runs_root() returns MUST be inside the sandbox
    allow-list, otherwise every worker run_dir is rejected."""
    allowed = {p.resolve() for p in path_utils._allowed_run_roots()}
    assert swarm_runs_root().resolve() in allowed


def test_default_run_roots_uses_single_source():
    assert swarm_runs_root() in path_utils._default_run_roots()


def test_swarm_runs_root_stable_and_swarm_scoped():
    root = swarm_runs_root()
    assert root == swarm_runs_root()  # deterministic
    assert root.name == "runs" and root.parent.name == ".swarm"


# ---- P03-B: filtered registry must keep / not silently drop tools ----------
def test_filtered_registry_keeps_bash_when_shell_enabled():
    reg = build_filtered_registry(["bash", "read_file", "write_file", "load_skill"], include_shell_tools=True)
    assert "bash" in reg.tool_names


def test_filtered_registry_warns_when_requested_tool_dropped(caplog):
    with caplog.at_level(logging.WARNING):
        reg = build_filtered_registry(["bash", "read_file", "write_file"], include_shell_tools=False)
    assert "bash" not in reg.tool_names
    assert any("bash" in r.message and r.levelno >= logging.WARNING for r in caplog.records), (
        "dropping a requested tool must be logged, not silent"
    )


# ---- P03-B: include_shell_tools propagates to the worker -------------------
def test_execute_run_propagates_include_shell_tools(tmp_path, monkeypatch):
    """mcp_server now passes include_shell_tools into start_run; pin that the
    runtime forwards it all the way to run_worker."""
    captured: dict[str, object] = {}

    def fake_worker(*args, **kwargs):
        captured["include_shell_tools"] = kwargs.get("include_shell_tools")
        return WorkerResult(status="completed", summary="real deliverable: ok")

    monkeypatch.setattr(rt, "run_worker", fake_worker)

    store = SwarmStore(base_dir=tmp_path)
    runtime = rt.SwarmRuntime(store=store)
    agent = SwarmAgentSpec(id="analyst", role="Analyst", system_prompt="x", max_retries=0)
    task = SwarmTask(id="t1", agent_id="analyst", prompt_template="do x")
    run = SwarmRun(id="r", preset_name="demo", created_at="2026-01-01T00:00:00Z", agents=[agent], tasks=[task])
    store.create_run(run)
    runtime._execute_run(run, threading.Event(), include_shell_tools=True)

    assert captured.get("include_shell_tools") is True
