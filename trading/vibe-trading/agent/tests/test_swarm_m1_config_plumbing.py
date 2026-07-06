"""M1 — SWARM external MCP tools: config plumbing regression tests.

Covers requirements R-03, R-05, R-09 and tests T-01, T-02, T-03 in
``docs/2026-05-25_swarm_mcp_tools_tdd.md``. M1 lands the parameter wiring
*only* — no remote tool registry assembly, no boot-time loading. Those land
in M2 / M3 and bring their own tests. The contract this file defends:

  * ``SwarmRuntime`` accepts an optional ``agent_config``.
  * ``agent_config=None`` keeps the existing local-tool-only behavior
    byte-for-byte (no construction surprises, no run-time surprises).
  * When set, the same value reaches ``run_worker`` on every worker call.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.config.schema import AgentConfig, MCPServerConfig
from src.swarm.models import SwarmAgentSpec, SwarmTask, WorkerResult, WorkerStatus
from src.swarm.runtime import SwarmRuntime
from src.swarm.store import SwarmStore


def _make_runtime(tmp_path: Path, **kwargs) -> SwarmRuntime:
    """Build a SwarmRuntime backed by a tmp-path SwarmStore."""
    store = SwarmStore(base_dir=tmp_path / "swarm_runs")
    return SwarmRuntime(store=store, **kwargs)


def _make_agent_spec() -> SwarmAgentSpec:
    """Build a minimal SwarmAgentSpec for direct worker invocation."""
    return SwarmAgentSpec(
        id="test_agent",
        role="Test analyst",
        system_prompt="You are a test agent.",
        tools=["read_file"],
        skills=[],
        max_iterations=1,
        timeout_seconds=5,
        max_retries=0,
    )


def _make_task() -> SwarmTask:
    """Build a minimal SwarmTask bound to ``test_agent``."""
    return SwarmTask(
        id="task-1",
        agent_id="test_agent",
        prompt_template="trivial prompt",
    )


# --------------------------------------------------------------------------- #
# T-01 — backwards-compatible default (R-03, R-05)
# --------------------------------------------------------------------------- #


def test_runtime_default_construction_keeps_agent_config_none(tmp_path: Path) -> None:
    """Default construction (no kwarg) leaves ``_agent_config`` at None.

    Existing callers (``api_server.py``, ``cli/_legacy.py``,
    ``mcp_server.py``, ``swarm_tool.py``) construct ``SwarmRuntime`` without
    the new kwarg. None of them should change behavior in M1.
    """
    runtime = _make_runtime(tmp_path)
    assert runtime._agent_config is None


def test_runtime_explicit_none_construction_is_identical(tmp_path: Path) -> None:
    """Passing ``agent_config=None`` explicitly is equivalent to omitting it."""
    runtime = _make_runtime(tmp_path, agent_config=None)
    assert runtime._agent_config is None


# --------------------------------------------------------------------------- #
# T-02 — forwarding into run_worker (R-05)
# --------------------------------------------------------------------------- #


def test_run_worker_receives_agent_config_from_runtime(tmp_path: Path) -> None:
    """``_run_worker_with_retries`` forwards ``self._agent_config`` to ``run_worker``.

    This is the load-bearing M1 contract: any future M2 registry assembly that
    reads ``agent_config`` from inside ``run_worker`` can rely on the value
    actually reaching it.
    """
    sentinel_config = AgentConfig(
        mcp_servers={
            "internal_kb": MCPServerConfig(
                type="stdio",
                command="/usr/bin/true",
                enabled_tools=["search"],
            )
        }
    )

    runtime = _make_runtime(tmp_path, agent_config=sentinel_config)
    agent_spec = _make_agent_spec()
    task = _make_task()
    run_dir = tmp_path / "run-x"
    run_dir.mkdir()

    fake_result = WorkerResult(status=WorkerStatus.completed, summary="ok")

    with patch("src.swarm.runtime.run_worker", return_value=fake_result) as spy:
        result = runtime._run_worker_with_retries(
            agent_spec=agent_spec,
            task=task,
            upstream_summaries={},
            user_vars={},
            run_dir=run_dir,
            event_callback=None,
            run_id="run-x",
            include_shell_tools=False,
            grounding_block="",
        )

    assert result.status == WorkerStatus.completed
    spy.assert_called_once()
    assert spy.call_args.kwargs["agent_config"] is sentinel_config


def test_run_worker_receives_none_when_runtime_has_no_agent_config(
    tmp_path: Path,
) -> None:
    """Default construction forwards ``agent_config=None`` to ``run_worker``.

    Guarantees that today's behavior (local tools only, no MCP plumbing) is
    preserved when the operator hasn't opted in. Pairs with M5 trust-model
    regressions: a caller cannot silently flip this on.
    """
    runtime = _make_runtime(tmp_path)  # no agent_config kwarg
    agent_spec = _make_agent_spec()
    task = _make_task()
    run_dir = tmp_path / "run-y"
    run_dir.mkdir()

    fake_result = WorkerResult(status=WorkerStatus.completed, summary="ok")

    with patch("src.swarm.runtime.run_worker", return_value=fake_result) as spy:
        runtime._run_worker_with_retries(
            agent_spec=agent_spec,
            task=task,
            upstream_summaries={},
            user_vars={},
            run_dir=run_dir,
            event_callback=None,
            run_id="run-y",
            include_shell_tools=False,
            grounding_block="",
        )

    assert spy.call_args.kwargs["agent_config"] is None


# --------------------------------------------------------------------------- #
# T-03 — lazy discovery: construction with non-None config never crashes
#         even when the configured MCP server would fail to spawn (R-05, R-09)
# --------------------------------------------------------------------------- #


def test_runtime_construction_with_unreachable_mcp_server_does_not_raise(
    tmp_path: Path,
) -> None:
    """A misconfigured MCP server must not break ``SwarmRuntime`` construction.

    Discovery of remote tools is M2's job and must stay lazy: a typo in an
    MCP server command should surface only when that server's tools are
    actually invoked, not at runtime construction time. M1 simply stores the
    config; it must not touch it. This test pins that invariant before M2
    introduces real discovery.
    """
    cfg = AgentConfig(
        mcp_servers={
            "definitely_does_not_exist": MCPServerConfig(
                type="stdio",
                command="/path/that/does/not/exist/mcp_server",
                args=["--no-such-flag"],
                enabled_tools=["*"],
            )
        }
    )

    runtime = _make_runtime(tmp_path, agent_config=cfg)
    assert runtime._agent_config is cfg
    assert "definitely_does_not_exist" in runtime._agent_config.mcp_servers
