"""Tests for ChinaFuturesEngine market rules.

Validates:
  - T+0: can close same-day positions (unlike A-shares)
  - Both long and short allowed
  - Price limit enforcement (varies by product)
  - Integer contract rounding
  - Commission (fixed per-lot and per-notional)
  - Contract multiplier lookup
  - Margin rate lookup
  - Product code extraction
"""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.engines.china_futures import (
    ChinaFuturesEngine,
    _extract_product,
    _MULTIPLIER,
    _MARGIN_RATE,
    _COMMISSION,
    _PRICE_LIMIT,
    _DEFAULT_PRICE_LIMIT,
)
from backtest.models import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bar(
    close: float = 5000.0,
    pre_close: float | None = None,
    pct_chg: float | None = None,
    settle: float | None = None,
    pre_settle: float | None = None,
    open_: float | None = None,
) -> pd.Series:
    d: dict = {"close": close, "open": open_ or close}
    if pre_close is not None:
        d["pre_close"] = pre_close
    if pct_chg is not None:
        d["pct_chg"] = pct_chg
    if settle is not None:
        d["settle"] = settle
    if pre_settle is not None:
        d["pre_settle"] = pre_settle
    return pd.Series(d)


def _make_engine(**overrides) -> ChinaFuturesEngine:
    config = {"initial_cash": 1_000_000, "codes": ["IF2406.CFFEX"]}
    config.update(overrides)
    return ChinaFuturesEngine(config)


# ---------------------------------------------------------------------------
# Product extraction
# ---------------------------------------------------------------------------


class TestExtractProduct:
    @pytest.mark.parametrize(
        "symbol, expected",
        [
            ("IF2406.CFFEX", "IF"),
            ("rb2410.SHFE", "rb"),
            ("au2412", "au"),
            ("CF501.ZCE", "CF"),
            ("sc2503.INE", "sc"),
            ("si2406.GFEX", "si"),
        ],
    )
    def test_extract(self, symbol: str, expected: str) -> None:
        assert _extract_product(symbol) == expected


# ---------------------------------------------------------------------------
# can_execute: T+0 (both directions allowed)
# ---------------------------------------------------------------------------


class TestDirectionAndT0:
    def test_long_allowed(self) -> None:
        engine = _make_engine()
        bar = _make_bar()
        assert engine.can_execute("IF2406.CFFEX", 1, bar) is True

    def test_short_allowed(self) -> None:
        """China futures allow short selling (unlike A-shares)."""
        engine = _make_engine()
        bar = _make_bar()
        assert engine.can_execute("IF2406.CFFEX", -1, bar) is True

    def test_close_same_day_allowed(self) -> None:
        """T+0: can close positions opened today."""
        engine = _make_engine()
        engine.positions["IF2406.CFFEX"] = Position(
            symbol="IF2406.CFFEX",
            direction=1,
            entry_price=5000.0,
            entry_time=pd.Timestamp("2025-06-10"),
            size=2.0,
            leverage=1 / 0.12,
        )
        bar = _make_bar()
        assert engine.can_execute("IF2406.CFFEX", 0, bar) is True


# ---------------------------------------------------------------------------
# can_execute: price limits
# ---------------------------------------------------------------------------


class TestPriceLimits:
    def test_stock_index_limit_up_blocks_long(self) -> None:
        """IF has ±10% limit; at limit-up, can't open long."""
        engine = _make_engine()
        bar = _make_bar(close=5500.0, pre_close=5000.0)  # +10%
        assert engine.can_execute("IF2406.CFFEX", 1, bar) is False

    def test_stock_index_limit_down_blocks_short(self) -> None:
        engine = _make_engine()
        bar = _make_bar(close=4500.0, pre_close=5000.0)  # -10%
        assert engine.can_execute("IF2406.CFFEX", -1, bar) is False

    def test_stock_index_within_limit(self) -> None:
        engine = _make_engine()
        bar = _make_bar(close=5200.0, pre_close=5000.0)  # +4%
        assert engine.can_execute("IF2406.CFFEX", 1, bar) is True

    def test_commodity_default_5pct(self) -> None:
        """Commodity like rb uses default ±5% limit."""
        engine = _make_engine(codes=["rb2410.SHFE"])
        bar = _make_bar(close=4250.0, pre_close=4000.0)  # +6.25% > 5%
        assert engine.can_execute("rb2410.SHFE", 1, bar) is False

    def test_commodity_within_limit(self) -> None:
        engine = _make_engine(codes=["rb2410.SHFE"])
        bar = _make_bar(close=4100.0, pre_close=4000.0)  # +2.5%
        assert engine.can_execute("rb2410.SHFE", 1, bar) is True

    def test_limit_down_blocks_long_close(self) -> None:
        """At limit-down, can't sell (close long position)."""
        engine = _make_engine()
        engine.positions["IF2406.CFFEX"] = Position(
            "IF2406.CFFEX", 1, 5000.0, pd.Timestamp("2025-06-09"), 2.0,
        )
        bar = _make_bar(close=4500.0, pre_close=5000.0)  # -10%
        assert engine.can_execute("IF2406.CFFEX", 0, bar) is False


