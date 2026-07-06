"""Tests for the iWenCai (问财) natural-language A-share search tool.

No request leaves the process: the HTTP boundary
(:func:`backtest.loaders._http.throttled_get_json`, imported into the tool
module) is mocked so the real auth/parsing/envelope path runs offline.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from src.tools import iwencai_tool
from src.tools.iwencai_tool import IWenCaiSearchTool, _coerce_limit, _extract_rows

_KEY_ENV = "VIBE_TRADING_IWENCAI_KEY"


def _robot_payload() -> dict[str, Any]:
    """An iWenCai robot-data response nesting two security rows."""
    return {
        "data": {
            "answer": [
                {
                    "txt": [
                        {
                            "content": {
                                "components": [
                                    {
                                        "data": {
                                            "datas": [
                                                {"code": "600036", "name": "招商银行", "pe": 6.1},
                                                {"code": "601398", "name": "工商银行", "pe": 5.2},
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    }


class TestHelpers:
    def test_coerce_limit_defaults_and_clamps(self) -> None:
        assert _coerce_limit(None) == iwencai_tool._DEFAULT_LIMIT
        assert _coerce_limit("nope") == iwencai_tool._DEFAULT_LIMIT
        assert _coerce_limit(0) == iwencai_tool._DEFAULT_LIMIT
        assert _coerce_limit(10) == 10
        assert _coerce_limit(9999) == iwencai_tool._MAX_LIMIT

    def test_extract_rows_handles_missing_branches(self) -> None:
        assert _extract_rows(None) == []
        assert _extract_rows({}) == []
        assert _extract_rows({"data": {"answer": []}}) == []
        assert len(_extract_rows(_robot_payload())) == 2


class TestAvailability:
    def test_excluded_when_key_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(_KEY_ENV, raising=False)
        assert IWenCaiSearchTool.check_available() is False

    def test_available_when_key_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_KEY_ENV, "secret-token")
        assert IWenCaiSearchTool.check_available() is True


class TestToolContract:
    def test_name_and_schema(self) -> None:
        tool = IWenCaiSearchTool()
        assert tool.name == "iwencai_search"
        assert tool.is_readonly is True
        assert tool.parameters["required"] == ["query"]
        assert "limit" in tool.parameters["properties"]


class TestExecuteSuccess:
    def test_returns_rows_with_auth_header(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_KEY_ENV, "secret-token")
        tool = IWenCaiSearchTool()
        with patch.object(
            iwencai_tool, "throttled_get_json", return_value=_robot_payload()
        ) as http:
            out = json.loads(tool.execute(query="市盈率低于15的银行股", limit=10))

        http.assert_called_once()
        _, kwargs = http.call_args
        assert kwargs["host_key"] == "iwencai"
        assert kwargs["headers"]["Authorization"] == "Bearer secret-token"
        assert kwargs["params"]["question"] == "市盈率低于15的银行股"
        assert kwargs["params"]["perpage"] == "10"

        assert out["ok"] is True
        assert out["market"] == "a_share"
        assert out["source"] == "iwencai"
        assert out["data"]["query"] == "市盈率低于15的银行股"
        assert out["data"]["count"] == 2
        assert out["data"]["results"][0]["code"] == "600036"

    def test_limit_clamps_result_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_KEY_ENV, "secret-token")
        tool = IWenCaiSearchTool()
        with patch.object(iwencai_tool, "throttled_get_json", return_value=_robot_payload()):
            out = json.loads(tool.execute(query="银行股", limit=1))
        assert out["data"]["count"] == 1


class TestExecuteError:
    def test_missing_key_returns_error_envelope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(_KEY_ENV, raising=False)
        out = json.loads(IWenCaiSearchTool().execute(query="银行股"))
        assert out["ok"] is False
        assert _KEY_ENV in out["error"]

    def test_missing_query_returns_error_envelope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_KEY_ENV, "secret-token")
        out = json.loads(IWenCaiSearchTool().execute())
        assert out["ok"] is False
        assert "query" in out["error"]

    def test_http_failure_returns_error_envelope(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(_KEY_ENV, "secret-token")
        tool = IWenCaiSearchTool()
        with patch.object(
            iwencai_tool,
            "throttled_get_json",
            side_effect=RuntimeError("iwencai banned"),
        ):
            out = json.loads(tool.execute(query="银行股"))
        assert out["ok"] is False
        assert "iwencai banned" in out["error"]
