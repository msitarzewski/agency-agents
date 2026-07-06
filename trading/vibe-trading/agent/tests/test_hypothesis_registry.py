"""Tests for the durable hypothesis registry MVP."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.hypotheses import HypothesisRegistry, default_hypotheses_path
from src.tools.hypothesis_tool import (
    CreateHypothesisTool,
    LinkBacktestTool,
    SearchHypothesesTool,
    UpdateHypothesisTool,
)


@pytest.fixture()
def storage_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use env-isolated storage for each test."""
    path = tmp_path / "hypotheses.json"
    monkeypatch.setenv("VIBE_TRADING_HYPOTHESES_PATH", str(path))
    return path


def test_default_path_uses_env_override(storage_path: Path) -> None:
    assert default_hypotheses_path() == storage_path


def test_create_persists_hypothesis(storage_path: Path) -> None:
    registry = HypothesisRegistry()
    hyp = registry.create(
        title="BTC funding mean reversion",
        thesis="Extreme perp funding mean-reverts over the next session.",
        universe="BTC-USDT perpetuals",
        signal_definition="zscore(funding) > 2",
        data_sources=["okx", "ccxt"],
        skills=["perp-funding-basis"],
    )

    assert hyp.hypothesis_id.startswith("hyp_")
    assert hyp.status == "exploring"
    assert storage_path.exists()

    reloaded = HypothesisRegistry().list()
    assert len(reloaded) == 1
    assert reloaded[0].title == "BTC funding mean reversion"
    assert reloaded[0].data_sources == ["okx", "ccxt"]


def test_update_status_and_invalidation_notes(storage_path: Path) -> None:
    registry = HypothesisRegistry()
    hyp = registry.create(title="A-share reversal", thesis="Post-gap reversal works.")

    updated = registry.update(
        hyp.hypothesis_id,
        status="testing",
        invalidation_notes="Reject if walk-forward Sharpe stays below 0.5.",
    )

    assert updated.status == "testing"
    assert "Sharpe" in updated.invalidation_notes
    assert updated.updated_at >= updated.created_at


def test_reject_invalid_status(storage_path: Path) -> None:
    registry = HypothesisRegistry()
    hyp = registry.create(title="Invalid status probe", thesis="Probe.")

    with pytest.raises(ValueError, match="unknown hypothesis status"):
        registry.update(hyp.hypothesis_id, status="live_trading")


def test_link_backtest_run_card(storage_path: Path) -> None:
    registry = HypothesisRegistry()
    hyp = registry.create(title="ETF momentum", thesis="ETF momentum persists monthly.")

    updated = registry.link_backtest(
        hyp.hypothesis_id,
        run_card_path="/tmp/run_card.json",
        backtest_run_dir="/tmp/backtest_run",
        metrics={"sharpe": 1.2},
        notes="First daily vectorized run.",
    )

    assert len(updated.run_cards) == 1
    link = updated.run_cards[0]
    assert link["run_card_path"] == "/tmp/run_card.json"
    assert link["metrics"]["sharpe"] == 1.2
    assert link["notes"] == "First daily vectorized run."


def test_search_by_text_and_status(storage_path: Path) -> None:
    registry = HypothesisRegistry()
    crypto = registry.create(
        title="Funding squeeze",
        thesis="Crowded negative funding predicts squeeze.",
        status="testing",
        universe="Crypto perps",
    )
    registry.create(
        title="Dividend drift",
        thesis="High dividend equities drift after ex-date.",
        status="exploring",
        universe="Global equities",
    )

    text_results = registry.search(query="funding squeeze")
    assert [hyp.hypothesis_id for hyp in text_results] == [crypto.hypothesis_id]

    status_results = registry.search(status="exploring")
    assert len(status_results) == 1
    assert status_results[0].title == "Dividend drift"


def test_tool_wrappers_use_env_isolated_storage(storage_path: Path) -> None:
    created = json.loads(CreateHypothesisTool().execute(
        title="Tool-created carry",
        thesis="Carry works when trend agrees.",
        data_sources=["yfinance"],
    ))
    assert created["status"] == "ok"
    hypothesis_id = created["hypothesis"]["hypothesis_id"]

    updated = json.loads(UpdateHypothesisTool().execute(
        hypothesis_id=hypothesis_id,
        status="validated",
        invalidation_notes="Monitor decay after costs.",
    ))
    assert updated["hypothesis"]["status"] == "validated"

    linked = json.loads(LinkBacktestTool().execute(
        hypothesis_id=hypothesis_id,
        run_card_path="/tmp/tool_run_card.json",
    ))
    assert linked["status"] == "ok"
    assert linked["hypothesis"]["run_cards"][0]["run_card_path"] == "/tmp/tool_run_card.json"

    found = json.loads(SearchHypothesesTool().execute(query="carry", status="validated"))
    assert found["count"] == 1
    assert found["hypotheses"][0]["hypothesis_id"] == hypothesis_id

    assert storage_path.exists()
