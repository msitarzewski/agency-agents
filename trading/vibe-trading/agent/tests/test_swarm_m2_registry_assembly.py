"""M2 — SWARM external MCP tools: registry assembly regression tests.

Covers requirements R-01, R-02, R-03 and tests T-04, T-05, T-06, T-07 in
``docs/2026-05-25_swarm_mcp_tools_tdd.md``. M2 introduces
``build_swarm_registry`` — the per-worker registry-builder that merges local
tools with remote MCP wrappers from ``agent_config.mcp_servers`` and then
filters the result through the agent's ``tools:`` whitelist.

The contract this file defends:

  * Local tools listed in the agent whitelist are still resolved as before.
  * Remote MCP tools listed in the whitelist AND surfaced by the boot allowlist
    are wrapped and returned.
  * Remote MCP tools listed in the whitelist but NOT surfaced (server missing,
    ``enabled_tools`` doesn't permit them, or no ``agent_config``) are dropped
    with an operator-facing warning instead of crashing the worker.
  * Remote tools surfaced by the server but NOT in the whitelist are filtered
    out — defense-in-depth on top of the per-server ``enabled_tools``.

Tests follow the existing fake-wrappers pattern from
``tests/test_registry_mcp_integration.py`` (patch ``src.tools.mcp.build_mcp_tool_wrappers``)
so we exercise the real ``build_registry`` merge logic without reaching for a
network. The MCP wire protocol stays untouched — we only mock the wrapper
builder, not the adapter or transport.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

from src.config.schema import AgentConfig
from src.tools import build_swarm_registry
from src.tools.mcp import MCPRemoteTool, resolve_mcp_server_tool_name_segments


def _make_agent_config(servers: dict[str, dict[str, Any]]) -> AgentConfig:
    """Build an AgentConfig from a server-name → config-dict map."""
    return AgentConfig.model_validate(
        {"mcpServers": {name: cfg for name, cfg in servers.items()}}
    )


def _make_fake_wrappers(server_name: str, tool_names: list[str]) -> list[MCPRemoteTool]:
    """Build lightweight ``MCPRemoteTool`` stubs without a live adapter.

    Mirrors the helper in ``tests/test_registry_mcp_integration.py`` so M2
    tests behave exactly like the existing main-path MCP regressions.
    """
    wrappers: list[MCPRemoteTool] = []
    for tname in tool_names:
        stub = MagicMock(spec=MCPRemoteTool)
        stub.name = f"mcp_{server_name}_{tname}"
        stub.description = f"Remote {tname}"
        stub.parameters = {"type": "object", "properties": {}, "required": []}
        stub.is_readonly = False
        wrappers.append(stub)
    return wrappers  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# T-04 — happy path: local + remote MCP tool both reachable (R-01)
# --------------------------------------------------------------------------- #


def test_build_swarm_registry_includes_local_and_remote_tools_when_both_whitelisted() -> None:
    """An agent whitelist containing one local and one remote tool yields both.

    The swarm whitelist should be the *only* gate on tool exposure. When the
    boot ``agent_config`` surfaces ``mcp_kb_search`` and the agent's
    ``tools:`` list also names it, both ``read_file`` (local) and
    ``mcp_kb_search`` (remote) must be on the resulting registry. This is the
    primary R-01 contract.
    """
    fake_wrappers = _make_fake_wrappers("kb", ["search"])
    cfg = _make_agent_config({"kb": {"command": "uvx", "args": ["kb-server"]}})

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        registry = build_swarm_registry(
            ["read_file", "mcp_kb_search"],
            agent_config=cfg,
        )

    names = registry.tool_names
    assert "read_file" in names
    assert "mcp_kb_search" in names
    assert len(names) == 2


# --------------------------------------------------------------------------- #
# T-05 — server-side enabled_tools narrows what the whitelist can reach (R-02)
# --------------------------------------------------------------------------- #


def test_build_swarm_registry_drops_whitelisted_tool_when_server_excludes_it(
    caplog,
) -> None:
    """An ``enabled_tools`` allowlist still wins over a permissive whitelist.

    Operators express trust at boot time (``enabled_tools`` on the server
    config). Even if a preset author writes ``mcp_kb_search`` into an agent's
    whitelist, the boot allowlist may only have surfaced ``mcp_kb_fetch`` —
    in which case the worker must run without ``search`` and surface a clear
    operator-facing log line. Crashing or silently exposing a tool the
    operator did not bless are both unacceptable outcomes.
    """
    fake_wrappers = _make_fake_wrappers("kb", ["fetch"])
    cfg = _make_agent_config(
        {
            "kb": {
                "command": "uvx",
                "args": ["kb-server"],
                "enabledTools": ["fetch"],
            }
        }
    )

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        with caplog.at_level(logging.WARNING):
            registry = build_swarm_registry(
                ["mcp_kb_search"],
                agent_config=cfg,
            )

    assert "mcp_kb_search" not in registry.tool_names
    assert registry.tool_names == []
    assert any(
        "mcp_kb_search" in record.message and "unavailable" in record.message
        for record in caplog.records
    ), "Expected operator-facing 'unavailable' warning for dropped MCP tool"


# --------------------------------------------------------------------------- #
# T-06 — no agent_config → MCP-named whitelist entries drop cleanly (R-02, R-03)
# --------------------------------------------------------------------------- #


def test_build_swarm_registry_without_agent_config_drops_mcp_tools(caplog) -> None:
    """``agent_config=None`` keeps swarm strictly local-tool-only.

    Today's behavior must continue to hold when no operator config is wired
    in. A preset that *requests* an ``mcp_*`` tool stays loadable, but the
    actual tool is absent from the registry and a warning is logged so the
    operator can see why.
    """
    with caplog.at_level(logging.WARNING):
        registry = build_swarm_registry(
            ["mcp_kb_search"],
            agent_config=None,
        )

    assert "mcp_kb_search" not in registry.tool_names
    assert registry.tool_names == []
    assert any(
        "mcp_kb_search" in record.message and "unavailable" in record.message
        for record in caplog.records
    )


# --------------------------------------------------------------------------- #
# T-07 — per-agent whitelist filters server tools beyond enabled_tools (S-06)
# --------------------------------------------------------------------------- #


def test_build_swarm_registry_filters_remote_tools_outside_agent_whitelist() -> None:
    """A remote tool surfaced by the server but absent from the whitelist stays out.

    The server may surface ``mcp_kb_search`` and ``mcp_kb_fetch`` via
    ``enabled_tools=["*"]``. If a particular agent only whitelists
    ``mcp_kb_search``, the worker must NOT see ``mcp_kb_fetch``. This is the
    per-worker whitelist invariant — the same protection we already give
    local tools, extended to remote ones.
    """
    fake_wrappers = _make_fake_wrappers("kb", ["search", "fetch"])
    cfg = _make_agent_config(
        {
            "kb": {
                "command": "uvx",
                "args": ["kb-server"],
                "enabledTools": ["*"],
            }
        }
    )

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        registry = build_swarm_registry(
            ["mcp_kb_search"],
            agent_config=cfg,
        )

    assert "mcp_kb_search" in registry.tool_names
    assert "mcp_kb_fetch" not in registry.tool_names


def test_build_swarm_registry_discovers_only_servers_named_by_whitelist() -> None:
    """Remote discovery is limited to MCP servers implied by the whitelist."""
    cfg = _make_agent_config(
        {
            "kb": {"command": "uvx", "args": ["kb-server"]},
            "expensive": {"command": "uvx", "args": ["expensive-server"]},
        }
    )

    def fake_build_mcp_tool_wrappers(server_name, *_args, **_kwargs):
        return _make_fake_wrappers(server_name, ["search"])

    with patch(
        "src.tools.mcp.build_mcp_tool_wrappers",
        side_effect=fake_build_mcp_tool_wrappers,
    ) as build_wrappers:
        registry = build_swarm_registry(
            ["mcp_kb_search"],
            agent_config=cfg,
        )

    assert "mcp_kb_search" in registry.tool_names
    assert [call.args[0] for call in build_wrappers.call_args_list] == ["kb"]


def test_build_swarm_registry_preserves_collision_hash_prefix_after_pruning() -> None:
    """Pruning keeps full-config MCP collision disambiguation stable."""
    cfg = _make_agent_config(
        {
            "foo-bar": {"command": "uvx", "args": ["foo-bar-server"]},
            "foo_bar": {"command": "uvx", "args": ["foo-bar-alt-server"]},
            "expensive": {"command": "uvx", "args": ["expensive-server"]},
        }
    )
    resolved_names = resolve_mcp_server_tool_name_segments(cfg.mcp_servers.keys())
    requested_tool = f"mcp_{resolved_names['foo-bar']}_ping"

    def fake_build_mcp_tool_wrappers(_server_name, *_args, **kwargs):
        return _make_fake_wrappers(kwargs["local_server_name"], ["ping"])

    with patch(
        "src.tools.mcp.build_mcp_tool_wrappers",
        side_effect=fake_build_mcp_tool_wrappers,
    ) as build_wrappers:
        registry = build_swarm_registry(
            [requested_tool],
            agent_config=cfg,
        )

    assert registry.tool_names == [requested_tool]
    assert [call.args[0] for call in build_wrappers.call_args_list] == ["foo-bar"]
    assert build_wrappers.call_args.kwargs["local_server_name"] == resolved_names["foo-bar"]


def test_build_swarm_registry_skips_mcp_discovery_for_local_only_whitelist() -> None:
    """A local-only agent whitelist must not discover any configured MCP server."""
    cfg = _make_agent_config({"kb": {"command": "uvx", "args": ["kb-server"]}})

    with patch("src.tools.mcp.build_mcp_tool_wrappers") as build_wrappers:
        registry = build_swarm_registry(
            ["read_file"],
            agent_config=cfg,
        )

    assert "read_file" in registry.tool_names
    build_wrappers.assert_not_called()


# --------------------------------------------------------------------------- #
# Backward compatibility: empty MCP config behaves like None (R-03)
# --------------------------------------------------------------------------- #


def test_build_swarm_registry_with_empty_mcp_servers_is_local_only() -> None:
    """An ``AgentConfig`` with no servers configured is equivalent to None.

    Operators who keep a swarm-agent.json file but haven't enrolled any MCP
    servers must see today's behavior: local tools resolve as before; any
    ``mcp_*`` whitelist entry drops with a warning. No partial discovery, no
    crash.
    """
    cfg = AgentConfig.model_validate({"mcpServers": {}})

    registry = build_swarm_registry(
        ["read_file"],
        agent_config=cfg,
    )

    assert "read_file" in registry.tool_names
    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_")]
    assert mcp_names == []
