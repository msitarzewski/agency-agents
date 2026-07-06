"""Tests for the Sina US-equity daily OHLCV loader.

All HTTP is mocked at :func:`backtest.loaders._http.throttled_get` (imported into
the loader module as ``sina_loader.throttled_get``), so no test touches a live
Sina endpoint.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from backtest.loaders.sina_loader import (
    DataLoader,
    _bars_to_frame,
    _is_us_equity,
    _strip_jsonp,
    _to_sina_symbol,
)


# ---------------------------------------------------------------------------
# Symbol detection / mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, expected",
    [
        ("AAPL.US", True),
        ("aapl.us", True),
        ("BRK.B.US", True),
        ("600519.SH", False),
        ("00700.HK", False),
        ("BTC-USDT", False),
        ("", False),
    ],
)
def test_is_us_equity(code: str, expected: bool) -> None:
    assert _is_us_equity(code) is expected


@pytest.mark.parametrize(
    "code, expected",
    [("AAPL.US", "AAPL"), ("aapl.us", "AAPL"), ("BRK.B.US", "BRK.B")],
)
def test_to_sina_symbol(code: str, expected: bool) -> None:
    assert _to_sina_symbol(code) == expected


# ---------------------------------------------------------------------------
# JSONP wrapper stripping
# ---------------------------------------------------------------------------


def _jsonp(bars_json: str) -> str:
    return f"var x=({bars_json});"


def test_strip_jsonp_extracts_array() -> None:
    raw = _jsonp('[{"d":"2024-01-02","o":"1","h":"2","l":"0.5","c":"1.5","v":"100"}]')
    bars = _strip_jsonp(raw)
    assert isinstance(bars, list)
    assert bars[0]["d"] == "2024-01-02"


def test_strip_jsonp_handles_extra_whitespace() -> None:
    raw = "  var x = ( [] )  ; \n"
    assert _strip_jsonp(raw) == []


def test_strip_jsonp_raises_on_garbage() -> None:
    with pytest.raises(ValueError, match="no JSON array"):
        _strip_jsonp("not jsonp at all")


def test_strip_jsonp_raises_when_payload_not_list() -> None:
    with pytest.raises(ValueError):
        _strip_jsonp('var x=({"d":"x"});')


# ---------------------------------------------------------------------------
# Bar reshaping
# ---------------------------------------------------------------------------


_SAMPLE_BARS = [
    {"d": "2024-01-02", "o": "10.0", "h": "11.0", "l": "9.5", "c": "10.5", "v": "1000"},
    {"d": "2024-01-03", "o": "10.5", "h": "12.0", "l": "10.0", "c": "11.5", "v": "2000"},
    {"d": "2024-01-04", "o": "11.5", "h": "13.0", "l": "11.0", "c": "12.5", "v": "3000"},
]


def test_bars_to_frame_shape_and_dtypes() -> None:
    df = _bars_to_frame(_SAMPLE_BARS, "2024-01-01", "2024-01-31")
    assert df is not None
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.name == "trade_date"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert all(str(df[c].dtype) == "float64" for c in df.columns)
    assert len(df) == 3
    assert df.index.is_monotonic_increasing


def test_bars_to_frame_clips_to_window() -> None:
    df = _bars_to_frame(_SAMPLE_BARS, "2024-01-03", "2024-01-03")
    assert df is not None
    assert len(df) == 1
    assert df.index[0] == pd.Timestamp("2024-01-03")


def test_bars_to_frame_empty_window_returns_none() -> None:
    assert _bars_to_frame(_SAMPLE_BARS, "2030-01-01", "2030-01-02") is None


def test_bars_to_frame_skips_malformed_rows() -> None:
    bars = [
        {"d": "2024-01-02", "o": "10", "h": "11", "l": "9", "c": "10", "v": "1"},
        {"d": "2024-01-03", "o": "bad", "h": "11", "l": "9", "c": "10", "v": "1"},
        {"no_date": True},
        "junk",
    ]
    df = _bars_to_frame(bars, "2024-01-01", "2024-01-31")
    assert df is not None
    assert len(df) == 1


def test_bars_to_frame_all_malformed_returns_none() -> None:
    assert _bars_to_frame([{"bad": 1}, "x"], "2024-01-01", "2024-01-31") is None


# ---------------------------------------------------------------------------
# Loader behavior (HTTP mocked)
# ---------------------------------------------------------------------------


def _fake_response(text: str, status_ok: bool = True):
    def raise_for_status() -> None:
        if not status_ok:
            raise RuntimeError("HTTP error")

    return SimpleNamespace(text=text, raise_for_status=raise_for_status)


def test_fetch_returns_frame_for_us_symbol() -> None:
    raw = _jsonp(
        '[{"d":"2024-01-02","o":"10.0","h":"11.0","l":"9.5","c":"10.5","v":"1000"},'
        '{"d":"2024-01-03","o":"10.5","h":"12.0","l":"10.0","c":"11.5","v":"2000"}]'
    )
    with patch(
        "backtest.loaders.sina_loader.throttled_get",
        return_value=_fake_response(raw),
    ) as mock_get:
        out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")

    assert "AAPL.US" in out
    df = out["AAPL.US"]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.name == "trade_date"
    assert len(df) == 2
    # Symbol stripping: Sina called with the bare ticker.
    assert mock_get.call_args.kwargs["params"] == {"symbol": "AAPL"}
    assert mock_get.call_args.kwargs["host_key"] == "sina"


def test_fetch_skips_non_us_symbols_without_http() -> None:
    with patch("backtest.loaders.sina_loader.throttled_get") as mock_get:
        out = DataLoader().fetch(["600519.SH", "00700.HK", "BTC-USDT"], "2024-01-01", "2024-01-31")
    assert out == {}
    mock_get.assert_not_called()


def test_fetch_one_symbol_failure_does_not_abort_batch() -> None:
    good = _jsonp('[{"d":"2024-01-02","o":"1","h":"2","l":"0.5","c":"1.5","v":"100"}]')

    def side_effect(*args, **kwargs):
        if kwargs["params"]["symbol"] == "BAD":
            raise RuntimeError("network blip")
        return _fake_response(good)

    with patch("backtest.loaders.sina_loader.throttled_get", side_effect=side_effect):
        out = DataLoader().fetch(["BAD.US", "AAPL.US"], "2024-01-01", "2024-01-31")

    assert "BAD.US" not in out
    assert "AAPL.US" in out


def test_fetch_non_2xx_status_skips_symbol() -> None:
    with patch(
        "backtest.loaders.sina_loader.throttled_get",
        return_value=_fake_response("var x=([]);", status_ok=False),
    ):
        out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
    assert out == {}


def test_fetch_rejects_non_daily_interval() -> None:
    with pytest.raises(ValueError, match="daily-only"):
        DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31", interval="5m")


def test_fetch_invalid_date_range_raises() -> None:
    with pytest.raises(ValueError):
        DataLoader().fetch(["AAPL.US"], "2024-02-01", "2024-01-01")


def test_is_available_always_true() -> None:
    assert DataLoader().is_available() is True


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


def test_register_decorator_added_sina_to_registry() -> None:
    from backtest.loaders.registry import LOADER_REGISTRY

    assert LOADER_REGISTRY.get("sina") is DataLoader
    assert DataLoader.markets == {"us_equity"}
    assert DataLoader.requires_auth is False
