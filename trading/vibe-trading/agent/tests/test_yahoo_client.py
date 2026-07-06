"""Tests for yahoo_client: symbol mapping, payload parsing, crumb retry, errors.

All HTTP is mocked — no test ever reaches a live Yahoo endpoint. The client
imports ``throttled_get`` / ``throttled_get_json`` from
:mod:`backtest.loaders._http` into its own namespace, so we monkeypatch those
names on the ``yahoo_client`` module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest
import requests

from backtest.loaders import yahoo_client


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` used by throttled_get."""

    def __init__(
        self,
        *,
        status_code: int = 200,
        text: str = "",
        json_body: Optional[Any] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._json_body = json_body
        self.cookies = requests.utils.cookiejar_from_dict(cookies or {})

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self) -> Any:
        return self._json_body


def _reset_crumb() -> None:
    """Clear the process-wide crumb cache so each test handshakes fresh."""
    yahoo_client._CRUMB_STORE = yahoo_client._CrumbStore()


# ---------------------------------------------------------------------------
# Symbol mapping
# ---------------------------------------------------------------------------


class TestMapSymbol:
    """Vibe-Trading -> Yahoo ticker translation."""

    def test_us_suffix_stripped(self):
        assert yahoo_client.map_symbol("AAPL.US") == "AAPL"
        assert yahoo_client.map_symbol("aapl.us") == "aapl"

    def test_hk_normalized_to_four_digits(self):
        assert yahoo_client.map_symbol("00700.HK") == "0700.HK"
        assert yahoo_client.map_symbol("09988.HK") == "9988.HK"

    def test_hk_already_four_digits_unchanged(self):
        assert yahoo_client.map_symbol("0700.HK") == "0700.HK"

    def test_passthrough_for_other_symbols(self):
        assert yahoo_client.map_symbol("BTC-USD") == "BTC-USD"
        assert yahoo_client.map_symbol("^GSPC") == "^GSPC"


# ---------------------------------------------------------------------------
# get_chart parsing
# ---------------------------------------------------------------------------


class TestGetChart:
    """v8 chart payload -> ascending OHLCV rows."""

    def test_parses_ascending_rows_and_maps_symbol(self, monkeypatch):
        captured: Dict[str, Any] = {}

        def fake_get_json(url, **kwargs):
            captured["url"] = url
            captured["params"] = kwargs.get("params")
            return {
                "chart": {
                    "error": None,
                    "result": [
                        {
                            "timestamp": [1700000000, 1700086400, 1700172800],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [10.0, 11.0, None],
                                        "high": [10.5, 11.5, None],
                                        "low": [9.5, 10.5, None],
                                        "close": [10.2, 11.2, None],
                                        "volume": [1000, 2000, None],
                                    }
                                ]
                            },
                        }
                    ],
                }
            }

        monkeypatch.setattr(yahoo_client, "throttled_get_json", fake_get_json)

        rows = yahoo_client.get_chart("AAPL.US", interval="1d", range_="5d")

        assert captured["url"].endswith("/AAPL")
        assert captured["params"] == {"interval": "1d", "range": "5d"}
        # Third bar has null OHLC and must be dropped.
        assert len(rows) == 2
        assert rows[0] == {
            "trade_date": 1700000000,
            "open": 10.0,
            "high": 10.5,
            "low": 9.5,
            "close": 10.2,
            "volume": 1000.0,
        }
        assert rows[1]["trade_date"] == 1700086400

    def test_period_window_when_no_range(self, monkeypatch):
        captured: Dict[str, Any] = {}

        def fake_get_json(url, **kwargs):
            captured["params"] = kwargs.get("params")
            return {"chart": {"result": [{"timestamp": [], "indicators": {"quote": [{}]}}]}}

        monkeypatch.setattr(yahoo_client, "throttled_get_json", fake_get_json)

        rows = yahoo_client.get_chart("0700.HK", period1=100, period2=200)

        assert rows == []
        assert captured["params"] == {"interval": "1d", "period1": 100, "period2": 200}

    def test_chart_error_raises(self, monkeypatch):
        def fake_get_json(url, **kwargs):
            return {"chart": {"error": {"code": "Not Found", "description": "No data found"}}}

        monkeypatch.setattr(yahoo_client, "throttled_get_json", fake_get_json)

        with pytest.raises(ValueError, match="No data found"):
            yahoo_client.get_chart("BOGUS.US", range_="1d")


# ---------------------------------------------------------------------------
# get_quote_summary crumb handshake + 401 retry
# ---------------------------------------------------------------------------