# ---------------------------------------------------------------------------
# round_size
# ---------------------------------------------------------------------------


class TestRoundSize:
    def test_rounds_down_to_integer(self) -> None:
        engine = _make_engine()
        assert engine.round_size(2.7, 5000.0) == 2

    def test_exact_integer(self) -> None:
        engine = _make_engine()
        assert engine.round_size(5.0, 5000.0) == 5

    def test_less_than_one_becomes_zero(self) -> None:
        engine = _make_engine()
        assert engine.round_size(0.9, 5000.0) == 0

    def test_negative_clamps_to_zero(self) -> None:
        engine = _make_engine()
        assert engine.round_size(-2.0, 5000.0) == 0


# ---------------------------------------------------------------------------
# calc_commission
# ---------------------------------------------------------------------------


class TestCommission:
    def test_rate_commission_via_active_symbol(self) -> None:
        """calc_commission uses _active_symbol for product-specific rate."""
        engine = _make_engine()
        engine._active_symbol = "IF2406.CFFEX"
        comm = engine.calc_commission(2, 5000.0, 1, is_open=True)
        # 2 contracts × 5000 × 300 (multiplier) × 0.000023 = 69
        expected = 2 * 5000 * 300 * 0.000023
        assert comm == pytest.approx(expected, rel=0.01)

    def test_fixed_commission_via_active_symbol(self) -> None:
        """au uses fixed per-lot commission."""
        engine = _make_engine()
        engine._active_symbol = "au2412.SHFE"
        comm = engine.calc_commission(3, 500.0, 1, is_open=True)
        expected = 3 * 10.0  # 10 RMB per lot
        assert comm == pytest.approx(expected)

    def test_symbol_aware_rate_commission(self) -> None:
        engine = _make_engine()
        comm = engine.calc_commission_for_symbol("IF2406.CFFEX", 2, 5000.0, is_open=True)
        expected = 2 * 5000 * 300 * 0.000023
        assert comm == pytest.approx(expected, rel=0.01)

    def test_commission_override(self) -> None:
        engine = _make_engine(commission_override=0.001)
        comm = engine.calc_commission(5, 4000.0, 1, is_open=True)
        assert comm == pytest.approx(5 * 4000.0 * 0.001)


# ---------------------------------------------------------------------------
# Contract multiplier and margin rate
# ---------------------------------------------------------------------------


class TestContractMultiplier:
    @pytest.mark.parametrize(
        "symbol, expected",
        [
            ("IF2406.CFFEX", 300),
            ("IC2406.CFFEX", 200),
            ("rb2410.SHFE", 10),
            ("au2412.SHFE", 1000),
            ("sc2503.INE", 1000),
            ("c2501.DCE", 10),
            ("CF501.ZCE", 5),
        ],
    )
    def test_multipliers(self, symbol: str, expected: int) -> None:
        engine = _make_engine()
        assert engine.get_contract_multiplier(symbol) == expected


class TestMarginRate:
    def test_stock_index_12pct(self) -> None:
        engine = _make_engine()
        assert engine.get_margin_rate("IF2406.CFFEX") == 0.12

    def test_copper_8pct(self) -> None:
        engine = _make_engine()
        assert engine.get_margin_rate("cu2410.SHFE") == 0.08

    def test_unknown_product_default_10pct(self) -> None:
        engine = _make_engine()
        assert engine.get_margin_rate("XX9999.SHFE") == 0.10


# ---------------------------------------------------------------------------
# Slippage
# ---------------------------------------------------------------------------


class TestSlippage:
    def test_buy_slippage_increases_price(self) -> None:
        engine = _make_engine()
        assert engine.apply_slippage(5000.0, 1) > 5000.0

    def test_sell_slippage_decreases_price(self) -> None:
        engine = _make_engine()
        assert engine.apply_slippage(5000.0, -1) < 5000.0

    def test_custom_slippage(self) -> None:
        engine = _make_engine(slippage=0.002)
        assert engine.apply_slippage(5000.0, 1) == pytest.approx(5010.0)


# ---------------------------------------------------------------------------
# Leverage derived from margin
# ---------------------------------------------------------------------------


class TestLeverageFromMargin:
    def test_if_leverage(self) -> None:
        """IF margin=12% → leverage≈8.33."""
        engine = _make_engine(codes=["IF2406.CFFEX"])
        assert engine.default_leverage == pytest.approx(1 / 0.12, rel=0.01)

    def test_override_margin_rate(self) -> None:
        engine = _make_engine(margin_rate_override=0.20)
        assert engine.default_leverage == pytest.approx(5.0)
