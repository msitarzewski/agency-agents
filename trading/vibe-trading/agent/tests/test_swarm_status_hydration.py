"""Regression tests for issue #132 — swarm status visibility & long-run MCP.

Coverage map:

1. ``hydrate_run`` merges live ``tasks/*.json`` and stays side-effect-free.
2. ``get_swarm_status`` surfaces both live progress and an ``is_stale`` flag.
3. ``run_swarm`` supports ``start_only`` and never returns "error" for a
   long-running budget — instead it returns the ``run_id`` so callers
   (or the caller's MCP client, via progress notifications) can pick up.
4. The stale-run reaper uses a per-run threshold (no fixed 1800s) and writes
   ``tasks/*.json`` so the final payload is self-consistent.
5. ``reap_stale_runs`` MCP tool gives users an explicit recovery path that
   does not depend on starting a new run.
6. Layer-boundary snapshot keeps ``run.json`` fresh enough for list_runs.
7. The swarm worker emits ``task_heartbeat`` events while a tool runs so the
   reaper has a precise liveness signal.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
import mcp_server
import src.swarm.runtime as rt
import src.swarm.store as store_mod
import src.swarm.worker as worker_mod
from src.swarm.models import (
    RunStatus,
    SwarmAgentSpec,
    SwarmEvent,
    SwarmRun,
    SwarmTask,
    TaskStatus,
)
from src.swarm.store import SwarmStore
from src.swarm.task_store import TaskStore


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _base_run(run_id: str = "r", *, timeout: int = 300, retries: int = 0) -> SwarmRun:
    agent = SwarmAgentSpec(
        id="analyst",
        role="Analyst",
        system_prompt="x",
        timeout_seconds=timeout,
        max_retries=retries,
    )
    task = SwarmTask(id="t1", agent_id="analyst", prompt_template="do x")
    return SwarmRun(
        id=run_id,
        preset_name="demo",
        created_at=_iso(datetime.now(timezone.utc)),
        agents=[agent],
        tasks=[task],
    )


def _run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


# ---------------------------------------------------------------------------
# 1. hydrate_run
# ---------------------------------------------------------------------------


def test_hydrate_run_merges_live_task_files(tmp_path):
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run()
    run.status = RunStatus.running
    store.create_run(run)

    TaskStore(store.run_dir(run.id)).save_task(
        run.tasks[0].model_copy(
            update={"status": TaskStatus.in_progress, "started_at": _iso(datetime.now(timezone.utc))}
        )
    )

    hydrated = store.hydrate_run(store.load_run(run.id))

    assert hydrated.tasks[0].status == TaskStatus.in_progress
    # Side-effect-free: run.json must still show the original pending state.
    assert store.load_run(run.id).tasks[0].status == TaskStatus.pending


def test_hydrate_run_is_noop_without_task_dir(tmp_path):
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run()
    store.create_run(run)
    (store.run_dir(run.id) / "tasks").rmdir()

    hydrated = store.hydrate_run(store.load_run(run.id))

    assert hydrated.tasks[0].status == TaskStatus.pending


# ---------------------------------------------------------------------------
# 2. get_swarm_status
# ---------------------------------------------------------------------------


def test_get_swarm_status_surfaces_live_progress(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run()
    run.status = RunStatus.running
    store.create_run(run)
    TaskStore(store.run_dir(run.id)).save_task(
        run.tasks[0].model_copy(update={"status": TaskStatus.in_progress})
    )
    store.append_event(
        run.id,
        SwarmEvent(type="task_started", data={}, timestamp=_iso(datetime.now(timezone.utc))),
    )
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.get_swarm_status(run.id))

    assert payload["status"] == "running"
    assert payload["tasks"][0]["status"] == "in_progress"
    assert payload["is_stale"] is False


# ``test_get_swarm_status_flags_silent_run_as_stale`` from v2 was removed in
# v3 — read paths now auto-reconcile, so a zombie surfaces as ``status=failed``
# immediately (see ``test_get_swarm_status_auto_recovers_zombie`` below). The
# ``is_stale`` field remains for the rare transient case where reconciliation
# hasn't yet run, but is no longer a stable observable on a stale zombie.


# ---------------------------------------------------------------------------
# 3. run_swarm async behavior
# ---------------------------------------------------------------------------


def test_run_swarm_start_only_returns_immediately(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "swarm_runs_root", lambda: tmp_path)

    def fake_start_run(self, preset_name, variables, **kwargs):
        run = _base_run("r-start-only")
        run.status = RunStatus.running
        self._store.create_run(run)
        TaskStore(self._store.run_dir(run.id)).save_task(
            run.tasks[0].model_copy(update={"status": TaskStatus.in_progress})
        )
        return run

    monkeypatch.setattr(rt.SwarmRuntime, "start_run", fake_start_run)

    payload = json.loads(
        asyncio.run(mcp_server.run_swarm("demo", {}, start_only=True))
    )

    assert payload["run_id"] == "r-start-only"
    assert payload["status"] == "running"
    assert payload["tasks"][0]["status"] == "in_progress"
    assert payload["timed_out"] is False


def test_run_swarm_wait_zero_returns_run_id_not_error(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "swarm_runs_root", lambda: tmp_path)

    def fake_start_run(self, preset_name, variables, **kwargs):
        run = _base_run("r-wait-zero")
        run.status = RunStatus.running
        self._store.create_run(run)
        return run

    monkeypatch.setattr(rt.SwarmRuntime, "start_run", fake_start_run)

    payload = json.loads(
        asyncio.run(mcp_server.run_swarm("demo", {}, wait_seconds=0))
    )

    assert payload["status"] == "running"
    assert payload["run_id"] == "r-wait-zero"


# ---------------------------------------------------------------------------
# 4. reaper — per-run threshold + writes task files
# ---------------------------------------------------------------------------


def test_reaper_threshold_lifts_when_heartbeat_disabled(tmp_path, monkeypatch):
    """When the user disables heartbeats (interval set very high), the
    threshold must rise so a legitimately slow run isn't false-positive-
    reaped. Conversely the default 3s heartbeat keeps detection at 60s —
    silence past that means the host is genuinely dead."""
    # Disable heartbeat by setting a huge interval; threshold should clamp
    # to the retry ceiling (≤ 3660s for the long-timeout preset).
    monkeypatch.setenv("SWARM_HEARTBEAT_INTERVAL_S", "600")
    store = SwarmStore(base_dir=tmp_path)
    long_run = _base_run("r-long", timeout=1800, retries=1)
    long_run.status = RunStatus.running
    store.create_run(long_run)
    store.append_event(
        long_run.id,
        SwarmEvent(
            type="task_started",
            data={},
            timestamp=_iso(datetime.now(timezone.utc) - timedelta(minutes=40)),
        ),
    )

    threshold = store.compute_stale_threshold(long_run)
    assert threshold == 3660, f"expected retry_ceiling=3660 with heartbeat=600s, got {threshold}"

    # 40 min < 3660s threshold → must not be reaped.
    reaped = store.reap_stale_running_runs()
    assert reaped == []
    assert store.load_run(long_run.id).status == RunStatus.running


def test_reaper_reaps_silent_run_and_writes_task_errors(tmp_path):
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run("r-orphan", timeout=60, retries=0)
    run.status = RunStatus.running
    store.create_run(run)
    TaskStore(store.run_dir(run.id)).save_task(
        run.tasks[0].model_copy(update={"status": TaskStatus.in_progress})
    )
    store.append_event(
        run.id,
        SwarmEvent(
            type="task_started",
            data={},
            timestamp=_iso(datetime.now(timezone.utc) - timedelta(hours=1)),
        ),
    )

    reaped = store.reap_stale_running_runs()

    assert reaped == ["r-orphan"]
    reloaded = store.load_run(run.id)
    assert reloaded.status == RunStatus.failed
    # Task file must reflect the failure so payloads are self-consistent.
    live_task = TaskStore(store.run_dir(run.id)).load_all()[0]
    assert live_task.status == TaskStatus.failed
    assert live_task.error and "reaped" in live_task.error.lower()
    assert live_task.completed_at is not None
    # run_reaped event emitted exactly once.
    assert sum(1 for e in store.read_events(run.id) if e.type == "run_reaped") == 1


def test_reaper_leaves_terminal_tasks_alone(tmp_path):
    """If some tasks already completed before the host died, do not overwrite
    them — only the still-in-flight ones should turn failed."""
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run("r-mixed", timeout=60, retries=0)
    run.tasks.append(SwarmTask(id="t2", agent_id="analyst", prompt_template="do y"))
    run.status = RunStatus.running
    store.create_run(run)
    task_store = TaskStore(store.run_dir(run.id))
    task_store.save_task(run.tasks[0].model_copy(update={"status": TaskStatus.completed, "summary": "ok"}))
    task_store.save_task(run.tasks[1].model_copy(update={"status": TaskStatus.in_progress}))
    store.append_event(
        run.id,
        SwarmEvent(
            type="task_completed",
            data={},
            timestamp=_iso(datetime.now(timezone.utc) - timedelta(hours=1)),
        ),
    )

    store.reap_stale_running_runs()

    by_id = {t.id: t for t in task_store.load_all()}
    assert by_id["t1"].status == TaskStatus.completed
    assert by_id["t1"].summary == "ok"
    assert by_id["t2"].status == TaskStatus.failed


# ---------------------------------------------------------------------------
# 5. reap_stale_runs MCP tool
# ---------------------------------------------------------------------------


def test_reap_stale_runs_mcp_tool(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run("r-tool", timeout=30, retries=0)
    run.status = RunStatus.running
    store.create_run(run)
    store.append_event(
        run.id,
        SwarmEvent(
            type="task_started",
            data={},
            timestamp=_iso(datetime.now(timezone.utc) - timedelta(hours=1)),
        ),
    )
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.reap_stale_runs())

    assert payload == {"reaped": ["r-tool"]}
    assert store.load_run(run.id).status == RunStatus.failed


# ---------------------------------------------------------------------------
# 6. Layer-boundary snapshot keeps run.json fresh
# ---------------------------------------------------------------------------


def test_runtime_layer_boundary_sync_writes_run_json(tmp_path, monkeypatch):
    """After a layer finishes, run.json must show the layer's terminal task
    statuses without needing hydrate."""
    store = SwarmStore(base_dir=tmp_path)
    runtime = rt.SwarmRuntime(store=store, max_workers=1)
    run = _base_run("r-layer", timeout=5, retries=0)
    store.create_run(run)

    def fake_worker(*args, **kwargs):
        from src.swarm.models import WorkerResult
        return WorkerResult(status="completed", summary="ok")

    import threading

    monkeypatch.setattr(rt, "run_worker", fake_worker)
    runtime._execute_run(run, threading.Event())

    # After _execute_run, run.json must reflect the completed task.
    reloaded = store.load_run(run.id)
    assert reloaded.tasks[0].status == TaskStatus.completed


# ---------------------------------------------------------------------------
# 7. Worker heartbeat
# ---------------------------------------------------------------------------


def test_worker_emits_task_heartbeat_during_tool_call():
    """A long-running tool call must emit task_heartbeat swarm events so the
    reaper has a precise liveness signal.

    Drives the same HeartbeatTimer wiring used in worker.py — proves the
    primitive ticks while a synthetic slow tool runs. The full worker pipeline
    needs an LLM + tool registry, which is out of scope for a unit test.
    """
    import time

    from src.agent.progress import HeartbeatTimer

    captured: list[dict] = []
    with HeartbeatTimer(tool_name="slow_tool", interval=0.5, emit=captured.append):
        time.sleep(1.3)

    assert len(captured) >= 2
    assert all(p["tool"] == "slow_tool" for p in captured)


def test_swarm_tool_format_result_preserves_running_status_on_budget_out():
    """_format_result(timed_out=True) must surface the real run status, not
    overwrite it with "timeout". Agents need to know "still running" so they
    can re-invoke with the run_id; the historical "timeout" mask hid that."""
    import src.tools.swarm_tool as swarm_tool

    run = _base_run("r-budget")
    run.status = RunStatus.running

    raw = swarm_tool._format_result(run, "demo", {"target": "AAPL"}, timed_out=True)
    payload = json.loads(raw)

    assert payload["status"] == "running"
    assert payload["wait_budget_exhausted"] is True
    assert payload["run_id"] == "r-budget"


def test_swarm_tool_no_longer_cancels_on_budget_out():
    """Source-level guard: the SwarmTool wait loop must not call cancel_run
    when its budget elapses — that used to throw away in-flight LLM work."""
    import inspect
    import src.tools.swarm_tool as swarm_tool

    source = inspect.getsource(swarm_tool.SwarmTool.execute)
    assert "cancel_run" not in source, (
        "SwarmTool.execute must not cancel the run on budget exhaustion; "
        "return partial state and let the agent decide."
    )


def test_run_swarm_first_progress_frame_carries_run_id(tmp_path, monkeypatch):
    """First Context.report_progress message must include ``swarm_started run_id=<id>``
    so a transport drop still leaves the caller with a recoverable handle."""
    monkeypatch.setattr(store_mod, "swarm_runs_root", lambda: tmp_path)

    def fake_start_run(self, preset_name, variables, **kwargs):
        run = _base_run("r-first-frame")
        run.status = RunStatus.running
        self._store.create_run(run)
        return run

    monkeypatch.setattr(rt.SwarmRuntime, "start_run", fake_start_run)

    progress_calls: list[dict] = []

    class FakeCtx:
        async def report_progress(self, progress, total=None, message=None):
            progress_calls.append({"progress": progress, "total": total, "message": message})

    # Run with very short budget so we exit fast after first frame.
    asyncio.run(
        mcp_server.run_swarm("demo", {}, wait_seconds=1, ctx=FakeCtx())
    )

    assert progress_calls, "expected at least one progress notification"
    first = progress_calls[0]
    assert first["message"].startswith("swarm_started run_id=r-first-frame")


def test_reconcile_run_completes_a_silently_finished_run(tmp_path):
    """All tasks completed in tasks/*.json but run.json still ``running`` —
    a host crash between last layer sync and finalize. Reconcile must NOT
    declare the run failed; it must recover the real terminal status."""
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run("r-silent-done", timeout=60, retries=0)
    run.status = RunStatus.running
    store.create_run(run)
    TaskStore(store.run_dir(run.id)).save_task(
        run.tasks[0].model_copy(
            update={"status": TaskStatus.completed, "summary": "the answer is 42"}
        )
    )

    reconciled = store.reconcile_run(store.load_run(run.id), write=True)

    assert reconciled.status == RunStatus.completed
    assert reconciled.final_report == "the answer is 42"
    # Persisted: a second read shouldn't have to recompute.
    assert store.load_run(run.id).status == RunStatus.completed


def test_reconcile_run_does_not_overwrite_already_terminal(tmp_path):
    """Reconcile must be a no-op for runs that are already terminal —
    don't ever clobber a real completed/failed run."""
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run("r-done", timeout=60, retries=0)
    run.status = RunStatus.completed
    run.final_report = "original report"
    store.create_run(run)
    TaskStore(store.run_dir(run.id)).save_task(
        run.tasks[0].model_copy(update={"status": TaskStatus.completed, "summary": "newer"})
    )

    reconciled = store.reconcile_run(store.load_run(run.id), write=True)

    assert reconciled.status == RunStatus.completed
    assert reconciled.final_report == "original report"


def test_compute_stale_threshold_obeys_heartbeat_floor(tmp_path, monkeypatch):
    """When SWARM_HEARTBEAT_INTERVAL_S is small (default 3s), threshold must
    be the heartbeat floor (60s), not the retry ceiling (3660s for a long-
    timeout preset). Earlier expression was algebraically equivalent to the
    ceiling and ignored heartbeat — defeated detection latency entirely."""
    monkeypatch.setenv("SWARM_HEARTBEAT_INTERVAL_S", "3.0")
    store = SwarmStore(base_dir=tmp_path)
    long_run = _base_run("r-long", timeout=1800, retries=1)  # retry_ceiling = 3660

    threshold = store.compute_stale_threshold(long_run)

    # heartbeat_floor = max(60, 30) = 60.
    # Correct math: max(60, min(60, 3660)) = 60.
    # Buggy math: min(3660, max(60, 3660)) = 3660.
    assert threshold == 60.0, f"expected 60s heartbeat floor, got {threshold}"


def test_get_swarm_status_auto_recovers_zombie(tmp_path, monkeypatch):
    """End-to-end: query a zombie via MCP and the second call sees terminal
    status — not just ``running + is_stale=true``. This is the user-visible
    fix for the core #132 symptom."""
    store = SwarmStore(base_dir=tmp_path)
    run = _base_run("r-zombie", timeout=60, retries=0)
    run.status = RunStatus.running
    store.create_run(run)
    TaskStore(store.run_dir(run.id)).save_task(
        run.tasks[0].model_copy(update={"status": TaskStatus.in_progress})
    )
    # Silent for an hour — past any reasonable threshold.
    store.append_event(
        run.id,
        SwarmEvent(
            type="task_started",
            data={},
            timestamp=_iso(datetime.now(timezone.utc) - timedelta(hours=1)),
        ),
    )
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.get_swarm_status(run.id))

    assert payload["status"] == "failed", "zombie must auto-finalize on read"
    assert payload["tasks"][0]["status"] == "failed"
    assert store.load_run(run.id).status == RunStatus.failed


def test_mcp_run_result_rejects_path_shaped_run_id_without_outside_write(tmp_path, monkeypatch):
    """MCP result lookups must not treat run_id as a filesystem path.

    HTTP swarm routes already reject traversal-shaped run ids; the MCP status
    tools need the same invariant because reads can reconcile and write run
    state back to disk.
    """
    base_dir = tmp_path / "runs"
    outside_dir = tmp_path / "outside" / "victim"
    base_dir.mkdir()
    outside_dir.mkdir(parents=True)
    traversal_id = os.path.relpath(outside_dir, base_dir)
    store = SwarmStore(base_dir=base_dir)
    run = _base_run(traversal_id)
    run.status = RunStatus.running
    run.tasks[0] = run.tasks[0].model_copy(
        update={"status": TaskStatus.completed, "summary": "SAFE_MCP_SWARM_MARKER"}
    )
    (outside_dir / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    payload = json.loads(mcp_server.get_run_result(traversal_id))

    assert payload["status"] == "error"
    assert "run_id" in payload["error"]
    assert not (outside_dir / "tasks").exists()
    assert not (outside_dir / "events.jsonl").exists()


def test_run_swarm_emits_keepalive_every_poll(tmp_path, monkeypatch):
    """Each polling iteration must emit a progress notification, even if the
    task counts haven't changed. Earlier dedup-on-message version emitted
    ``0/1`` once and then went silent for the whole run."""
    monkeypatch.setattr(store_mod, "swarm_runs_root", lambda: tmp_path)

    def fake_start_run(self, preset_name, variables, **kwargs):
        run = _base_run("r-keepalive")
        run.status = RunStatus.running
        self._store.create_run(run)
        TaskStore(self._store.run_dir(run.id)).save_task(
            run.tasks[0].model_copy(update={"status": TaskStatus.in_progress})
        )
        # Fresh event so reconcile won't auto-finalize during the test.
        self._store.append_event(
            run.id,
            SwarmEvent(
                type="task_started",
                data={},
                timestamp=_iso(datetime.now(timezone.utc)),
            ),
        )
        return run

    monkeypatch.setattr(rt.SwarmRuntime, "start_run", fake_start_run)

    progress_calls: list[dict] = []

    class FakeCtx:
        async def report_progress(self, progress, total=None, message=None):
            progress_calls.append({"progress": progress, "total": total, "message": message})

    # Patch asyncio.sleep to avoid actually sleeping in the test.
    real_sleep = asyncio.sleep

    async def fast_sleep(_):
        await real_sleep(0)

    monkeypatch.setattr("asyncio.sleep", fast_sleep)

    asyncio.run(mcp_server.run_swarm("demo", {}, wait_seconds=3, ctx=FakeCtx()))

    # Expect: 1 swarm_started frame + multiple keepalive frames (≥2 polls).
    keepalive = [c for c in progress_calls if not c["message"].startswith("swarm_started")]
    assert len(keepalive) >= 2, f"expected ≥2 keepalive frames, got {len(keepalive)}"
    # Elapsed should appear in the message so dedup-on-message clients see it move.
    assert any("elapsed" in c["message"] for c in keepalive)


def test_worker_source_wires_heartbeat_around_llm_streaming():
    """LLM call must also be wrapped — slow first-token / reasoning-mode /
    pure-tool-call responses can go 30s+ without text chunks. Earlier
    versions only wrapped registry.execute, leaving a real loophole where
    reconcile_run would mark a healthy run failed mid-LLM-call."""
    import inspect
    import re
    source = inspect.getsource(worker_mod)
    timer_match = re.search(
        r'with HeartbeatTimer\(\s*\n\s*tool_name=f"llm:', source
    )
    timer_idx = timer_match.start() if timer_match else -1
    stream_idx = source.find("llm.stream_chat(", timer_idx)
    assert 0 < timer_idx < stream_idx, (
        "llm.stream_chat must be wrapped in a HeartbeatTimer so the stale-"
        "run reaper can't false-positive a slow LLM call."
    )


def test_heartbeat_interval_env_var_is_robust_to_garbage(monkeypatch):
    """A bad SWARM_HEARTBEAT_INTERVAL_S value must NOT crash worker import.
    Previously a typo (``"abc"``) raised ValueError at module top-level and
    took down every swarm path. Falls back to 3.0s now."""
    monkeypatch.setenv("SWARM_HEARTBEAT_INTERVAL_S", "abc")

    # Force re-evaluation by calling the resolver directly.
    import importlib
    import src.swarm.worker as w
    importlib.reload(w)

    assert w._HEARTBEAT_INTERVAL_S == 3.0


def test_worker_source_wires_heartbeat_around_tool_execute():
    """Belt-and-braces: assert worker.py wraps registry.execute in HeartbeatTimer.

    A pure-source check (no LLM/tool needed) guards against accidental
    refactors that re-expose the silent-tool-call symptom from #132.
    """
    import inspect
    source = inspect.getsource(worker_mod)
    assert "HeartbeatTimer(" in source
    assert "task_heartbeat" in source
    # The wrapping must enclose registry.execute, not sit beside it.
    timer_idx = source.find("with HeartbeatTimer(")
    exec_idx = source.find("registry.execute(", timer_idx)
    next_dedent = source.find("\n        ", exec_idx)  # exit the `with` block
    assert 0 < timer_idx < exec_idx < next_dedent


def test_swarm_tool_forwards_started_and_live_events(monkeypatch):
    """Web chat sessions should receive a status card seed plus live swarm events."""
    import src.tools.swarm_tool as swarm_tool

    run = _base_run("r-web-chat")
    run.status = RunStatus.running
    captured: list[tuple[str, dict]] = []

    class FakeStore:
        def __init__(self, base_dir):
            self.base_dir = base_dir

        def load_run(self, run_id):
            return run if run_id == run.id else None

        def reconcile_run(self, loaded, write=False):
            return loaded

    class FakeRuntime:
        def __init__(self, store, max_workers=4, agent_config=None):
            self._store = store

        def start_run(self, preset, variables, live_callback=None, include_shell_tools=False):
            assert live_callback is not None
            live_callback(
                SwarmEvent(
                    type="task_started",
                    agent_id="analyst",
                    task_id="t1",
                    data={},
                    timestamp=_iso(datetime.now(timezone.utc)),
                )
            )
            return run

    monkeypatch.setattr(swarm_tool, "_MAX_WAIT_SECONDS", 0)
    monkeypatch.setattr(swarm_tool, "_match_preset", lambda prompt: "demo")
    monkeypatch.setattr(swarm_tool, "_build_variables", lambda preset, prompt: {"goal": prompt})
    monkeypatch.setattr("src.config.load_swarm_agent_config", lambda: None)
    monkeypatch.setattr("src.swarm.store.SwarmStore", FakeStore)
    monkeypatch.setattr("src.swarm.runtime.SwarmRuntime", FakeRuntime)

    tool = swarm_tool.SwarmTool(event_callback=lambda etype, data: captured.append((etype, data)))
    payload = json.loads(tool.execute(prompt="analyze AAPL"))

    assert payload["run_id"] == "r-web-chat"
    assert captured[0][0] == "swarm.started"
    assert captured[0][1]["run_id"] == "r-web-chat"
    assert captured[0][1]["agents"][0]["id"] == "analyst"
    assert captured[1][0] == "swarm.event"
    assert captured[1][1]["run_id"] == "r-web-chat"
    assert captured[1][1]["event"]["type"] == "task_started"


def test_swarm_tool_without_session_callback_preserves_plain_runtime(monkeypatch):
    """No session bridge means no live callback is installed."""
    import src.tools.swarm_tool as swarm_tool

    run = _base_run("r-no-session")
    run.status = RunStatus.running

    class FakeStore:
        def __init__(self, base_dir):
            self.base_dir = base_dir

        def load_run(self, run_id):
            return run if run_id == run.id else None

        def reconcile_run(self, loaded, write=False):
            return loaded

    class FakeRuntime:
        def __init__(self, store, max_workers=4, agent_config=None):
            self._store = store

        def start_run(self, preset, variables, live_callback=None, include_shell_tools=False):
            assert live_callback is None
            return run

    monkeypatch.setattr(swarm_tool, "_MAX_WAIT_SECONDS", 0)
    monkeypatch.setattr(swarm_tool, "_match_preset", lambda prompt: "demo")
    monkeypatch.setattr(swarm_tool, "_build_variables", lambda preset, prompt: {"goal": prompt})
    monkeypatch.setattr("src.config.load_swarm_agent_config", lambda: None)
    monkeypatch.setattr("src.swarm.store.SwarmStore", FakeStore)
    monkeypatch.setattr("src.swarm.runtime.SwarmRuntime", FakeRuntime)

    payload = json.loads(swarm_tool.SwarmTool().execute(prompt="analyze AAPL"))

    assert payload["run_id"] == "r-no-session"
    assert payload["status"] == "running"
