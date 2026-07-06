"""Tests for the Eastmoney-backed lockup-expiry (限售解禁) tool.

No request ever leaves the process: the success/shape paths mock the shared
client (:mod:`backtest.loaders.eastmoney_client`), and the end-to-end path mocks
the frozen HTTP boundary (``throttled_get_json``) so the real client routing and
this tool's parsing both run while nothing hits the network.
"""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import patch

from backtest.loaders import eastmoney_client
from src.tools import lockup_expiry_tool
from src.tools.lockup_expiry_tool import LockupExpiryTool


def _payload(rows: list[dict]) -> dict:
    """Wrap report rows in the datacenter ``result.data`` envelope."""
    return {"result": {"data": rows, "count": len(rows)}}


def _row(code: str, free_date: str) -> dict:
    """One RPT_LIFT_STOCK-shaped record."""
    return {
        "SECURITY_CODE": code,
        "SECURITY_NAME_ABBR": "贵州茅台",
        "FREE_DATE": f"{free_date} 00:00:00",
        "FREE_SHARES_TYPE": "首发原股东限售股份",
        "FREE_SHARES": 1000000.0,
        "ABLE_FREE_SHARES": 900000.0,
        "LIFT_MARKET_CAP": 1.7e9,
        "FREE_RATIO": 0.8,
        "TOTAL_RATIO": 1.2,
    }


# ---------------------------------------------------------------------------
# Tool contract
# ---------------------------------------------------------------------------


class TestToolContract:
    def test_class_attributes(self) -> None:
        tool = LockupExpiryTool()
        assert tool.name == "get_lockup_expiry"
        assert tool.is_readonly is True
        assert tool.parameters["required"] == []
        assert "code" in tool.parameters["properties"]
        assert "horizon_days" in tool.parameters["properties"]

    def test_description_self_contained(self) -> None:
        desc = LockupExpiryTool().description
        assert "解禁" in desc
        assert "Example" in desc


# ---------------------------------------------------------------------------
# Success — client.get_json mocked
# ---------------------------------------------------------------------------


class TestSuccess:
    def test_single_code_returns_history(self) -> None:
        rows = [_row("600519", "2024-06-01"), _row("600519", "2023-06-01")]
        with patch.object(
            eastmoney_client, "get_json", return_value=_payload(rows)
        ) as get_json:
            out = json.loads(LockupExpiryTool().execute(code="600519.SH"))

        # Single-code path keys on the bare numeric code, newest-first.
        _, kwargs = get_json.call_args
        params = kwargs["params"]
        assert params["reportName"] == "RPT_LIFT_STOCK"
        assert 'SECURITY_CODE="600519"' in params["filter"]
        assert params["sortTypes"] == "-1"

        assert out["ok"] is True
        assert out["market"] == "a_share"
        assert out["source"] == "eastmoney"
        assert out["data"]["scope"] == "single_code"
        assert out["data"]["code"] == "600519"
        assert out["data"]["count"] == 2
        first = out["data"]["records"][0]
        assert first["free_date"] == "2024-06-01"
        assert first["lift_market_cap"] == 1.7e9

    def test_market_calendar_uses_horizon_window(self) -> None:
        rows = [_row("000001", "2026-07-01")]
        with patch.object(
            lockup_expiry_tool, "_today", return_value=date(2026, 6, 19)
        ), patch.object(
            eastmoney_client, "get_json", return_value=_payload(rows)
        ) as get_json:
            out = json.loads(LockupExpiryTool().execute(horizon_days=30))

        _, kwargs = get_json.call_args
        params = kwargs["params"]
        # Soonest-first calendar bounded by [today, today+30d].
        assert params["sortTypes"] == "1"
        assert "FREE_DATE>='2026-06-19'" in params["filter"]
        assert "FREE_DATE<='2026-07-19'" in params["filter"]

        assert out["data"]["scope"] == "market_calendar"
        assert out["data"]["horizon_days"] == 30
        assert out["data"]["as_of"] == "2026-06-19"

    def test_horizon_clamped_to_max(self) -> None:
        with patch.object(
            eastmoney_client, "get_json", return_value=_payload([])
        ):
            out = json.loads(LockupExpiryTool().execute(horizon_days=99999))
        assert out["data"]["horizon_days"] == 365

    def test_payload_capped(self) -> None:
        rows = [_row(f"6005{i:02d}", "2026-07-01") for i in range(250)]
        with patch.object(
            eastmoney_client, "get_json", return_value=_payload(rows)
        ):
            out = json.loads(LockupExpiryTool().execute(horizon_days=90))
        assert out["data"]["count"] == 200
        assert out["data"]["truncated"] is True


# ---------------------------------------------------------------------------
# Error envelopes
# ---------------------------------------------------------------------------


class TestErrors:
    def test_bad_code_returns_error_envelope(self) -> None:
        out = json.loads(LockupExpiryTool().execute(code="AAPL.US"))
        assert out["ok"] is False
        assert "unrecognized" in out["error"]

    def test_upstream_failure_returns_error_envelope(self) -> None:
        with patch.object(
            eastmoney_client, "get_json", side_effect=RuntimeError("eastmoney boom")
        ):
            out = json.loads(LockupExpiryTool().execute(code="600519"))
        assert out["ok"] is False
        assert "eastmoney boom" in out["error"]


# ---------------------------------------------------------------------------
# End-to-end — only the frozen HTTP boundary mocked, real client routing runs.
# ---------------------------------------------------------------------------


class TestEndToEndHttpMocked:
    def test_single_code_through_real_client(self) -> None:
        rows = [_row("600519", "2024-06-01")]
        with patch.object(
            eastmoney_client, "throttled_get_json", return_value=_payload(rows)
        ) as http:
            out = json.loads(LockupExpiryTool().execute(code="600519"))

        http.assert_called_once()
        _, kwargs = http.call_args
        assert kwargs["host_key"] == "eastmoney"
        assert kwargs["params"]["reportName"] == "RPT_LIFT_STOCK"
        assert out["ok"] is True
        assert out["data"]["records"][0]["name"] == "贵州茅台"
