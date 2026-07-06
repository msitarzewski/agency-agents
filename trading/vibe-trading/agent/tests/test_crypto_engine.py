"""Tests for CryptoEngine market rules.

Validates:
  - 24/7 execution (no direction/time restrictions)
  - Fractional position sizing
  - Maker/Taker fee separation
  - Funding fee settlement (every 8 hours)
  - Forced liquidation (maintenance margin check)
  - Tiered maintenance margin rates
"""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.engines.crypto import CryptoEngine
from backtest.engines._market_hooks import (
    FUNDING_HOURS as _FUNDING_HOURS,
    _TIER_TABLE,
    calc_crypto_funding_fee,
    check_crypto_liquidation,
    _maintenance_rate,
)
from backtest.models import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bar(close: float = 60000.0, open_: float | None = None) -> pd.Series:
    return pd.Series({"close": close, "open": open_ or close})


def _make_engine(**overrides) -> CryptoEngine:
    config = {
        "initial_cash": 100_000,
        "leverage": 10.0,
        "maker_rate": 0.0002,
        "taker_rate": 0.0005,
        "funding_rate": 0.0001,
    }
    config.update(overrides)
    return CryptoEngine(config)


# ---------------------------------------------------------------------------
# can_execute: no restrictions
# ---------------------------------------------------------------------------


class TestCanExecute:
    def test_long_allowed(self) -> None:
        engine = _make_engine()
        assert engine.can_execute("BTC-USDT", 1, _make_bar()) is True

    def test_short_allowed(self) -> None:
        engine = _make_engine()
        assert engine.can_execute("BTC-USDT", -1, _make_bar()) is True

    def test_close_allowed(self) -> None:
        engine = _make_engine()
        assert engine.can_execute("BTC-USDT", 0, _make_bar()) is True


# ---------------------------------------------------------------------------
# round_size: fractional
# ---------------------------------------------------------------------------


class TestRoundSize:
    def test_fractional_preserved(self) -> None:
        engine = _make_engine()
        assert engine.round_size(0.123456, 60000.0) == 0.123456

    def test_six_decimal_precision(self) -> None:
        engine = _make_engine()
        assert engine.round_size(0.1234567890, 60000.0) == pytest.approx(0.123457, abs=1e-7)

    def test_negative_clamps_to_zero(self) -> None:
        engine = _make_engine()
        assert engine.round_size(-0.5, 60000.0) == 0.0


# ---------------------------------------------------------------------------
# calc_commission: maker/taker
# ---------------------------------------------------------------------------


class TestCommission:
    def test_open_uses_taker(self) -> None:
        engine = _make_engine(taker_rate=0.0005, maker_rate=0.0002)
        comm = engine.calc_commission(1.0, 60000.0, 1, is_open=True)
        # 1 BTC × $60000 × 0.0005 = $30
        assert comm == pytest.approx(30.0)

    def test_close_uses_maker(self) -> None:
        engine = _make_engine(taker_rate=0.0005, maker_rate=0.0002)
        comm = engine.calc_commission(1.0, 60000.0, 1, is_open=False)
        # 1 BTC × $60000 × 0.0002 = $12
        assert comm == pytest.approx(12.0)

    def test_taker_higher_than_maker(self) -> None:
        engine = _make_engine()
        open_comm = engine.calc_commission(1.0, 60000.0, 1, is_open=True)
        close_comm = engine.calc_commission(1.0, 60000.0, 1, is_open=False)
        assert open_comm > close_comm


# ---------------------------------------------------------------------------
# apply_slippage
# ---------------------------------------------------------------------------


class TestSlippage:
    def test_long_slippage_increases_price(self) -> None:
        engine = _make_engine(slippage=0.001)
        assert engine.apply_slippage(60000.0, 1) == pytest.approx(60060.0)

    def test_short_slippage_decreases_price(self) -> None:
        engine = _make_engine(slippage=0.001)
        assert engine.apply_slippage(60000.0, -1) == pytest.approx(59940.0)


