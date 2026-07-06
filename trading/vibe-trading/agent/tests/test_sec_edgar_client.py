"""Tests for sec_edgar_client: ticker->CIK mapping, CIK padding, payload parse.

All HTTP is fully mocked by patching ``throttled_get_json`` in the client
module — no test makes a real SEC request.
"""
from unittest.mock import patch

import pytest
import requests

from backtest.loaders import sec_edgar_client as sec


_TICKERS_PAYLOAD = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    # lower-case ticker + already-int CIK to exercise normalization
    "2": {"cik_str": 1318605, "ticker": "tsla", "title": "Tesla, Inc."},
}


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the memoized ticker map before and after every test."""
    sec._reset_ticker_cache_for_tests()
    yield
    sec._reset_ticker_cache_for_tests()


class TestCikFor:
    """Ticker -> zero-padded 10-digit CIK resolution."""

    def test_resolves_and_pads_cik(self):
        with patch.object(sec, "throttled_get_json", return_value=_TICKERS_PAYLOAD):
            assert sec.cik_for("AAPL") == "0000320193"

    def test_case_insensitive(self):
        with patch.object(sec, "throttled_get_json", return_value=_TICKERS_PAYLOAD):
            assert sec.cik_for("aapl") == "0000320193"
            assert sec.cik_for("Tsla") == "0001318605"

    def test_unknown_ticker_returns_none(self):
        with patch.object(sec, "throttled_get_json", return_value=_TICKERS_PAYLOAD):
            assert sec.cik_for("NOPE") is None

    def test_empty_ticker_returns_none_without_fetch(self):
        with patch.object(sec, "throttled_get_json") as mock_get:
            assert sec.cik_for("") is None
            assert sec.cik_for("   ") is None
            mock_get.assert_not_called()

    def test_map_is_fetched_once_and_memoized(self):
        with patch.object(
            sec, "throttled_get_json", return_value=_TICKERS_PAYLOAD
        ) as mock_get:
            assert sec.cik_for("AAPL") == "0000320193"
            assert sec.cik_for("MSFT") == "0000789019"
            assert mock_get.call_count == 1

    def test_malformed_rows_skipped(self):
        payload = {
            "0": {"cik_str": 320193, "ticker": "AAPL"},
            "1": {"ticker": "NOCIK"},          # missing cik
            "2": {"cik_str": 5},               # missing ticker
            "3": "garbage",                    # not a dict
        }
        with patch.object(sec, "throttled_get_json", return_value=payload):
            assert sec.cik_for("AAPL") == "0000320193"
            assert sec.cik_for("NOCIK") is None


class TestCikPadding:
    """_pad_cik normalizes ints, padded strings, and CIK-prefixed strings."""

    def test_pads_int(self):
        assert sec._pad_cik(320193) == "0000320193"

    def test_passes_through_already_padded(self):
        assert sec._pad_cik("0000320193") == "0000320193"

    def test_strips_cik_prefix(self):
        assert sec._pad_cik("CIK0000320193") == "0000320193"

    def test_no_digits_raises(self):
        with pytest.raises(ValueError):
            sec._pad_cik("ABC")


class TestSubmissionsAndFacts:
    """Endpoint URL construction + raw payload passthrough."""

    def test_get_submissions_builds_padded_url(self):
        payload = {"cik": "320193", "name": "Apple Inc.", "filings": {}}
        with patch.object(
            sec, "throttled_get_json", return_value=payload
        ) as mock_get:
            out = sec.get_submissions(320193)
        assert out == payload
        called_url = mock_get.call_args[0][0]
        assert called_url == "https://data.sec.gov/submissions/CIK0000320193.json"
        kwargs = mock_get.call_args.kwargs
        assert kwargs["host_key"] == "sec"
        assert kwargs["min_interval"] >= 0.12

    def test_get_company_facts_builds_padded_url(self):
        payload = {"cik": 320193, "facts": {"us-gaap": {}}}
        with patch.object(
            sec, "throttled_get_json", return_value=payload
        ) as mock_get:
            out = sec.get_company_facts("CIK0000320193")
        assert out == payload
        called_url = mock_get.call_args[0][0]
        assert called_url == (
            "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
        )

    def test_compliant_user_agent_sent(self):
        with patch.object(
            sec, "throttled_get_json", return_value={}
        ) as mock_get:
            sec.get_submissions(320193)
        ua = mock_get.call_args.kwargs["headers"]["User-Agent"]
        assert "Vibe-Trading" in ua and "contact" in ua.lower()

    def test_user_agent_env_override(self, monkeypatch):
        monkeypatch.setenv("VIBE_TRADING_SEC_UA", "MyApp/2.0 (me@example.com)")
        with patch.object(
            sec, "throttled_get_json", return_value={}
        ) as mock_get:
            sec.get_company_facts(320193)
        assert mock_get.call_args.kwargs["headers"]["User-Agent"] == (
            "MyApp/2.0 (me@example.com)"
        )


class TestErrorPath:
    """A transport error propagates unchanged for the caller's retry policy."""

    def test_http_error_propagates(self):
        with patch.object(
            sec,
            "throttled_get_json",
            side_effect=requests.HTTPError("404 Not Found"),
        ):
            with pytest.raises(requests.HTTPError):
                sec.get_submissions(999999)

    def test_ticker_fetch_error_propagates(self):
        with patch.object(
            sec,
            "throttled_get_json",
            side_effect=requests.ConnectionError("boom"),
        ):
            with pytest.raises(requests.ConnectionError):
                sec.cik_for("AAPL")
