"""Tests for Research Autopilot bridge tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.hypotheses import HypothesisRegistry
from src.tools import build_registry
from src.tools.autopilot_tool import (
    GenerateBacktestConfigTool,
    RunResearchAutopilotTool,
    _lookup_codes,
)
from src.tools.path_utils import safe_run_dir


def _seed_hypothesis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, universe: str):
    """Create a persisted hypothesis in an isolated registry."""
    monkeypatch.setenv("VIBE_TRADING_HYPOTHESES_PATH", str(tmp_path / "hypotheses.json"))
    return HypothesisRegistry().create(
        title="Momentum in target universe",
        thesis="A momentum signal should outperform over the test window.",
        universe=universe,
        signal_definition="Rank by trailing returns and buy the leaders.",
        data_sources=["local"],
    )


def test_lookup_codes_matches_chinext_case_insensitively() -> None:
    """Universe lookup should use the same normalized casing as input handling."""
    assert _lookup_codes("chiNext") == ["399006.SZ"]
    assert _lookup_codes("Chi-Next") == ["399006.SZ"]


def test_generate_backtest_config_writes_safe_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tool should write a config with mapped codes under the run root."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    hypothesis = _seed_hypothesis(tmp_path, monkeypatch, universe="chiNext")

    payload = json.loads(
        GenerateBacktestConfigTool().execute(
            hypothesis_id=hypothesis.hypothesis_id,
            start_date="2026-01-01",
            end_date="2026-01-31",
        )
    )

    assert payload["status"] == "ok"
    assert payload["config"]["codes"] == ["399006.SZ"]
    assert payload["config"]["source"] == "local"
    run_dir = Path(payload["run_dir"])
    assert run_dir.parent == tmp_path / ".vibe-trading" / "runs"
    assert run_dir.name.startswith("autopilot_")
    assert (run_dir / "code").is_dir()
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    assert config["start_date"] == "2026-01-01"


def test_generate_backtest_config_rejects_invalid_date_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid date ranges must fail before run artifacts are created."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    hypothesis = _seed_hypothesis(tmp_path, monkeypatch, universe="CSI 300")

    payload = json.loads(
        GenerateBacktestConfigTool().execute(
            hypothesis_id=hypothesis.hypothesis_id,
            start_date="2026-02-01",
            end_date="2026-01-01",
        )
    )

    assert payload["status"] == "error"
    assert "start_date" in payload["error"]
    assert not (tmp_path / ".vibe-trading" / "runs").exists()


def test_run_research_autopilot_uses_host_injected_session_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tool must work through build_registry without the LLM passing a session_id.

    Regression for the dead-on-arrival defect: the tool only read session_id from
    kwargs, but the LLM never knows it, so every call errored. It must fall back to
    the host-injected default the registry wires in (like the goal tools).
    """
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    hypothesis = _seed_hypothesis(tmp_path, monkeypatch, universe="CSI 300")

    registry = build_registry(session_id="sess_autopilot")
    tool = registry.get("run_research_autopilot")
    assert tool is not None

    # No session_id in kwargs — it must come from the host-injected default.
    payload = json.loads(tool.execute(hypothesis_id=hypothesis.hypothesis_id))

    assert payload["status"] == "ok"
    assert payload["hypothesis"]["hypothesis_id"] == hypothesis.hypothesis_id
    assert len(payload["goal"]["criteria"]) == 4
    assert hypothesis.thesis in json.dumps(payload, ensure_ascii=False)


def test_run_research_autopilot_unknown_hypothesis_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing hypothesis id returns a clean not-found error, not a crash."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("VIBE_TRADING_HYPOTHESES_PATH", str(tmp_path / "hypotheses.json"))

    tool = RunResearchAutopilotTool(default_session_id="sess_x")
    payload = json.loads(tool.execute(hypothesis_id="hyp_missing"))

    assert payload["status"] == "error"
    assert "not found" in payload["error"].lower()


def test_generate_backtest_config_run_dir_passes_safe_run_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The returned run_dir must be accepted by safe_run_dir.

    Regression for the high-severity defect: the tool wrote run_dir under
    ~/.vibe-trading/runs, which safe_run_dir rejected, so the advertised
    write_file -> backtest handoff could never execute.
    """
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    hypothesis = _seed_hypothesis(tmp_path, monkeypatch, universe="CSI 300")

    payload = json.loads(
        GenerateBacktestConfigTool().execute(
            hypothesis_id=hypothesis.hypothesis_id,
            start_date="2026-01-01",
            end_date="2026-01-31",
        )
    )

    assert payload["status"] == "ok"
    # The exact handoff the agent performs next; before the fix this raised
    # "run_dir ... is outside allowed run roots".
    resolved = safe_run_dir(payload["run_dir"])
    assert resolved == Path(payload["run_dir"]).resolve()


def test_generate_backtest_config_falls_back_on_unknown_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A free-text data_source that is not a real loader degrades to 'auto'."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("VIBE_TRADING_HYPOTHESES_PATH", str(tmp_path / "hypotheses.json"))
    hypothesis = HypothesisRegistry().create(
        title="Free-text source",
        thesis="Momentum should outperform.",
        universe="CSI 300",
        signal_definition="Rank by trailing returns.",
        data_sources=["my personal notes"],
    )

    payload = json.loads(
        GenerateBacktestConfigTool().execute(
            hypothesis_id=hypothesis.hypothesis_id,
            start_date="2026-01-01",
            end_date="2026-01-31",
        )
    )

    assert payload["status"] == "ok"
    assert payload["config"]["source"] == "auto"
    assert "warning" in payload