# ---------------------------------------------------------------------------
# Funding fee
# ---------------------------------------------------------------------------


class TestFundingFee:
    def test_funding_deducted_at_settlement_hour(self) -> None:
        engine = _make_engine(funding_rate=0.0001)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        initial_capital = engine.capital
        bar = _make_bar(close=60000.0)
        ts = pd.Timestamp("2025-01-01 08:00:00")  # settlement hour
        engine.on_bar("BTC-USDT", bar, ts)
        # Long pays: 1.0 × 60000 × 0.0001 × 1(long) = $6
        assert engine.capital == pytest.approx(initial_capital - 6.0)

    def test_non_settlement_hour_applies_daily_fallback(self) -> None:
        """Non-settlement hour still applies funding once per day (daily bar support)."""
        engine = _make_engine(funding_rate=0.0001)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        initial_capital = engine.capital
        bar = _make_bar(close=60000.0)
        ts = pd.Timestamp("2025-01-01 05:00:00")  # not settlement hour
        engine.on_bar("BTC-USDT", bar, ts)
        # Daily fallback: applies once even at non-settlement hour
        assert engine.capital == pytest.approx(initial_capital - 6.0)

    def test_short_receives_funding(self) -> None:
        engine = _make_engine(funding_rate=0.0001)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", -1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        initial_capital = engine.capital
        bar = _make_bar(close=60000.0)
        ts = pd.Timestamp("2025-01-01 08:00:00")
        engine.on_bar("BTC-USDT", bar, ts)
        # Short: direction=-1, fee = notional × rate × direction = negative → capital increases
        assert engine.capital > initial_capital

    def test_no_double_settlement(self) -> None:
        engine = _make_engine(funding_rate=0.0001)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        bar = _make_bar(close=60000.0)
        ts = pd.Timestamp("2025-01-01 08:00:00")
        engine.on_bar("BTC-USDT", bar, ts)
        capital_after_first = engine.capital
        # Call again at same hour — should not deduct again
        engine.on_bar("BTC-USDT", bar, ts)
        assert engine.capital == capital_after_first

    def test_no_funding_without_position(self) -> None:
        engine = _make_engine()
        initial_capital = engine.capital
        bar = _make_bar()
        ts = pd.Timestamp("2025-01-01 08:00:00")
        engine.on_bar("BTC-USDT", bar, ts)
        assert engine.capital == initial_capital

    def test_daily_bars_apply_each_day(self) -> None:
        """Regression: daily bars (all hour=0) must apply funding every day, not just day 1."""
        engine = _make_engine(funding_rate=0.0001)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        bar = _make_bar(close=60000.0)
        initial = engine.capital

        # Day 1
        engine.on_bar("BTC-USDT", bar, pd.Timestamp("2025-01-01"))
        after_day1 = engine.capital
        assert after_day1 < initial  # fee deducted

        # Day 2 (same hour=0, different date)
        engine.on_bar("BTC-USDT", bar, pd.Timestamp("2025-01-02"))
        after_day2 = engine.capital
        assert after_day2 < after_day1  # fee deducted again

        # Day 3
        engine.on_bar("BTC-USDT", bar, pd.Timestamp("2025-01-03"))
        after_day3 = engine.capital
        assert after_day3 < after_day2  # fee deducted again

        # Each day: 1 × 60000 × 0.0001 = $6
        assert initial - after_day3 == pytest.approx(18.0)

    def test_multi_symbol_funding(self) -> None:
        """Each symbol gets independent funding settlement."""
        engine = _make_engine(funding_rate=0.0001)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        engine.positions["ETH-USDT"] = Position(
            "ETH-USDT", 1, 3000.0, pd.Timestamp("2025-01-01"), 10.0, leverage=10.0,
        )
        initial = engine.capital
        bar_btc = _make_bar(close=60000.0)
        bar_eth = _make_bar(close=3000.0)
        ts = pd.Timestamp("2025-01-01 08:00:00")

        engine.on_bar("BTC-USDT", bar_btc, ts)
        after_btc = engine.capital
        engine.on_bar("ETH-USDT", bar_eth, ts)
        after_both = engine.capital

        # BTC: 1 × 60000 × 0.0001 = $6
        # ETH: 10 × 3000 × 0.0001 = $3
        assert initial - after_btc == pytest.approx(6.0)
        assert initial - after_both == pytest.approx(9.0)

    def test_funding_hours_correct(self) -> None:
        assert _FUNDING_HOURS == {0, 8, 16}


