"""Tests for local agent research goal tools."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.agent.skills import SkillsLoader
from src.goal import GoalStore
from src.tools.goal_tool import (
    AddGoalEvidenceTool,
    GetResearchGoalTool,
    StartResearchGoalTool,
    UpdateResearchGoalStatusTool,
)


def test_local_goal_tools_use_injected_session(tmp_path: Path) -> None:
    """Agent tools can start, inspect, and mutate the current session goal."""
    store = GoalStore(tmp_path / "goals.db")
    start = StartResearchGoalTool(default_session_id="session-1", store=store)
    get = GetResearchGoalTool(default_session_id="session-1", store=store)
    add = AddGoalEvidenceTool(default_session_id="session-1", store=store)

    created = json.loads(
        start.execute(
            objective="Evaluate NVDA momentum as a research-only thesis.",
            criteria=["Define thesis", "Check price action"],
        )
    )

    assert created["status"] == "ok"
    assert created["snapshot"]["goal"]["session_id"] == "session-1"

    fetched = json.loads(get.execute())
    assert fetched["status"] == "ok"
    assert fetched["snapshot"]["goal"]["goal_id"] == created["snapshot"]["goal"]["goal_id"]

    evidence = json.loads(
        add.execute(
            criterion_index=2,
            text="NVDA outperformed QQQ over the last 5 sessions.",
            source_provider="pytest",
            source_type="manual_note",
        )
    )

    assert evidence["status"] == "ok"
    assert evidence["snapshot"]["evidence_count"] == 1
    assert (
        evidence["evidence"]["criterion_id"]
        == created["snapshot"]["criteria"][1]["criterion_id"]
    )


def test_goal_tool_without_session_returns_validation_error(tmp_path: Path) -> None:
    """Goal tools fail cleanly when no session id was injected or supplied."""
    store = GoalStore(tmp_path / "goals.db")
    result = json.loads(GetResearchGoalTool(store=store).execute())

    assert result["status"] == "error"
    assert result["error_type"] == "validation"
    assert "session_id" in result["error"]


def test_goal_tool_rejects_live_trading_objective(tmp_path: Path) -> None:
    """Local agent tools keep the research-only boundary."""
    store = GoalStore(tmp_path / "goals.db")
    tool = StartResearchGoalTool(default_session_id="session-1", store=store)

    result = json.loads(tool.execute(objective="Buy 1 BTC now."))

    assert result["status"] == "error"
    assert result["error_type"] == "validation"
    assert "live trading" in result["error"]


def test_registry_injects_session_id_into_goal_tools() -> None:
    """SessionService can build a registry with session-scoped goal tools."""
    from src.tools import build_registry

    registry = build_registry(session_id="session-xyz")
    tool = registry.get("start_research_goal")

    assert tool is not None
    assert getattr(tool, "_default_session_id") == "session-xyz"


def test_goal_tools_emit_mutation_events(tmp_path: Path) -> None:
    """Goal tools notify the host when they mutate session-scoped goal state."""
    store = GoalStore(tmp_path / "goals.db")
    events: list[tuple[str, dict]] = []

    def emit(event_type: str, data: dict) -> None:
        events.append((event_type, data))

    start = StartResearchGoalTool(default_session_id="session-1", store=store, event_callback=emit)
    add = AddGoalEvidenceTool(default_session_id="session-1", store=store, event_callback=emit)

    created = json.loads(
        start.execute(
            objective="Evaluate NVDA momentum as a research-only thesis.",
            criteria=["Define thesis", "Check price action"],
        )
    )
    evidence = json.loads(
        add.execute(
            goal_id=created["snapshot"]["goal"]["goal_id"],
            criterion_index=1,
            text="Evidence from a local tool call.",
        )
    )

    assert created["status"] == "ok"
    assert evidence["status"] == "ok"
    assert [item[0] for item in events] == ["goal.created", "goal.evidence"]
    assert events[0][1]["goal"]["session_id"] == "session-1"
    assert events[1][1]["goal_id"] == created["snapshot"]["goal"]["goal_id"]


def test_goal_evidence_tool_binds_runtime_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Runtime run_dir artifacts become verified goal evidence automatically."""
    run_root = tmp_path / "runs"
    run_dir = run_root / "goal-tool-run"
    artifact = run_dir / "artifacts" / "metrics.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("symbol,return\nNVDA,0.12\n", encoding="utf-8")
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(run_root))
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(run_root))

    store = GoalStore(tmp_path / "goals.db")
    start = StartResearchGoalTool(default_session_id="session-1", store=store)
    add = AddGoalEvidenceTool(default_session_id="session-1", store=store)
    created = json.loads(
        start.execute(
            objective="Evaluate NVDA momentum as a research-only thesis.",
            criteria=["Check price action"],
        )
    )

    result = json.loads(
        add.execute(
            goal_id=created["snapshot"]["goal"]["goal_id"],
            criterion_index=1,
            text="Generated metrics artifact for NVDA momentum.",
            source_provider="pytest",
            source_type="market_data",
            artifact_path="artifacts/metrics.csv",
            run_dir=str(run_dir),
        )
    )

    expected_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    evidence = result["evidence"]
    assert result["status"] == "ok"
    assert evidence["run_id"] == "goal-tool-run"
    assert evidence["artifact_path"] == str(artifact.resolve())
    assert evidence["artifact_hash"] == expected_hash
    assert evidence["verification_status"] == "verified"


def test_goal_status_tool_can_cancel_current_goal(tmp_path: Path) -> None:
    """Agent tools can move a current goal to a terminal status."""
    store = GoalStore(tmp_path / "goals.db")
    start = StartResearchGoalTool(default_session_id="session-1", store=store)
    update = UpdateResearchGoalStatusTool(default_session_id="session-1", store=store)
    created = json.loads(
        start.execute(
            objective="Evaluate NVDA momentum as a research-only thesis.",
            criteria=["Define thesis"],
        )
    )
    goal_id = created["snapshot"]["goal"]["goal_id"]

    result = json.loads(
        update.execute(
            goal_id=goal_id,
            expected_goal_id=goal_id,
            status="cancelled",
            recap="Cancelled during tool test.",
        )
    )

    assert result["status"] == "ok"
    assert result["snapshot"]["goal"]["status"] == "cancelled"
    assert store.get_current_snapshot("session-1") is None


def test_registry_injects_goal_event_callback() -> None:
    """SessionService can build goal tools that emit through the event bus."""
    from src.tools import build_registry

    events: list[tuple[str, dict]] = []
    registry = build_registry(
        session_id="session-xyz",
        event_callback=lambda event_type, data: events.append((event_type, data)),
    )
    tool = registry.get("start_research_goal")

    assert tool is not None
    assert getattr(tool, "_event_callback") is not None


def test_research_goal_skill_is_bundled() -> None:
    """The agent can load workflow guidance for self-managed goals."""
    content = SkillsLoader().get_content("research-goal")

    assert "start_research_goal" in content
    assert "add_goal_evidence" in content
