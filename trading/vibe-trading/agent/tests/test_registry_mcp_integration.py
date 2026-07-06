"""Integration tests for MCP tool injection into the tool registry (Phase 3)."""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.config.schema import AgentConfig, MCPServerConfig
from src.tools import build_registry
from src.tools.mcp import MCPRemoteTool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_config(servers: dict[str, dict[str, Any]]) -> AgentConfig:
    """Build an AgentConfig from a plain server-name → config-dict map."""
    return AgentConfig.model_validate(
        {"mcpServers": {name: cfg for name, cfg in servers.items()}}
    )


def _make_fake_wrappers(server_name: str, tool_names: list[str]) -> list[MCPRemoteTool]:
    """Build lightweight MCPRemoteTool stubs without a live adapter."""
    adapter = MagicMock()
    adapter.server_name = server_name
    wrappers = []
    for tname in tool_names:
        stub = MagicMock(spec=MCPRemoteTool)
        stub.name = f"mcp_{server_name}_{tname}"
        stub.description = f"Remote {tname}"
        stub.parameters = {"type": "object", "properties": {}, "required": []}
        stub.is_readonly = False
        wrappers.append(stub)
    return wrappers  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Regression: no agent_config → unchanged behaviour
# ---------------------------------------------------------------------------


def test_no_agent_config_produces_no_mcp_tools() -> None:
    """build_registry() with no agent_config must not add any mcp_ tools."""
    registry = build_registry()

    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_")]
    assert mcp_names == [], f"Unexpected MCP tools in registry: {mcp_names}"


def test_empty_mcp_servers_produces_no_mcp_tools() -> None:
    """An AgentConfig with no mcp_servers must behave like no config at all."""
    empty_config = AgentConfig.model_validate({"mcpServers": {}})
    registry = build_registry(agent_config=empty_config)

    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_")]
    assert mcp_names == [], f"Unexpected MCP tools in registry: {mcp_names}"


# ---------------------------------------------------------------------------
# Happy path: MCP tools appear after local tools
# ---------------------------------------------------------------------------


