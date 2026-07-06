"""Tests for fund_flow_tool: envelope shape, parsing, per-symbol isolation.

All HTTP is mocked at the Eastmoney client functions the tool imports
(:func:`get_json` / :func:`resolve_secid`), so no test touches a live endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools.fund_flow_tool import FundFlowTool

_DAILY_PAYLOAD = {
    "data": {
        "code": "600519",
        "klines": [
            "2024-01-02,100.0,-10.0,5.0,60.0,40.0,0,0,0,0,0,0,0,0,0",
            "2024-01-03,-50.0,20.0,-5.0,-30.0,-20.0,0,0,0,0,0,0,0,0,0",
        ],
    }
}


class TestSuccessEnvelope:
    """A resolvable symbol yields the ok envelope with labelled buckets."""

    def test_daily_flow_parses_into_buckets(self):
        with patch(
            "src.tools.fund_flow_tool.resolve_secid", return_value="1.600519"
        ), patch(
            "src.tools.fund_flow_tool.get_json", return_value=_DAILY_PAYLOAD
        ):
            text = FundFlowTool().execute(codes=["600519.SH"], period="daily", days=30)

        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["market"] == "stock"
        assert payload["source"] == "eastmoney"
        assert payload["period"] == "daily"
        assert payload["buckets"] == ["main", "small", "medium", "large", "super_large"]

        rows = payload["data"]["600519.SH"]["rows"]
        assert len(rows) == 2
        assert rows[0] == {
            "timestamp": "2024-01-02",
            "main": 100.0,
            "small": -10.0,
            "medium": 5.0,
            "large": 60.0,
            "super_large": 40.0,
        }

    def test_days_cap_keeps_most_recent_rows(self):
        with patch(
            "src.tools.fund_flow_tool.resolve_secid", return_value="1.600519"
        ), patch(
            "src.tools.fund_flow_tool.get_json", return_value=_DAILY_PAYLOAD
        ):
            text = FundFlowTool().execute(codes=["600519.SH"], period="daily", days=1)

        rows = json.loads(text)["data"]["600519.SH"]["rows"]
        assert len(rows) == 1
        assert rows[0]["timestamp"] == "2024-01-03"

    def test_minute_period_uses_minute_url(self):
        minute_payload = {"data": {"klines": ["2024-01-02 09:31,1.0,2.0,3.0,4.0,5.0"]}}
        with patch(
            "src.tools.fund_flow_tool.resolve_secid", return_value="1.600519"
        ), patch(
            "src.tools.fund_flow_tool.get_json", return_value=minute_payload
        ) as mock_get:
            text = FundFlowTool().execute(codes=["600519.SH"], period="min")

        url = mock_get.call_args[0][0]
        assert "fflow/kline/get" in url
        rows = json.loads(text)["data"]["600519.SH"]["rows"]
        assert rows[0]["timestamp"] == "2024-01-02 09:31"
        assert rows[0]["main"] == 1.0


class TestPerSymbolIsolation:
    """A single failing/unresolvable symbol never aborts the batch."""

    def test_unresolvable_symbol_is_reported_not_fatal(self):
        def fake_resolve(symbol):
            return None if symbol == "BAD" else "1.600519"

        with patch(
            "src.tools.fund_flow_tool.resolve_secid", side_effect=fake_resolve
        ), patch(
            "src.tools.fund_flow_tool.get_json", return_value=_DAILY_PAYLOAD
        ):
            text = FundFlowTool().execute(codes=["BAD", "600519.SH"])

        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["data"]["BAD"]["error"] == "unresolvable symbol"
        assert len(payload["data"]["600519.SH"]["rows"]) == 2

    def test_http_failure_on_one_symbol_is_captured(self):
        with patch(
            "src.tools.fund_flow_tool.resolve_secid", return_value="1.600519"
        ), patch(
            "src.tools.fund_flow_tool.get_json", side_effect=RuntimeError("HTTP 429")
        ):
            text = FundFlowTool().execute(codes=["600519.SH"])

        payload = json.loads(text)
        assert payload["ok"] is True
        assert "429" in payload["data"]["600519.SH"]["error"]

    def test_malformed_row_skipped(self):
        bad = {"data": {"klines": ["garbage", "2024-01-03,-50.0,20.0,-5.0,-30.0,-20.0"]}}
        with patch(
            "src.tools.fund_flow_tool.resolve_secid", return_value="1.600519"
        ), patch("src.tools.fund_flow_tool.get_json", return_value=bad):
            text = FundFlowTool().execute(codes=["600519.SH"])

        rows = json.loads(text)["data"]["600519.SH"]["rows"]
        assert len(rows) == 1


class TestErrorEnvelope:
    """Input validation returns the ok=false envelope before any HTTP."""

    def test_empty_codes_rejected(self):
        payload = json.loads(FundFlowTool().execute(codes=[]))
        assert payload["ok"] is False
        assert "codes" in payload["error"]

    def test_missing_codes_rejected(self):
        payload = json.loads(FundFlowTool().execute())
        assert payload["ok"] is False

    def test_non_string_code_rejected(self):
        payload = json.loads(FundFlowTool().execute(codes=[123]))
        assert payload["ok"] is False

    def test_invalid_period_rejected(self):
        payload = json.loads(
            FundFlowTool().execute(codes=["600519.SH"], period="hourly")
        )
        assert payload["ok"] is False
        assert "period" in payload["error"]

    def test_non_positive_days_rejected(self):
        payload = json.loads(
            FundFlowTool().execute(codes=["600519.SH"], days=0)
        )
        assert payload["ok"] is False
        assert "days" in payload["error"]

    def test_bool_days_rejected(self):
        payload = json.loads(
            FundFlowTool().execute(codes=["600519.SH"], days=True)
        )
        assert payload["ok"] is False


class TestRoutingDescription:
    """Description must scope to PER-STOCK flow so vague prompts don't misroute.

    Regression for B10-routing-desc: get_fund_flow and get_northbound_flow both
    used to open on a generic 'net capital flow' phrase, so a vague prompt could
    route to either. The fund-flow description must lead with the per-stock,
    order-level scope and point market-wide intent at get_northbound_flow.
    """

    def test_description_leads_with_per_stock_order_level(self):
        desc = FundFlowTool().description
        # Leads with the per-stock, order-level scope, not a generic phrase.
        assert desc.startswith("PER-STOCK order-level net inflow")
        assert "market-wide" not in desc.lower().split("not market-wide")[0]
        # Disambiguates against the market-wide tool.
        assert "get_northbound_flow" in desc

    def test_description_keeps_a_concrete_example(self):
        assert '{"codes": ["600519.SH"' in FundFlowTool().description
