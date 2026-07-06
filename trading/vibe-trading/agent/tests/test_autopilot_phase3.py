"""Tests for Research Autopilot Phase 3 tools.

Covers ``scaffold_signal_engine`` (contract-correct stub generation) and
``link_autopilot_backtest`` (run-card metrics -> hypothesis link) in
``src.tools.autopilot_tool``.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

from src.hypotheses import HypothesisRegistry
from src.tools.autopilot_tool import (
    LinkAutopilotBacktestTool,
    ScaffoldSignalEngineTool,
    _get_hypothesis,
)


@pytest.fixture()
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate the hypothesis registry and allow tmp_path as a run root."""
    monkeypatch.setenv(
        "VIBE_TRADING_HYPOTHESES_PATH", str(tmp_path / "hypotheses.json")
    )
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))
    return tmp_path


def _make_hypothesis(**overrides) -> str:
    registry = HypothesisRegistry()
    kwargs = dict(
        title="A-share momentum",
        thesis="Cross-sectional momentum persists in large caps.",
        universe="CSI 300",
        signal_definition="rank(returns_20d) top decile",
        data_sources=["akshare"],
    )
    kwargs.update(overrides)
    return registry.create(**kwargs).hypothesis_id


def _run_dir(base: Path) -> Path:
    d = base / "runs" / "autopilot_test"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------
# scaffold_signal_engine
# --------------------------------------------------------------------------


def test_scaffold_requires_hypothesis_id(isolated_env: Path) -> None:
    result = json.loads(
        ScaffoldSignalEngineTool().execute(
            hypothesis_id="", run_dir=str(_run_dir(isolated_env))
        )
    )
    assert result["status"] == "error"
    assert "hypothesis_id is required" in result["error"]


