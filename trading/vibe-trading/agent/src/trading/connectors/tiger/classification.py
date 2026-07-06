"""Curated read/write classification for Tiger Brokers SDK operations.

The trading layer classifies each connector operation as READ or WRITE so the
live gate can keep writes behind the mandate. Tiger is a direct-SDK connector
(not MCP), so the keys here are the connector's own operation names rather than
remote MCP tool names. Anything not listed and not a known read resolves to
WRITE (fail-closed) when the live gate consults this map.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Tiger SDK operation read/write catalog. Read operations mirror the connector's
#: public read functions; write operations are the order-mutating SDK calls,
#: pinned WRITE so the live gate never treats them as plain reads.
TIGER_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "get_account": ToolClass.READ,
    "get_assets": ToolClass.READ,
    "get_positions": ToolClass.READ,
    "get_open_orders": ToolClass.READ,
    "get_orders": ToolClass.READ,
    "get_filled_orders": ToolClass.READ,
    "get_stock_briefs": ToolClass.READ,
    "get_bars": ToolClass.READ,
    # WRITE
    "place_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
    "modify_order": ToolClass.WRITE,
}
