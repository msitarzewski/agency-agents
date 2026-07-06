"""Curated read/write classification for Shoonya (Finvasia) SDK operations.

Keys are the connector's own operation names. Order-mutating SDK calls are
pinned WRITE so the live gate never treats them as plain reads; anything
unlisted and not a known read is treated as WRITE (fail-closed) by the gate.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Shoonya SDK operation read/write catalog.
SHOONYA_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "get_limits": ToolClass.READ,
    "get_holdings": ToolClass.READ,
    "get_positions": ToolClass.READ,
    "get_order_book": ToolClass.READ,
    "get_trade_book": ToolClass.READ,
    "get_quotes": ToolClass.READ,
    "get_time_price_series": ToolClass.READ,
    "get_daily_price_series": ToolClass.READ,
    "searchscrip": ToolClass.READ,
    "get_security_info": ToolClass.READ,
    # WRITE
    "place_order": ToolClass.WRITE,
    "modify_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
}
