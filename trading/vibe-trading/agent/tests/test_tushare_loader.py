"""Tests for tushare loader symbol-type routing.

Pins #310: tushare daily() only serves A-share stocks. ETF/LOF needs
fund_daily(), indices need index_daily(), HK needs hk_daily(). US/crypto
are unsupported and should warn+skip.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pandas as pd
import pytest

from backtest.loaders.tushare import (
    DataLoader,
    _is_crypto,
    _is_etf_listed,
    _is_hk_equity,
    _is_index,
    _is_us_equity,
)


# ---------------------------------------------------------------------------
# Predicate tests
# ---------------------------------------------------------------------------


class TestIsEtfListed:
    @pytest.mark.parametrize("code", [
        "510050.SH",  # 50 ETF
        "510300.SH",  # CSI 300 ETF
        "159915.SZ",  # ChiNext ETF
        "161725.SZ",  # LOF
        "520000.SH",  # 52 prefix
        "560000.SH",  # 56 prefix
        "588000.SH",  # STAR ETF
    ])
    def test_etf_codes_match(self, code: str) -> None:
        assert _is_etf_listed(code)

    @pytest.mark.parametrize("code", [
        "000001.SZ",   # Ping An Bank — stock
        "600519.SH",   # Moutai — stock
        "300750.SZ",   # CATL — ChiNext stock
        "002594.SZ",   # BYD — SME stock
        "AAPL.US",     # US equity
        "00700.HK",    # HK equity
        "BTC-USDT",    # crypto
        "",            # empty
        "ABC.SH",      # non-digit
        "12345.SH",    # too short
        "5188800.SH",  # too long
    ])
    def test_non_etf_codes_skip(self, code: str) -> None:
        assert not _is_etf_listed(code)


class TestIsIndex:
    @pytest.mark.parametrize("code", [
        "000001.SH",  # Shanghai Composite
        "000300.SH",  # CSI 300
        "000016.SH",  # SSE 50
        "399001.SZ",  # Shenzhen Component
        "399006.SZ",  # ChiNext Index
    ])
    def test_index_codes_match(self, code: str) -> None:
        assert _is_index(code)

    @pytest.mark.parametrize("code", [
        "600519.SH",   # stock
        "000001.SZ",   # stock (SZ 000 is not index)
        "510050.SH",   # ETF
        "300750.SZ",   # ChiNext stock (300 not 399)
        "AAPL.US",
        "",
    ])
    def test_non_index_codes_skip(self, code: str) -> None:
        assert not _is_index(code)


class TestIsHkEquity:
    def test_hk_code_matches(self) -> None:
        assert _is_hk_equity("00700.HK")
        assert _is_hk_equity("09988.HK")

    def test_non_hk_codes_skip(self) -> None:
        assert not _is_hk_equity("000001.SZ")
        assert not _is_hk_equity("600519.SH")
        assert not _is_hk_equity("AAPL.US")
        assert not _is_hk_equity("")


class TestIsUsEquity:
    def test_us_code_matches(self) -> None:
        assert _is_us_equity("AAPL.US")
        assert _is_us_equity("TSLA.US")

    def test_non_us_codes_skip(self) -> None:
        assert not _is_us_equity("00700.HK")
        assert not _is_us_equity("600519.SH")
        assert not _is_us_equity("")


class TestIsCrypto:
    def test_crypto_code_matches(self) -> None:
        assert _is_crypto("BTC-USDT")
        assert _is_crypto("ETH-USDT")
        assert _is_crypto("BTC/USDT")

    def test_non_crypto_codes_skip(self) -> None:
        assert not _is_crypto("AAPL.US")
        assert not _is_crypto("600519.SH")
        assert not _is_crypto("")


# ---------------------------------------------------------------------------
# Routing tests (mock — no network)
# ---------------------------------------------------------------------------


def _make_ohlcv_df() -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame matching tushare's column layout."""
    return pd.DataFrame({
        "ts_code": ["X"] * 3,
        "trade_date": ["20250102", "20250103", "20250106"],
        "open": [10.0, 10.5, 11.0],
        "high": [11.0, 11.5, 12.0],
        "low": [9.5, 10.0, 10.5],
        "close": [10.5, 11.0, 11.5],
        "vol": [1000.0, 1200.0, 1100.0],
        "amount": [10500.0, 13200.0, 12650.0],
    })


