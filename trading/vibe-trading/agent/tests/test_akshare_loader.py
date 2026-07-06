"""Tests for AKShare loader symbol routing.

Pins issues #50 (ETF) and #54 (forex): the previous _fetch_one routed every
unrecognized code to stock_zh_a_hist, masking ETFs (518880.SH) and forex pairs
(EURUSD) as broken A-shares. These tests use mocks so they don't hit the
network — real-data smoke is in tests/_smoke_akshare_real.py if/when needed.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest

from backtest.loaders.akshare_loader import (
    DataLoader,
    _is_a_share,
    _is_etf_listed,
    _is_forex,
    _is_hk,
    _is_us,
)


# ---------------------------------------------------------------------------
# Predicate tests
# ---------------------------------------------------------------------------


class TestIsETFListed:
    @pytest.mark.parametrize("code", [
        "518880.SH",  # gold ETF (issue #50)
        "510300.SH",  # CSI 300 ETF
        "159915.SZ",  # ChiNext ETF
        "161005.SZ",  # LOF
    ])
    def test_etf_codes_match(self, code: str) -> None:
        assert _is_etf_listed(code)

    @pytest.mark.parametrize("code", [
        "600519.SH",   # Moutai — A-share, not ETF
        "000001.SZ",   # Ping An Bank — A-share
        "300750.SZ",   # CATL — ChiNext stock
        "AAPL.US",     # not Chinese
        "EURUSD",      # forex
        "12345.SH",    # malformed
        "5188800.SH",  # too long
    ])
    def test_non_etf_codes_skip(self, code: str) -> None:
        assert not _is_etf_listed(code)


class TestIsForex:
    def test_eurusd_matches(self) -> None:
        assert _is_forex("EURUSD")

    def test_lowercase_matches(self) -> None:
        assert _is_forex("eurusd")

    def test_fx_suffix_matches(self) -> None:
        assert _is_forex("EURUSD.FX")

    def test_a_share_does_not_match(self) -> None:
        assert not _is_forex("600519.SH")

    def test_unknown_pair_does_not_match(self) -> None:
        # "ZZZZZZ" isn't in akshare's symbol_market_map
        assert not _is_forex("ZZZZZZ")


# ---------------------------------------------------------------------------
# Routing tests — verify _fetch_one dispatches to the right endpoint without
# actually hitting AKShare.
# ---------------------------------------------------------------------------


def _stub_etf_response() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "open": [5.0, 5.1],
        "high": [5.2, 5.3],
        "low": [4.9, 5.0],
        "close": [5.15, 5.25],
        "volume": [1000, 1100],
    })


def _stub_forex_response() -> pd.DataFrame:
    return pd.DataFrame({
        "日期": pd.to_datetime(["2024-01-02", "2024-01-03"]),
        "代码": ["EURUSD", "EURUSD"],
        "名称": ["欧元兑美元", "欧元兑美元"],
        "今开": [1.10, 1.11],
        "最新价": [1.105, 1.115],
        "最高": [1.12, 1.13],
        "最低": [1.09, 1.10],
        "振幅": [0.5, 0.4],
    })


def _stub_a_share_response() -> pd.DataFrame:
    return pd.DataFrame({
        "日期": pd.to_datetime(["2024-01-02"]),
        "开盘": [1700.0],
        "最高": [1720.0],
        "最低": [1690.0],
        "收盘": [1710.0],
        "成交量": [100000],
    })


@pytest.fixture
def fake_akshare(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Install a stub `akshare` module with mocked endpoints."""
    fake = SimpleNamespace(
        fund_etf_hist_sina=MagicMock(return_value=_stub_etf_response()),
        forex_hist_em=MagicMock(return_value=_stub_forex_response()),
        stock_zh_a_hist=MagicMock(return_value=_stub_a_share_response()),
        stock_us_hist=MagicMock(return_value=pd.DataFrame()),
        stock_hk_hist=MagicMock(return_value=pd.DataFrame()),
    )
    monkeypatch.setitem(sys.modules, "akshare", fake)
    return fake


class TestRouting:
    def test_etf_routes_to_fund_etf_hist_sina(self, fake_akshare: SimpleNamespace) -> None:
        loader = DataLoader()
        df = loader._fetch_one("518880.SH", "2024-01-01", "2024-12-31", "1D")

        fake_akshare.fund_etf_hist_sina.assert_called_once_with(symbol="sh518880")
        fake_akshare.stock_zh_a_hist.assert_not_called()
        assert df is not None
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 2

    def test_etf_sz_uses_sz_prefix(self, fake_akshare: SimpleNamespace) -> None:
        loader = DataLoader()
        loader._fetch_one("159915.SZ", "2024-01-01", "2024-12-31", "1D")

        fake_akshare.fund_etf_hist_sina.assert_called_once_with(symbol="sz159915")

    def test_forex_routes_to_forex_hist_em(self, fake_akshare: SimpleNamespace) -> None:
        loader = DataLoader()
        df = loader._fetch_one("EURUSD", "2024-01-01", "2024-12-31", "1D")

        fake_akshare.forex_hist_em.assert_called_once_with(symbol="EURUSD")
        fake_akshare.stock_zh_a_hist.assert_not_called()
        assert df is not None
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        # forex has no volume — should be zero-filled
        assert (df["volume"] == 0.0).all()
        # 最新价 → close mapping
        assert df.iloc[0]["close"] == pytest.approx(1.105)

    def test_forex_strips_fx_suffix(self, fake_akshare: SimpleNamespace) -> None:
        loader = DataLoader()
        loader._fetch_one("EURUSD.FX", "2024-01-01", "2024-12-31", "1D")
        fake_akshare.forex_hist_em.assert_called_once_with(symbol="EURUSD")

    def test_a_share_still_routes_to_stock_zh_a_hist(
        self, fake_akshare: SimpleNamespace
    ) -> None:
        loader = DataLoader()
        loader._fetch_one("600519.SH", "2024-01-01", "2024-12-31", "1D")

        fake_akshare.stock_zh_a_hist.assert_called_once()
        fake_akshare.fund_etf_hist_sina.assert_not_called()
        fake_akshare.forex_hist_em.assert_not_called()
