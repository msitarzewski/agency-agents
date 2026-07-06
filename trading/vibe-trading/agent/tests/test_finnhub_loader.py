"""Tests for finnhub_loader: symbol mapping, payload parsing, auth gating, errors.

All HTTP is mocked — no test ever reaches a live Finnhub endpoint. The loader
imports ``throttled_get_json`` from :mod:`backtest.loaders._http` into its own
namespace, so we monkeypatch that name on the ``finnhub_loader`` module.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backtest.loaders import finnhub_loader
from backtest.loaders.finnhub_loader import (
    DataLoader,
    _to_epoch_seconds,
    _to_finnhub_symbol,
)


def _ok_payload() -> Dict[str, Any]:
    """Two ascending daily candles in Finnhub's parallel-array layout."""
    return {
        "s": "ok",
        "t": [1704067200, 1704153600],  # 2024-01-01, 2024-01-02 (UTC)
        "o": [10.0, 11.0],
        "h": [12.0, 13.0],
        "l": [9.0, 10.5],
        "c": [11.5, 12.5],
        "v": [1000, 2000],
    }


# ---------------------------------------------------------------------------
# Symbol mapping
# ---------------------------------------------------------------------------


class TestToFinnhubSymbol:
    """Vibe-Trading -> Finnhub ticker translation."""

    def test_us_suffix_stripped(self):
        assert _to_finnhub_symbol("AAPL.US") == "AAPL"
        assert _to_finnhub_symbol("aapl.us") == "AAPL"

    def test_bare_ticker_uppercased(self):
        assert _to_finnhub_symbol("msft") == "MSFT"
        assert _to_finnhub_symbol(" tsla ") == "TSLA"


# ---------------------------------------------------------------------------
# Epoch-second bounds
# ---------------------------------------------------------------------------


class TestToEpochSeconds:
    """Inclusive date -> UTC epoch-second bound."""

    def test_start_is_midnight(self):
        assert _to_epoch_seconds("2024-01-01", end_of_day=False) == 1704067200

    def test_end_pushes_to_end_of_day(self):
        # 2024-01-01 23:59:59 UTC.
        assert _to_epoch_seconds("2024-01-01", end_of_day=True) == 1704153599


# ---------------------------------------------------------------------------
# Availability / auth gating
# ---------------------------------------------------------------------------


class TestAvailability:
    """is_available reflects only the env key; __init__ never raises."""

    def test_construct_without_key_does_not_raise(self, monkeypatch):
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        loader = DataLoader()  # must not raise
        assert loader.is_available() is False

    def test_available_when_key_present(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        assert DataLoader().is_available() is True

    def test_metadata(self):
        assert DataLoader.name == "finnhub"
        assert DataLoader.markets == {"us_equity"}
        assert DataLoader.requires_auth is True


# ---------------------------------------------------------------------------
# fetch — happy path, gating, and per-symbol isolation
# ---------------------------------------------------------------------------


class TestFetch:
    """fetch parses payloads, gates on key, and isolates per-symbol failures."""

    def test_returns_empty_without_key(self, monkeypatch):
        monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
        monkeypatch.setenv("VIBE_TRADING_DATA_CACHE", "0")

        def boom(*args, **kwargs):  # pragma: no cover - must never be called
            raise AssertionError("no network call without a key")

        monkeypatch.setattr(finnhub_loader, "throttled_get_json", boom)
        assert DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31") == {}

    def test_parses_candles_into_ohlcv_frame(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        monkeypatch.setenv("VIBE_TRADING_DATA_CACHE", "0")

        captured: Dict[str, Any] = {}

        def fake_get_json(url, **kwargs):
            captured["url"] = url
            captured["params"] = kwargs.get("params")
            return _ok_payload()

        monkeypatch.setattr(finnhub_loader, "throttled_get_json", fake_get_json)

        out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")

        assert list(out.keys()) == ["AAPL.US"]
        df = out["AAPL.US"]
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "trade_date"
        assert isinstance(df.index, pd.DatetimeIndex)
        assert len(df) == 2
        assert df.index.is_monotonic_increasing
        assert df["close"].dtype == float
        assert df["volume"].iloc[0] == 1000.0
        # Symbol is mapped to the bare Finnhub ticker and the token is sent.
        assert captured["url"] == finnhub_loader._CANDLE_URL
        assert captured["params"]["symbol"] == "AAPL"
        assert captured["params"]["resolution"] == "D"
        assert captured["params"]["token"] == "tok_123"

    def test_index_is_nanosecond_resolution(self, monkeypatch):
        """Regression (B9): the trade_date index must be datetime64[ns].

        The epoch ``t`` array used to flow through a ``unit="s"`` conversion
        that left the index at second resolution, diverging from the other
        loaders' nanosecond index and from a plain ``datetime64[ns]`` literal.
        """
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        monkeypatch.setenv("VIBE_TRADING_DATA_CACHE", "0")
        monkeypatch.setattr(
            finnhub_loader, "throttled_get_json", lambda url, **kwargs: _ok_payload()
        )

        df = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")["AAPL.US"]
        assert df.index.dtype == "datetime64[ns]"
        # The actual instants must survive the resolution coercion intact.
        assert list(df.index) == [
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-02"),
        ]

    def test_no_data_status_yields_no_entry(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        monkeypatch.setenv("VIBE_TRADING_DATA_CACHE", "0")
        monkeypatch.setattr(
            finnhub_loader,
            "throttled_get_json",
            lambda url, **kwargs: {"s": "no_data"},
        )
        assert DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31") == {}

    def test_one_failing_symbol_does_not_abort_batch(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        monkeypatch.setenv("VIBE_TRADING_DATA_CACHE", "0")

        def selective(url, **kwargs):
            if kwargs["params"]["symbol"] == "BAD":
                raise RuntimeError("429 rate limited")
            return _ok_payload()

        monkeypatch.setattr(finnhub_loader, "throttled_get_json", selective)

        out = DataLoader().fetch(["BAD.US", "AAPL.US"], "2024-01-01", "2024-01-31")
        assert list(out.keys()) == ["AAPL.US"]

    def test_skips_bars_with_missing_ohlc(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        monkeypatch.setenv("VIBE_TRADING_DATA_CACHE", "0")
        payload = _ok_payload()
        payload["c"] = [None, 12.5]  # first bar's close is a gap

        monkeypatch.setattr(
            finnhub_loader, "throttled_get_json", lambda url, **kwargs: payload
        )
        df = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")["AAPL.US"]
        assert len(df) == 1
        assert df["close"].iloc[0] == 12.5

    def test_empty_codes_returns_empty(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "tok_123")
        assert DataLoader().fetch([], "2024-01-01", "2024-01-31") == {}


class TestRowParsing:
    """_rows_from_payload tolerance for malformed bodies."""

    def test_non_dict_payload(self):
        assert finnhub_loader._rows_from_payload(None) == []
        assert finnhub_loader._rows_from_payload("error") == []

    def test_missing_timestamp_array(self):
        assert finnhub_loader._rows_from_payload({"s": "ok"}) == []

    def test_status_not_ok(self):
        assert finnhub_loader._rows_from_payload({"s": "no_data", "t": [1]}) == []
