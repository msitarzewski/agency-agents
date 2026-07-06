"""Tests for the get_block_trades tool.

All HTTP is mocked at :func:`backtest.loaders.eastmoney_client.get_json` as it is
imported into the tool module, so no test touches a live Eastmoney endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools import block_trades_tool as bt


def _sample_payload() -> dict:
    return {
        "result": {
            "data": [
                {
                    "TRADE_DATE": "2026-06-18",
                    "SECURITY_CODE": "600519",
                    "SECURITY_NAME_ABBR": "贵州茅台",
                    "CLOSE_PRICE": "1700.00",
                    "DEAL_PRICE": "1650.00",
                    "PREMIUM_RATIO": "-2.94",
                    "DEAL_VOLUME": "10000",
                    "DEAL_AMT": "16500000",
                    "BUYER_NAME": "机构专用",
                    "SELLER_NAME": "中信证券某营业部",
                },
                {
                    "TRADE_DATE": "2026-06-17",
                    "SECURITY_CODE": "600519",
                    "SECURITY_NAME_ABBR": "贵州茅台",
                    "CLOSE_PRICE": "1690.00",
                    "DEAL_PRICE": "",
                    "PREMIUM_RATIO": None,
                    "DEAL_VOLUME": "5000",
                    "DEAL_AMT": "8400000",
                    "BUYER_NAME": "中金某营业部",
                    "SELLER_NAME": "机构专用",
                },
            ]
        }
    }


class TestBlockTradesSuccess:
    """Happy-path envelope shape and field normalization."""

    def test_success_envelope_normalizes_records(self):
        with patch.object(
            bt, "get_json", return_value=_sample_payload()
        ) as mock_get:
            out = bt.BlockTradesTool().execute(code="600519.SH", days=30)

        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["market"] == "china_a"
        assert payload["source"] == "eastmoney"
        data = payload["data"]
        assert data["code"] == "600519.SH"
        assert data["days"] == 30
        assert data["count"] == 2

        first = data["records"][0]
        assert first["trade_date"] == "2026-06-18"
        assert first["deal_price"] == 1650.0
        assert first["premium_ratio"] == -2.94
        assert first["buyer_seat"] == "机构专用"
        assert first["seller_seat"] == "中信证券某营业部"

        # Blank/None cells coerce to None, not a crash.
        second = data["records"][1]
        assert second["deal_price"] is None
        assert second["premium_ratio"] is None

        # The bare 6-digit code (no market prefix) flows into the filter.
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["reportName"] == "RPT_DATA_BLOCKTRADE"
        assert '600519' in kwargs["params"]["filter"]

    def test_empty_window_is_ok_with_zero_records(self):
        with patch.object(bt, "get_json", return_value={"result": {"data": None}}):
            out = bt.BlockTradesTool().execute(code="000001.SZ")
        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["data"]["count"] == 0
        assert payload["data"]["records"] == []
        # Default lookback window applies when days is omitted.
        assert payload["data"]["days"] == bt._DEFAULT_DAYS

    def test_days_clamped_to_max(self):
        with patch.object(bt, "get_json", return_value=_sample_payload()):
            out = bt.BlockTradesTool().execute(code="600519.SH", days=99999)
        assert json.loads(out)["data"]["days"] == bt._MAX_DAYS


class TestBlockTradesErrors:
    """Error envelopes: bad symbol, missing code, upstream failure."""

    def test_missing_code_returns_error_envelope(self):
        out = bt.BlockTradesTool().execute(code="  ")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "required" in payload["error"]

    def test_non_a_share_symbol_rejected(self):
        # HK/US listings have no A-share block-trade report here.
        out = bt.BlockTradesTool().execute(code="00700.HK")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "A-share" in payload["error"]

    def test_upstream_failure_becomes_error_envelope(self):
        with patch.object(
            bt, "get_json", side_effect=RuntimeError("HTTP 429 banned")
        ):
            out = bt.BlockTradesTool().execute(code="600519.SH", days=10)
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "eastmoney request failed" in payload["error"]
        assert "429" in payload["error"]
