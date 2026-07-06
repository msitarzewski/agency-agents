"""Tests for the get_stock_profile tool.

All HTTP is mocked at :func:`get_quote_summary` as it is imported into the tool
module, so no test touches a live Yahoo Finance endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools import stock_profile_tool as sp


def _sample_summary() -> dict:
    return {
        "defaultKeyStatistics": {
            "forwardPE": {"raw": 28.5, "fmt": "28.50"},
            "trailingEps": {"raw": 6.13},
            "beta": {"raw": 1.25},
            "heldPercentInstitutions": {"raw": 0.61},
            "sharesOutstanding": {"raw": 15_000_000_000},
        },
        "financialData": {
            "currentPrice": {"raw": 195.0},
            "targetMeanPrice": {"raw": 210.0},
            "recommendationKey": "buy",
            "numberOfAnalystOpinions": {"raw": 40},
            "returnOnEquity": {"raw": 1.47},
        },
        "earningsTrend": {
            "trend": [
                {
                    "period": "0q",
                    "endDate": "2026-06-30",
                    "growth": {"raw": 0.08},
                    "earningsEstimate": {
                        "avg": {"raw": 1.34},
                        "low": {"raw": 1.30},
                        "high": {"raw": 1.40},
                        "numberOfAnalysts": {"raw": 28},
                    },
                    "revenueEstimate": {"avg": {"raw": 89_000_000_000}},
                }
            ]
        },
        "institutionOwnership": {
            "ownershipList": [
                {
                    "organization": "Vanguard Group Inc",
                    "reportDate": {"raw": 1_711_843_200},
                    "pctHeld": {"raw": 0.084},
                    "position": {"raw": 1_300_000_000},
                    "value": {"raw": 250_000_000_000},
                }
            ]
        },
        "insiderHolders": {
            "holders": [
                {
                    "name": "COOK TIMOTHY D",
                    "relation": "Chief Executive Officer",
                    "latestTransDate": "2026-04-01",
                    "positionDirect": {"raw": 3_280_000},
                }
            ]
        },
        "recommendationTrend": {
            "trend": [
                {
                    "period": "0m",
                    "strongBuy": 12,
                    "buy": 20,
                    "hold": 8,
                    "sell": 1,
                    "strongSell": 0,
                }
            ]
        },
    }


class TestStockProfileSuccess:
    """Happy-path envelope shape and section shaping."""

    def test_default_returns_all_sections(self):
        with patch.object(
            sp, "get_quote_summary", return_value=_sample_summary()
        ) as mock_get:
            out = sp.StockProfileTool().execute(ticker="AAPL.US")

        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["market"] == "us"
        assert payload["source"] == "yahoo"
        data = payload["data"]
        assert data["ticker"] == "AAPL.US"
        assert set(data["sections"]) == set(sp._ALL_SECTIONS)

        # raw cells are unwrapped to scalars.
        assert data["sections"]["key_stats"]["forwardPE"] == 28.5
        assert data["sections"]["financials"]["recommendationKey"] == "buy"

        # list sections are projected into compact rows.
        est = data["sections"]["earnings_trend"][0]
        assert est["period"] == "0q"
        assert est["eps_avg"] == 1.34
        assert est["eps_analysts"] == 28

        inst = data["sections"]["institution_ownership"][0]
        assert inst["organization"] == "Vanguard Group Inc"
        assert inst["pct_held"] == 0.084

        insider = data["sections"]["insider_holders"][0]
        assert insider["name"] == "COOK TIMOTHY D"
        assert insider["position"] == 3_280_000

        rec = data["sections"]["recommendation_trend"][0]
        assert rec["strong_buy"] == 12

        # Default fans out to all six Yahoo modules.
        _, args, kwargs = mock_get.mock_calls[0]
        requested_modules = args[1]
        assert "defaultKeyStatistics" in requested_modules
        assert "recommendationTrend" in requested_modules
        assert len(requested_modules) == len(sp._ALL_SECTIONS)

    def test_section_subset_only_requests_those_modules(self):
        with patch.object(
            sp, "get_quote_summary", return_value=_sample_summary()
        ) as mock_get:
            out = sp.StockProfileTool().execute(
                ticker="00700.HK", sections=["financials", "financials"]
            )

        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["market"] == "hk"
        # De-duplicated subset only.
        assert list(payload["data"]["sections"]) == ["financials"]

        _, args, _ = mock_get.mock_calls[0]
        assert args[1] == ["financialData"]

    def test_missing_module_yields_empty_shaped_section(self):
        # Yahoo can omit a module for a symbol; shaper must not crash.
        with patch.object(sp, "get_quote_summary", return_value={}):
            out = sp.StockProfileTool().execute(
                ticker="AAPL.US", sections=["key_stats", "insider_holders"]
            )
        data = json.loads(out)["data"]["sections"]
        assert data["key_stats"]["forwardPE"] is None
        assert data["insider_holders"] == []


class TestStockProfileErrors:
    """Error envelopes: missing ticker, bad section, upstream failure."""

    def test_missing_ticker_returns_error_envelope(self):
        out = sp.StockProfileTool().execute(ticker="  ")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "required" in payload["error"]

    def test_unknown_section_returns_error_envelope(self):
        out = sp.StockProfileTool().execute(ticker="AAPL.US", sections=["bogus"])
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "unknown section" in payload["error"]

    def test_upstream_failure_becomes_error_envelope(self):
        with patch.object(
            sp, "get_quote_summary", side_effect=RuntimeError("HTTP 429 banned")
        ):
            out = sp.StockProfileTool().execute(ticker="AAPL.US")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "yahoo quoteSummary request failed" in payload["error"]
        assert "429" in payload["error"]
