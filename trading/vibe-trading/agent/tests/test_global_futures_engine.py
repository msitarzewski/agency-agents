"""Tests for GlobalFuturesEngine market rules.

Validates:
  - T+0, both long and short allowed
  - Equity index price-limit enforcement (7% simplified)
  - Commodity futures: no price limit
  - Integer contract rounding
  - Per-contract commission
  - Contract multiplier lookup
  - Product code extraction
"""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.engines.global_futures import (
    GlobalFuturesEngine,
    _extract_product,
    _MULTIPLIER,
    _MARGIN_PER_CONTRACT,
    _COMMISSION_PER_CONTRACT,
)
from backtest.models import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bar(
    close: float = 5000.0,
    pre_close: float | None = None,
    pct_chg: float | None = None,
    open_: float | None = None,
) -> pd.Series:
    d: dict = {"close": close, "open": open_ or close}
    if pre_close is not None:
        d["pre_close"] = pre_close
    if pct_chg is not None:
        d["pct_chg"] = pct_chg
    return pd.Series(d)


def _make_engine(**overrides) -> GlobalFuturesEngine:
    config = {"initial_cash": 1_000_000, "codes": ["ESZ4"]}
    config.update(overrides)
    return GlobalFuturesEngine(config)


# ---------------------------------------------------------------------------
# Product extraction
# ---------------------------------------------------------------------------


class TestExtractProduct:
    @pytest.mark.parametrize(
        "symbol, expected",
        [
            ("ESZ4", "ES"),
            ("CLF25", "CL"),
            ("GCM2025", "GC"),
            ("NQ2503", "NQ"),
            ("ES.CME", "ES"),
            ("ZCH4", "ZC"),
        ],
    )
    def test_extract(self, symbol: str, expected: str) -> None:
        assert _extract_product(symbol) == expected


# ---------------------------------------------------------------------------
# can_execute: T+0, both directions
# ---------------------------------------------------------------------------


class TestDirections:
    def test_long_allowed(self) -> None:
        engine = _make_engine()
        bar = _make_bar()
        assert engine.can_execute("ESZ4", 1, bar) is True

    def test_short_allowed(self) -> None:
        engine = _make_engine()
        bar = _make_bar()
        assert engine.can_execute("ESZ4", -1, bar) is True

    def test_close_allowed(self) -> None:
        engine = _make_engine()
        bar = _make_bar()
        assert engine.can_execute("ESZ4", 0, bar) is True


# ---------------------------------------------------------------------------
# can_execute: price limits (equity index only)
# ---------------------------------------------------------------------------


class TestPriceLimits:
    def test_es_limit_up_blocks_long(self) -> None:
        """ES has 7% limit; at limit-up, can't open long."""
        engine = _make_engine()
        bar = _make_bar(close=5400.0, pre_close=5000.0)  # +8% > 7%
        assert engine.can_execute("ESZ4", 1, bar) is False

    def test_es_limit_down_blocks_short(self) -> None:
        engine = _make_engine()
        bar = _make_bar(close=4600.0, pre_close=5000.0)  # -8% > 7%
        assert engine.can_execute("ESZ4", -1, bar) is False

    def test_es_within_limit(self) -> None:
        engine = _make_engine()
        bar = _make_bar(close=5200.0, pre_close=5000.0)  # +4%
        assert engine.can_execute("ESZ4", 1, bar) is True

    def test_commodity_no_limit(self) -> None:
        """CL has no configured price limit; always allowed."""
        engine = _make_engine(codes=["CLF25"])
        bar = _make_bar(close=100.0, pre_close=70.0)  # +43%
        assert engine.can_execute("CLF25", 1, bar) is True
        assert engine.can_execute("CLF25", -1, bar) is True

    def test_gc_no_limit(self) -> None:
        engine = _make_engine(codes=["GCM25"])
        bar = _make_bar(close=2500.0, pre_close=2000.0)  # +25%
        assert engine.can_execute("GCM25", 1, bar) is True


# ---------------------------------------------------------------------------
# round_size
# ---------------------------------------------------------------------------


class TestRoundSize:
    def test_integer_rounding(self) -> None:
        engine = _make_engine()
        assert engine.round_size(3.7, 5000.0) == 3

    def test_exact_integer(self) -> None:
        engine = _make_engine()
        assert engine.round_size(5.0, 5000.0) == 5

    def test_zero(self) -> None:
        engine = _make_engine()
        assert engine.round_size(0.5, 5000.0) == 0

    def test_negative_to_zero(self) -> None:
        engine = _make_engine()
        assert engine.round_size(-1.0, 5000.0) == 0


# ---------------------------------------------------------------------------
# calc_commission
# ---------------------------------------------------------------------------


class TestCommission:
    def test_es_commission_via_active_symbol(self) -> None:
        """calc_commission uses _active_symbol for product lookup."""
        engine = _make_engine()
        engine._active_symbol = "ESZ4"
        comm = engine.calc_commission(2, 5000.0, 1, is_open=True)
        assert comm == pytest.approx(2 * 2.25)

    def test_micro_commission_via_active_symbol(self) -> None:
        engine = _make_engine()
        engine._active_symbol = "MESZ4"
        comm = engine.calc_commission(10, 5000.0, 1, is_open=True)
        assert comm == pytest.approx(10 * 0.62)

    def test_symbol_aware_direct(self) -> None:
        engine = _make_engine()
        comm = engine.calc_commission_for_symbol("ESZ4", 2, 5000.0, is_open=True)
        assert comm == pytest.approx(2 * 2.25)

    def test_commission_override(self) -> None:
        engine = _make_engine(commission_per_contract=1.0)
        comm = engine.calc_commission(5, 5000.0, 1, is_open=True)
        assert comm == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Contract multiplier
# ---------------------------------------------------------------------------


class TestContractMultiplier:
    @pytest.mark.parametrize(
        "symbol, expected",
        [
            ("ESZ4", 50),
            ("NQH5", 20),
            ("CLF25", 1000),
            ("GCM25", 100),
            ("SIH25", 5000),
            ("ZCH4", 50),
            ("ZBM5", 1000),
            ("MESZ4", 5),
        ],
    )
    def test_multipliers(self, symbol: str, expected: float) -> None:
        engine = _make_engine()
        assert engine.get_contract_multiplier(symbol) == expected


# ---------------------------------------------------------------------------
# Slippage
# ---------------------------------------------------------------------------


class TestSlippage:
    def test_buy_increases_price(self) -> None:
        engine = _make_engine()
        assert engine.apply_slippage(5000.0, 1) > 5000.0

    def test_sell_decreases_price(self) -> None:
        engine = _make_engine()
        assert engine.apply_slippage(5000.0, -1) < 5000.0

    def test_custom_slippage(self) -> None:
        engine = _make_engine(slippage=0.001)
        assert engine.apply_slippage(5000.0, 1) == pytest.approx(5005.0)
