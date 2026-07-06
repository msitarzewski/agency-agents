"""Curated read/write classification for Futu (futu-api) SDK operations.

The trading layer classifies each connector operation as READ or WRITE so the
live gate can keep writes behind the mandate. Futu is a direct local-SDK
connector (the SDK talks to a local OpenD gateway, not a remote MCP server), so
the keys here are the SDK's own method names rather than remote MCP tool names.
Anything not listed and not a known read resolves to WRITE (fail-closed) when
the live gate consults this map.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Futu SDK operation read/write catalog. Read operations mirror the connector's
#: public read functions; write operations are the order-mutating / trade-unlock
#: SDK calls, pinned WRITE so the live gate never treats them as plain reads.
FUTU_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "accinfo_query": ToolClass.READ,
    "position_list_query": ToolClass.READ,
    "order_list_query": ToolClass.READ,
    "deal_list_query": ToolClass.READ,
    "get_market_snapshot": ToolClass.READ,
    "request_history_kline": ToolClass.READ,
    "get_acc_list": ToolClass.READ,
    # WRITE
    "place_order": ToolClass.WRITE,
    "modify_order": ToolClass.WRITE,
    "unlock_trade": ToolClass.WRITE,
}
