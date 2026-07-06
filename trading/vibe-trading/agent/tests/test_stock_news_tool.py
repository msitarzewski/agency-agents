"""Tests for the stock-news tool.

No request leaves the process: the Eastmoney HTTP boundary
(:func:`backtest.loaders.eastmoney_client.throttled_get_json`) and the Yahoo
:func:`backtest.loaders.yahoo_client.search` helper are mocked so the real
client + tool parsing run fully offline.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from backtest.loaders import eastmoney_client, yahoo_client
from src.tools.stock_news_tool import (
    StockNewsTool,
    _bare_query,
    _clamp_limit,
    _snippet,
    _suffix_of,
)


def _em_news_payload() -> dict[str, Any]:
    """An Eastmoney search payload carrying two CMS articles."""
    return {
        "result": {
            "cmsArticleWebOld": [
                {
                    "title": "贵州茅台一季度净利大增",
                    "url": "https://finance.eastmoney.com/a/1.html",
                    "mediaName": "东方财富",
                    "date": "2024-04-30 08:00:00",
                    "content": "公司披露一季报，营收同比增长 " * 30,
                },
                {
                    "title": "白酒板块全线走强",
                    "url": "https://finance.eastmoney.com/a/2.html",
                    "mediaName": "证券时报",
                    "date": "2024-04-29 18:30:00",
                    "content": "市场情绪回暖",
                },
            ]
        }
    }


def _yahoo_matches() -> list[dict[str, Any]]:
    """A Yahoo search result list with two instrument matches."""
    return [
        {
            "symbol": "AAPL",
            "shortname": "Apple Inc.",
            "exchange": "NMS",
            "quoteType": "EQUITY",
        },
        {
            "symbol": "AAPL.MX",
            "shortname": "Apple Inc.",
            "exchange": "MEX",
            "quoteType": "EQUITY",
        },
    ]


class TestHelpers:
    def test_suffix_of(self) -> None:
        assert _suffix_of("600519.SH") == "SH"
        assert _suffix_of("AAPL.US") == "US"
        assert _suffix_of("NOSUFFIX") == ""

    def test_bare_query(self) -> None:
        assert _bare_query("600519.SH") == "600519"
        assert _bare_query(" AAPL.US ") == "AAPL"

    def test_clamp_limit(self) -> None:
        assert _clamp_limit(None) == 20
        assert _clamp_limit("garbage") == 20
        assert _clamp_limit(0) == 1
        assert _clamp_limit(999) == 50
        assert _clamp_limit(5) == 5

    def test_snippet_trims(self) -> None:
        assert _snippet(None) == ""
        long = "x" * 400
        out = _snippet(long)
        assert len(out) <= 281
        assert out.endswith("…")


class TestToolContract:
    def test_name_and_schema(self) -> None:
        tool = StockNewsTool()
        assert tool.name == "get_stock_news"
        assert tool.is_readonly is True
        assert tool.parameters["required"] == []
        assert tool.parameters["properties"]["scope"]["enum"] == ["stock", "global"]
        # Description must honestly state US/HK returns matches, not articles (B6).
        desc = tool.description.lower()
        assert "matches" in desc
        assert "not return news articles" in desc or "not 'articles'" in desc


class TestExecuteSuccess:
    def test_a_share_stock_news(self) -> None:
        tool = StockNewsTool()
        with patch.object(
            eastmoney_client, "throttled_get_json", return_value=_em_news_payload()
        ) as http:
            out = json.loads(tool.execute(code="600519.SH", scope="stock", limit=10))

        http.assert_called_once()
        _, kwargs = http.call_args
        assert kwargs["host_key"] == "eastmoney"

        assert out["ok"] is True
        assert out["market"] == "a_share"
        assert out["source"] == "eastmoney"
        assert out["data"]["code"] == "600519.SH"
        assert len(out["data"]["articles"]) == 2
        first = out["data"]["articles"][0]
        assert first["title"] == "贵州茅台一季度净利大增"
        assert first["source"] == "东方财富"
        assert first["snippet"].endswith("…")

    def test_global_scope_needs_no_code(self) -> None:
        tool = StockNewsTool()
        with patch.object(
            eastmoney_client, "throttled_get_json", return_value=_em_news_payload()
        ):
            out = json.loads(tool.execute(scope="global"))

        assert out["ok"] is True
        assert out["market"] == "global"
        assert out["source"] == "eastmoney"
        assert out["data"]["scope"] == "global"
        assert len(out["data"]["articles"]) == 2

    def test_us_stock_via_yahoo_returns_matches_not_articles(self) -> None:
        tool = StockNewsTool()
        with patch.object(yahoo_client, "search", return_value=_yahoo_matches()) as srch:
            out = json.loads(tool.execute(code="AAPL.US", limit=1))

        srch.assert_called_once_with("AAPL")
        assert out["ok"] is True
        assert out["market"] == "us"
        assert out["source"] == "yahoo"
        # Instrument hits must NOT be mislabelled as articles (B6 regression).
        assert "articles" not in out["data"]
        assert out["data"]["result_type"] == "matches"
        # limit=1 caps the two matches to one.
        assert len(out["data"]["matches"]) == 1
        first = out["data"]["matches"][0]
        assert first["symbol"] == "AAPL"
        assert first["exchange"] == "NMS"
        assert first["quote_type"] == "EQUITY"

    def test_hk_stock_routes_to_yahoo(self) -> None:
        tool = StockNewsTool()
        with patch.object(yahoo_client, "search", return_value=[]):
            out = json.loads(tool.execute(code="00700.HK"))

        assert out["ok"] is True
        assert out["market"] == "hk"
        assert out["source"] == "yahoo"
        assert "articles" not in out["data"]
        assert out["data"]["result_type"] == "matches"
        assert out["data"]["matches"] == []


class TestExecuteError:
    def test_missing_code_when_stock_scope(self) -> None:
        out = json.loads(StockNewsTool().execute(scope="stock"))
        assert out["ok"] is False
        assert "code" in out["error"]

    def test_invalid_scope(self) -> None:
        out = json.loads(StockNewsTool().execute(scope="weird"))
        assert out["ok"] is False
        assert "invalid scope" in out["error"]

    def test_unsupported_market(self) -> None:
        out = json.loads(StockNewsTool().execute(code="BTC-USDT"))
        assert out["ok"] is False
        assert "unsupported market" in out["error"]

    def test_eastmoney_http_failure_envelope(self) -> None:
        tool = StockNewsTool()
        with patch.object(
            eastmoney_client,
            "throttled_get_json",
            side_effect=RuntimeError("eastmoney banned"),
        ):
            out = json.loads(tool.execute(code="600519.SH"))

        assert out["ok"] is False
        assert "eastmoney banned" in out["error"]

    def test_yahoo_failure_envelope(self) -> None:
        tool = StockNewsTool()
        with patch.object(
            yahoo_client, "search", side_effect=RuntimeError("yahoo 429")
        ):
            out = json.loads(tool.execute(code="AAPL.US"))

        assert out["ok"] is False
        assert "yahoo 429" in out["error"]
        assert "yahoo search fetch failed" in out["error"]
