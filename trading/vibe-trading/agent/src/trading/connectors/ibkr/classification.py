"""Curated IBKR MCP tool classification overrides.

IBKR's official MCP tool catalog is discovered only after OAuth, so this map is
intentionally sparse. READ tools are expected to come from MCP annotations under
the read-only ``mcp.read`` scope. State-changing names listed here are pinned
WRITE when they appear, and anything not annotated read-only remains UNKNOWN
and therefore fail-closed by the live registry.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Sparse IBKR write catalog. Unknown names still fail closed.
IBKR_TOOL_CLASS: dict[str, ToolClass] = {
    "place_order": ToolClass.WRITE,
    "placeOrder": ToolClass.WRITE,
    "submit_order": ToolClass.WRITE,
    "submitOrder": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
    "cancelOrder": ToolClass.WRITE,
    "modify_order": ToolClass.WRITE,
    "modifyOrder": ToolClass.WRITE,
    "replace_order": ToolClass.WRITE,
    "replaceOrder": ToolClass.WRITE,
}
