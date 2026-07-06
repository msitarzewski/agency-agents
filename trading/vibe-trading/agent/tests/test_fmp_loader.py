"""Tests for fmp_loader: auth gating, symbol mapping, parsing, batch resilience.

All HTTP is mocked at :func:`backtest.loaders._http.throttled_get_json` (imported
into the loader module), so no test touches a live FMP endpoint.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from backtest.loaders import fmp_loader as fl
from backtest.loaders.fmp_loader import DataLoader, _fmp_symbol, _parse_historical


def _body(symbol, bars):
    """Build a minimal FMP historical-price-full body."""
    return {"symbol": symbol, "historical": bars}


_AAPL_BARS = [
    {"date": "2024-01-04", "open": 3.0, "high": 4.0, "low": 2.5, "close": 3.5, "volume": 200.0},
    {"date": "2024-01-03", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100.0},
]


class TestRegistration:
    """Loader self-registers with the expected metadata."""

    def test_registered_in_registry(self):
        from backtest.loaders import registry

        registry._ensure_registered()
        # Importing the module fired @register regardless of registry bootstrap.
        assert registry.LOADER_REGISTRY.get("fmp") is DataLoader

    def test_metadata(self):
        assert DataLoader.name == "fmp"
        assert DataLoader.markets == {"us_equity"}
        assert DataLoader.requires_auth is True


class TestIsAvailable:
    """Availability is gated purely on FMP_API_KEY presence."""

    def test_available_with_key(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "secret")
        assert DataLoader().is_available() is True

    def test_unavailable_without_key(self, monkeypatch):
        monkeypatch.delenv("FMP_API_KEY", raising=False)
        assert DataLoader().is_available() is False

    def test_unavailable_with_blank_key(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "   ")
        assert DataLoader().is_available() is False


class TestSymbolMapping:
    """US tickers are bare; the .US project suffix is dropped."""

    def test_strips_us_suffix(self):
        assert _fmp_symbol("AAPL.US") == "AAPL"

    def test_bare_ticker_uppercased(self):
        assert _fmp_symbol("msft") == "MSFT"

    def test_passthrough_other(self):
        assert _fmp_symbol("brk-b") == "BRK-B"


class TestParseHistorical:
    """Pure parsing of the JSON body needs no network."""

    def test_sorts_ascending_and_typed(self):
        df = _parse_historical(_body("AAPL", _AAPL_BARS))
        assert list(df.index) == [pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-04")]
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "trade_date"
        assert df["close"].iloc[0] == 1.5
        for col in df.columns:
            assert df[col].dtype == float

    def test_integer_volume_cast_to_float(self):
        # FMP often returns integer volume; the float-OHLCV contract requires
        # every numeric column (incl. volume) to be float, not int64.
        bars = [
            {"date": "2024-01-03", "open": 1, "high": 2, "low": 0, "close": 1, "volume": 100},
            {"date": "2024-01-04", "open": 3, "high": 4, "low": 2, "close": 3, "volume": 200},
        ]
        df = _parse_historical(_body("AAPL", bars))
        assert df["volume"].dtype == float
        for col in df.columns:
            assert df[col].dtype == float

    def test_empty_historical_returns_none(self):
        assert _parse_historical(_body("AAPL", [])) is None

    def test_missing_historical_key_returns_none(self):
        assert _parse_historical({"symbol": "AAPL"}) is None

    def test_non_dict_payload_returns_none(self):
        assert _parse_historical(None) is None
        assert _parse_historical([]) is None

    def test_rows_with_incomplete_ohlc_dropped(self):
        bars = [
            {"date": "2024-01-03", "open": None, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100.0},
        ]
        assert _parse_historical(_body("AAPL", bars)) is None


class TestFetch:
    """End-to-end fetch with the HTTP layer mocked."""

    def test_fetch_one_symbol(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "secret")
        with patch.object(fl, "throttled_get_json", return_value=_body("AAPL", _AAPL_BARS)) as mock_get:
            out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
        assert set(out) == {"AAPL.US"}
        assert len(out["AAPL.US"]) == 2
        # .US suffix stripped in the request URL.
        url = mock_get.call_args[0][0]
        assert url.endswith("/AAPL")
        params = mock_get.call_args.kwargs["params"]
        assert params == {"from": "2024-01-01", "to": "2024-01-31", "apikey": "secret"}

    def test_one_failing_symbol_does_not_abort_batch(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "secret")

        def _side(url, **kwargs):
            if url.endswith("/BAD"):
                raise RuntimeError("boom")
            return _body("AAPL", _AAPL_BARS)

        with patch.object(fl, "throttled_get_json", side_effect=_side):
            out = DataLoader().fetch(["BAD.US", "AAPL.US"], "2024-01-01", "2024-01-31")
        assert set(out) == {"AAPL.US"}

    def test_empty_result_symbol_omitted(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "secret")
        with patch.object(fl, "throttled_get_json", return_value=_body("ZZZZ", [])):
            out = DataLoader().fetch(["ZZZZ.US"], "2024-01-01", "2024-01-31")
        assert out == {}

    def test_non_daily_interval_returns_empty(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "secret")
        with patch.object(fl, "throttled_get_json") as mock_get:
            out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31", interval="5m")
        assert out == {}
        mock_get.assert_not_called()

    def test_invalid_date_range_raises(self, monkeypatch):
        monkeypatch.setenv("FMP_API_KEY", "secret")
        with pytest.raises(ValueError):
            DataLoader().fetch(["AAPL.US"], "2024-02-01", "2024-01-01")

    def test_missing_key_at_fetch_time_skips_symbol(self, monkeypatch):
        monkeypatch.delenv("FMP_API_KEY", raising=False)
        with patch.object(fl, "throttled_get_json") as mock_get:
            out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
        assert out == {}
        mock_get.assert_not_called()
