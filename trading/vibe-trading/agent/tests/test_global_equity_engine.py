"""Tests for GlobalEquityEngine (US / HK) market rules.

Validates:
  - US: zero commission, fractional shares, low slippage
  - HK: stamp tax bilateral, 100-share lots, levies
  - T+0 for both markets
  - Both directions allowed
"""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.engines.global_equity import GlobalEquityEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bar(close: float = 180.0) -> pd.Series:
    return pd.Series({"close": close, "open": close})


def _us_engine(**overrides) -> GlobalEquityEngine:
    config = {"initial_cash": 500_000}
    config.update(overrides)
    return GlobalEquityEngine(config, market="us")


def _hk_engine(**overrides) -> GlobalEquityEngine:
    config = {"initial_cash": 1_000_000}
    config.update(overrides)
    return GlobalEquityEngine(config, market="hk")


# ---------------------------------------------------------------------------
# can_execute: T+0 both directions
# ---------------------------------------------------------------------------


class TestCanExecute:
    def test_us_long(self) -> None:
        assert _us_engine().can_execute("AAPL.US", 1, _make_bar()) is True

    def test_us_short(self) -> None:
        assert _us_engine().can_execute("AAPL.US", -1, _make_bar()) is True

    def test_us_close(self) -> None:
        assert _us_engine().can_execute("AAPL.US", 0, _make_bar()) is True

    def test_hk_long(self) -> None:
        assert _hk_engine().can_execute("0700.HK", 1, _make_bar()) is True

    def test_hk_short(self) -> None:
        assert _hk_engine().can_execute("0700.HK", -1, _make_bar()) is True


# ---------------------------------------------------------------------------
# round_size: US fractional vs HK lots
# ---------------------------------------------------------------------------


class TestRoundSize:
    def test_us_fractional(self) -> None:
        engine = _us_engine()
        assert engine.round_size(10.567, 180.0) == 10.57

    def test_us_tiny_fraction(self) -> None:
        engine = _us_engine()
        assert engine.round_size(0.005, 180.0) == 0.01

    def test_us_negative_clamps(self) -> None:
        engine = _us_engine()
        assert engine.round_size(-5.0, 180.0) == 0.0

    def test_hk_100_share_lots(self) -> None:
        engine = _hk_engine()
        assert engine.round_size(350.0, 350.0) == 300
        assert engine.round_size(99.0, 350.0) == 0
        assert engine.round_size(500.0, 350.0) == 500

    def test_hk_rounds_down(self) -> None:
        engine = _hk_engine()
        assert engine.round_size(199.0, 80.0) == 100


# ---------------------------------------------------------------------------
# calc_commission: US zero vs HK complex
# ---------------------------------------------------------------------------


class TestCommission:
    def test_us_zero_commission(self) -> None:
        engine = _us_engine()
        comm = engine.calc_commission(100.0, 180.0, 1, is_open=True)
        assert comm == 0.0

    def test_us_zero_both_sides(self) -> None:
        engine = _us_engine()
        assert engine.calc_commission(100.0, 180.0, 1, is_open=True) == 0.0
        assert engine.calc_commission(100.0, 180.0, 1, is_open=False) == 0.0

    def test_hk_has_commission(self) -> None:
        engine = _hk_engine()
        comm = engine.calc_commission(1000, 350.0, 1, is_open=True)
        assert comm > 0

    def test_hk_stamp_tax_bilateral(self) -> None:
        """HK stamp tax charged on both buy and sell."""
        engine = _hk_engine()
        comm_buy = engine.calc_commission(1000, 350.0, 1, is_open=True)
        comm_sell = engine.calc_commission(1000, 350.0, 1, is_open=False)
        # Both should be approximately equal (stamp tax bilateral)
        assert comm_buy == pytest.approx(comm_sell, rel=0.01)

    def test_hk_commission_components(self) -> None:
        """Verify HK commission includes all components."""
        engine = _hk_engine()
        size, price = 1000, 350.0
        notional = size * price  # 350,000
        comm = engine.calc_commission(size, price, 1, is_open=True)
        # Expected components:
        expected = (
            notional * engine.hk_commission      # broker ~¥52.5
            + notional * engine.hk_stamp_tax     # stamp ~¥350
            + notional * engine.hk_levy          # SFC+FRC ~¥19.8
            + notional * engine.hk_settlement    # CCASS ~¥7
        )
        assert comm == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# apply_slippage: US low vs HK moderate
# ---------------------------------------------------------------------------


class TestSlippage:
    def test_us_lower_slippage(self) -> None:
        engine = _us_engine()
        us_slipped = engine.apply_slippage(100.0, 1) - 100.0
        hk_engine = _hk_engine()
        hk_slipped = hk_engine.apply_slippage(100.0, 1) - 100.0
        assert us_slipped < hk_slipped

    def test_us_slippage_rate(self) -> None:
        engine = _us_engine()
        assert engine.apply_slippage(100.0, 1) == pytest.approx(100.05)

    def test_hk_slippage_rate(self) -> None:
        engine = _hk_engine()
        assert engine.apply_slippage(100.0, 1) == pytest.approx(100.1)

    def test_custom_slippage(self) -> None:
        engine = GlobalEquityEngine(
            {"initial_cash": 500_000, "slippage_us": 0.002}, market="us",
        )
        assert engine.apply_slippage(100.0, 1) == pytest.approx(100.2)


# ---------------------------------------------------------------------------
# Market parameter
# ---------------------------------------------------------------------------


class TestMarketParam:
    def test_default_is_us(self) -> None:
        engine = GlobalEquityEngine({"initial_cash": 100_000})
        assert engine.market == "us"

    def test_hk_market(self) -> None:
        engine = GlobalEquityEngine({"initial_cash": 100_000}, market="hk")
        assert engine.market == "hk"
