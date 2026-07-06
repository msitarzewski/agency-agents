"""Tests for ForexEngine market rules.

Validates:
  - 24x5: no restrictions on direction or timing
  - Zero explicit commission (cost via spread)
  - Spread-based slippage
  - Micro-lot rounding (1000 units)
  - Swap (overnight rollover)
  - Symbol normalization
  - Pip value detection
"""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.engines.forex import (
    ForexEngine,
    _normalize_symbol,
    _pip_value,
    _SPREAD_PIPS,
    STANDARD_LOT,
)
from backtest.engines._market_hooks import _SWAP_LONG
from backtest.models import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bar(close: float = 1.1050, open_: float | None = None) -> pd.Series:
    return pd.Series({"close": close, "open": open_ or close})


def _make_engine(**overrides) -> ForexEngine:
    config = {"initial_cash": 100_000}
    config.update(overrides)
    return ForexEngine(config)


# ---------------------------------------------------------------------------
# Symbol normalization
# ---------------------------------------------------------------------------


class TestNormalize:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("EUR/USD", "EUR/USD"),
            ("EURUSD", "EUR/USD"),
            ("EURUSD.FX", "EUR/USD"),
            ("gbpjpy", "GBP/JPY"),
            ("usd/jpy", "USD/JPY"),
        ],
    )
    def test_normalize(self, raw: str, expected: str) -> None:
        assert _normalize_symbol(raw) == expected


# ---------------------------------------------------------------------------
# Pip values
# ---------------------------------------------------------------------------


class TestPipValue:
    def test_eurusd(self) -> None:
        assert _pip_value("EUR/USD") == 0.0001

    def test_usdjpy(self) -> None:
        assert _pip_value("USD/JPY") == 0.01

    def test_gbpjpy(self) -> None:
        assert _pip_value("GBP/JPY") == 0.01

    def test_audusd(self) -> None:
        assert _pip_value("AUD/USD") == 0.0001


# ---------------------------------------------------------------------------
# can_execute: always allowed
# ---------------------------------------------------------------------------


class TestCanExecute:
    def test_long_allowed(self) -> None:
        engine = _make_engine()
        assert engine.can_execute("EUR/USD", 1, _make_bar()) is True

    def test_short_allowed(self) -> None:
        engine = _make_engine()
        assert engine.can_execute("EUR/USD", -1, _make_bar()) is True

    def test_close_allowed(self) -> None:
        engine = _make_engine()
        assert engine.can_execute("EUR/USD", 0, _make_bar()) is True


# ---------------------------------------------------------------------------
# round_size: micro-lot (1000 units)
# ---------------------------------------------------------------------------


class TestRoundSize:
    def test_rounds_to_micro_lot(self) -> None:
        engine = _make_engine()
        assert engine.round_size(15500.0, 1.1) == 15000

    def test_exact_lot(self) -> None:
        engine = _make_engine()
        assert engine.round_size(100000.0, 1.1) == 100000

    def test_less_than_micro_is_zero(self) -> None:
        engine = _make_engine()
        assert engine.round_size(999.0, 1.1) == 0

    def test_negative_clamps(self) -> None:
        engine = _make_engine()
        assert engine.round_size(-5000.0, 1.1) == 0


# ---------------------------------------------------------------------------
# Commission: zero (cost in spread)
# ---------------------------------------------------------------------------


class TestCommission:
    def test_zero_commission(self) -> None:
        engine = _make_engine()
        assert engine.calc_commission(100000, 1.1, 1, is_open=True) == 0.0

    def test_zero_on_close(self) -> None:
        engine = _make_engine()
        assert engine.calc_commission(100000, 1.1, -1, is_open=False) == 0.0


# ---------------------------------------------------------------------------
# Slippage: half-spread + extra
# ---------------------------------------------------------------------------


class TestSlippage:
    def test_buy_increases_price(self) -> None:
        engine = _make_engine()
        engine._active_symbol = "EUR/USD"
        assert engine.apply_slippage(1.1050, 1) > 1.1050

    def test_sell_decreases_price(self) -> None:
        engine = _make_engine()
        engine._active_symbol = "EUR/USD"
        assert engine.apply_slippage(1.1050, -1) < 1.1050

    def test_symbol_aware_spread(self) -> None:
        """EUR/USD has 1.0 pip spread; half = 0.5 pip + 0.3 slippage."""
        engine = _make_engine(slippage_pips=0.0)  # no extra slippage
        slipped = engine.apply_slippage_for_symbol("EUR/USD", 1.1050, 1)
        pip = 0.0001
        expected = 1.1050 + 0.5 * pip  # half spread
        assert slipped == pytest.approx(expected)

    def test_jpy_pair_pip(self) -> None:
        """JPY pairs have pip = 0.01."""
        engine = _make_engine(slippage_pips=0.0)
        slipped = engine.apply_slippage_for_symbol("USD/JPY", 150.00, 1)
        pip = 0.01
        expected = 150.00 + 0.5 * pip  # half of 1.0 pip spread
        assert slipped == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Swap (overnight rollover)