class TestGetQuoteSummary:
    """v10 quoteSummary with the cookie+crumb handshake."""

    def test_handshake_then_success(self, monkeypatch):
        _reset_crumb()
        calls: List[str] = []

        def fake_get(url, **kwargs):
            calls.append(url)
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "token"})
            if url == yahoo_client._CRUMB_URL:
                assert kwargs["headers"]["Cookie"] == "A1=token"
                return _FakeResponse(text="the-crumb\n")
            # quoteSummary call
            assert kwargs["params"]["crumb"] == "the-crumb"
            assert kwargs["params"]["modules"] == "price,summaryDetail"
            assert kwargs["headers"]["Cookie"] == "A1=token"
            return _FakeResponse(
                json_body={"quoteSummary": {"error": None, "result": [{"price": {"symbol": "AAPL"}}]}}
            )

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        result = yahoo_client.get_quote_summary("AAPL.US", ["price", "summaryDetail"])

        assert result == {"price": {"symbol": "AAPL"}}
        # cookie + crumb handshake, then the data call.
        assert calls.count(yahoo_client._COOKIE_URL) == 1
        assert calls.count(yahoo_client._CRUMB_URL) == 1

    def test_401_triggers_single_crumb_refresh(self, monkeypatch):
        _reset_crumb()
        crumbs = iter(["stale-crumb", "fresh-crumb"])
        summary_attempts: List[str] = []

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            if url == yahoo_client._CRUMB_URL:
                return _FakeResponse(text=next(crumbs))
            crumb = kwargs["params"]["crumb"]
            summary_attempts.append(crumb)
            if crumb == "stale-crumb":
                return _FakeResponse(status_code=401)
            return _FakeResponse(json_body={"quoteSummary": {"result": [{"ok": True}]}})

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        result = yahoo_client.get_quote_summary("MSFT", ["price"])

        assert result == {"ok": True}
        # First attempt with stale crumb 401s, refreshed crumb succeeds.
        assert summary_attempts == ["stale-crumb", "fresh-crumb"]

    def test_persistent_401_propagates(self, monkeypatch):
        _reset_crumb()

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            if url == yahoo_client._CRUMB_URL:
                return _FakeResponse(text="any-crumb")
            return _FakeResponse(status_code=401)

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        with pytest.raises(requests.HTTPError):
            yahoo_client.get_quote_summary("MSFT", ["price"])

    def test_empty_crumb_raises(self, monkeypatch):
        _reset_crumb()

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            return _FakeResponse(text="   ")

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        with pytest.raises(ValueError, match="empty crumb"):
            yahoo_client.get_quote_summary("MSFT", ["price"])


# ---------------------------------------------------------------------------
# get_options + search
# ---------------------------------------------------------------------------


class TestGetOptions:
    """v7 option chain — now behind the same cookie+crumb handshake."""

    def test_handshake_carries_crumb_and_cookie(self, monkeypatch):
        _reset_crumb()
        captured: Dict[str, Any] = {}
        calls: List[str] = []

        def fake_get(url, **kwargs):
            calls.append(url)
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "token"})
            if url == yahoo_client._CRUMB_URL:
                assert kwargs["headers"]["Cookie"] == "A1=token"
                return _FakeResponse(text="the-crumb\n")
            # options call must carry both the crumb param and the cookie.
            captured["url"] = url
            captured["params"] = kwargs.get("params")
            captured["headers"] = kwargs.get("headers")
            return _FakeResponse(
                json_body={"optionChain": {"result": [{"expirationDates": [1, 2]}]}}
            )

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        result = yahoo_client.get_options("00700.HK", expiration=1700000000)

        assert captured["url"].endswith("/0700.HK")
        assert captured["params"] == {"crumb": "the-crumb", "date": 1700000000}
        assert captured["headers"]["Cookie"] == "A1=token"
        assert result == {"expirationDates": [1, 2]}
        assert calls.count(yahoo_client._COOKIE_URL) == 1
        assert calls.count(yahoo_client._CRUMB_URL) == 1

    def test_401_triggers_single_crumb_refresh(self, monkeypatch):
        _reset_crumb()
        crumbs = iter(["stale-crumb", "fresh-crumb"])
        options_attempts: List[str] = []

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            if url == yahoo_client._CRUMB_URL:
                return _FakeResponse(text=next(crumbs))
            crumb = kwargs["params"]["crumb"]
            options_attempts.append(crumb)
            if crumb == "stale-crumb":
                return _FakeResponse(status_code=401)
            return _FakeResponse(json_body={"optionChain": {"result": [{"ok": True}]}})

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        result = yahoo_client.get_options("AAPL.US")

        assert result == {"ok": True}
        # Stale crumb 401s, refreshed crumb succeeds — exactly one refresh.
        assert options_attempts == ["stale-crumb", "fresh-crumb"]

    def test_persistent_401_propagates(self, monkeypatch):
        _reset_crumb()

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            if url == yahoo_client._CRUMB_URL:
                return _FakeResponse(text="any-crumb")
            return _FakeResponse(status_code=401)

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        with pytest.raises(requests.HTTPError):
            yahoo_client.get_options("MSFT")

    def test_no_date_param_when_expiration_omitted(self, monkeypatch):
        _reset_crumb()
        captured: Dict[str, Any] = {}

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            if url == yahoo_client._CRUMB_URL:
                return _FakeResponse(text="crumb")
            captured["params"] = kwargs.get("params")
            return _FakeResponse(json_body={"optionChain": {"result": [{}]}})

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        yahoo_client.get_options("AAPL.US")

        assert captured["params"] == {"crumb": "crumb"}

    def test_error_raises(self, monkeypatch):
        _reset_crumb()

        def fake_get(url, **kwargs):
            if url == yahoo_client._COOKIE_URL:
                return _FakeResponse(cookies={"A1": "c"})
            if url == yahoo_client._CRUMB_URL:
                return _FakeResponse(text="crumb")
            return _FakeResponse(
                json_body={"optionChain": {"error": {"description": "bad symbol"}}}
            )

        monkeypatch.setattr(yahoo_client, "throttled_get", fake_get)

        with pytest.raises(ValueError, match="bad symbol"):
            yahoo_client.get_options("NOPE.US")


class TestSearch:
    """v1 search."""

    def test_filters_to_dict_quotes(self, monkeypatch):
        def fake_get_json(url, **kwargs):
            assert kwargs["params"] == {"q": "apple"}
            return {"quotes": [{"symbol": "AAPL"}, "garbage", {"symbol": "APLE"}]}

        monkeypatch.setattr(yahoo_client, "throttled_get_json", fake_get_json)

        quotes = yahoo_client.search("apple")

        assert quotes == [{"symbol": "AAPL"}, {"symbol": "APLE"}]

    def test_empty_payload_returns_empty(self, monkeypatch):
        monkeypatch.setattr(yahoo_client, "throttled_get_json", lambda url, **kw: {})
        assert yahoo_client.search("zzz") == []
