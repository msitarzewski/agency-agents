"""Regression test for P07 — get_market_data must bound its per-symbol output.

Pre-fix: every row of every symbol was emitted, so "1 symbol, 1 year, daily"
(~251 rows) already breached the MCP token cap and had to spool to a file.
Post-fix (G3): a `max_rows` cap (default 250) returns an *even-stride*
downsample (every step-th bar, last bar pinned) plus truncation metadata for
oversized symbols — spanning the full range with no `_gap` sentinel; small
queries are unchanged (plain list); `max_rows=0` restores the unbounded
legacy behavior; a negative `max_rows` is invalid and enforces the cap.
"""

from __future__ import annotations

import json

import pandas as pd

import mcp_server

_gmd = getattr(mcp_server.get_market_data, "fn", None) or getattr(
    mcp_server.get_market_data, "__wrapped__", mcp_server.get_market_data
)


def _loader_with_rows(n: int):
    idx = pd.date_range("2025-01-01", periods=n, freq="D")
    df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}, index=idx)
    df.index.name = "trade_date"

    class _L:
        def fetch(self, codes, start, end, interval="1D"):
            return {"X.US": df}

    return _L


def _call(monkeypatch, n, **kw):
    monkeypatch.setattr(mcp_server, "_get_loader", lambda src: _loader_with_rows(n))
    return json.loads(_gmd(codes=["X.US"], start_date="2025-01-01", end_date="2026-01-01", source="yfinance", **kw))


def test_oversized_symbol_is_capped_with_metadata(monkeypatch):
    out = _call(monkeypatch, 300)["X.US"]
    assert out["truncated"] is True
    assert out["rows"] == 300
    assert out["returned"] == len(out["data"])
    assert out["returned"] <= 251  # 250-stride sample, last bar maybe pinned
    assert "every-" in out["policy"]
    assert not any(isinstance(row, dict) and "_gap" in row for row in out["data"])


def test_small_query_unchanged_plain_list(monkeypatch):
    """No-regression: under the cap the shape is the original plain list."""
    out = _call(monkeypatch, 50)["X.US"]
    assert isinstance(out, list) and len(out) == 50


def test_max_rows_zero_disables_cap(monkeypatch):
    out = _call(monkeypatch, 300, max_rows=0)["X.US"]
    assert isinstance(out, list) and len(out) == 300


def test_default_caps_canonical_one_year_daily(monkeypatch):
    """The canonical ~251-row 1y-daily request must no longer be unbounded."""
    out = _call(monkeypatch, 251)["X.US"]
    assert isinstance(out, dict) and out["truncated"] is True


def test_boundary_n_equals_max_rows_is_plain_list(monkeypatch):
    """G3 (i): exactly at the cap returns the plain list, not truncated."""
    out = _call(monkeypatch, 250, max_rows=250)["X.US"]
    assert isinstance(out, list) and len(out) == 250


def test_negative_max_rows_still_caps(monkeypatch):
    """G3 (ii): a negative max_rows is invalid -> cap enforced, never unbounded."""
    out = _call(monkeypatch, 300, max_rows=-1)["X.US"]
    assert isinstance(out, dict)
    assert out["truncated"] is True
    assert out["returned"] == len(out["data"]) < 300


def test_stride_form_last_pinned_increasing_no_gap(monkeypatch):
    """G3 (iii): stride sample — last row == original last, dates strictly
    increasing, and no {"_gap": ...} sentinel anywhere."""
    out = _call(monkeypatch, 1000)["X.US"]
    data = out["data"]
    assert not any(isinstance(row, dict) and "_gap" in row for row in data)
    dates = [row["trade_date"] for row in data]
    assert dates == sorted(dates) and len(set(dates)) == len(dates)
    # original series ends 2025-01-01 + 999 days; last sampled bar is pinned.
    last_expected = pd.Timestamp("2025-01-01") + pd.Timedelta(days=999)
    assert pd.Timestamp(data[-1]["trade_date"]) == last_expected


def test_multi_symbol_capped_independently(monkeypatch):
    """G3 (iv): each symbol in a multi-symbol payload is capped on its own."""
    big = pd.date_range("2025-01-01", periods=400, freq="D")
    small = pd.date_range("2025-01-01", periods=10, freq="D")

    def _frame(idx):
        df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}, index=idx)
        df.index.name = "trade_date"
        return df

    class _Multi:
        def fetch(self, codes, start, end, interval="1D"):
            return {"BIG.US": _frame(big), "SMALL.US": _frame(small)}

    monkeypatch.setattr(mcp_server, "_get_loader", lambda src: _Multi)
    out = json.loads(
        _gmd(
            codes=["BIG.US", "SMALL.US"],
            start_date="2025-01-01",
            end_date="2026-01-01",
            source="yfinance",
        )
    )
    assert isinstance(out["BIG.US"], dict) and out["BIG.US"]["truncated"] is True
    assert isinstance(out["SMALL.US"], list) and len(out["SMALL.US"]) == 10
