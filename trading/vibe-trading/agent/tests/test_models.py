"""Tests for backtest data models (Position, TradeRecord, EquitySnapshot)."""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.models import EquitySnapshot, Position, TradeRecord


class TestPosition:
    def test_creation(self) -> None:
        pos = Position(
            symbol="AAPL.US",
            direction=1,
            entry_price=150.0,
            entry_time=pd.Timestamp("2025-01-02"),
            size=100.0,
        )
        assert pos.symbol == "AAPL.US"
        assert pos.direction == 1
        assert pos.leverage == 1.0  # default

    def test_frozen(self) -> None:
        pos = Position(
            symbol="AAPL.US",
            direction=1,
            entry_price=150.0,
            entry_time=pd.Timestamp("2025-01-02"),
            size=100.0,
        )
        with pytest.raises(AttributeError):
            pos.size = 200.0  # type: ignore[misc]

    def test_leverage_default(self) -> None:
        pos = Position("BTC-USDT", -1, 60000.0, pd.Timestamp("2025-01-01"), 0.5)
        assert pos.leverage == 1.0

    def test_leverage_custom(self) -> None:
        pos = Position("BTC-USDT", -1, 60000.0, pd.Timestamp("2025-01-01"), 0.5, leverage=10.0)
        assert pos.leverage == 10.0


class TestTradeRecord:
    def test_creation(self) -> None:
        trade = TradeRecord(
            symbol="000001.SZ",
            direction=1,
            entry_price=15.0,
            exit_price=16.0,
            entry_time=pd.Timestamp("2025-01-02"),
            exit_time=pd.Timestamp("2025-01-10"),
            size=1000.0,
            leverage=1.0,
            pnl=1000.0,
            pnl_pct=0.0667,
            exit_reason="signal",
            holding_bars=6,
            commission=12.5,
        )
        assert trade.pnl == 1000.0
        assert trade.exit_reason == "signal"

    def test_frozen(self) -> None:
        trade = TradeRecord(
            "X", 1, 10.0, 11.0,
            pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-02"),
            100.0, 1.0, 100.0, 0.1, "signal", 1, 0.0,
        )
        with pytest.raises(AttributeError):
            trade.pnl = 999.0  # type: ignore[misc]


class TestEquitySnapshot:
    def test_creation(self) -> None:
        snap = EquitySnapshot(
            timestamp=pd.Timestamp("2025-06-15"),
            capital=900_000.0,
            unrealized=50_000.0,
            equity=950_000.0,
            positions=3,
        )
        assert snap.equity == 950_000.0
        assert snap.positions == 3

    def test_frozen(self) -> None:
        snap = EquitySnapshot(pd.Timestamp("2025-01-01"), 1e6, 0.0, 1e6, 0)
        with pytest.raises(AttributeError):
            snap.capital = 0.0  # type: ignore[misc]
