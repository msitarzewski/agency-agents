"""Tests for alphavantage_loader: availability, payload parsing, error paths.

All HTTP is mocked at :func:`backtest.loaders._http.throttled_get_json` (imported
into the loader module), so no test touches a live Alpha Vantage endpoint.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from backtest.loaders import alphavantage_loader as av


def _payload(*dates_rows) -> dict:
    """Build a TIME_SERIES_DAILY-shaped payload from (date, o, h, l, c, v) tuples."""
    series = {}
    for date, o, h, l, c, vol in dates_rows:
        series[date] = {
            "1. open": str(o),
            "2. high": str(h),
            "3. low": str(l),
            "4. close": str(c),
            "5. volume": str(vol),
        }
    return {"Time Series (Daily)": series}


@pytest.fixture(autouse=True)
def _clear_key(monkeypatch):
    """Default every test to no key unless it sets one explicitly."""
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    yield


class TestAvailability:
    """is_available() keys off a non-placeholder ALPHAVANTAGE_API_KEY."""

    def test_unset_key_is_unavailable(self):
        assert av.DataLoader().is_available() is False

    def test_placeholder_key_is_unavailable(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "your-alphavantage-api-key")
        assert av.DataLoader().is_available() is False
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "demo")
        assert av.DataLoader().is_available() is False

    def test_real_key_is_available(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        assert av.DataLoader().is_available() is True


class TestRegistration:
    """Loader metadata matches the parcel contract."""

    def test_classvars(self):
        assert av.DataLoader.name == "alphavantage"
        assert av.DataLoader.markets == {"us_equity"}
        assert av.DataLoader.requires_auth is True


class TestFetch:
    """fetch() parses, shapes, and date-slices the daily series."""

    def test_returns_shaped_dataframe(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        payload = _payload(
            ("2024-01-02", 100.0, 112.0, 99.0, 110.0, 1000),
            ("2024-01-03", 110.0, 111.0, 107.0, 108.0, 2000),
        )
        with patch.object(av, "throttled_get_json", return_value=payload) as mock_get:
            out = av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31")

        assert set(out) == {"AAPL"}
        df = out["AAPL"]
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "trade_date"
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.is_monotonic_increasing
        assert all(df[col].dtype == float for col in df.columns)
        assert df.loc["2024-01-02", "open"] == 100.0
        assert df.loc["2024-01-02", "close"] == 110.0
        assert df.loc["2024-01-03", "volume"] == 2000.0
        # Request params carry the documented function + symbol + key.
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["function"] == "TIME_SERIES_DAILY"
        assert kwargs["params"]["symbol"] == "AAPL"
        assert kwargs["params"]["apikey"] == "ABC123"

    def test_slices_to_requested_range(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        payload = _payload(
            ("2023-12-29", 1, 1, 1, 1, 1),
            ("2024-01-02", 2, 2, 2, 2, 2),
            ("2024-02-15", 3, 3, 3, 3, 3),
        )
        with patch.object(av, "throttled_get_json", return_value=payload):
            df = av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31")["AAPL"]
        assert [d.strftime("%Y-%m-%d") for d in df.index] == ["2024-01-02"]

    def test_lowercase_symbol_is_upcased(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        payload = _payload(("2024-01-02", 1, 1, 1, 1, 1))
        with patch.object(av, "throttled_get_json", return_value=payload) as mock_get:
            av.DataLoader().fetch(["aapl"], "2024-01-01", "2024-01-31")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["symbol"] == "AAPL"

    def test_no_key_returns_empty_without_http(self):
        with patch.object(av, "throttled_get_json") as mock_get:
            out = av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31")
        assert out == {}
        mock_get.assert_not_called()


class TestErrorPaths:
    """Bad symbols and quota envelopes never abort the batch."""

    def test_rate_limit_note_skips_symbol(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        with patch.object(
            av, "throttled_get_json", return_value={"Note": "call frequency limit"}
        ):
            assert av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31") == {}

    def test_error_message_skips_symbol(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        with patch.object(
            av, "throttled_get_json", return_value={"Error Message": "invalid symbol"}
        ):
            assert av.DataLoader().fetch(["NOPE"], "2024-01-01", "2024-01-31") == {}

    def test_one_failure_does_not_abort_batch(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        good = _payload(("2024-01-02", 5, 5, 5, 5, 5))

        def side_effect(url, **kwargs):
            if kwargs["params"]["symbol"] == "BAD":
                raise RuntimeError("HTTP 500")
            return good

        with patch.object(av, "throttled_get_json", side_effect=side_effect):
            out = av.DataLoader().fetch(["BAD", "AAPL"], "2024-01-01", "2024-01-31")
        assert set(out) == {"AAPL"}

    def test_data_with_upsell_note_is_parsed_not_rejected(self, monkeypatch):
        """A payload carrying BOTH a usable series and a note keeps the data."""
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        payload = _payload(("2024-01-02", 1, 2, 0.5, 1.5, 10))
        payload["Information"] = (
            "Thank you for using Alpha Vantage! Premium plans unlock higher limits."
        )
        with patch.object(av, "throttled_get_json", return_value=payload):
            out = av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31")
        assert set(out) == {"AAPL"}
        df = out["AAPL"]
        assert [d.strftime("%Y-%m-%d") for d in df.index] == ["2024-01-02"]
        assert df.loc["2024-01-02", "close"] == 1.5

    def test_empty_series_with_note_skips_symbol(self, monkeypatch):
        """An empty series alongside a note still surfaces as an error skip."""
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        payload = {"Time Series (Daily)": {}, "Note": "call frequency limit"}
        with patch.object(av, "throttled_get_json", return_value=payload):
            assert av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31") == {}

    def test_empty_series_omits_symbol(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        with patch.object(
            av, "throttled_get_json", return_value={"Time Series (Daily)": {}}
        ):
            assert av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31") == {}

    def test_malformed_bar_is_skipped(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        payload = {
            "Time Series (Daily)": {
                "2024-01-02": {"1. open": "oops"},
                "2024-01-03": {
                    "1. open": "1", "2. high": "1", "3. low": "1",
                    "4. close": "1", "5. volume": "1",
                },
            }
        }
        with patch.object(av, "throttled_get_json", return_value=payload):
            df = av.DataLoader().fetch(["AAPL"], "2024-01-01", "2024-01-31")["AAPL"]
        assert [d.strftime("%Y-%m-%d") for d in df.index] == ["2024-01-03"]

    def test_invalid_date_range_raises(self, monkeypatch):
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "ABC123")
        with pytest.raises(ValueError):
            av.DataLoader().fetch(["AAPL"], "2024-02-01", "2024-01-01")
