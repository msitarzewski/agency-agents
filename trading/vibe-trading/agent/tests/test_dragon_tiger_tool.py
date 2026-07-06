"""Tests for the dragon-tiger (龙虎榜) tool.

No request leaves the process: the HTTP boundary
(:func:`backtest.loaders.eastmoney_client.throttled_get_json`) is mocked so the
real client + tool parsing runs offline.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from backtest.loaders import eastmoney_client
from src.tools.dragon_tiger_tool import DragonTigerTool, _bare_code, _compact_date


def _appearance_payload() -> dict[str, Any]:
    """A datacenter appearance payload with two board rows."""
    return {
        "result": {
            "data": [
                {
                    "SECURITY_CODE": "600519",
                    "SECURITY_NAME_ABBR": "贵州茅台",
                    "CLOSE_PRICE": 1700.0,
                    "CHANGE_RATE": 5.2,
                    "BILLBOARD_NET_AMT": 1.2e8,
                    "BILLBOARD_BUY_AMT": 3.0e8,
                    "BILLBOARD_SELL_AMT": 1.8e8,
                    "ACCUM_AMOUNT": 9.0e8,
                    "EXPLANATION": "日涨幅偏离值达7%",
                },
                {
                    "SECURITY_CODE": "000001",
                    "SECURITY_NAME_ABBR": "平安银行",
                    "CLOSE_PRICE": 12.0,
                    "CHANGE_RATE": -4.1,
                    "BILLBOARD_NET_AMT": -5.0e7,
                    "BILLBOARD_BUY_AMT": 1.0e8,
                    "BILLBOARD_SELL_AMT": 1.5e8,
                    "ACCUM_AMOUNT": 4.0e8,
                    "EXPLANATION": "日跌幅偏离值达7%",
                },
            ]
        }
    }


def _seat_payload() -> dict[str, Any]:
    """A datacenter seat payload with one buy seat."""
    return {
        "result": {
            "data": [
                {
                    "OPERATEDEPT_NAME": "机构专用",
                    "SIDE": "BUY",
                    "BUY": 2.0e8,
                    "SELL": 0.0,
                    "NET": 2.0e8,
                    "RANK": 1,
                }
            ]
        }
    }


class TestHelpers:
    def test_compact_date_normalizes(self) -> None:
        assert _compact_date("20240102") == "2024-01-02"
        assert _compact_date(" 2024-01-02 ") == "2024-01-02"

    def test_compact_date_rejects_garbage(self) -> None:
        with pytest.raises(ValueError):
            _compact_date("not-a-date")

    def test_bare_code_strips_suffix(self) -> None:
        assert _bare_code("600519.SH") == "600519"
        assert _bare_code("000001") == "000001"


class TestToolContract:
    def test_name_and_schema(self) -> None:
        tool = DragonTigerTool()
        assert tool.name == "get_dragon_tiger"
        assert tool.is_readonly is True
        assert tool.parameters["required"] == ["date"]
        assert "code" in tool.parameters["properties"]


class TestExecuteSuccess:
    def test_full_market_list_no_code(self) -> None:
        tool = DragonTigerTool()
        with patch.object(
            eastmoney_client, "throttled_get_json", return_value=_appearance_payload()
        ) as http:
            out = json.loads(tool.execute(date="2024-01-02"))

        # Only the appearance report is queried when no code is supplied.
        http.assert_called_once()
        _, kwargs = http.call_args
        assert kwargs["host_key"] == "eastmoney"
        assert kwargs["params"]["reportName"] == "RPT_DAILYBILLBOARD_DETAILS"

        assert out["ok"] is True
        assert out["market"] == "a_share"
        assert out["source"] == "eastmoney"
        assert out["data"]["date"] == "2024-01-02"
        assert "seats" not in out["data"]
        assert len(out["data"]["appearances"]) == 2
        assert out["data"]["appearances"][0]["code"] == "600519"
        assert out["data"]["appearances"][0]["net_buy"] == pytest.approx(1.2e8)

    def test_with_code_adds_seats(self) -> None:
        tool = DragonTigerTool()
        payloads = [_appearance_payload(), _seat_payload()]
        with patch.object(
            eastmoney_client, "throttled_get_json", side_effect=payloads
        ) as http:
            out = json.loads(tool.execute(date="2024-01-02", code="600519.SH"))

        assert http.call_count == 2
        assert out["ok"] is True
        assert out["data"]["code"] == "600519"
        assert len(out["data"]["seats"]) == 1
        assert out["data"]["seats"][0]["seat"] == "机构专用"
        assert out["data"]["seats"][0]["net"] == pytest.approx(2.0e8)


class TestExecuteError:
    def test_missing_date_returns_error_envelope(self) -> None:
        out = json.loads(DragonTigerTool().execute())
        assert out["ok"] is False
        assert "date" in out["error"]

    def test_bad_date_returns_error_envelope(self) -> None:
        out = json.loads(DragonTigerTool().execute(date="nope"))
        assert out["ok"] is False
        assert "invalid date" in out["error"]

    def test_http_failure_returns_error_envelope(self) -> None:
        tool = DragonTigerTool()
        with patch.object(
            eastmoney_client,
            "throttled_get_json",
            side_effect=RuntimeError("eastmoney banned"),
        ):
            out = json.loads(tool.execute(date="2024-01-02"))

        assert out["ok"] is False
        assert "eastmoney banned" in out["error"]