def test_scaffold_requires_run_dir(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    result = json.loads(
        ScaffoldSignalEngineTool().execute(hypothesis_id=hyp_id, run_dir="")
    )
    assert result["status"] == "error"
    assert "run_dir is required" in result["error"]


def test_scaffold_rejects_path_outside_run_roots(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    result = json.loads(
        ScaffoldSignalEngineTool().execute(
            hypothesis_id=hyp_id, run_dir="/etc/evil_run"
        )
    )
    assert result["status"] == "error"
    assert "run roots" in result["error"]


def test_scaffold_unknown_hypothesis(isolated_env: Path) -> None:
    result = json.loads(
        ScaffoldSignalEngineTool().execute(
            hypothesis_id="hyp_missing", run_dir=str(_run_dir(isolated_env))
        )
    )
    assert result["status"] == "error"
    assert "not found" in result["error"]


def test_scaffold_writes_contract_correct_stub(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    run_dir = _run_dir(isolated_env)
    result = json.loads(
        ScaffoldSignalEngineTool().execute(
            hypothesis_id=hyp_id, run_dir=str(run_dir)
        )
    )

    assert result["status"] == "ok"
    signal_path = Path(result["signal_engine_path"])
    assert signal_path.exists()
    assert signal_path == run_dir / "code" / "signal_engine.py"

    # The signal_definition is embedded for the agent to implement against.
    text = signal_path.read_text(encoding="utf-8")
    assert "rank(returns_20d) top decile" in text

    # The stub must satisfy the backtest runner contract: a SignalEngine
    # class instantiable with no args, with a callable generate(data_map).
    spec = importlib.util.spec_from_file_location("scaffolded_engine", signal_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine_cls = module.SignalEngine

    init_sig = inspect.signature(engine_cls.__init__)
    required = [
        p.name
        for p in init_sig.parameters.values()
        if p.name != "self" and p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    assert required == []  # runner can call SignalEngine()
    assert callable(getattr(engine_cls, "generate", None))

    # The flat default returns a dict of pd.Series aligned to the input index.
    idx = pd.date_range("2020-01-01", periods=5)
    data_map = {"000300.SH": pd.DataFrame({"close": range(5)}, index=idx)}
    out = engine_cls().generate(data_map)
    assert set(out) == {"000300.SH"}
    assert isinstance(out["000300.SH"], pd.Series)
    assert (out["000300.SH"] == 0.0).all()
    assert list(out["000300.SH"].index) == list(idx)


def test_scaffold_refuses_overwrite_by_default(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    run_dir = _run_dir(isolated_env)
    tool = ScaffoldSignalEngineTool()
    first = json.loads(tool.execute(hypothesis_id=hyp_id, run_dir=str(run_dir)))
    assert first["status"] == "ok"

    # Mark the file so we can detect an unwanted overwrite.
    signal_path = Path(first["signal_engine_path"])
    signal_path.write_text("# user edits\n", encoding="utf-8")

    second = json.loads(tool.execute(hypothesis_id=hyp_id, run_dir=str(run_dir)))
    assert second["status"] == "error"
    assert "already exists" in second["error"]
    assert signal_path.read_text(encoding="utf-8") == "# user edits\n"

    third = json.loads(
        tool.execute(hypothesis_id=hyp_id, run_dir=str(run_dir), overwrite=True)
    )
    assert third["status"] == "ok"
    assert "SignalEngine" in signal_path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# link_autopilot_backtest
# --------------------------------------------------------------------------


def _write_run_card(run_dir: Path, metrics: dict | None) -> None:
    card: dict = {"schema_version": 1, "run_dir": str(run_dir)}
    if metrics is not None:
        card["metrics"] = metrics
    (run_dir / "run_card.json").write_text(
        json.dumps(card, ensure_ascii=False), encoding="utf-8"
    )


def test_link_requires_run_dir(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    result = json.loads(
        LinkAutopilotBacktestTool().execute(hypothesis_id=hyp_id, run_dir="")
    )
    assert result["status"] == "error"
    assert "run_dir is required" in result["error"]


def test_link_missing_run_card(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    run_dir = _run_dir(isolated_env)
    result = json.loads(
        LinkAutopilotBacktestTool().execute(
            hypothesis_id=hyp_id, run_dir=str(run_dir)
        )
    )
    assert result["status"] == "error"
    assert "run_card.json not found" in result["error"]


def test_link_corrupt_run_card(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    run_dir = _run_dir(isolated_env)
    (run_dir / "run_card.json").write_text("{not json", encoding="utf-8")
    result = json.loads(
        LinkAutopilotBacktestTool().execute(
            hypothesis_id=hyp_id, run_dir=str(run_dir)
        )
    )
    assert result["status"] == "error"
    assert "parse error" in result["error"]


def test_link_unknown_hypothesis(isolated_env: Path) -> None:
    run_dir = _run_dir(isolated_env)
    _write_run_card(run_dir, {"sharpe": 1.2})
    result = json.loads(
        LinkAutopilotBacktestTool().execute(
            hypothesis_id="hyp_missing", run_dir=str(run_dir)
        )
    )
    assert result["status"] == "error"
    assert "not found" in result["error"]


def test_link_extracts_metrics_and_links(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    run_dir = _run_dir(isolated_env)
    _write_run_card(run_dir, {"sharpe": 1.42, "total_return": 0.31})

    result = json.loads(
        LinkAutopilotBacktestTool().execute(
            hypothesis_id=hyp_id, run_dir=str(run_dir), notes="phase3 link"
        )
    )

    assert result["status"] == "ok"
    assert result["metrics"] == {"sharpe": 1.42, "total_return": 0.31}
    assert result["hypothesis"]["run_cards_count"] == 1

    # The link is persisted on the hypothesis run_cards.
    reloaded = _get_hypothesis(hyp_id)
    assert len(reloaded.run_cards) == 1
    card = reloaded.run_cards[0]
    assert card["backtest_run_dir"] == str(run_dir)
    assert card["metrics"] == {"sharpe": 1.42, "total_return": 0.31}


def test_link_absent_metrics_degrades_with_warning(isolated_env: Path) -> None:
    hyp_id = _make_hypothesis()
    run_dir = _run_dir(isolated_env)
    _write_run_card(run_dir, None)  # no metrics key

    result = json.loads(
        LinkAutopilotBacktestTool().execute(
            hypothesis_id=hyp_id, run_dir=str(run_dir)
        )
    )
    assert result["status"] == "ok"
    assert result["metrics"] == {}
    assert "warning" in result
    assert "empty metrics" in result["warning"]
