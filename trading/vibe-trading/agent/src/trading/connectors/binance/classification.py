"""Curated read/write classification for Binance (ccxt) spot operations.

Keys are the ccxt unified method names this connector uses. Order-mutating ccxt
calls are pinned WRITE so the live gate never treats them as plain reads;
anything unlisted and not a known read is treated as WRITE (fail-closed) by the
gate.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Binance (ccxt) spot operation read/write catalog.
BINANCE_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "fetch_balance": ToolClass.READ,
    "fetch_open_orders": ToolClass.READ,
    "fetch_my_trades": ToolClass.READ,
    "fetch_ticker": ToolClass.READ,
    "fetch_ohlcv": ToolClass.READ,
    # WRITE
    "create_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
}