class TestFetchDailyFrameRouting:
    """Verify _fetch_daily_frame calls the correct tushare endpoint per symbol type."""

    def _make_loader(self) -> DataLoader:
        loader = object.__new__(DataLoader)
        loader.api = MagicMock()
        return loader

    def test_stock_routes_to_daily(self) -> None:
        loader = self._make_loader()
        loader.api.daily.return_value = _make_ohlcv_df()
        result = loader._fetch_daily_frame("000001.SZ", "20250102", "20250110")
        loader.api.daily.assert_called_once()
        loader.api.fund_daily.assert_not_called()
        loader.api.index_daily.assert_not_called()
        loader.api.hk_daily.assert_not_called()
        assert result is not None
        assert not result.empty

    def test_etf_routes_to_fund_daily(self) -> None:
        loader = self._make_loader()
        loader.api.fund_daily.return_value = _make_ohlcv_df()
        result = loader._fetch_daily_frame("510050.SH", "20250102", "20250110")
        loader.api.fund_daily.assert_called_once()
        loader.api.daily.assert_not_called()
        assert result is not None

    def test_index_routes_to_index_daily(self) -> None:
        loader = self._make_loader()
        loader.api.index_daily.return_value = _make_ohlcv_df()
        result = loader._fetch_daily_frame("000001.SH", "20250102", "20250110")
        loader.api.index_daily.assert_called_once()
        loader.api.daily.assert_not_called()
        assert result is not None

    def test_hk_routes_to_hk_daily(self) -> None:
        loader = self._make_loader()
        loader.api.hk_daily.return_value = _make_ohlcv_df()
        result = loader._fetch_daily_frame("00700.HK", "20250102", "20250110")
        loader.api.hk_daily.assert_called_once()
        loader.api.daily.assert_not_called()
        assert result is not None

    def test_us_returns_none_and_warns(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_daily_frame("AAPL.US", "20250102", "20250110")
        assert result is None
        loader.api.daily.assert_not_called()
        loader.api.fund_daily.assert_not_called()

    def test_crypto_returns_none_and_warns(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_daily_frame("BTC-USDT", "20250102", "20250110")
        assert result is None
        loader.api.daily.assert_not_called()

    def test_empty_result_warns(self) -> None:
        loader = self._make_loader()
        loader.api.daily.return_value = pd.DataFrame()
        result = loader._fetch_daily_frame("600519.SH", "20250102", "20250110")
        assert result is None


# ---------------------------------------------------------------------------
# E2E tests (real tushare API — gated behind TUSHARE_TOKEN env var)
# ---------------------------------------------------------------------------

def _make_minute_df() -> pd.DataFrame:
    return pd.DataFrame({
        "ts_code": ["X"] * 3,
        "trade_time": ["2025-01-02 09:31:00", "2025-01-02 09:32:00", "2025-01-02 09:33:00"],
        "open": [10.0, 10.5, 11.0],
        "high": [11.0, 11.5, 12.0],
        "low": [9.5, 10.0, 10.5],
        "close": [10.5, 11.0, 11.5],
        "vol": [1000.0, 1200.0, 1100.0],
    })


class TestFetchMinutesRouting:
    """Verify _fetch_minutes routes by symbol type (B1 fix)."""

    def _make_loader(self) -> DataLoader:
        loader = object.__new__(DataLoader)
        loader.api = MagicMock()
        return loader

    def test_stock_routes_to_stk_mins(self) -> None:
        loader = self._make_loader()
        loader.api.stk_mins.return_value = _make_minute_df()
        result = loader._fetch_minutes(["000001.SZ"], "2025-01-02", "2025-01-03", "5m")
        loader.api.stk_mins.assert_called_once()
        assert "000001.SZ" in result

    def test_etf_warns_and_skips(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_minutes(["510050.SH"], "2025-01-02", "2025-01-03", "5m")
        loader.api.stk_mins.assert_not_called()
        assert result == {}

    def test_index_warns_and_skips(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_minutes(["000300.SH"], "2025-01-02", "2025-01-03", "5m")
        loader.api.stk_mins.assert_not_called()
        assert result == {}

    def test_hk_warns_and_skips(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_minutes(["00700.HK"], "2025-01-02", "2025-01-03", "5m")
        loader.api.stk_mins.assert_not_called()
        assert result == {}

    def test_us_warns_and_skips(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_minutes(["AAPL.US"], "2025-01-02", "2025-01-03", "5m")
        loader.api.stk_mins.assert_not_called()
        assert result == {}

    def test_crypto_warns_and_skips(self) -> None:
        loader = self._make_loader()
        result = loader._fetch_minutes(["BTC-USDT"], "2025-01-02", "2025-01-03", "5m")
        loader.api.stk_mins.assert_not_called()
        assert result == {}

    def test_mixed_batch_routes_only_stocks(self) -> None:
        loader = self._make_loader()
        loader.api.stk_mins.return_value = _make_minute_df()
        result = loader._fetch_minutes(
            ["600519.SH", "510050.SH", "000300.SH", "00700.HK"],
            "2025-01-02", "2025-01-03", "5m",
        )
        loader.api.stk_mins.assert_called_once()
        assert "600519.SH" in result
        assert "510050.SH" not in result
        assert "000300.SH" not in result
        assert "00700.HK" not in result


class TestMergeBasicFieldsGuard:
    """Verify _merge_basic_fields skips non-stock codes (B2 fix)."""

    def _make_loader(self) -> DataLoader:
        loader = object.__new__(DataLoader)
        loader.api = MagicMock()
        return loader

    def _make_daily_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {"open": [10.0], "high": [11.0], "low": [9.5], "close": [10.5], "volume": [1000.0]},
            index=pd.to_datetime(["2025-01-02"]),
        )

    def test_stock_calls_daily_basic(self) -> None:
        loader = self._make_loader()
        loader.api.daily_basic.return_value = pd.DataFrame({
            "ts_code": ["000001.SZ"],
            "trade_date": ["20250102"],
            "pe_ttm": [12.5],
        })
        result = {"000001.SZ": self._make_daily_df()}
        loader._merge_basic_fields(result, ["000001.SZ"], "2025-01-02", "2025-01-03", ["pe_ttm"])
        loader.api.daily_basic.assert_called_once()

    @pytest.mark.parametrize("code", [
        "510050.SH",  # ETF
        "000300.SH",  # index
        "00700.HK",   # HK
        "AAPL.US",    # US
        "BTC-USDT",   # crypto
    ])
    def test_non_stock_skips_daily_basic(self, code: str) -> None:
        loader = self._make_loader()
        result = {code: self._make_daily_df()}
        loader._merge_basic_fields(result, [code], "2025-01-02", "2025-01-03", ["pe_ttm"])
        loader.api.daily_basic.assert_not_called()


_token = os.getenv("TUSHARE_TOKEN", "")
_skip_e2e = _token in ("", "your-tushare-token")


@pytest.mark.skipif(_skip_e2e, reason="TUSHARE_TOKEN not set")
class TestTushareE2E:
    """Real API calls — requires TUSHARE_TOKEN env var."""

    def _fetch(self, codes: list[str]) -> dict[str, pd.DataFrame]:
        loader = DataLoader()
        return loader.fetch(codes, "2025-01-02", "2025-01-10")

    def test_stock_returns_data(self) -> None:
        result = self._fetch(["000001.SZ"])
        assert "000001.SZ" in result
        assert not result["000001.SZ"].empty

    def test_etf_returns_data(self) -> None:
        result = self._fetch(["510050.SH"])
        assert "510050.SH" in result
        assert not result["510050.SH"].empty

    def test_index_returns_data(self) -> None:
        result = self._fetch(["000001.SH"])
        assert "000001.SH" in result
        assert not result["000001.SH"].empty

    def test_mixed_batch_returns_all(self) -> None:
        result = self._fetch(["600519.SH", "510050.SH", "000001.SH"])
        assert len(result) == 3
        for code in ["600519.SH", "510050.SH", "000001.SH"]:
            assert code in result
            assert not result[code].empty
