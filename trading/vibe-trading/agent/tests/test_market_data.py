"""Tests for the shared market-data helper layer.

``src.market_data`` is the source-resolution + normalization layer shared by
the MCP server and the agent ``get_market_data`` tool. It shipped (with the
#270 global data layer) without dedicated tests. These cover the
network-free logic: source detection, row capping, JSON-safety, and the
``fetch_market_data`` orchestration via an injected stub loader.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.market_data import (
    DEFAULT_MAX_ROWS,
    _json_safe,
    cap_rows,
    detect_source,
    fetch_market_data,
    fetch_market_data_json,
)


# --------------------------------------------------------------------------
# detect_source
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code,expected",
    [
        ("600519.SH", "tencent"),
        ("000001.SZ", "tencent"),
        ("430139.BJ", "tencent"),
        ("AAPL.US", "yahoo"),
        ("700.HK", "yahoo"),
        ("00700.HK", "yahoo"),
        ("BTC-USDT", "okx"),
        ("ETH/USDT", "ccxt"),
        ("local:my_file", "local"),
        ("something_weird", "tushare"),  # documented fallback
    ],
)
def test_detect_source(code: str, expected: str) -> None:
    assert detect_source(code) == expected


# --------------------------------------------------------------------------
# cap_rows
# --------------------------------------------------------------------------


def test_cap_rows_passthrough_when_under_limit() -> None:
    rows = [{"a": i} for i in range(3)]
    assert cap_rows(rows, 250) is rows


def test_cap_rows_zero_means_no_cap() -> None:
    rows = [{"a": i} for i in range(1000)]
    assert cap_rows(rows, 0) is rows


def test_cap_rows_negative_falls_back_to_default() -> None:
    rows = [{"a": i} for i in range(DEFAULT_MAX_ROWS + 10)]
    out = cap_rows(rows, -5)
    # Negative max_rows is treated as DEFAULT_MAX_ROWS -> truncated payload.
    assert isinstance(out, dict)
    assert out["truncated"] is True


def test_cap_rows_samples_with_stride_and_pins_last() -> None:
    rows = [{"a": i} for i in range(10)]
    out = cap_rows(rows, 4)
    assert isinstance(out, dict)
    assert out["rows"] == 10
    assert out["truncated"] is True
    # Even stride of ceil(10/4)=3 plus the pinned final bar.
    assert out["data"][0] == {"a": 0}
    assert out["data"][-1] == {"a": 9}  # last bar always pinned
    assert out["returned"] == len(out["data"])


# --------------------------------------------------------------------------
# _json_safe
# --------------------------------------------------------------------------


def test_json_safe_non_finite_becomes_none() -> None:
    assert _json_safe(float("nan")) is None
    assert _json_safe(float("inf")) is None
    assert _json_safe(float("-inf")) is None


def test_json_safe_timestamp_isoformat() -> None:
    assert _json_safe(pd.Timestamp("2026-01-01")) == "2026-01-01T00:00:00"


def test_json_safe_numpy_scalar_unwrapped() -> None:
    out = _json_safe(np.int64(5))
    assert out == 5
    assert not isinstance(out, np.integer)


def test_json_safe_plain_value_passthrough() -> None:
    assert _json_safe("hello") == "hello"
    assert _json_safe(3.5) == 3.5


# --------------------------------------------------------------------------
# fetch_market_data (stub loader — no network)
# --------------------------------------------------------------------------


class _StubLoader:
    """Returns a fixed 2-row OHLCV frame for every requested code."""

    def __init__(self) -> None:
        pass

    def fetch(self, codes, start_date, end_date, interval="1D"):
        idx = pd.to_datetime(["2026-01-01", "2026-01-02"])
        idx.name = "trade_date"
        return {
            code: pd.DataFrame({"close": [1.0, 2.0], "volume": [100, 200]}, index=idx)
            for code in codes
        }


class _BadLoader:
    def __init__(self) -> None:
        pass

    def fetch(self, *args, **kwargs):
        raise RuntimeError("loader exploded")


class _PartialLoader:
    """Returns data for only the first requested code."""

    def __init__(self) -> None:
        pass

    def fetch(self, codes, start_date, end_date, interval="1D"):
        idx = pd.to_datetime(["2026-01-01"])
        idx.name = "trade_date"
        return {codes[0]: pd.DataFrame({"close": [1.0]}, index=idx)}


def test_fetch_explicit_source_normalizes_rows() -> None:
    out = fetch_market_data(
        codes=["AAPL.US"],
        start_date="2026-01-01",
        end_date="2026-01-02",
        source="yahoo",
        loader_resolver=lambda src: _StubLoader,
    )
    assert "AAPL.US" in out
    rows = out["AAPL.US"]
    assert rows[0]["trade_date"] == "2026-01-01T00:00:00"  # index reset + isoformat
    assert rows[0]["close"] == 1.0


def test_fetch_auto_groups_by_detected_source() -> None:
    seen: dict[str, list[str]] = {}

    def resolver(src: str):
        seen[src] = []
        return _StubLoader

    out = fetch_market_data(
        codes=["AAPL.US", "BTC-USDT"],
        start_date="2026-01-01",
        end_date="2026-01-02",
        source="auto",
        loader_resolver=resolver,
    )
    # AAPL.US -> yahoo, BTC-USDT -> okx: two distinct loader groups resolved.
    assert set(seen) == {"yahoo", "okx"}
    assert "AAPL.US" in out and "BTC-USDT" in out


def test_fetch_loader_error_falls_through_to_unresolved() -> None:
    out = fetch_market_data(
        codes=["X.US"],
        start_date="2026-01-01",
        end_date="2026-01-02",
        source="yahoo",
        loader_resolver=lambda src: _BadLoader,
    )
    assert out["_unresolved"] == ["X.US"]


def test_fetch_missing_symbol_listed_as_unresolved() -> None:
    out = fetch_market_data(
        codes=["A.US", "B.US"],
        start_date="2026-01-01",
        end_date="2026-01-02",
        source="yahoo",
        loader_resolver=lambda src: _PartialLoader,
    )
    assert "A.US" in out
    assert out["_unresolved"] == ["B.US"]


# --------------------------------------------------------------------------
# fetch_market_data_json
# --------------------------------------------------------------------------


def test_fetch_json_is_strict_and_parseable() -> None:
    payload = fetch_market_data_json(
        codes=["AAPL.US"],
        start_date="2026-01-01",
        end_date="2026-01-02",
        source="yahoo",
        loader_resolver=lambda src: _StubLoader,
    )
    parsed = json.loads(payload)  # must be valid JSON
    assert "AAPL.US" in parsed


def test_fetch_json_rejects_nan_via_allow_nan_false() -> None:
    class _NanLoader:
        def __init__(self) -> None:
            pass

        def fetch(self, codes, start_date, end_date, interval="1D"):
            idx = pd.to_datetime(["2026-01-01"])
            idx.name = "trade_date"
            # A NaN close must be sanitized to null by _json_safe, so strict
            # JSON (allow_nan=False) still succeeds.
            return {codes[0]: pd.DataFrame({"close": [float("nan")]}, index=idx)}

    payload = fetch_market_data_json(
        codes=["A.US"],
        start_date="2026-01-01",
        end_date="2026-01-02",
        source="yahoo",
        loader_resolver=lambda src: _NanLoader,
    )
    parsed = json.loads(payload)
    assert parsed["A.US"][0]["close"] is None
