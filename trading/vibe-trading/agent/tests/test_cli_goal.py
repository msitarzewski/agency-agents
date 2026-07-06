"""CLI tests for the finance research goal slash command."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.goal import GoalStore


def test_goal_command_is_registered() -> None:
    """The interactive slash router exposes /goal."""
    from cli.commands.slash_router import find_exact, match_commands

    cmd = find_exact("goal")

    assert cmd is not None
    assert cmd.handler_module == "cli.commands.goal"
    assert "goal" in [item.name for item in match_commands("/go")]


def test_goal_command_creates_goal(tmp_path: Path, monkeypatch) -> None:
    """A bare /goal <objective> starts a research goal for the current session."""
    from cli.commands import goal as goal_cmd

    store = GoalStore(tmp_path / "goals.db")
    monkeypatch.setattr(goal_cmd, "_goal_store", store)
    ctx = SimpleNamespace(session_id="session-1")

    rc = goal_cmd.run(
        ctx,
        "Evaluate",
        "NVDA",
        "momentum",
        "as",
        "a",
        "research-only",
        "thesis.",
    )

    current = store.get_current_snapshot("session-1")
    assert rc == 0
    assert current is not None
    assert current["goal"]["objective"] == "Evaluate NVDA momentum as a research-only thesis."
    assert len(current["criteria"]) >= 2


def test_goal_command_appends_evidence_by_criterion_index(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Manual CLI evidence can target criteria by 1-based index."""
    from cli.commands import goal as goal_cmd

    store = GoalStore(tmp_path / "goals.db")
    monkeypatch.setattr(goal_cmd, "_goal_store", store)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis", "Check price action"],
    )
    ctx = SimpleNamespace(session_id="session-1")

    rc = goal_cmd.run(
        ctx,
        "evidence",
        "2",
        "NVDA",
        "outperformed",
        "QQQ",
        "over",
        "the",
        "last",
        "5",
        "sessions.",
    )

    snapshot = store.get_goal_snapshot(goal.goal_id)
    assert rc == 0
    assert snapshot is not None
    assert snapshot["evidence"][0]["criterion_id"] == snapshot["criteria"][1]["criterion_id"]
    assert snapshot["evidence"][0]["text"] == "NVDA outperformed QQQ over the last 5 sessions."


def test_goal_command_rejects_live_trading_objective(tmp_path: Path, monkeypatch) -> None:
    """CLI /goal keeps the research-only boundary."""
    from cli.commands import goal as goal_cmd

    store = GoalStore(tmp_path / "goals.db")
    monkeypatch.setattr(goal_cmd, "_goal_store", store)
    ctx = SimpleNamespace(session_id="session-1")

    rc = goal_cmd.run(ctx, "buy", "1", "BTC", "now")

    assert rc == 1
    assert store.get_current_goal("session-1") is None


def test_goal_status_without_session_does_not_create_session(monkeypatch) -> None:
    """Read-only /goal status should not create a new session."""
    from cli.commands import goal as goal_cmd

    def fail_create(*args, **kwargs):  # noqa: ANN001
        raise AssertionError("status should not create a session")

    monkeypatch.delenv("VIBE_GOAL_SESSION_ID", raising=False)
    monkeypatch.setattr(goal_cmd, "_create_cli_session", fail_create)

    assert goal_cmd.run(SimpleNamespace(), "status") == 0


def test_goal_start_persists_session_id_on_plain_context(tmp_path: Path, monkeypatch) -> None:
    """A ctx without session_id still remembers the session after /goal start."""
    from cli.commands import goal as goal_cmd

    store = GoalStore(tmp_path / "goals.db")
    monkeypatch.setattr(goal_cmd, "_goal_store", store)
    monkeypatch.setattr(goal_cmd, "_create_cli_session", lambda ctx, title: setattr(ctx, "session_id", "session-1") or "session-1")
    ctx = SimpleNamespace()

    assert goal_cmd.run(ctx, "Evaluate", "NVDA", "momentum.") == 0
    assert ctx.session_id == "session-1"
    assert goal_cmd.run(ctx, "status") == 0


def test_goal_cancel_moves_goal_out_of_current_set(tmp_path: Path, monkeypatch) -> None:
    """CLI users can end an active goal without replacing it."""
    from cli.commands import goal as goal_cmd

    store = GoalStore(tmp_path / "goals.db")
    monkeypatch.setattr(goal_cmd, "_goal_store", store)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis"],
    )
    ctx = SimpleNamespace(session_id="session-1")

    rc = goal_cmd.run(ctx, "cancel", "No", "longer", "needed.")

    assert rc == 0
    assert store.get_current_snapshot("session-1") is None
    cancelled = store.get_goal(goal.goal_id)
    assert cancelled is not None
    assert cancelled.status.value == "cancelled"
    assert cancelled.recap == "No longer needed."
