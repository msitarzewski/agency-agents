"""Tests that content_filter_warnings from config flows through to run_card.json warnings."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backtest.run_card import write_run_card


def test_content_filter_warnings_surfaced_in_run_card(tmp_path: Path) -> None:
    """When config carries content_filter_warnings, run_card.json warnings must contain them."""
    config = {
        "codes": ["SPY"],
        "start_date": "2025-01-01",
        "end_date": "2025-01-06",
        "source": "yfinance",
        "engine": "options",
        "content_filter_warnings": [
            "3/10 LLM responses (30%) were blocked by content moderation."
            " Consider switching to a provider with less aggressive filtering"
            " for event-driven analysis."
        ],
    }
    warnings = config.get("content_filter_warnings") or None

    card = write_run_card(
        tmp_path,
        config,
        {"sharpe": 1.0},
        warnings=warnings,
    )

    json_path = tmp_path / "run_card.json"
    loaded = json.loads(json_path.read_text(encoding="utf-8"))

    assert loaded["warnings"] == card["warnings"]
    assert len(loaded["warnings"]) == 1
    assert "30%" in loaded["warnings"][0]
    assert "content moderation" in loaded["warnings"][0]


def test_no_content_filter_warnings_yields_empty_warnings(tmp_path: Path) -> None:
    """When config has no content_filter_warnings, run_card.json warnings is empty."""
    config = {
        "codes": ["AAPL"],
        "start_date": "2025-01-01",
        "end_date": "2025-02-01",
        "source": "yfinance",
        "engine": "daily",
    }
    warnings = config.get("content_filter_warnings") or None

    write_run_card(
        tmp_path,
        config,
        {"sharpe": 1.2},
        warnings=warnings,
    )

    json_path = tmp_path / "run_card.json"
    loaded = json.loads(json_path.read_text(encoding="utf-8"))

    assert loaded["warnings"] == []


def test_options_engine_surfaces_content_filter_warnings(tmp_path: Path) -> None:
    """End-to-end: options engine passes config content_filter_warnings to run_card."""
    from backtest.engines.options_portfolio import run_options_backtest

    dates = pd.bdate_range("2025-01-01", periods=4)
    bars = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [101.0, 102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0, 102.0],
            "close": [100.5, 101.5, 102.5, 103.5],
            "volume": [1000, 1100, 1200, 1300],
        },
        index=dates,
    )

    class FakeLoader:
        name = "yfinance"

        def fetch(self, codes, start_date, end_date):
            return {"SPY": bars.copy()}

    class SignalEngine:
        def generate(self, data_map):
            return [
                {
                    "date": "2025-01-01",
                    "action": "open",
                    "underlying": "SPY",
                    "legs": [{"type": "call", "strike": 101.0, "expiry": "2025-03-21", "qty": 1}],
                },
                {
                    "date": "2025-01-03",
                    "action": "close",
                    "underlying": "SPY",
                    "legs": [{"type": "call", "strike": 101.0, "expiry": "2025-03-21", "qty": 1}],
                },
            ]

    run_options_backtest(
        {
            "codes": ["SPY"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-06",
            "source": "yfinance",
            "engine": "options",
            "initial_cash": 100_000,
            "content_filter_warnings": [
                "2/10 LLM responses (20%) were blocked by content moderation."
                " Consider switching to a provider with less aggressive filtering"
                " for event-driven analysis."
            ],
        },
        FakeLoader(),
        SignalEngine(),
        tmp_path,
    )

    card = json.loads((tmp_path / "run_card.json").read_text(encoding="utf-8"))
    assert len(card["warnings"]) == 1
    assert "20%" in card["warnings"][0]
    assert "content moderation" in card["warnings"][0]


def test_options_engine_no_warnings_yields_empty(tmp_path: Path) -> None:
    """End-to-end: options engine without content_filter_warnings produces empty warnings."""
    from backtest.engines.options_portfolio import run_options_backtest

    dates = pd.bdate_range("2025-01-01", periods=4)
    bars = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [101.0, 102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0, 102.0],
            "close": [100.5, 101.5, 102.5, 103.5],
            "volume": [1000, 1100, 1200, 1300],
        },
        index=dates,
    )

    class FakeLoader:
        name = "yfinance"

        def fetch(self, codes, start_date, end_date):
            return {"SPY": bars.copy()}

    class SignalEngine:
        def generate(self, data_map):
            return [
                {
                    "date": "2025-01-01",
                    "action": "open",
                    "underlying": "SPY",
                    "legs": [{"type": "call", "strike": 101.0, "expiry": "2025-03-21", "qty": 1}],
                },
                {
                    "date": "2025-01-03",
                    "action": "close",
                    "underlying": "SPY",
                    "legs": [{"type": "call", "strike": 101.0, "expiry": "2025-03-21", "qty": 1}],
                },
            ]

    run_options_backtest(
        {
            "codes": ["SPY"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-06",
            "source": "yfinance",
            "engine": "options",
            "initial_cash": 100_000,
        },
        FakeLoader(),
        SignalEngine(),
        tmp_path,
    )

    card = json.loads((tmp_path / "run_card.json").read_text(encoding="utf-8"))
    assert card["warnings"] == []