def test_mcp_tools_are_injected_and_come_after_local_tools() -> None:
    """MCP tools must be appended after local tools, preserving local order."""
    fake_wrappers = _make_fake_wrappers("demo", ["price_quote", "search"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        config = _make_agent_config({"demo": {"command": "uvx", "args": []}})
        registry = build_registry(agent_config=config)

    all_names = registry.tool_names
    mcp_names = [n for n in all_names if n.startswith("mcp_")]
    local_names = [n for n in all_names if not n.startswith("mcp_")]

    assert "mcp_demo_price_quote" in mcp_names
    assert "mcp_demo_search" in mcp_names

    # Every local tool must appear before every MCP tool in the ordered list.
    if local_names and mcp_names:
        last_local_idx = max(all_names.index(n) for n in local_names)
        first_mcp_idx = min(all_names.index(n) for n in mcp_names)
        assert last_local_idx < first_mcp_idx, (
            "MCP tools must come after all local tools in the registry"
        )


def test_mcp_tools_registration_order_matches_config_order() -> None:
    """Tools from the same server are registered in discovery order."""
    fake_wrappers = _make_fake_wrappers("alpha", ["tool_a", "tool_b", "tool_c"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        config = _make_agent_config({"alpha": {"command": "uvx", "args": []}})
        registry = build_registry(agent_config=config)

    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_alpha_")]
    assert mcp_names == ["mcp_alpha_tool_a", "mcp_alpha_tool_b", "mcp_alpha_tool_c"]


def test_colliding_sanitized_server_names_receive_stable_unique_prefixes() -> None:
    """Different raw server names that sanitize identically must still stay unique."""

    def _wrapper_factory(
        server_name: str,
        server_config: MCPServerConfig,
        *,
        local_server_name: str | None = None,
        **_kw: Any,
    ):
        del server_name, server_config
        assert local_server_name is not None
        return _make_fake_wrappers(local_server_name, ["search"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", side_effect=_wrapper_factory):
        config = _make_agent_config({
            "foo-bar": {"command": "uvx", "args": []},
            "foo_bar": {"command": "uvx", "args": []},
        })
        registry = build_registry(agent_config=config)

    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_foo_bar_")]
    assert len(mcp_names) == 2
    assert len(set(mcp_names)) == 2
    assert "mcp_foo_bar_search" not in mcp_names
    assert all(name.endswith("_search") for name in mcp_names)


# ---------------------------------------------------------------------------
# is_readonly enforcement
# ---------------------------------------------------------------------------


def test_mcp_tools_are_not_readonly() -> None:
    """All MCP tools injected into the registry must have is_readonly=False."""
    fake_wrappers = _make_fake_wrappers("srv", ["query"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        config = _make_agent_config({"srv": {"command": "uvx", "args": []}})
        registry = build_registry(agent_config=config)

    mcp_tools = [registry.get(n) for n in registry.tool_names if n.startswith("mcp_")]
    assert mcp_tools, "Expected at least one MCP tool to be registered"
    for tool in mcp_tools:
        assert tool is not None
        assert tool.is_readonly is False, (
            f"Tool {tool.name} must have is_readonly=False to stay on the serial path"
        )


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------


def test_failed_mcp_server_does_not_block_local_tools(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A server that raises during discovery must be skipped with a warning."""
    with patch(
        "src.tools.mcp.build_mcp_tool_wrappers",
        side_effect=RuntimeError("connection refused"),
    ):
        config = _make_agent_config({"broken": {"command": "uvx", "args": []}})
        with caplog.at_level(logging.WARNING, logger="src.tools"):
            registry = build_registry(agent_config=config)

    # Local tools must still be present.
    assert len(registry) > 0

    # No MCP tools should appear.
    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_")]
    assert mcp_names == []

    # A warning must be emitted naming the skipped server.
    assert any("broken" in record.message for record in caplog.records), (
        "Expected a warning mentioning the skipped server name"
    )


def test_one_failed_server_does_not_affect_other_mcp_servers() -> None:
    """Tools from a healthy server must be registered even if another server fails."""
    good_wrappers = _make_fake_wrappers("good", ["alpha"])

    def _selective_factory(server_name: str, server_config: MCPServerConfig, **_kw: Any):
        if server_name == "broken":
            raise RuntimeError("refused")
        return good_wrappers

    with patch("src.tools.mcp.build_mcp_tool_wrappers", side_effect=_selective_factory):
        config = _make_agent_config({
            "broken": {"command": "uvx", "args": []},
            "good": {"command": "uvx", "args": []},
        })
        registry = build_registry(agent_config=config)

    assert "mcp_good_alpha" in registry.tool_names
    broken_tools = [n for n in registry.tool_names if n.startswith("mcp_broken_")]
    assert broken_tools == []


# ---------------------------------------------------------------------------
# No-config regression: existing call sites unaffected
# ---------------------------------------------------------------------------


def test_build_registry_default_call_is_unchanged() -> None:
    """Calling build_registry() with no kwargs must produce identical results."""
    r1 = build_registry()
    r2 = build_registry(agent_config=None)

    assert set(r1.tool_names) == set(r2.tool_names)


# ---------------------------------------------------------------------------
# Phase 4: warn_callback surfaces server-name collision warnings
# ---------------------------------------------------------------------------


def test_warn_callback_called_on_server_name_collision() -> None:
    """build_registry() must invoke warn_callback when two servers collide after sanitization."""
    received: list[str] = []

    def _wrapper_factory(
        server_name: str,
        server_config: MCPServerConfig,
        *,
        local_server_name: str | None = None,
        **_kw: Any,
    ):
        del server_name, server_config
        return _make_fake_wrappers(local_server_name or "x", ["ping"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", side_effect=_wrapper_factory):
        config = _make_agent_config({
            "foo-bar": {"command": "uvx", "args": []},
            "foo_bar": {"command": "uvx", "args": []},
        })
        build_registry(agent_config=config, warn_callback=received.append)

    assert len(received) > 0, "warn_callback must be called at least once for a collision"
    assert any("foo" in msg for msg in received), (
        "warn_callback message must mention the colliding server name"
    )


def test_warn_callback_not_called_when_no_collision() -> None:
    """build_registry() must NOT invoke warn_callback when server names are unique after sanitization."""
    received: list[str] = []
    fake_wrappers = _make_fake_wrappers("alpha", ["tool_a"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", return_value=fake_wrappers):
        config = _make_agent_config({"alpha": {"command": "uvx", "args": []}})
        build_registry(agent_config=config, warn_callback=received.append)

    assert received == [], f"warn_callback must not fire without a collision; got: {received}"


def test_warn_callback_omitted_still_logs_collision(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When warn_callback is absent, logger.warning must still fire for collisions."""

    def _wrapper_factory(
        server_name: str,
        server_config: MCPServerConfig,
        *,
        local_server_name: str | None = None,
        **_kw: Any,
    ):
        del server_name, server_config
        return _make_fake_wrappers(local_server_name or "x", ["ping"])

    with patch("src.tools.mcp.build_mcp_tool_wrappers", side_effect=_wrapper_factory):
        config = _make_agent_config({
            "foo-bar": {"command": "uvx", "args": []},
            "foo_bar": {"command": "uvx", "args": []},
        })
        with caplog.at_level(logging.WARNING, logger="src.tools"):
            registry = build_registry(agent_config=config)  # no warn_callback — must not raise

    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_")]
    assert len(mcp_names) == 2

    assert any("foo" in record.message for record in caplog.records), (
        "logger.warning must still fire for the collision even without warn_callback"
    )

