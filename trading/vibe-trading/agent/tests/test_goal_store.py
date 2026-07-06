"""Tests for the finance research goal store MVP."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.goal import (
    AuditRow,
    EvidenceInput,
    GoalStatus,
    GoalStore,
    RiskTier,
    StaleGoalError,
)


def _store(tmp_path: Path) -> GoalStore:
    return GoalStore(tmp_path / "goals.db")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_replace_goal_supersedes_current_goal(tmp_path: Path) -> None:
    store = _store(tmp_path)

    first = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum as a research-only thesis.",
        criteria=["Define thesis", "Check price action"],
    )
    second = store.replace_goal(
        session_id="session-1",
        objective="Evaluate BTC ETF flow divergence as a research-only thesis.",
        criteria=["Define thesis", "Check ETF flow"],
    )

    current = store.get_current_goal("session-1")
    first_fresh = store.get_goal(first.goal_id)

    assert current is not None
    assert current.goal_id == second.goal_id
    assert current.status is GoalStatus.ACTIVE
    assert first_fresh is not None
    assert first_fresh.status is GoalStatus.SUPERSEDED


def test_replace_goal_creates_initial_thesis_claim(tmp_path: Path) -> None:
    store = _store(tmp_path)

    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum as a research-only thesis.",
        criteria=["Define thesis", "Check price action"],
    )

    claims = store.list_claims(goal.goal_id)

    assert len(claims) == 1
    assert claims[0].claim_type == "thesis"
    assert claims[0].text == goal.objective
    assert claims[0].status == "active"


def test_update_goal_edits_current_objective_without_replacing_goal(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis"],
    )

    updated = store.update_goal(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        objective="Evaluate NVDA versus QQQ momentum.",
    )

    assert updated.goal_id == goal.goal_id
    assert updated.objective == "Evaluate NVDA versus QQQ momentum."
    current = store.get_current_goal("session-1")
    assert current is not None
    assert current.goal_id == goal.goal_id
    assert store.list_claims(goal.goal_id)[0].text == "Evaluate NVDA versus QQQ momentum."


def test_replace_goal_rejects_live_execution_objective(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="live trading"):
        store.replace_goal(
            session_id="session-1",
            objective="Place a live BTC order now.",
            criteria=["Execute order"],
        )


def test_replace_goal_rejects_live_execution_risk_tier(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="live trading"):
        store.replace_goal(
            session_id="session-1",
            objective="Evaluate BTC momentum as research only.",
            criteria=["Check price action"],
            risk_tier=RiskTier.LIVE_TRADING_OR_EXECUTION,
        )


def test_list_criteria_preserves_numeric_protocol_order(tmp_path: Path) -> None:
    store = _store(tmp_path)
    criteria = [f"Criterion {index}" for index in range(1, 13)]

    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum as a research-only thesis.",
        criteria=criteria,
    )

    assert [item.text for item in store.list_criteria(goal.goal_id)] == criteria


def test_blank_session_id_is_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="session_id"):
        store.replace_goal(
            session_id="   ",
            objective="Evaluate NVDA momentum.",
            criteria=["Check price action"],
        )


def test_replace_goal_rejects_non_positive_budgets(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="token_budget"):
        store.replace_goal(
            session_id="session-1",
            objective="Evaluate NVDA momentum.",
            criteria=["Check price action"],
            token_budget=0,
        )


def test_append_evidence_rejects_stale_expected_goal_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    old_goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    new_goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate TSLA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(new_goal.goal_id)[0]

    with pytest.raises(StaleGoalError):
        store.append_evidence(
            session_id="session-1",
            goal_id=new_goal.goal_id,
            expected_goal_id=old_goal.goal_id,
            evidence=EvidenceInput(
                criterion_id=criterion.criterion_id,
                text="TSLA outperformed QQQ over the sample window.",
                source_provider="yfinance",
                data_as_of="2026-05-23T16:00:00-04:00",
                tool_call_id="tool_123",
            ),
        )


def test_cross_connection_stale_goal_rejected(tmp_path: Path) -> None:
    db_path = tmp_path / "goals.db"
    first_store = GoalStore(db_path)
    second_store = GoalStore(db_path)
    old_goal = first_store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    second_store.replace_goal(
        session_id="session-1",
        objective="Evaluate TSLA momentum.",
        criteria=["Check price action"],
    )
    old_criterion = first_store.list_criteria(old_goal.goal_id)[0]

    with pytest.raises(StaleGoalError):
        first_store.append_evidence(
            session_id="session-1",
            goal_id=old_goal.goal_id,
            expected_goal_id=old_goal.goal_id,
            evidence=EvidenceInput(
                criterion_id=old_criterion.criterion_id,
                text="This should not write to a superseded goal.",
            ),
        )


def test_completion_requires_verified_evidence_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]

    with pytest.raises(ValueError, match="verified evidence"):
        store.update_status(
            session_id="session-1",
            goal_id=goal.goal_id,
            expected_goal_id=goal.goal_id,
            status=GoalStatus.COMPLETE,
            audit=[
                AuditRow(
                    criterion_id=criterion.criterion_id,
                    result="satisfied",
                    evidence_ids=[],
                    notes="Model says price action was checked.",
                )
            ],
        )


def test_completion_rejects_caveated_result_without_verified_evidence(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]

    with pytest.raises(ValueError, match="verified evidence"):
        store.update_status(
            session_id="session-1",
            goal_id=goal.goal_id,
            expected_goal_id=goal.goal_id,
            status=GoalStatus.COMPLETE,
            audit=[
                AuditRow(
                    criterion_id=criterion.criterion_id,
                    result="satisfied_with_caveat",
                    evidence_ids=[],
                    notes="Caveated but still needs evidence.",
                )
            ],
        )


def test_completion_rejects_not_applicable_without_acceptance_notes(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]

    with pytest.raises(ValueError, match="acceptance notes"):
        store.update_status(
            session_id="session-1",
            goal_id=goal.goal_id,
            expected_goal_id=goal.goal_id,
            status=GoalStatus.COMPLETE,
            audit=[
                AuditRow(
                    criterion_id=criterion.criterion_id,
                    result="not_applicable_user_accepted",
                    evidence_ids=[],
                    notes="",
                )
            ],
        )


def test_tool_call_id_alone_does_not_mark_evidence_verified(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]

    evidence = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Model says a tool was called, but no run/artifact exists.",
            tool_call_id="tool_123",
        ),
    )

    assert evidence.verification_status == "unverified"


def test_complete_goal_with_verified_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = _store(tmp_path)
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    artifact = tmp_path / "nvda_momentum.txt"
    artifact.write_text("NVDA outperformed QQQ over the last 5 sessions.", encoding="utf-8")
    evidence = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="NVDA outperformed QQQ over the last 5 sessions.",
            source_provider="yfinance",
            data_as_of="2026-05-23T16:00:00-04:00",
            artifact_path=str(artifact),
            artifact_hash=_sha256(artifact),
            symbol_universe=["NVDA"],
            benchmark=["QQQ"],
        ),
    )

    completed = store.update_status(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        status=GoalStatus.COMPLETE,
        audit=[
            AuditRow(
                criterion_id=criterion.criterion_id,
                result="satisfied",
                evidence_ids=[evidence.evidence_id],
                notes="Price action evidence is linked to a tool result.",
            )
        ],
        recap="Research-only evidence check completed.",
    )

    assert completed.status is GoalStatus.COMPLETE
    assert completed.recap == "Research-only evidence check completed."
    assert store.list_criteria(goal.goal_id)[0].status == "satisfied"


def test_completion_allows_mixed_verified_and_historical_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audit rows may cite old evidence as long as each criterion has verified evidence."""
    store = _store(tmp_path)
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    old_evidence = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Historical unverified note from an earlier model turn.",
        ),
    )
    artifact = tmp_path / "nvda_momentum.txt"
    artifact.write_text("Verified NVDA momentum artifact.", encoding="utf-8")
    verified_evidence = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Verified artifact evidence for the same criterion.",
            artifact_path=str(artifact),
            artifact_hash=_sha256(artifact),
        ),
    )

    completed = store.update_status(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        status=GoalStatus.COMPLETE,
        audit=[
            AuditRow(
                criterion_id=criterion.criterion_id,
                result="satisfied",
                evidence_ids=[old_evidence.evidence_id, verified_evidence.evidence_id],
                notes="Historical note plus current verified evidence.",
            )
        ],
    )

    assert old_evidence.verification_status == "unverified"
    assert verified_evidence.verification_status == "verified"
    assert completed.status is GoalStatus.COMPLETE


