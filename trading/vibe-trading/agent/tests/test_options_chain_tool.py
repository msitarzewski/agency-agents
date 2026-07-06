"""Tests for the get_options_chain tool.

All HTTP is mocked at ``yahoo_client.get_options`` (the client function the tool
imports), so no test ever reaches a live Yahoo endpoint.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.tools import options_chain_tool as oc


def _sample_result() -> dict:
    return {
        "expirationDates": [1750000000, 1750604800],
        "strikes": [190.0, 195.0, 200.0],
        "options": [
            {
                "expirationDate": 1750000000,
                "calls": [
                    {
                        "contractSymbol": "AAPL250101C00190000",
                        "strike": 190.0,
                        "lastPrice": 12.5,
                        "bid": 12.3,
                        "ask": 12.7,
                        "volume": 1500,
                        "openInterest": 8000,
                        "impliedVolatility": 0.2841,
                        "inTheMoney": True,
                        "expiration": 1750000000,
                    }
                ],
                "puts": [
                    {
                        "contractSymbol": "AAPL250101P00190000",
                        "strike": 190.0,
                        "lastPrice": 3.1,
                        "bid": 3.0,
                        "ask": 3.2,
                        "volume": 900,
                        "openInterest": 4200,
                        "impliedVolatility": 0.3012,
                        "inTheMoney": False,
                        "expiration": 1750000000,
                    }
                ],
            }
        ],
    }


class TestOptionsChainSuccess:
    """Happy-path envelope shape and field normalization."""

    def test_success_envelope_normalizes_contracts(self):
        with patch.object(
            oc.yahoo_client, "get_options", return_value=_sample_result()
        ) as mock_get:
            out = oc.OptionsChainTool().execute(ticker="AAPL.US")

        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["market"] == "us"
        assert payload["source"] == "yahoo"

        data = payload["data"]
        assert data["ticker"] == "AAPL.US"
        assert data["expiration"] == 1750000000
        assert data["expirations"] == [1750000000, 1750604800]
        assert data["calls_count"] == 1
        assert data["puts_count"] == 1

        call = data["calls"][0]
        assert call["contract_symbol"] == "AAPL250101C00190000"
        assert call["strike"] == 190.0
        assert call["implied_volatility"] == 0.2841
        assert call["open_interest"] == 8000
        assert call["in_the_money"] is True

        put = data["puts"][0]
        assert put["in_the_money"] is False
        assert put["bid"] == 3.0

        # Ticker flows through unchanged; no expiration -> nearest.
        _, kwargs = mock_get.call_args
        assert kwargs["expiration"] is None

    def test_explicit_expiration_passed_through(self):
        with patch.object(
            oc.yahoo_client, "get_options", return_value=_sample_result()
        ) as mock_get:
            oc.OptionsChainTool().execute(ticker="AAPL", expiration="1750000000")
        _, kwargs = mock_get.call_args
        assert kwargs["expiration"] == 1750000000

    def test_empty_chain_is_ok_with_zero_contracts(self):
        with patch.object(oc.yahoo_client, "get_options", return_value={}):
            out = oc.OptionsChainTool().execute(ticker="AAPL")
        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["data"]["calls"] == []
        assert payload["data"]["puts"] == []
        assert payload["data"]["expiration"] is None

    def test_contracts_capped(self):
        bloated = _sample_result()
        bloated["options"][0]["calls"] = [
            {"strike": float(i)} for i in range(500)
        ]
        with patch.object(oc.yahoo_client, "get_options", return_value=bloated):
            out = oc.OptionsChainTool().execute(ticker="AAPL")
        payload = json.loads(out)
        assert payload["data"]["calls_count"] == oc._MAX_CONTRACTS_PER_SIDE


class TestOptionsChainErrors:
    """Error envelopes: missing ticker, bad expiration, upstream failure."""

    def test_missing_ticker_returns_error_envelope(self):
        out = oc.OptionsChainTool().execute(ticker="  ")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "required" in payload["error"]

    def test_bad_expiration_returns_error_envelope(self):
        out = oc.OptionsChainTool().execute(ticker="AAPL", expiration="not-an-int")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "epoch" in payload["error"]

    def test_upstream_failure_becomes_error_envelope(self):
        with patch.object(
            oc.yahoo_client,
            "get_options",
            side_effect=RuntimeError("HTTP 429 banned"),
        ):
            out = oc.OptionsChainTool().execute(ticker="AAPL")
        payload = json.loads(out)
        assert payload["ok"] is False
        assert "yahoo options request failed" in payload["error"]
        assert "429" in payload["error"]
