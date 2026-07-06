"""Regression tests for strict run card JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from backtest.run_card import write_run_card


def test_run_card_replaces_non_finite_metrics_with_null(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    card = write_run_card(
        run_dir,
        {"codes": ["AAPL"], "source": "yfinance"},
        {
            "sharpe": float("nan"),
            "sortino": float("inf"),
            "max_drawdown": float("-inf"),
            "total_return": 0.12,
            "validation": {
                "consistency": float("nan"),
                "windows": [1.0, float("inf"), {"tail_risk": float("-inf")}],
            },
        },
    )

    raw_json = (run_dir / "run_card.json").read_text(encoding="utf-8")
    markdown = (run_dir / "run_card.md").read_text(encoding="utf-8")

    for token in ("NaN", "Infinity", "-Infinity"):
        assert token not in raw_json
        assert token not in markdown

    loaded = json.loads(raw_json)
    assert loaded == card
    assert loaded["metrics"] == {
        "max_drawdown": None,
        "sharpe": None,
        "sortino": None,
        "total_return": 0.12,
    }
    assert loaded["validation"] == {
        "consistency": None,
        "windows": [1.0, None, {"tail_risk": None}],
    }
