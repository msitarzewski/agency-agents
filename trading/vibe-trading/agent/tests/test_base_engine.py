"""Tests for BaseEngine shared logic: _align, _close_position, _calc_equity.

Uses ChinaAEngine as a concrete implementation since BaseEngine is abstract.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.engines.base import BaseEngine, _align, _load_optimizer
from backtest.engines.china_a import ChinaAEngine
from backtest.models import Position


# ---------------------------------------------------------------------------
# _align: signal alignment and normalization
# ---------------------------------------------------------------------------


def _simple_data_and_signals():
    """Build minimal data_map and signal_map for alignment tests."""
    dates = pd.bdate_range("2025-01-01", periods=10)
    df_a = pd.DataFrame(
        {"close": np.linspace(10, 20, 10), "open": np.linspace(10, 20, 10)},
        index=dates,
    )
    df_b = pd.DataFrame(
        {"close": np.linspace(100, 110, 10), "open": np.linspace(100, 110, 10)},
        index=dates,
    )
    data_map = {"A": df_a, "B": df_b}

    sig_a = pd.Series(0.0, index=dates)
    sig_a.iloc[3:] = 1.0
    sig_b = pd.Series(0.0, index=dates)
    sig_b.iloc[5:] = 1.0
    signal_map = {"A": sig_a, "B": sig_b}

    return data_map, signal_map, dates


class TestAlign:
    def test_output_shapes(self) -> None:
        data_map, signal_map, dates = _simple_data_and_signals()
        out_dates, close_df, pos_df, ret_df = _align(data_map, signal_map, ["A", "B"])
        assert len(out_dates) == len(dates)
        assert close_df.shape == (len(dates), 2)
        assert pos_df.shape == (len(dates), 2)
        assert ret_df.shape == (len(dates), 2)

    def test_signal_shifted_by_one(self) -> None:
        """Signal at bar i should produce position at bar i+1 (next-bar-open)."""
        data_map, signal_map, dates = _simple_data_and_signals()
        _, _, pos_df, _ = _align(data_map, signal_map, ["A", "B"])
        # Signal A goes to 1.0 at index 3 → position should be 0 at index 3, non-zero at index 4
        assert pos_df.at[dates[3], "A"] == 0.0
        assert pos_df.at[dates[4], "A"] > 0.0

    def test_positions_normalized(self) -> None:
        """Sum of abs(weights) should be <= 1.0 per row."""
        data_map, signal_map, dates = _simple_data_and_signals()
        _, _, pos_df, _ = _align(data_map, signal_map, ["A", "B"])
        row_sums = pos_df.abs().sum(axis=1)
        assert (row_sums <= 1.0 + 1e-10).all()

    def test_signals_clipped(self) -> None:
        """Signals outside [-1, 1] should be clipped."""
        dates = pd.bdate_range("2025-01-01", periods=5)
        df = pd.DataFrame({"close": [100] * 5, "open": [100] * 5}, index=dates)
        sig = pd.Series([0, 0, 2.0, -3.0, 0.5], index=dates)
        data_map = {"X": df}
        signal_map = {"X": sig}
        _, _, pos_df, _ = _align(data_map, signal_map, ["X"])
        # After shift, clipped values show up at indices 3 and 4
        assert pos_df["X"].abs().max() <= 1.0 + 1e-10

    def test_nan_signals_filled_zero(self) -> None:
        dates = pd.bdate_range("2025-01-01", periods=5)
        df = pd.DataFrame({"close": [100] * 5, "open": [100] * 5}, index=dates)
        sig = pd.Series([np.nan, 1.0, np.nan, 0.5, np.nan], index=dates)
        data_map = {"X": df}
        signal_map = {"X": sig}
        _, _, pos_df, _ = _align(data_map, signal_map, ["X"])
        assert not pos_df.isna().any().any()

    def test_close_ffill_bfill(self) -> None:
        """Missing close prices should be forward/backward filled."""
        dates = pd.bdate_range("2025-01-01", periods=5)
        df = pd.DataFrame(
            {"close": [100, np.nan, np.nan, 110, 115], "open": [100] * 5},
            index=dates,
        )
        sig = pd.Series([0, 1, 1, 1, 0], index=dates)
        _, close_df, _, _ = _align({"X": df}, {"X": sig}, ["X"])
        assert not close_df.isna().any().any()

    def test_with_optimizer(self) -> None:
        """Optimizer callable gets applied."""
        data_map, signal_map, dates = _simple_data_and_signals()

        def dummy_optimizer(ret, pos, dates_arg):
            return pos * 0.5  # halve everything

        _, _, pos_df, _ = _align(data_map, signal_map, ["A", "B"], optimizer=dummy_optimizer)
        # Positions should be smaller due to optimizer
        _, _, pos_no_opt, _ = _align(data_map, signal_map, ["A", "B"])
        assert pos_df.abs().sum().sum() <= pos_no_opt.abs().sum().sum() + 1e-10


# ---------------------------------------------------------------------------
# _load_optimizer
# ---------------------------------------------------------------------------


class TestLoadOptimizer:
    def test_no_optimizer(self) -> None:
        assert _load_optimizer({}) is None
        assert _load_optimizer({"optimizer": ""}) is None

    def test_valid_optimizer(self) -> None:
        opt = _load_optimizer({"optimizer": "risk_parity"})
        assert opt is not None and callable(opt)

    def test_invalid_optimizer_returns_none(self) -> None:
        opt = _load_optimizer({"optimizer": "nonexistent_module_xyz"})
        assert opt is None


# ---------------------------------------------------------------------------
# _close_position: PnL calculation
# ---------------------------------------------------------------------------


class TestClosePosition:
    def test_profitable_long(self) -> None:
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine._bar_idx = 5
        engine.positions["000001.SZ"] = Position(
            "000001.SZ", 1, 15.0, pd.Timestamp("2025-01-02"), 1000.0, entry_bar_idx=0,
        )
        engine.capital = 985_000.0  # after buying
        engine._close_position("000001.SZ", 16.0, pd.Timestamp("2025-01-10"), "signal")

        assert "000001.SZ" not in engine.positions
        assert len(engine.trades) == 1
        t = engine.trades[0]
        assert t.pnl == pytest.approx(1000.0)  # 1000 × (16 - 15) = +1000
        assert t.exit_reason == "signal"
        assert t.holding_bars == 5

    def test_losing_long(self) -> None:
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine._bar_idx = 3
        engine.positions["600519.SH"] = Position(
            "600519.SH", 1, 1800.0, pd.Timestamp("2025-01-02"), 100.0, entry_bar_idx=0,
        )
        engine.capital = 820_000.0
        engine._close_position("600519.SH", 1750.0, pd.Timestamp("2025-01-06"), "signal")

        t = engine.trades[0]
        assert t.pnl == pytest.approx(-5000.0)  # 100 × (1750 - 1800) = -5000
        assert t.direction == 1

    def test_close_nonexistent_position_noop(self) -> None:
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine._close_position("NOPE.SZ", 10.0, pd.Timestamp("2025-01-01"), "signal")
        assert len(engine.trades) == 0

    def test_capital_returned(self) -> None:
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine._bar_idx = 1
        engine.positions["000001.SZ"] = Position(
            "000001.SZ", 1, 15.0, pd.Timestamp("2025-01-02"), 1000.0,
        )
        capital_before = 985_000.0
        engine.capital = capital_before
        engine._close_position("000001.SZ", 15.0, pd.Timestamp("2025-01-03"), "signal")
        # Margin returned + 0 PnL - exit commission
        assert engine.capital > capital_before  # margin returned exceeds commission


# ---------------------------------------------------------------------------
# _calc_equity
# ---------------------------------------------------------------------------


class TestCalcEquity:
    def test_no_positions(self) -> None:
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        dates = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
        close_df = pd.DataFrame({"X": [15.0]}, index=dates)
        eq = engine._calc_equity(close_df, dates[0])
        assert eq == 1_000_000.0

    def test_with_unrealized_gain(self) -> None:
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine.capital = 985_000.0
        engine.positions["X"] = Position("X", 1, 15.0, pd.Timestamp("2025-01-02"), 1000.0)
        dates = pd.DatetimeIndex([pd.Timestamp("2025-01-03")])
        close_df = pd.DataFrame({"X": [16.0]}, index=dates)
        eq = engine._calc_equity(close_df, dates[0])
        # capital + margin + unrealized = 985000 + (1000×15/1) + (1×1000×(16-15)) = 985000 + 15000 + 1000 = 1001000
        assert eq == pytest.approx(1_001_000.0)


# ---------------------------------------------------------------------------
# _safe_price
# ---------------------------------------------------------------------------


class TestSafePrice:
    def test_returns_close_price(self) -> None:
        dates = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
        close_df = pd.DataFrame({"X": [15.5]}, index=dates)
        assert BaseEngine._safe_price(close_df, dates[0], "X", 10.0) == 15.5

    def test_fallback_on_missing_symbol(self) -> None:
        dates = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
        close_df = pd.DataFrame({"X": [15.5]}, index=dates)
        assert BaseEngine._safe_price(close_df, dates[0], "MISSING", 10.0) == 10.0

    def test_fallback_on_missing_timestamp(self) -> None:
        dates = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
        close_df = pd.DataFrame({"X": [15.5]}, index=dates)
        assert BaseEngine._safe_price(close_df, pd.Timestamp("2025-06-01"), "X", 10.0) == 10.0

    def test_fallback_on_nan(self) -> None:
        dates = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
        close_df = pd.DataFrame({"X": [np.nan]}, index=dates)
        assert BaseEngine._safe_price(close_df, dates[0], "X", 10.0) == 10.0
