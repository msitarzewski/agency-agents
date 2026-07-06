"""Curated read/write classification for OKX SDK operations.

The trading layer classifies each connector operation as READ or WRITE so the
live gate can keep writes behind the mandate. OKX is a direct-SDK connector (not
MCP), so the keys here are the OKX SDK method names rather than remote MCP tool
names. Anything not listed and not a known read resolves to WRITE (fail-closed)
when the live gate consults this map.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: OKX SDK operation read/write catalog. Read operations mirror the connector's
#: public read functions; write operations are the order-mutating SDK calls,
#: pinned WRITE so the live gate never treats them as plain reads.
OKX_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "get_account_balance": ToolClass.READ,
    "get_positions": ToolClass.READ,
    "get_order_list": ToolClass.READ,
    "get_fills": ToolClass.READ,
    "get_ticker": ToolClass.READ,
    "get_candlesticks": ToolClass.READ,
    # WRITE
    "place_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
    "amend_order": ToolClass.WRITE,
}
