"""Curated read/write classification for Alpaca SDK operations.

Keys are the connector's own operation names. Order-mutating SDK calls are
pinned WRITE so the live gate never treats them as plain reads; anything
unlisted and not a known read is treated as WRITE (fail-closed) by the gate.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Alpaca SDK operation read/write catalog.
ALPACA_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "get_account": ToolClass.READ,
    "get_all_positions": ToolClass.READ,
    "get_open_position": ToolClass.READ,
    "get_orders": ToolClass.READ,
    "get_stock_latest_quote": ToolClass.READ,
    "get_stock_bars": ToolClass.READ,
    # WRITE
    "submit_order": ToolClass.WRITE,
    "cancel_order_by_id": ToolClass.WRITE,
    "cancel_orders": ToolClass.WRITE,
}
