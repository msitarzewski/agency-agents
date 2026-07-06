"""Curated read/write classification for Dhan SDK operations.

Keys are the connector's own operation names. Order-mutating SDK calls are
pinned WRITE so the live gate never treats them as plain reads; anything
unlisted and not a known read is treated as WRITE (fail-closed) by the gate.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Dhan SDK operation read/write catalog.
DHAN_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "get_fund_limits": ToolClass.READ,
    "get_holdings": ToolClass.READ,
    "get_positions": ToolClass.READ,
    "get_order_list": ToolClass.READ,
    "get_order_by_id": ToolClass.READ,
    "get_trade_book": ToolClass.READ,
    "intraday_daily_candle_data": ToolClass.READ,
    "historical_daily_candle_data": ToolClass.READ,
    "ltp": ToolClass.READ,
    "ohlc": ToolClass.READ,
    "quote": ToolClass.READ,
    "market_depth": ToolClass.READ,
    # WRITE
    "place_order": ToolClass.WRITE,
    "modify_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
    "place_slice_order": ToolClass.WRITE,
}
