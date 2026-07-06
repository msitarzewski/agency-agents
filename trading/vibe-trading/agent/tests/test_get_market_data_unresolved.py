"""Regression test for P05 — get_market_data must not silently drop a
requested symbol that returned no data.

Pre-fix: the result dict only held winners, so a typo / wrong-suffix /
delisted / no-data code just vanished — indistinguishable from "no data",
and a loader exception lost every already-resolved symbol. Post-fix: any
unresolved requested code is surfaced under the reserved ``_unresolved``
key (additive: omitted entirely when all codes resolve, so the happy-path
payload is byte-identical to before), and a loader blow-up is contained.
"""

from __future__ import annotations

import json
import logging

import pandas as pd
import pytest

import mcp_server

# fastmcp wraps the tool; reach the raw callable.
_gmd = getattr(mcp_server.get_market_data, "fn", None) or getattr(
    mcp_server.get_market_data, "__wrapped__", mcp_server.get_market_data
)


def _df():
    df = pd.DataFrame(
        {"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0], "volume": [1.0]},
        index=pd.to_datetime(["2026-05-01"]),
    )
    df.index.name = "trade_date"
    return df


class _GoodOnlyLoader:
    def fetch(self, codes, start, end, interval="1D"):
        return {"GOOD.US": _df()} if "GOOD.US" in codes else {}


class _PartialLoader:
    """Returns only a subset of the requested codes."""

    def fetch(self, codes, start, end, interval="1D"):
        return {c: _df() for c in codes if c.startswith("OK")}


class _BoomLoader:
    def fetch(self, codes, start, end, interval="1D"):
        raise RuntimeError("simulated loader blow-up")


@pytest.fixture
def good_only(monkeypatch):
    monkeypatch.setattr(mcp_server, "_get_loader", lambda src: _GoodOnlyLoader)


def _call(codes):
    return json.loads(_gmd(codes=codes, start_date="2026-05-01", end_date="2026-05-02", source="yfinance"))


def test_unresolved_symbol_is_surfaced(good_only):
    out = _call(["GOOD.US", "BOGUS.US"])
    assert "GOOD.US" in out
    assert out.get("_unresolved") == ["BOGUS.US"]


def test_all_resolved_has_no_unresolved_key(good_only):
    """Happy path must stay byte-identical (additive only)."""
    out = _call(["GOOD.US"])
    assert "GOOD.US" in out
    assert "_unresolved" not in out


def test_loader_exception_is_contained_not_lost(monkeypatch):
    monkeypatch.setattr(mcp_server, "_get_loader", lambda src: _BoomLoader)
    out = _call(["AAA.US", "BBB.US"])  # must not raise an opaque MCP error
    assert sorted(out.get("_unresolved", [])) == ["AAA.US", "BBB.US"]


def test_partial_loader_only_missing_codes_unresolved(monkeypatch):
    """G2: a loader returning only SOME requested codes -> the rest land
    under _unresolved (not silently dropped)."""
    monkeypatch.setattr(mcp_server, "_get_loader", lambda src: _PartialLoader)
    out = _call(["OK1.US", "OK2.US", "MISS1.US", "MISS2.US"])
    assert "OK1.US" in out and "OK2.US" in out
    assert sorted(out.get("_unresolved", [])) == ["MISS1.US", "MISS2.US"]


def test_swallowed_loader_exception_is_logged(monkeypatch, caplog):
    """G2: the contained loader blow-up must still be logged (was silent)."""
    monkeypatch.setattr(mcp_server, "_get_loader", lambda src: _BoomLoader)
    with caplog.at_level(logging.ERROR, logger=mcp_server.logger.name):
        _call(["AAA.US", "BBB.US"])
    assert any("market-data loader" in r.message for r in caplog.records)
