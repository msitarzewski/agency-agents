"""Tests for market_screener_tool: envelope shape, sorting params, validation.

All HTTP is mocked at the Eastmoney client function the tool imports
(:func:`get_json`), so no test touches a live endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools.market_screener_tool import MarketScreenerTool

_CLIST_PAYLOAD = {
    "data": {
        "total": 2,
        "diff": [
            {
                "f12": "600519",
                "f14": "贵州茅台",
                "f2": 1688.0,
                "f3": 9.98,
                "f4": 153.0,
                "f5": 1234567.0,
                "f6": 2.08e9,
                "f8": 1.23,
            },
            {
                "f12": "000001",
                "f14": "平安银行",
                "f2": 11.5,
                "f3": 5.01,
                "f4": 0.55,
                "f5": 9876543.0,
                "f6": 1.1e8,
                "f8": "-",
            },
        ],
    }
}


class TestSuccessEnvelope:
    """A successful screen yields the ok envelope with shaped rows."""

    def test_change_pct_screen_parses_rows(self):
        with patch(
            "src.tools.market_screener_tool.get_json", return_value=_CLIST_PAYLOAD
        ):
            text = MarketScreenerTool().execute(
                market="a", sort_by="change_pct", top_n=20
            )

        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["market"] == "a"
        assert payload["source"] == "eastmoney"
        # The row list nests under data:{...} like every other tool's envelope,
        # never a bare list directly under "data".
        data = payload["data"]
        assert isinstance(data, dict)
        assert data["market"] == "a"
        assert data["sort_by"] == "change_pct"

        rows = data["rows"]
        assert len(rows) == 2
        assert rows[0] == {
            "code": "600519",
            "name": "贵州茅台",
            "price": 1688.0,
            "change_pct": 9.98,
            "change": 153.0,
            "volume": 1234567.0,
            "amount": 2.08e9,
            "turnover_rate": 1.23,
        }
        # The "-" sentinel turnover rate becomes None, not 0.0.
        assert rows[1]["turnover_rate"] is None

    def test_sort_by_maps_to_eastmoney_fid(self):
        with patch(
            "src.tools.market_screener_tool.get_json", return_value=_CLIST_PAYLOAD
        ) as mock_get:
            MarketScreenerTool().execute(market="us", sort_by="amount", top_n=5)

        params = mock_get.call_args.kwargs["params"]
        assert params["fid"] == "f6"  # amount
        assert params["po"] == "1"  # descending
        assert params["pz"] == "5"
        assert params["fs"] == "m:105,m:106,m:107"  # US universe

    def test_diff_as_dict_is_normalized(self):
        dict_diff = {"data": {"diff": {"0": _CLIST_PAYLOAD["data"]["diff"][0]}}}
        with patch(
            "src.tools.market_screener_tool.get_json", return_value=dict_diff
        ):
            text = MarketScreenerTool().execute(market="hk")

        rows = json.loads(text)["data"]["rows"]
        assert len(rows) == 1
        assert rows[0]["code"] == "600519"

    def test_top_n_caps_returned_rows(self):
        with patch(
            "src.tools.market_screener_tool.get_json", return_value=_CLIST_PAYLOAD
        ):
            text = MarketScreenerTool().execute(market="a", top_n=1)

        assert len(json.loads(text)["data"]["rows"]) == 1

    def test_rowless_payload_yields_empty_data(self):
        with patch(
            "src.tools.market_screener_tool.get_json", return_value={"data": None}
        ):
            text = MarketScreenerTool().execute(market="a")

        payload = json.loads(text)
        assert payload["ok"] is True
        # Rowless payload still yields the nested data:{...} envelope, not a
        # bare list, with an empty "rows".
        assert payload["data"]["rows"] == []
        assert payload["data"]["sort_by"] == "change_pct"


class TestErrorEnvelope:
    """Validation and request failures return the ok=false envelope."""

    def test_missing_market_rejected(self):
        payload = json.loads(MarketScreenerTool().execute())
        assert payload["ok"] is False
        assert "market" in payload["error"]

    def test_invalid_market_rejected(self):
        payload = json.loads(MarketScreenerTool().execute(market="jp"))
        assert payload["ok"] is False
        assert "market" in payload["error"]

    def test_invalid_sort_by_rejected(self):
        payload = json.loads(
            MarketScreenerTool().execute(market="a", sort_by="price")
        )
        assert payload["ok"] is False
        assert "sort_by" in payload["error"]

    def test_non_positive_top_n_rejected(self):
        payload = json.loads(MarketScreenerTool().execute(market="a", top_n=0))
        assert payload["ok"] is False
        assert "top_n" in payload["error"]

    def test_bool_top_n_rejected(self):
        payload = json.loads(MarketScreenerTool().execute(market="a", top_n=True))
        assert payload["ok"] is False
        assert "top_n" in payload["error"]

    def test_http_failure_surfaces_as_error_envelope(self):
        with patch(
            "src.tools.market_screener_tool.get_json",
            side_effect=RuntimeError("HTTP 429"),
        ):
            text = MarketScreenerTool().execute(market="a")

        payload = json.loads(text)
        assert payload["ok"] is False
        assert "429" in payload["error"]
