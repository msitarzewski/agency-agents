"""Curated read/write classification for Longbridge SDK operations.

Keys are the connector's own operation names (Longbridge is a direct-SDK
connector, not MCP). Order-mutating SDK calls are pinned WRITE so the live gate
never treats them as plain reads; anything unlisted and not a known read is
treated as WRITE (fail-closed) by the gate.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Longbridge SDK operation read/write catalog.
LONGBRIDGE_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "account_balance": ToolClass.READ,
    "stock_positions": ToolClass.READ,
    "today_orders": ToolClass.READ,
    "history_orders": ToolClass.READ,
    "today_executions": ToolClass.READ,
    "history_executions": ToolClass.READ,
    "quote": ToolClass.READ,
    "depth": ToolClass.READ,
    "candlesticks": ToolClass.READ,
    # WRITE
    "submit_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
    "replace_order": ToolClass.WRITE,
}
