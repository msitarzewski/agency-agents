"""Tests for get_sec_filings: success + error envelopes, HTTP fully mocked.

The SEC client functions (``cik_for`` / ``get_submissions`` /
``get_company_facts``) are patched on the tool module, so no test reaches a
live ``sec.gov`` endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools import sec_filings_tool as sft
from src.tools.sec_filings_tool import SecFilingsTool

_SUBMISSIONS = {
    "cik": "320193",
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "form": ["10-K", "8-K", "10-Q"],
            "accessionNumber": [
                "0000320193-23-000106",
                "0000320193-23-000077",
                "0000320193-23-000064",
            ],
            "filingDate": ["2023-11-03", "2023-08-04", "2023-08-04"],
            "reportDate": ["2023-09-30", "", "2023-07-01"],
            "primaryDocument": ["aapl-20230930.htm", "ex.htm", "aapl-20230701.htm"],
            "primaryDocDescription": ["10-K", "8-K", "10-Q"],
        }
    },
}

_FACTS = {
    "cik": 320193,
    "facts": {
        "us-gaap": {
            "Revenues": {
                "label": "Revenues",
                "units": {
                    # richer bucket should win the unit pick
                    "USD": [
                        {"end": "2021-09-25", "val": 365817000000, "fy": 2021, "fp": "FY", "form": "10-K", "accn": "a1"},
                        {"end": "2022-09-24", "val": 394328000000, "fy": 2022, "fp": "FY", "form": "10-K", "accn": "a2"},
                    ],
                    "USD-shares": [
                        {"end": "2022-09-24", "val": 1, "fy": 2022, "fp": "FY", "form": "10-K", "accn": "a3"},
                    ],
                },
            }
        }
    },
}


def test_success_lists_filings_with_document_urls():
    with patch.object(sft, "cik_for", return_value="0000320193") as mock_cik, patch.object(
        sft, "get_submissions", return_value=_SUBMISSIONS
    ) as mock_sub:
        out = SecFilingsTool().execute(ticker="aapl")

    mock_cik.assert_called_once_with("AAPL")
    mock_sub.assert_called_once_with("0000320193")

    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["market"] == "US"
    assert payload["source"] == "sec_edgar"
    assert payload["data"]["ticker"] == "AAPL"
    assert payload["data"]["cik"] == "0000320193"

    filings = payload["data"]["filings"]
    assert len(filings) == 3
    assert filings[0]["form"] == "10-K"
    assert filings[0]["accession_number"] == "0000320193-23-000106"
    assert filings[0]["report_date"] == "2023-09-30"
    assert filings[0]["document_url"] == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019323000106/aapl-20230930.htm"
    )
    # empty reportDate normalizes to None, not ""
    assert filings[1]["report_date"] is None
    # no metric requested -> key absent
    assert "metric" not in payload["data"]


def test_form_filter_keeps_only_matching_forms():
    with patch.object(sft, "cik_for", return_value="0000320193"), patch.object(
        sft, "get_submissions", return_value=_SUBMISSIONS
    ):
        out = SecFilingsTool().execute(ticker="AAPL", form="10-q")
    payload = json.loads(out)
    filings = payload["data"]["filings"]
    assert len(filings) == 1
    assert filings[0]["form"] == "10-Q"


def test_metric_series_picks_richest_unit_and_caps_limit():
    with patch.object(sft, "cik_for", return_value="0000320193"), patch.object(
        sft, "get_submissions", return_value=_SUBMISSIONS
    ), patch.object(sft, "get_company_facts", return_value=_FACTS) as mock_facts:
        out = SecFilingsTool().execute(ticker="AAPL", metric="Revenues", limit=1)

    mock_facts.assert_called_once_with("0000320193")
    payload = json.loads(out)
    metric = payload["data"]["metric"]
    assert metric["concept"] == "Revenues"
    assert metric["unit"] == "USD"
    assert metric["label"] == "Revenues"
    # limit=1 keeps the most recent point (last in source order)
    assert len(metric["points"]) == 1
    assert metric["points"][0]["val"] == 394328000000.0
    assert metric["points"][0]["fiscal_year"] == 2022


def test_unknown_metric_returns_empty_series_not_error():
    with patch.object(sft, "cik_for", return_value="0000320193"), patch.object(
        sft, "get_submissions", return_value=_SUBMISSIONS
    ), patch.object(sft, "get_company_facts", return_value=_FACTS):
        out = SecFilingsTool().execute(ticker="AAPL", metric="NotAConcept")
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["data"]["metric"]["points"] == []
    assert payload["data"]["metric"]["unit"] is None


def test_missing_ticker_returns_error_envelope():
    out = SecFilingsTool().execute()
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "required" in payload["error"]


def test_unknown_ticker_returns_error_envelope():
    with patch.object(sft, "cik_for", return_value=None):
        out = SecFilingsTool().execute(ticker="NOPE")
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "not found" in payload["error"]


def test_submissions_failure_is_caught_as_error_envelope():
    with patch.object(sft, "cik_for", return_value="0000320193"), patch.object(
        sft, "get_submissions", side_effect=RuntimeError("HTTP 429")
    ):
        out = SecFilingsTool().execute(ticker="AAPL")
    payload = json.loads(out)
    assert payload["ok"] is False
    assert "429" in payload["error"]