# ---------------------------------------------------------------------------
# Liquidation
# ---------------------------------------------------------------------------


class TestLiquidation:
    def test_liquidation_on_large_loss(self) -> None:
        """Position wiped when equity drops below maintenance margin."""
        engine = _make_engine(leverage=10.0)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        # Margin = 1.0 × 60000 / 10 = $6000
        # If price drops to 54500: unrealized = 1 × (54500 - 60000) = -$5500
        # equity_in_pos = 6000 + (-5500) = $500
        # Notional = 1 × 54500 = 54500, maint_rate(54500) = 0.004
        # Maint margin = 54500 × 0.004 = $218
        # $500 > $218 → no liquidation

        # But if price drops to 54000:
        # unrealized = -6000, equity = 0 → clearly liquidated
        bar = _make_bar(close=54000.0)
        ts = pd.Timestamp("2025-01-02")
        engine.on_bar("BTC-USDT", bar, ts)
        assert "BTC-USDT" not in engine.positions
        assert len(engine.trades) == 1
        assert engine.trades[0].exit_reason == "liquidation"

    def test_no_liquidation_when_profitable(self) -> None:
        engine = _make_engine(leverage=10.0)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        bar = _make_bar(close=65000.0)
        ts = pd.Timestamp("2025-01-02")
        engine.on_bar("BTC-USDT", bar, ts)
        assert "BTC-USDT" in engine.positions

    def test_no_liquidation_for_spot(self) -> None:
        """Spot (leverage=1) should never get liquidated."""
        engine = _make_engine(leverage=1.0)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", 1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=1.0,
        )
        bar = _make_bar(close=30000.0)  # 50% drop
        ts = pd.Timestamp("2025-01-02")
        engine.on_bar("BTC-USDT", bar, ts)
        assert "BTC-USDT" in engine.positions

    def test_short_liquidation(self) -> None:
        """Short position liquidated when price rises sharply."""
        engine = _make_engine(leverage=10.0)
        engine.positions["BTC-USDT"] = Position(
            "BTC-USDT", -1, 60000.0, pd.Timestamp("2025-01-01"), 1.0, leverage=10.0,
        )
        # Margin = $6000, unrealized = -1 × 1 × (66500 - 60000) = -$6500
        # equity_in_pos = 6000 - 6500 = -$500 < 0 → liquidated
        bar = _make_bar(close=66500.0)
        ts = pd.Timestamp("2025-01-02")
        engine.on_bar("BTC-USDT", bar, ts)
        assert "BTC-USDT" not in engine.positions


# ---------------------------------------------------------------------------
# Tiered maintenance margin
# ---------------------------------------------------------------------------


class TestMaintenanceRate:
    def test_small_position(self) -> None:
        assert _maintenance_rate(50_000) == 0.004

    def test_medium_position(self) -> None:
        assert _maintenance_rate(300_000) == 0.006

    def test_large_position(self) -> None:
        assert _maintenance_rate(2_000_000) == 0.02

    def test_tier_boundaries(self) -> None:
        assert _maintenance_rate(100_000) == 0.004
        assert _maintenance_rate(100_001) == 0.006

    def test_maximum_tier(self) -> None:
        assert _maintenance_rate(100_000_000) == 0.10
