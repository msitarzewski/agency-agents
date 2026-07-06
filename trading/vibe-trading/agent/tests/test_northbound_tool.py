"""Tests for get_northbound_flow: success + error envelopes, HTTP fully mocked.

All Eastmoney HTTP is mocked at ``src.tools.northbound_tool.get_json`` (the name
the tool imported), so no test touches a live Eastmoney endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src.tools import northbound_tool as nb


def _realtime_payload() -> dict:
    return {
        "data": {
            "hk2sh": {"netBuyAmt": 1200.5},
            "hk2sz": {"netBuyAmt": -300.0},
        }
    }


def _history_payload() -> dict:
    return {
        "data": {
            "klines": [
                "2024-01-02,100.0,50.0",
                "2024-01-03,-20.0,80.0",
                "2024-01-04,-,-",
            ]
        }
    }


def _fake_get_json(url: str, *, params: dict):
    if "kamt.kline" in url:
        return _history_payload()
    return _realtime_payload()


class TestSuccessEnvelope:
    def test_returns_realtime_and_history(self):
        with patch.object(nb, "get_json", side_effect=_fake_get_json):
            text = nb.NorthboundFlowTool().execute(lookback_days=10)

        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["market"] == "China A"
        assert payload["source"] == "eastmoney"

        data = payload["data"]
        assert data["lookback_days"] == 10
        assert data["realtime"]["shanghai_connect"] == 1200.5
        assert data["realtime"]["shenzhen_connect"] == -300.0
        assert data["realtime"]["total"] == 900.5

        history = data["history"]
        assert len(history) == 3
        assert history[0] == {
            "trade_date": "2024-01-02",
            "shanghai_connect": 100.0,
            "shenzhen_connect": 50.0,
            "total": 150.0,
        }
        # A "-" sentinel row coerces to None without aborting the batch.
        assert history[-1]["shanghai_connect"] is None
        assert history[-1]["total"] is None

    def test_default_lookback_applied_when_absent(self):
        with patch.object(nb, "get_json", side_effect=_fake_get_json):
            text = nb.NorthboundFlowTool().execute()
        payload = json.loads(text)
        assert payload["data"]["lookback_days"] == nb._DEFAULT_LOOKBACK_DAYS

    def test_lookback_is_clamped_to_ceiling(self):
        with patch.object(nb, "get_json", side_effect=_fake_get_json):
            text = nb.NorthboundFlowTool().execute(lookback_days=99999)
        payload = json.loads(text)
        assert payload["data"]["lookback_days"] == nb._MAX_LOOKBACK_DAYS

    def test_history_trimmed_to_lookback(self):
        with patch.object(nb, "get_json", side_effect=_fake_get_json):
            text = nb.NorthboundFlowTool().execute(lookback_days=1)
        payload = json.loads(text)
        history = payload["data"]["history"]
        assert len(history) == 1
        assert history[0]["trade_date"] == "2024-01-04"


class TestErrorEnvelope:
    def test_http_failure_returns_error_envelope(self):
        with patch.object(nb, "get_json", side_effect=RuntimeError("HTTP 429")):
            text = nb.NorthboundFlowTool().execute(lookback_days=5)
        payload = json.loads(text)
        assert payload["ok"] is False
        assert "429" in payload["error"]

    def test_missing_data_block_yields_empty_history_and_null_realtime(self):
        with patch.object(nb, "get_json", return_value={"data": None}):
            text = nb.NorthboundFlowTool().execute(lookback_days=5)
        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["data"]["history"] == []
        assert payload["data"]["realtime"]["total"] is None


class TestToolMetadata:
    def test_name_and_required_params(self):
        tool = nb.NorthboundFlowTool()
        assert tool.name == "get_northbound_flow"
        assert tool.is_readonly is True
        assert tool.parameters["required"] == []
        assert "lookback_days" in tool.parameters["properties"]


class TestRoutingDescription:
    """Description must scope to MARKET-WIDE Stock-Connect flow, not per-stock.

    Regression for B10-routing-desc: get_fund_flow and get_northbound_flow both
    used to open on a generic 'net capital flow' phrase, so a vague prompt could
    route to either. The northbound description must lead with the market-wide
    Stock-Connect scope and point per-stock intent at get_fund_flow.
    """

    def test_description_leads_with_market_wide_stock_connect(self):
        desc = nb.NorthboundFlowTool().description
        assert desc.startswith("MARKET-WIDE Northbound")
        assert "北向" in desc
        # Disambiguates against the per-stock tool.
        assert "get_fund_flow" in desc
        assert "NOT per-stock" in desc

    def test_description_keeps_a_concrete_example(self):
        assert "get_northbound_flow(lookback_days=10)" in nb.NorthboundFlowTool().description
