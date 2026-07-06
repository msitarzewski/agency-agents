"""Tests for get_shareholder_count: success + error envelopes, HTTP mocked.

The Eastmoney datacenter call is mocked at ``get_json`` (imported into the tool
module), so no test reaches a live endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools import shareholder_count_tool as sct
from src.tools.shareholder_count_tool import ShareholderCountTool

_SAMPLE_PAYLOAD = {
    "result": {
        "data": [
            {
                "SECUCODE": "600519.SH",
                "END_DATE": "2024-03-31 00:00:00",
                "HOLDER_NUM": 188000,
                "HOLDER_NUM_CHANGE": -2000,
                "HOLDER_NUM_RATIO": -1.05,
                "AVG_HOLD_NUM": 6680.0,
                "AVG_HOLD_AMT": 12345678.0,
                "TOTAL_MARKET_CAP": 2.1e12,
            },
            {
                "SECUCODE": "600519.SH",
                "END_DATE": "2023-12-31 00:00:00",
                "HOLDER_NUM": 190000,
                "HOLDER_NUM_CHANGE": 1500,
                "HOLDER_NUM_RATIO": 0.80,
                "AVG_HOLD_NUM": 6610.0,
                "AVG_HOLD_AMT": 12000000.0,
                "TOTAL_MARKET_CAP": 2.0e12,
            },
        ]
    }
}


def test_success_envelope_parses_periods_newest_first():
    with patch.object(sct, "get_json", return_value=_SAMPLE_PAYLOAD) as mock_get:
        out = ShareholderCountTool().execute(code="600519.SH")

    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["market"] == "CN"
    assert payload["source"] == "eastmoney"
    assert payload["data"]["code"] == "600519.SH"

    periods = payload["data"]["periods"]
    assert len(periods) == 2
    assert periods[0] == {
        "end_date": "2024-03-31",
        "holder_count": 188000.0,
        "holder_count_change": -2000.0,
        "holder_count_change_pct": -1.05,
        "avg_hold_shares": 6680.0,
        "avg_hold_amount": 12345678.0,
        "total_market_cap": 2.1e12,
    }

    # SECUCODE filter flows through to the datacenter request.
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["filter"] == '(SECUCODE="600519.SH")'


def test_max_periods_caps_returned_rows():
    with patch.object(sct, "get_json", return_value=_SAMPLE_PAYLOAD):
        out = ShareholderCountTool().execute(code="600519.SH", max_periods=1)
    payload = json.loads(out)
    assert len(payload["data"]["periods"]) == 1


def test_non_a_share_returns_error_envelope():
    out = ShareholderCountTool().execute(code="AAPL.US")
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "A-share" in payload["error"]


def test_missing_code_returns_error_envelope():
    out = ShareholderCountTool().execute()
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "required" in payload["error"]


def test_empty_disclosure_returns_error_envelope():
    with patch.object(sct, "get_json", return_value={"result": {"data": []}}):
        out = ShareholderCountTool().execute(code="600519.SH")
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "no shareholder-count" in payload["error"]


def test_request_failure_is_caught_as_error_envelope():
    with patch.object(sct, "get_json", side_effect=RuntimeError("HTTP 429")):
        out = ShareholderCountTool().execute(code="600519.SH")
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "429" in payload["error"]
