"""Tests for the margin-trading (融资融券) tool.

No request leaves the process: the success path patches the shared Eastmoney
client (:func:`backtest.loaders.eastmoney_client.get_json`) so the tool's own
parsing/envelope logic runs against a canned datacenter payload, and the error
path makes that boundary raise.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from backtest.loaders import eastmoney_client
from src.tools.margin_trading_tool import MarginTradingTool


def _datacenter_payload() -> dict:
    """Two daily rows in the Eastmoney RZRQ datacenter response shape."""
    return {
        "result": {
            "data": [
                {
                    "DATE": "2024-01-03 00:00:00",
                    "SCODE": "600519",
                    "RZYE": 1.23e9,
                    "RZMRE": 4.5e7,
                    "RZCHE": 3.0e7,
                    "RQYE": 2.0e6,
                    "RQYL": 1500.0,
                    "RZRQYE": 1.232e9,
                },
                {
                    "DATE": "2024-01-02 00:00:00",
                    "SCODE": "600519",
                    "RZYE": 1.20e9,
                    "RZMRE": 4.0e7,
                    "RZCHE": 2.5e7,
                    "RQYE": "",
                    "RQYL": None,
                    "RZRQYE": 1.202e9,
                },
            ]
        }
    }


class TestSuccess:
    def test_a_share_returns_envelope(self) -> None:
        tool = MarginTradingTool()
        with patch.object(
            eastmoney_client, "get_json", return_value=_datacenter_payload()
        ) as get_json:
            out = tool.execute(code="600519.SH", days=30)

        # Query went through the throttled client with the bare code filter.
        get_json.assert_called_once()
        _, kwargs = get_json.call_args
        assert kwargs["params"]["filter"] == '(SCODE="600519")'
        assert kwargs["params"]["pageSize"] == "30"

        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["market"] == "a_share"
        assert payload["source"] == "eastmoney"
        assert payload["data"]["code"] == "600519"

        rows = payload["data"]["rows"]
        assert len(rows) == 2
        assert rows[0]["trade_date"] == "2024-01-03"
        assert rows[0]["financing_balance"] == 1.23e9
        assert rows[0]["margin_total_balance"] == 1.232e9
        # Missing/empty cells normalize to None, not a crash.
        assert rows[1]["short_balance"] is None
        assert rows[1]["short_volume"] is None

    def test_bare_code_and_days_clamped(self) -> None:
        tool = MarginTradingTool()
        with patch.object(
            eastmoney_client, "get_json", return_value=_datacenter_payload()
        ) as get_json:
            out = tool.execute(code="000001", days=99999)

        _, kwargs = get_json.call_args
        # Days clamped to the hard cap (250).
        assert kwargs["params"]["pageSize"] == "250"
        assert kwargs["params"]["filter"] == '(SCODE="000001")'
        assert json.loads(out)["ok"] is True


class TestErrors:
    def test_unsupported_symbol_rejected_without_request(self) -> None:
        tool = MarginTradingTool()
        with patch.object(eastmoney_client, "get_json") as get_json:
            out = tool.execute(code="AAPL.US")

        get_json.assert_not_called()
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "A-shares only" in payload["error"]

    def test_provider_failure_becomes_error_envelope(self) -> None:
        tool = MarginTradingTool()
        with patch.object(
            eastmoney_client, "get_json", side_effect=RuntimeError("eastmoney boom")
        ):
            out = tool.execute(code="600519.SH", days=5)

        payload = json.loads(out)
        assert payload["ok"] is False
        assert "eastmoney boom" in payload["error"]

    def test_empty_data_becomes_error_envelope(self) -> None:
        tool = MarginTradingTool()
        with patch.object(
            eastmoney_client, "get_json", return_value={"result": {"data": []}}
        ):
            out = tool.execute(code="600519.SH")

        payload = json.loads(out)
        assert payload["ok"] is False
        assert "No margin-trading data" in payload["error"]