def test_artifact_evidence_requires_allowed_path_and_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _store(tmp_path)
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    artifact = tmp_path / "nvda_momentum.txt"
    artifact.write_text("NVDA outperformed QQQ.", encoding="utf-8")

    missing_hash = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Artifact without hash should not verify.",
            artifact_path=str(artifact),
        ),
    )
    traversal = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Traversal handle should not verify.",
            artifact_path="uploads/../api_server.py",
            artifact_hash="sha256:deadbeef",
        ),
    )

    assert missing_hash.verification_status == "unverified"
    assert traversal.verification_status == "unverified"


def test_delete_session_goals_removes_ledger(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Evidence to remove with the session.",
        ),
    )

    assert store.delete_session_goals("session-1") == 1
    assert store.get_current_snapshot("session-1") is None
    assert store.get_goal_snapshot(goal.goal_id) is None


def test_goal_snapshot_includes_claims_criteria_and_evidence(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    evidence = store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="NVDA outperformed QQQ over the last 5 sessions.",
            tool_call_id="tool_123",
            data_as_of="2026-05-23T16:00:00-04:00",
        ),
    )

    snapshot = store.get_current_snapshot("session-1")

    assert snapshot is not None
    assert snapshot["goal"]["goal_id"] == goal.goal_id
    assert snapshot["claims"][0]["claim_type"] == "thesis"
    assert snapshot["criteria"][0]["criterion_id"] == criterion.criterion_id
    assert snapshot["evidence"][0]["evidence_id"] == evidence.evidence_id
    assert snapshot["evidence_count"] == 1


