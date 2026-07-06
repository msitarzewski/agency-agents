"""Tests for stooq_loader: symbol mapping, CSV parsing, batch isolation, errors.

All HTTP is mocked — no test reaches a live Stooq endpoint. The loader imports
``throttled_get`` from :mod:`backtest.loaders._http` into its own namespace, so
we monkeypatch that name on the ``stooq_loader`` module.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import pytest
import requests

from backtest.loaders import stooq_loader

_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2024-01-03,184.22,185.88,183.43,184.25,58414460\n"
    "2024-01-02,187.15,188.44,183.89,185.64,82488700\n"
)


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` used by throttled_get."""

    def __init__(self, *, status_code: int = 200, text: str = "") -> None:
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


# ---------------------------------------------------------------------------
# Loader contract / registration
# ---------------------------------------------------------------------------


class TestLoaderContract:
    """Static attributes and availability."""

    def test_attributes(self):
        loader = stooq_loader.DataLoader()
        assert loader.name == "stooq"
        assert loader.markets == {"us_equity"}
        assert loader.requires_auth is False
        assert loader.is_available() is True


# ---------------------------------------------------------------------------
# Symbol mapping
# ---------------------------------------------------------------------------


class TestMapSymbol:
    """Vibe-Trading -> Stooq ticker translation."""

    def test_us_lowercased(self):
        assert stooq_loader.map_symbol("AAPL.US") == "aapl.us"

    def test_strips_and_lowercases(self):
        assert stooq_loader.map_symbol("  MSFT.US ") == "msft.us"


# ---------------------------------------------------------------------------
# CSV parsing via fetch
# ---------------------------------------------------------------------------


class TestFetch:
    """End-to-end fetch with throttled_get mocked."""

    def test_parses_csv_into_sorted_ohlcv(self, monkeypatch):
        captured: Dict[str, Any] = {}

        def fake_get(url, **kwargs):
            captured["url"] = url
            captured["params"] = kwargs.get("params")
            captured["host_key"] = kwargs.get("host_key")
            return _FakeResponse(text=_CSV)

        monkeypatch.setattr(stooq_loader, "throttled_get", fake_get)

        out = stooq_loader.DataLoader().fetch(
            ["AAPL.US"], "2024-01-01", "2024-01-31",
        )

        assert captured["url"] == stooq_loader._BASE_URL
        assert captured["host_key"] == "stooq"
        assert captured["params"] == {
            "s": "aapl.us",
            "d1": "20240101",
            "d2": "20240131",
            "i": "d",
        }

        assert list(out) == ["AAPL.US"]
        df = out["AAPL.US"]
        assert df.index.name == "trade_date"
        assert isinstance(df.index, pd.DatetimeIndex)
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        # Sorted ascending: 01-02 before 01-03.
        assert list(df.index) == [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]
        assert df.loc[pd.Timestamp("2024-01-02"), "open"] == pytest.approx(187.15)
        assert df.loc[pd.Timestamp("2024-01-03"), "close"] == pytest.approx(184.25)
        assert df["volume"].dtype == float

    def test_nd_body_yields_no_data(self, monkeypatch):
        monkeypatch.setattr(
            stooq_loader, "throttled_get", lambda url, **kw: _FakeResponse(text="N/D\n")
        )
        out = stooq_loader.DataLoader().fetch(["BOGUS.US"], "2024-01-01", "2024-01-31")
        assert out == {}

    def test_empty_body_yields_no_data(self, monkeypatch):
        monkeypatch.setattr(
            stooq_loader, "throttled_get", lambda url, **kw: _FakeResponse(text="   ")
        )
        out = stooq_loader.DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
        assert out == {}

    def test_one_bad_symbol_does_not_abort_batch(self, monkeypatch):
        def fake_get(url, **kwargs):
            symbol = kwargs["params"]["s"]
            if symbol == "boom.us":
                raise requests.ConnectionError("network down")
            return _FakeResponse(text=_CSV)

        monkeypatch.setattr(stooq_loader, "throttled_get", fake_get)

        out = stooq_loader.DataLoader().fetch(
            ["BOOM.US", "AAPL.US"], "2024-01-01", "2024-01-31",
        )
        # The failing symbol is skipped; the good one still comes through.
        assert list(out) == ["AAPL.US"]

    def test_http_error_skips_symbol(self, monkeypatch):
        monkeypatch.setattr(
            stooq_loader,
            "throttled_get",
            lambda url, **kw: _FakeResponse(status_code=429, text=""),
        )
        out = stooq_loader.DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
        assert out == {}

    def test_invalid_date_range_raises(self):
        with pytest.raises(ValueError):
            stooq_loader.DataLoader().fetch(["AAPL.US"], "2024-02-01", "2024-01-01")


# ---------------------------------------------------------------------------
# Direct CSV parser unit coverage
# ---------------------------------------------------------------------------


class TestParseCsv:
    """`_parse_csv` edge handling."""

    def test_rows_with_nan_ohlc_dropped(self):
        body = (
            "Date,Open,High,Low,Close,Volume\n"
            "2024-01-02,,,,,\n"
            "2024-01-03,1,2,0.5,1.5,100\n"
        )
        df = stooq_loader._parse_csv(body)
        assert list(df.index) == [pd.Timestamp("2024-01-03")]

    def test_missing_columns_returns_none(self):
        assert stooq_loader._parse_csv("Date,Close\n2024-01-03,1.5\n") is None

    def test_all_rows_dropped_returns_none(self):
        body = "Date,Open,High,Low,Close,Volume\n2024-01-02,,,,,\n"
        assert stooq_loader._parse_csv(body) is None
