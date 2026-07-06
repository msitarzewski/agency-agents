"""Tests for financial_statements_tool: envelope shape, dispatch, isolation.

All HTTP is mocked at the functions the tool imports — every market routes
through the Eastmoney client's ``get_json`` / ``resolve_secid`` — so no test
touches a live endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools.financial_statements_tool import FinancialStatementsTool

# Eastmoney datacenter report success body: result.data is a list of rows.
_EM_PAYLOAD = {
    "result": {
        "data": [
            {"REPORT_DATE": "2024-12-31", "TOTAL_REVENUE": 383.0, "NETPROFIT": 96.0},
        ]
    }
}

# Eastmoney A-share report success body: two periods of flat rows.
_EM_A_PAYLOAD = {
    "result": {
        "data": [
            {"REPORT_DATE": "2024-12-31", "TOTAL_ASSETS": 100.0, "NETPROFIT": 12.0},
            {"REPORT_DATE": "2023-12-31", "TOTAL_ASSETS": 90.0, "NETPROFIT": 10.0},
        ]
    }
}


class TestSuccessEnvelope:
    """A resolvable symbol yields the ok envelope with parsed periods."""

    def test_a_share_uses_eastmoney_and_parses_periods(self):
        with patch(
            "src.tools.financial_statements_tool.resolve_secid",
            return_value="1.600519",
        ), patch(
            "src.tools.financial_statements_tool.get_json",
            return_value=_EM_A_PAYLOAD,
        ) as mock_get:
            text = FinancialStatementsTool().execute(
                code="600519.SH", statement="balance", period="annual"
            )

        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["market"] == "a_share"
        assert payload["source"] == "eastmoney"
        assert payload["statement"] == "balance"
        assert payload["period"] == "annual"
        assert "error" not in payload

        periods = payload["data"]["600519.SH"]["periods"]
        assert len(periods) == 2
        assert periods[0]["REPORT_DATE"] == "2024-12-31"

        # A-share balance sheet hits the A-share F10 report, filtered on the
        # dotted SECUCODE (not the bare SECURITY_CODE used for US/HK).
        sent_params = mock_get.call_args.kwargs["params"]
        assert sent_params["reportName"] == "RPT_F10_FINANCE_GBALANCE"
        assert 'SECUCODE="600519.SH"' in sent_params["filter"]
        assert "SECURITY_CODE" not in sent_params["filter"]

    def test_us_uses_eastmoney_report_api(self):
        with patch(
            "src.tools.financial_statements_tool.resolve_secid",
            return_value="105.AAPL",
        ), patch(
            "src.tools.financial_statements_tool.get_json",
            return_value=_EM_PAYLOAD,
        ) as mock_get:
            text = FinancialStatementsTool().execute(
                code="AAPL.US", statement="income", period="quarter"
            )

        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["market"] == "us"
        assert payload["source"] == "eastmoney"

        periods = payload["data"]["AAPL.US"]["periods"]
        assert periods[0]["REPORT_DATE"] == "2024-12-31"

        # US income report name + bare code filter were passed through.
        sent_params = mock_get.call_args.kwargs["params"]
        assert sent_params["reportName"] == "RPT_USF10_FN_INCOME"
        assert 'SECURITY_CODE="AAPL"' in sent_params["filter"]

    def test_hk_indicators_use_hk_report_name(self):
        with patch(
            "src.tools.financial_statements_tool.resolve_secid",
            return_value="116.00700",
        ), patch(
            "src.tools.financial_statements_tool.get_json",
            return_value=_EM_PAYLOAD,
        ) as mock_get:
            FinancialStatementsTool().execute(
                code="00700.HK", statement="indicators", period="annual"
            )

        assert (
            mock_get.call_args.kwargs["params"]["reportName"]
            == "RPT_HKF10_FN_GMAININDICATOR"
        )


class TestAllFailedSurfacesError:
    """When the fetch fails for every requested code, the envelope is ok=false.

    The failure detail stays in the per-code result AND is mirrored to a
    top-level ``error`` so a nested fetch failure is never masked by a
    top-level ``ok: true``.
    """

    def test_http_failure_yields_top_level_ok_false(self):
        with patch(
            "src.tools.financial_statements_tool.resolve_secid",
            return_value="1.600519",
        ), patch(
            "src.tools.financial_statements_tool.get_json",
            side_effect=RuntimeError("HTTP 429"),
        ):
            text = FinancialStatementsTool().execute(
                code="600519.SH", statement="income"
            )

        payload = json.loads(text)
        assert payload["ok"] is False
        assert "429" in payload["error"]
        assert "429" in payload["data"]["600519.SH"]["error"]

    def test_unresolvable_us_symbol_yields_ok_false(self):
        with patch(
            "src.tools.financial_statements_tool.resolve_secid",
            return_value=None,
        ):
            text = FinancialStatementsTool().execute(code="ZZZZ.US")

        payload = json.loads(text)
        assert payload["ok"] is False
        assert payload["error"] == "unresolvable symbol"
        assert payload["data"]["ZZZZ.US"]["error"] == "unresolvable symbol"

    def test_empty_a_share_payload_yields_no_periods_but_ok_true(self):
        # An empty-but-well-formed payload is data (zero periods), not a fetch
        # failure, so the envelope stays ok=true.
        with patch(
            "src.tools.financial_statements_tool.resolve_secid",
            return_value="0.000001",
        ), patch(
            "src.tools.financial_statements_tool.get_json",
            return_value={"result": {}},
        ):
            text = FinancialStatementsTool().execute(code="000001.SZ")

        payload = json.loads(text)
        assert payload["ok"] is True
        assert "error" not in payload
        assert payload["data"]["000001.SZ"]["periods"] == []


class TestPeriodSelection:
    """Period is chosen client-side. Eastmoney's REPORT_TYPE is locale text
    (年报 / 一季报) or a market-specific string (2026/Q1), so no REPORT_TYPE
    filter is sent; 'annual' keeps fiscal-year-end rows, falling back to the
    full series when an issuer has no December year-end (e.g. a US fiscal year).
    """

    _MIXED = {
        "result": {
            "data": [
                {"REPORT_DATE": "2025-03-31 00:00:00", "TOTAL_ASSETS": 1},
                {"REPORT_DATE": "2024-12-31 00:00:00", "TOTAL_ASSETS": 2},
                {"REPORT_DATE": "2024-09-30 00:00:00", "TOTAL_ASSETS": 3},
                {"REPORT_DATE": "2023-12-31 00:00:00", "TOTAL_ASSETS": 4},
            ]
        }
    }
    _NO_YEAR_END = {
        "result": {
            "data": [
                {"REPORT_DATE": "2026-03-28 00:00:00", "TOTAL_ASSETS": 1},
                {"REPORT_DATE": "2025-09-28 00:00:00", "TOTAL_ASSETS": 2},
            ]
        }
    }

    def _run(self, payload, *, period, statement="balance",
             code="600519.SH", secid="1.600519"):
        with patch(
            "src.tools.financial_statements_tool.resolve_secid", return_value=secid,
        ), patch(
            "src.tools.financial_statements_tool.get_json", return_value=payload,
        ) as mock_get:
            text = FinancialStatementsTool().execute(
                code=code, statement=statement, period=period
            )
        return json.loads(text), mock_get

    def test_no_report_type_clause_in_filter(self):
        _, mock_get = self._run(self._MIXED, period="annual")
        assert "REPORT_TYPE" not in mock_get.call_args.kwargs["params"]["filter"]

    def test_annual_keeps_only_fiscal_year_end(self):
        payload, _ = self._run(self._MIXED, period="annual")
        dates = [p["REPORT_DATE"] for p in payload["data"]["600519.SH"]["periods"]]
        assert dates == ["2024-12-31 00:00:00", "2023-12-31 00:00:00"]

    def test_quarter_returns_full_series(self):
        payload, _ = self._run(self._MIXED, period="quarter")
        assert len(payload["data"]["600519.SH"]["periods"]) == 4

    def test_annual_falls_back_when_no_december_year_end(self):
        payload, _ = self._run(
            self._NO_YEAR_END, period="annual", code="AAPL.US", secid="105.AAPL"
        )
        # No -12-31 row -> return the full series rather than drop all data.
        assert len(payload["data"]["AAPL.US"]["periods"]) == 2

    def test_a_share_indicators_use_mainfinadata_report(self):
        _, mock_get = self._run(self._MIXED, period="annual", statement="indicators")
        assert (
            mock_get.call_args.kwargs["params"]["reportName"]
            == "RPT_F10_FINANCE_MAINFINADATA"
        )


class TestErrorEnvelope:
    """Input validation returns the ok=false envelope before any HTTP."""

    def test_missing_code_rejected(self):
        payload = json.loads(FinancialStatementsTool().execute())
        assert payload["ok"] is False
        assert "code" in payload["error"]

    def test_blank_code_rejected(self):
        payload = json.loads(FinancialStatementsTool().execute(code="   "))
        assert payload["ok"] is False

    def test_unknown_suffix_rejected(self):
        payload = json.loads(FinancialStatementsTool().execute(code="BTC-USDT"))
        assert payload["ok"] is False
        assert "suffix" in payload["error"]

    def test_invalid_statement_rejected(self):
        payload = json.loads(
            FinancialStatementsTool().execute(code="600519.SH", statement="equity")
        )
        assert payload["ok"] is False
        assert "statement" in payload["error"]

    def test_invalid_period_rejected(self):
        payload = json.loads(
            FinancialStatementsTool().execute(code="600519.SH", period="ttm")
        )
        assert payload["ok"] is False
        assert "period" in payload["error"]
