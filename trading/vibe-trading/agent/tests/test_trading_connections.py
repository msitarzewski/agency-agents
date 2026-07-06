"""Tests for connector-first trading profile operations."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.trading import profiles, service
from src.tools import build_registry
from src.tools.trading_connector_tool import TradingSelectConnectionTool

pytestmark = pytest.mark.unit


def _agent_config(server) -> SimpleNamespace:
    return SimpleNamespace(mcp_servers={"robinhood": server})


def test_remote_call_requires_enabled_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generic remote reads must respect the operator MCP allowlist."""
    server = SimpleNamespace(
        url="https://agent.robinhood.com/mcp/trading",
        enabled_tools=["get_account"],
        auth=SimpleNamespace(cache_dir="/tmp/vibe-no-token"),
    )
    monkeypatch.setattr("src.config.loader.load_agent_config", lambda: _agent_config(server))
    monkeypatch.setattr("src.live.registry.has_cached_oauth_token", lambda *_: True)

    result = service.get_positions("robinhood-live-mcp")

    assert result["status"] == "error"
    assert "not enabled" in result["error"]


def test_remote_call_requires_cached_oauth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generic remote reads must not trigger OAuth from tool/API/MCP paths."""
    server = SimpleNamespace(
        url="https://agent.robinhood.com/mcp/trading",
        enabled_tools=["get_positions"],
        auth=SimpleNamespace(cache_dir="/tmp/vibe-no-token"),
    )
    monkeypatch.setattr("src.config.loader.load_agent_config", lambda: _agent_config(server))
    monkeypatch.setattr("src.live.registry.has_cached_oauth_token", lambda *_: False)

    result = service.get_positions("robinhood-live-mcp")

    assert result["status"] == "not_authorized"
    assert "connector authorize robinhood-live-mcp" in result["error"]


def test_ibkr_official_profile_does_not_advertise_unknown_generic_reads() -> None:
    """IBKR official MCP stays honest until stable remote tool names are known."""
    profile = profiles.profile_by_id("ibkr-live-official-mcp-readonly")

    assert profile.capabilities == ("mcp.read.discovery",)
    result = service.get_account(profile.id)
    assert result["status"] == "error"
    assert "does not support" in result["error"]


def test_connector_profile_id_for_broker_prefers_live_remote_mcp() -> None:
    """Broker on-ramps should resolve through the centralized profile registry."""
    assert service.connector_profile_id_for_broker("robinhood") == "robinhood-live-mcp"
    assert service.connector_profile_id_for_broker("ibkr") == "ibkr-live-official-mcp-readonly"
    assert service.connector_profile_id_for_broker("futurebroker") == "futurebroker-live-mcp"


def test_select_connection_tool_returns_canonical_profile_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Selecting a profile should persist and return the canonical id."""
    monkeypatch.setattr(profiles, "get_runtime_root", lambda: tmp_path)

    result = TradingSelectConnectionTool().execute(connection="IBKR-PAPER-LOCAL")

    assert result
    payload = json.loads(result)
    assert payload["status"] == "ok"
    assert payload["selected_profile"] == "ibkr-paper-local"
    assert profiles.load_selected_profile_id() == "ibkr-paper-local"


def test_live_broker_mcp_wrappers_are_hidden_from_agent_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Connector-first registry must not expose broker-specific mcp_* tools."""
    server = SimpleNamespace(
        url="https://agent.robinhood.com/mcp/trading",
        enabled_tools=["get_positions"],
        auth=SimpleNamespace(cache_dir="/tmp/vibe-token"),
    )
    agent_config = SimpleNamespace(mcp_servers={"robinhood": server})
    monkeypatch.setattr("src.live.registry.is_live_broker", lambda *_: True)
    monkeypatch.setattr("src.live.registry.should_register_live_channel", lambda **_: True)

    def fail_build_wrappers(*_, **__):
        raise AssertionError("live broker wrappers should not be registered directly")

    monkeypatch.setattr("src.tools.mcp.build_mcp_tool_wrappers", fail_build_wrappers)

    registry = build_registry(agent_config=agent_config, include_shell_tools=False)

    assert "trading_positions" in registry.tool_names
    assert not any(name.startswith("mcp_robinhood_") for name in registry.tool_names)
