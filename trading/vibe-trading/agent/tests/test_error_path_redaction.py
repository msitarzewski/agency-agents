"""Regression tests for P10 — user-facing errors must not leak internal
absolute filesystem paths (CWE-209 / CWE-497).

Pre-fix: an unknown preset / workspace-escape / missing run dir embedded the
full install path (OS username, .venvs/site-packages topology). Post-fix the
message keeps the actionable bits (name, Available list, the boundary) but
not the absolute path.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

import src.swarm.runtime as rt
from src.swarm.presets import load_preset
from src.swarm.store import SwarmStore
from src.swarm.models import SwarmAgentSpec, SwarmRun, SwarmTask, WorkerResult
from src.tools.path_utils import safe_path

_LEAKS = (str(Path.home()), "site-packages", ".venvs", str(Path.cwd()))


def _assert_no_abs(msg: str):
    for marker in _LEAKS:
        assert marker not in msg, f"leaked {marker!r} in: {msg}"


def test_unknown_preset_does_not_leak_path():
    with pytest.raises(FileNotFoundError) as ei:
        load_preset("nope_xyz_not_a_preset")
    msg = str(ei.value)
    _assert_no_abs(msg)
    assert "nope_xyz_not_a_preset" in msg and "Available" in msg  # still actionable


def test_workspace_escape_does_not_leak_root(tmp_path):
    with pytest.raises(ValueError) as ei:
        safe_path("../../../../etc/passwd", workdir=tmp_path)
    msg = str(ei.value)
    _assert_no_abs(msg)
    assert "escapes the workspace root" in msg


def test_missing_run_dir_does_not_leak_abs(tmp_path):
    store = SwarmStore(base_dir=tmp_path / "runs")
    with pytest.raises(FileNotFoundError) as ei:
        store.update_run(SwarmRun(id="swarm-rid-001", preset_name="demo", created_at="2026-01-01T00:00:00Z"))
    msg = str(ei.value)
    _assert_no_abs(msg)
    assert "swarm-rid-001" in msg  # logical id retained, absolute path dropped


# --- P10 residual: swarm EVENT payloads (read_events / SSE / get_swarm_status)
# also project the raw error. update_status was redacted by G1 but the
# task_failed / run_error events still emitted raw text. These drive the real
# runtime hermetically (no network, no .env) and read the events back.

_ABS_LEAK = str(Path.home())  # an internal root redact_internal_paths anchors on


def _drive_run(tmp_path: Path) -> tuple[SwarmStore, SwarmRun]:
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
    return store, run


def _event_data(store: SwarmStore, run_id: str, event_type: str) -> dict:
    matches = [e for e in store.read_events(run_id) if e.type == event_type]
    assert matches, f"no {event_type!r} event emitted"
    return matches[-1].data


def test_task_failed_event_does_not_leak_abs_path(tmp_path, monkeypatch):
    """task_failed event payload (surfaced via read_events/SSE/get_swarm_status)
    must redact the internal absolute path. Pre-fix: raw result.error → FAIL."""

    def fake_worker(*a, **k):
        return WorkerResult(
            status="failed",
            summary="",
            error=f"worker blew up writing {_ABS_LEAK}/secret/topology.log",
        )

    monkeypatch.setattr(rt, "run_worker", fake_worker)
    store, run = _drive_run(tmp_path)

    err = _event_data(store, run.id, "task_failed")["error"]
    assert _ABS_LEAK not in err, f"leaked abs path in task_failed event: {err}"
    assert "<redacted>" in err  # boundary still actionable (relative tail kept)
    assert "secret/topology.log" in err or "secret\\topology.log" in err


def test_run_error_event_does_not_leak_abs_path(tmp_path, monkeypatch):
    """A run-level exception that escapes the per-layer worker containment
    (caught by the top-level ``except Exception`` in _execute_run) surfaces via
    the run_error event. Worker-raised exceptions are absorbed into a failed
    WorkerResult by _execute_layer, so the run_error branch is only reachable
    by a structural failure of the layer machinery itself — injected here by
    failing _execute_layer. Pre-fix: raw str(exc) → FAIL."""

    def boom(*a, **k):
        raise RuntimeError(f"fatal: config missing under {_ABS_LEAK}/.venvs/cfg")

    monkeypatch.setattr(rt.SwarmRuntime, "_execute_layer", boom)
    store, run = _drive_run(tmp_path)

    err = _event_data(store, run.id, "run_error")["error"]
    assert _ABS_LEAK not in err, f"leaked abs path in run_error event: {err}"
    assert "<redacted>" in err
    assert ".venvs/cfg" in err or ".venvs\\cfg" in err
