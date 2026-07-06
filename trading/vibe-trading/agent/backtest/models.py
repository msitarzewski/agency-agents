"""Shared data models for backtest engines.

Immutable dataclasses for positions, trades, and equity snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Position:
    """An open position in a single instrument.

    Args:
        symbol: Instrument identifier.
        direction: 1 for long, -1 for short.
        entry_price: Execution price at entry.
        entry_time: Timestamp when position was opened.
        size: Number of shares / coins.
        leverage: Effective leverage (1 for spot/stocks).
        entry_bar_idx: Index in the dates array at entry (for holding_bars).
        entry_commission: Commission paid at entry.
    """

    symbol: str
    direction: int
    entry_price: float
    entry_time: pd.Timestamp
    size: float
    leverage: float = 1.0
    entry_bar_idx: int = 0
    entry_commission: float = 0.0


@dataclass(frozen=True)
class TradeRecord:
    """A completed round-trip trade.

    Args:
        symbol: Instrument identifier.
        direction: 1 for long, -1 for short.
        entry_price: Entry execution price.
        exit_price: Exit execution price.
        entry_time: Entry timestamp.
        exit_time: Exit timestamp.
        size: Number of shares / coins traded.
        leverage: Effective leverage.
        pnl: Realised profit/loss in cash terms.
        pnl_pct: Realised P&L as percentage of margin.
        exit_reason: Why closed (signal / liquidation / end_of_backtest).
        holding_bars: Number of bars held.
        commission: Total commission (entry + exit).
    """

    symbol: str
    direction: int
    entry_price: float
    exit_price: float
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    size: float
    leverage: float
    pnl: float
    pnl_pct: float
    exit_reason: str
    holding_bars: int
    commission: float


@dataclass(frozen=True)
class EquitySnapshot:
    """Portfolio state at a single point in time.

    Args:
        timestamp: Bar timestamp.
        capital: Free cash.
        unrealized: Total unrealised P&L across all positions.
        equity: capital + margin_in_use + unrealized.
        positions: Number of open positions.
    """

    timestamp: pd.Timestamp
    capital: float
    unrealized: float
    equity: float
    positions: int
