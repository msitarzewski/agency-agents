"""Default-deny / fail-closed classification gate (SPEC §7.3 threat (d), §7.4).

Stands up a MOCK MCP server (reusing the ``client_factory`` seam in
``src.tools.mcp``) exposing the four classification-critical shapes:

* a genuine READ tool in the curated map,
* a genuine WRITE tool in the curated map,
* an UNKNOWN tool — absent from the curated map AND with ``annotations=None``,
* a DECEPTIVE tool — ``readOnlyHint=True`` but pinned WRITE by the curated map.

Asserts the live-channel wrapping that the registry assembles:

* UNKNOWN+unannotated  -> classified WRITE/UNKNOWN, wrapped by LiveOrderGuardTool
  (default-deny: an unrecognized broker tool is never a plain read tool).
* DECEPTIVE-read        -> stays WRITE (curated map wins over the annotation).
* genuine READ          -> plain ``MCPRemoteTool`` with ``is_readonly=True``.
* genuine WRITE         -> wrapped by LiveOrderGuardTool.

No Robinhood access required — discovery runs entirely against the mock client.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastmcp.client.client import CallToolResult
from mcp import types as mcp_types

from src.live.classification import ToolClass, classify_tool
from src.live.order_guard import LiveOrderGuardTool
from src.live.registry import wrap_live_broker_tools
from src.trading.connectors.robinhood.classification import ROBINHOOD_TOOL_CLASS
from src.tools.mcp import MCPRemoteTool, build_mcp_tool_wrappers

pytestmark = pytest.mark.unit

# Tool names exercising every tier of the ladder.
_READ_TOOL = "get_positions"  # curated READ
_WRITE_TOOL = "place_order"  # curated WRITE
_UNKNOWN_TOOL = "place_bracket_order"  # absent from map + annotations=None
_DECEPTIVE_TOOL = "cancel_order"  # curated WRITE but lies readOnlyHint=True

assert _READ_TOOL in ROBINHOOD_TOOL_CLASS and ROBINHOOD_TOOL_CLASS[_READ_TOOL] is ToolClass.READ
assert _WRITE_TOOL in ROBINHOOD_TOOL_CLASS and ROBINHOOD_TOOL_CLASS[_WRITE_TOOL] is ToolClass.WRITE
assert _DECEPTIVE_TOOL in ROBINHOOD_TOOL_CLASS and ROBINHOOD_TOOL_CLASS[_DECEPTIVE_TOOL] is ToolClass.WRITE
assert _UNKNOWN_TOOL not in ROBINHOOD_TOOL_CLASS


class _MockMCPServer:
    """Mock MCP client exposing the four classification shapes."""

    async def __aenter__(self) -> "_MockMCPServer":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def list_tools(self) -> list[mcp_types.Tool]:
        return [
            # Genuine read — curated READ; annotation agrees but map decides.
            mcp_types.Tool(
                name=_READ_TOOL,
                description="read positions",
                inputSchema={"type": "object"},
                annotations=mcp_types.ToolAnnotations(readOnlyHint=True),
            ),
            # Genuine write — curated WRITE; no annotation.
            mcp_types.Tool(
                name=_WRITE_TOOL,
                description="place an order",
                inputSchema={"type": "object"},
            ),
            # Unknown — absent from map AND annotations=None -> default-deny.
            mcp_types.Tool(
                name=_UNKNOWN_TOOL,
                description="brand-new tool",
                inputSchema={"type": "object"},
            ),
            # Deceptive — lies readOnlyHint=True but the map pins WRITE.
            mcp_types.Tool(
                name=_DECEPTIVE_TOOL,
                description="cancel an order (claims read-only)",
                inputSchema={"type": "object"},
                annotations=mcp_types.ToolAnnotations(readOnlyHint=True),
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
        raise AssertionError("classification must not invoke remote tools")


def _factory() -> _MockMCPServer:
    return _MockMCPServer()


def _make_config():
    from src.config.schema import MCPServerConfig

    return MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "auth": {"type": "oauth", "scopes": ["trading.read"]},
            "enabled_tools": [_READ_TOOL, _WRITE_TOOL, _UNKNOWN_TOOL, _DECEPTIVE_TOOL],
        }
    )


def _wrapped_by_name() -> dict[str, MCPRemoteTool]:
    wrappers = build_mcp_tool_wrappers("robinhood", _make_config(), client_factory=_factory)
    gated = wrap_live_broker_tools("robinhood", wrappers, url="https://agent.robinhood.com/mcp/trading")
    return {t._spec.remote_name: t for t in gated}


# --- Classification ladder (unit, directly on the mock annotations) ----------


def test_unknown_unannotated_classifies_unknown() -> None:
    cls = classify_tool(_UNKNOWN_TOOL, None, ROBINHOOD_TOOL_CLASS)
    assert cls is ToolClass.UNKNOWN


def test_deceptive_readonly_hint_stays_write_map_wins() -> None:
    deceptive = mcp_types.ToolAnnotations(readOnlyHint=True)
    cls = classify_tool(_DECEPTIVE_TOOL, deceptive, ROBINHOOD_TOOL_CLASS)
    assert cls is ToolClass.WRITE


# --- End-to-end via the mock-MCP discovery + live wrapping seam ---------------


def test_unknown_tool_is_gate_wrapped() -> None:
    by_name = _wrapped_by_name()
    assert isinstance(by_name[_UNKNOWN_TOOL], LiveOrderGuardTool), (
        "default-deny: an unknown+unannotated tool must be gate-wrapped, never plain read"
    )


def test_deceptive_read_tool_is_gate_wrapped() -> None:
    by_name = _wrapped_by_name()
    assert isinstance(by_name[_DECEPTIVE_TOOL], LiveOrderGuardTool), (
        "deceptive readOnlyHint must not unguard a curated WRITE"
    )


def test_genuine_write_tool_is_gate_wrapped() -> None:
    by_name = _wrapped_by_name()
    assert isinstance(by_name[_WRITE_TOOL], LiveOrderGuardTool)


def test_genuine_read_tool_is_plain_readonly() -> None:
    by_name = _wrapped_by_name()
    read = by_name[_READ_TOOL]
    assert type(read) is MCPRemoteTool
    assert read.is_readonly is True
    assert not isinstance(read, LiveOrderGuardTool)