def test_append_evidence_marks_linked_pending_criterion_covered(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]

    store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="NVDA outperformed QQQ over the last 5 sessions.",
        ),
    )

    assert store.list_criteria(goal.goal_id)[0].status == "covered"


def test_goal_snapshot_caps_evidence_but_reports_total_count(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    for index in range(55):
        store.append_evidence(
            session_id="session-1",
            goal_id=goal.goal_id,
            expected_goal_id=goal.goal_id,
            evidence=EvidenceInput(
                criterion_id=criterion.criterion_id,
                text=f"Evidence {index}",
            ),
        )

    snapshot = store.get_goal_snapshot(goal.goal_id)

    assert snapshot is not None
    assert snapshot["evidence_count"] == 55
    assert len(snapshot["evidence"]) == 50


def test_append_evidence_is_safe_from_parallel_cli_or_api_calls(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]

    def append_note(index: int) -> str:
        return store.append_evidence(
            session_id="session-1",
            goal_id=goal.goal_id,
            expected_goal_id=goal.goal_id,
            evidence=EvidenceInput(
                criterion_id=criterion.criterion_id,
                text=f"Parallel evidence note {index}",
                tool_call_id=f"tool_{index}",
            ),
        ).evidence_id

    with ThreadPoolExecutor(max_workers=8) as pool:
        evidence_ids = list(pool.map(append_note, range(20)))

    snapshot = store.get_goal_snapshot(goal.goal_id)
    assert snapshot is not None
    assert len(evidence_ids) == 20
    assert len(set(evidence_ids)) == 20
    assert len(snapshot["evidence"]) == 20


def test_account_usage_marks_goal_budget_limited(tmp_path: Path) -> None:
    store = _store(tmp_path)
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
        token_budget=100,
        turn_budget=3,
    )

    active = store.account_usage(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        token_delta=40,
        time_delta_seconds=10,
        turn_delta=1,
    )
    limited = store.account_usage(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        token_delta=60,
        time_delta_seconds=10,
        turn_delta=1,
    )

    assert active.status is GoalStatus.ACTIVE
    assert active.tokens_used == 40
    assert limited.status is GoalStatus.BUDGET_LIMITED
    assert limited.tokens_used == 100


def test_account_usage_is_serialized_across_connections(tmp_path: Path) -> None:
    db_path = tmp_path / "goals.db"
    first_store = GoalStore(db_path)
    second_store = GoalStore(db_path)
    goal = first_store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Check price action"],
    )

    def add_usage(index: int) -> None:
        store = first_store if index % 2 == 0 else second_store
        store.account_usage(
            session_id="session-1",
            goal_id=goal.goal_id,
            expected_goal_id=goal.goal_id,
            token_delta=1,
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(add_usage, range(40)))

    current = first_store.get_goal(goal.goal_id)
    assert current is not None
    assert current.tokens_used == 40
