"""IBKR official MCP read-only probe wiring.

The IBKR endpoint exposes tool names only after OAuth, so the seed uses a
read-only ``mcp.read`` wildcard probe. These tests keep that narrow exception
from becoming an ungated live-broker wildcard.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastmcp.client.client import CallToolResult
from mcp import types as mcp_types

from src.config.schema import AgentConfig, IBKR_MCP_SERVER_SEED
from src.live.order_guard import LiveOrderGuardTool
from src.live.registry import is_live_broker, wrap_live_broker_tools
from src.tools.mcp import MCPRemoteTool, build_mcp_tool_wrappers

pytestmark = pytest.mark.unit


class _FakeIBKRClient:
    """Mock IBKR MCP client exposing one annotated read and one write."""

    async def __aenter__(self) -> "_FakeIBKRClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def list_tools(self) -> list[mcp_types.Tool]:
        return [
            mcp_types.Tool(
                name="portfolio",
                description="read account portfolio",
                inputSchema={"type": "object"},
                annotations=mcp_types.ToolAnnotations(readOnlyHint=True),
            ),
            mcp_types.Tool(
                name="place_order",
                description="place an order",
                inputSchema={"type": "object"},
                annotations=mcp_types.ToolAnnotations(readOnlyHint=False),
            ),
        ]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: float | int | None = None,
        raise_on_error: bool = False,
    ) -> CallToolResult:
        raise AssertionError("registry assembly must not call tools")


def _factory() -> _FakeIBKRClient:
    return _FakeIBKRClient()


def test_ibkr_seed_validates_as_readonly_probe() -> None:
    cfg = AgentConfig.model_validate({"mcpServers": {"ibkr": IBKR_MCP_SERVER_SEED}})
    server = cfg.mcp_servers["ibkr"]

    assert server.url == "https://api.ibkr.com/v1/api/mcp"
    assert server.auth is not None
    assert server.auth.scopes == ["mcp.read"]
    assert server.enabled_tools == ["*"]


def test_ibkr_alias_url_resolves_to_live_broker_and_wraps_writes() -> None:
    cfg = AgentConfig.model_validate({"mcpServers": {"ib": IBKR_MCP_SERVER_SEED}})
    server = cfg.mcp_servers["ib"]

    assert is_live_broker("ib", server.url)

    wrappers = build_mcp_tool_wrappers("ib", server, client_factory=_factory)
    gated = wrap_live_broker_tools("ib", wrappers, url=server.url)
    by_name = {tool._spec.remote_name: tool for tool in gated}

    assert type(by_name["portfolio"]) is MCPRemoteTool
    assert by_name["portfolio"].is_readonly is True
    assert isinstance(by_name["place_order"], LiveOrderGuardTool)
    assert by_name["place_order"].broker == "ibkr"


def test_ibkr_lookalike_host_is_not_live_broker() -> None:
    assert not is_live_broker("ib", "https://api.ibkr.com.evil.test/v1/api/mcp")
