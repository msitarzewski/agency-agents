"""Tests for yfinance loader crypto support: symbol conversion and market registration."""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.loaders.yfinance_loader import DataLoader, _to_yfinance_symbol


# ---------------------------------------------------------------------------
# _to_yfinance_symbol — crypto conversions
# ---------------------------------------------------------------------------


class TestToYfinanceSymbolCrypto:
    def test_usdt_suffix_converted_to_usd(self) -> None:
        assert _to_yfinance_symbol("BTC-USDT") == "BTC-USD"

    def test_usdc_suffix_converted_to_usd(self) -> None:
        assert _to_yfinance_symbol("ETH-USDC") == "ETH-USD"

    def test_lowercase_normalized(self) -> None:
        assert _to_yfinance_symbol("sol-usdt") == "SOL-USD"

    def test_existing_usd_pair_unchanged(self) -> None:
        assert _to_yfinance_symbol("BTC-USD") == "BTC-USD"

    def test_non_crypto_symbol_unchanged(self) -> None:
        assert _to_yfinance_symbol("AAPL") == "AAPL"

    def test_hk_symbol_converted(self) -> None:
        assert _to_yfinance_symbol("0700.HK") == "0700.HK"

    def test_us_suffix_stripped(self) -> None:
        assert _to_yfinance_symbol("AAPL.US") == "AAPL"

    def test_whitespace_stripped(self) -> None:
        assert _to_yfinance_symbol("  BTC-USDT  ") == "BTC-USD"


# ---------------------------------------------------------------------------
# DataLoader — crypto market registration
# ---------------------------------------------------------------------------


class TestDataLoaderCryptoMarket:
    def test_crypto_in_markets(self) -> None:
        assert "crypto" in DataLoader.markets

    def test_us_equity_still_supported(self) -> None:
        assert "us_equity" in DataLoader.markets

    def test_hk_equity_still_supported(self) -> None:
        assert "hk_equity" in DataLoader.markets

    def test_does_not_require_auth(self) -> None:
        assert DataLoader.requires_auth is False

    def test_is_available(self) -> None:
        """yfinance should be available if the package is installed."""
        loader = DataLoader()
        assert loader.is_available() is True


def _download_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [1.0, 2.0],
            "High": [1.5, 2.5],
            "Low": [0.5, 1.5],
            "Close": [1.2, 2.2],
            "Volume": [100, 200],
        },
        index=pd.DatetimeIndex(["2025-01-02", "2025-01-03"], name="Date"),
    )


def test_fetch_passes_inclusive_end_date_to_yfinance_as_exclusive_end(monkeypatch: pytest.MonkeyPatch) -> None:
    import backtest.loaders.yfinance_loader as yfl

    monkeypatch.delenv("VIBE_TRADING_DATA_CACHE", raising=False)
    calls = []

    def fake_download(tickers, start_date, end_date, interval):
        calls.append((tickers, start_date, end_date, interval))
        return _download_frame()

    monkeypatch.setattr(yfl, "_download_history", fake_download)

    result = yfl.DataLoader().fetch(["AAPL.US"], "2025-01-01", "2025-01-03")

    assert "AAPL.US" in result
    assert calls == [(["AAPL"], "2025-01-01", "2025-01-04", "1d")]


def test_fallback_single_symbol_download_uses_inclusive_end_date(monkeypatch: pytest.MonkeyPatch) -> None:
    import backtest.loaders.yfinance_loader as yfl

    monkeypatch.delenv("VIBE_TRADING_DATA_CACHE", raising=False)
    calls = []

    def fake_download(tickers, start_date, end_date, interval):
        calls.append((tickers, start_date, end_date, interval))
        if isinstance(tickers, list):
            return pd.DataFrame()
        return _download_frame()

    monkeypatch.setattr(yfl, "_download_history", fake_download)

    result = yfl.DataLoader().fetch(["AAPL.US"], "2025-01-01", "2025-01-03")

    assert "AAPL.US" in result
    assert calls == [
        (["AAPL"], "2025-01-01", "2025-01-04", "1d"),
        ("AAPL", "2025-01-01", "2025-01-04", "1d"),
    ]


def test_yfinance_cache_lookup_keeps_requested_end_date(monkeypatch: pytest.MonkeyPatch) -> None:
    import backtest.loaders.yfinance_loader as yfl

    cache_calls = []

    def fake_cache_get(**kwargs):
        cache_calls.append(kwargs)
        return _download_frame()

    def fail_download(*_args, **_kwargs):
        raise AssertionError("cache hit should skip yfinance download")

    monkeypatch.setattr(yfl, "loader_cache_get", fake_cache_get)
    monkeypatch.setattr(yfl, "_download_history", fail_download)

    result = yfl.DataLoader().fetch(["AAPL.US"], "2025-01-01", "2025-01-03")

    assert "AAPL.US" in result
    assert cache_calls[0]["symbol"] == "AAPL"
    assert cache_calls[0]["start_date"] == "2025-01-01"
    assert cache_calls[0]["end_date"] == "2025-01-03"