# ---------------------------------------------------------------------------


class TestSwap:
    def test_swap_applied_once_per_day(self) -> None:
        engine = _make_engine()
        engine.positions["EUR/USD"] = Position(
            symbol="EUR/USD", direction=1, entry_price=1.1050,
            entry_time=pd.Timestamp("2025-06-10"), size=100000,
        )
        initial_capital = engine.capital
        ts = pd.Timestamp("2025-06-10 17:00")
        engine.on_bar("EUR/USD", _make_bar(), ts)
        # Long EUR/USD swap is negative → capital decreases
        swap = _SWAP_LONG.get("EUR/USD", 0)
        expected = initial_capital + 1.0 * swap  # 1 standard lot
        assert engine.capital == pytest.approx(expected, abs=0.1)

    def test_swap_not_applied_twice_same_day(self) -> None:
        engine = _make_engine()
        engine.positions["EUR/USD"] = Position(
            symbol="EUR/USD", direction=1, entry_price=1.1050,
            entry_time=pd.Timestamp("2025-06-10"), size=100000,
        )
        ts = pd.Timestamp("2025-06-10 17:00")
        engine.on_bar("EUR/USD", _make_bar(), ts)
        capital_after_first = engine.capital
        engine.on_bar("EUR/USD", _make_bar(), ts)
        assert engine.capital == capital_after_first

    def test_swap_multi_symbol(self) -> None:
        """Each symbol gets its own daily swap (not shared)."""
        engine = _make_engine()
        engine.positions["EUR/USD"] = Position(
            symbol="EUR/USD", direction=1, entry_price=1.1050,
            entry_time=pd.Timestamp("2025-06-10"), size=100000,
        )
        engine.positions["USD/JPY"] = Position(
            symbol="USD/JPY", direction=1, entry_price=150.00,
            entry_time=pd.Timestamp("2025-06-10"), size=100000,
        )
        initial = engine.capital
        ts = pd.Timestamp("2025-06-10 17:00")
        engine.on_bar("EUR/USD", _make_bar(), ts)
        after_eur = engine.capital
        engine.on_bar("USD/JPY", _make_bar(close=150.0), ts)
        after_both = engine.capital
        # Both symbols should have gotten swap, not just the first
        assert after_both != after_eur

    def test_triple_swap_wednesday(self) -> None:
        """Wednesday gets 3x swap (covers weekend)."""
        engine = _make_engine()
        engine.positions["EUR/USD"] = Position(
            symbol="EUR/USD", direction=1, entry_price=1.1050,
            entry_time=pd.Timestamp("2025-06-10"), size=100000,
        )
        initial = engine.capital
        # 2025-06-11 is a Wednesday
        ts = pd.Timestamp("2025-06-11 17:00")
        engine.on_bar("EUR/USD", _make_bar(), ts)
        swap = _SWAP_LONG.get("EUR/USD", 0)
        expected = initial + 1.0 * swap * 3.0
        assert engine.capital == pytest.approx(expected, abs=0.1)

    def test_swap_disabled(self) -> None:
        engine = _make_engine(swap_enabled=False)
        engine.positions["EUR/USD"] = Position(
            symbol="EUR/USD", direction=1, entry_price=1.1050,
            entry_time=pd.Timestamp("2025-06-10"), size=100000,
        )
        initial = engine.capital
        engine.on_bar("EUR/USD", _make_bar(), pd.Timestamp("2025-06-10 17:00"))
        assert engine.capital == initial

    def test_no_position_no_swap(self) -> None:
        engine = _make_engine()
        initial = engine.capital
        engine.on_bar("EUR/USD", _make_bar(), pd.Timestamp("2025-06-10 17:00"))
        assert engine.capital == initial


# ---------------------------------------------------------------------------
# Leverage default
# ---------------------------------------------------------------------------


class TestLeverage:
    def test_default_100x(self) -> None:
        engine = _make_engine()
        assert engine.default_leverage == 100.0

    def test_custom_leverage(self) -> None:
        engine = _make_engine(leverage=50.0)
        assert engine.default_leverage == 50.0


# ---------------------------------------------------------------------------
# Contract multiplier
# ---------------------------------------------------------------------------


class TestContractMultiplier:
    def test_forex_multiplier_is_one(self) -> None:
        engine = _make_engine()
        assert engine.get_contract_multiplier("EUR/USD") == 1.0
