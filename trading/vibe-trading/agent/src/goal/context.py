"""Context helpers for session-scoped research goals."""

from __future__ import annotations

from typing import Any

OPEN_CRITERION_STATUSES = {"", "pending", "open", "unsatisfied", "missing", "stale", "too_weak"}
CONTINUABLE_GOAL_STATUSES = {"active", "needs_refresh", "insufficient_evidence"}


DEFAULT_GOAL_CRITERIA = [
    "Define the research-only thesis and symbol universe",
    "Collect fresh market or benchmark evidence",
    "Record caveats, contradictions, and non-advice boundary",
]


def default_goal_criteria() -> list[str]:
    """Return the default research goal acceptance checklist."""
    return list(DEFAULT_GOAL_CRITERIA)


def format_goal_context(snapshot: dict[str, Any]) -> str:
    """Format a compact active-goal block for the agent prompt.

    Args:
        snapshot: Goal snapshot returned by GoalStore.

    Returns:
        XML-ish context block injected into the next model turn.
    """
    goal = snapshot["goal"]
    evidence = snapshot.get("evidence") or []
    lines = [
        "<current-research-goal>",
        f"goal_id: {goal['goal_id']}",
        f"expected_goal_id: {goal['goal_id']}",
        f"status: {goal['status']}",
        f"objective: {goal['objective']}",
        f"risk_tier: {goal.get('risk_tier', 'research_general')}",
        f"evidence_count: {snapshot.get('evidence_count', len(evidence))}",
        "criteria:",
    ]
    for index, criterion in enumerate(snapshot.get("criteria") or [], start=1):
        criterion_id = criterion["criterion_id"]
        count = sum(1 for item in evidence if item.get("criterion_id") == criterion_id)
        lines.append(
            f"- {index}. [{criterion.get('status', 'pending')}] "
            f"{criterion_id}: {criterion['text']} (evidence={count})"
        )
    lines.extend(
        [
            "instructions:",
            "- Continue this goal unless the user explicitly replaces or cancels it.",
            "- Use get_research_goal before mutating if you need the freshest snapshot.",
            "- Add evidence with add_goal_evidence after tool-backed or concrete research steps.",
            "- Do not treat a normal answer as finished while the goal status is still active.",
            "- If all criteria are covered, audit the ledger and use update_research_goal_status.",
            "- Complete or block the goal with update_research_goal_status only after an audit.",
            "</current-research-goal>",
        ]
    )
    return "\n".join(lines)


def criterion_is_covered(snapshot: dict[str, Any], criterion: dict[str, Any]) -> bool:
    """Return whether a criterion is already covered by status or evidence."""
    status = str(criterion.get("status") or "").lower()
    if status not in OPEN_CRITERION_STATUSES:
        return True
    criterion_id = criterion.get("criterion_id")
    return any(item.get("criterion_id") == criterion_id for item in snapshot.get("evidence") or [])


def goal_progress_tuple(snapshot: dict[str, Any]) -> tuple[int, int]:
    """Return comparable progress as ``(covered_criteria, evidence_count)``."""
    criteria = snapshot.get("criteria") or []
    covered = sum(1 for item in criteria if criterion_is_covered(snapshot, item))
    return covered, int(snapshot.get("evidence_count") or len(snapshot.get("evidence") or []))


def goal_needs_continuation(snapshot: dict[str, Any]) -> bool:
    """Return whether the runtime should keep working on this goal."""
    goal = snapshot.get("goal") or {}
    status = str(goal.get("status") or "").lower()
    if status not in CONTINUABLE_GOAL_STATUSES:
        return False
    criteria = snapshot.get("criteria") or []
    if not criteria:
        return True
    return True


def format_goal_continuation_prompt(snapshot: dict[str, Any], previous_answer: str = "") -> str:
    """Build the runtime-driven prompt for continuing an incomplete goal."""
    goal = snapshot["goal"]
    claims = snapshot.get("claims") or []
    evidence = snapshot.get("evidence") or []
    open_items = [
        f"- {item['criterion_id']}: {item['text']}"
        for item in snapshot.get("criteria") or []
        if item.get("required", True) and not criterion_is_covered(snapshot, item)
    ]
    if not open_items:
        open_items = ["- All criteria appear covered; audit evidence and update goal status if completion is justified."]

    prior = previous_answer.strip()
    prior_block = f"\nPrevious assistant text:\n{prior[:1200]}\n" if prior else ""
    criteria_lines = []
    for item in snapshot.get("criteria") or []:
        count = sum(1 for ev in evidence if ev.get("criterion_id") == item.get("criterion_id"))
        coverage = "covered" if criterion_is_covered(snapshot, item) else "open"
        criteria_lines.append(
            f"- {item['criterion_id']}: {item['text']} | status={item.get('status', 'pending')} "
            f"| coverage={coverage} | evidence={count}"
        )
    claim_lines = [
        f"- {item.get('claim_id')}: {item.get('claim_type')} | {item.get('status')} | {item.get('text')}"
        for item in claims[:8]
    ]
    evidence_lines = []
    for item in evidence[-6:]:
        evidence_lines.append(
            "- "
            f"{item.get('evidence_id')}: criterion={item.get('criterion_id') or 'none'} "
            f"| provider={item.get('source_provider') or item.get('source_type') or 'unknown'} "
            f"| as_of={item.get('data_as_of') or 'unknown'} "
            f"| verification={item.get('verification_status') or 'unknown'} "
            f"| text={str(item.get('text') or '')[:240]}"
        )
    covered, total_evidence = goal_progress_tuple(snapshot)
    return "\n".join(
        [
            "<goal-continuation>",
            f"goal_id: {goal['goal_id']}",
            f"expected_goal_id: {goal['goal_id']}",
            f"status: {goal.get('status', 'active')}",
            f"objective: {goal['objective']}",
            f"snapshot_progress: covered_criteria={covered}/{len(snapshot.get('criteria') or [])}; evidence_count={total_evidence}",
            "claims_snapshot:",
            *(claim_lines or ["- none"]),
            "criteria_snapshot:",
            *(criteria_lines or ["- none"]),
            "recent_evidence_snapshot:",
            *(evidence_lines or ["- none"]),
            "open_required_items:",
            *open_items,
            prior_block.rstrip(),
            "Rules:",
            "- Drive the next step from the snapshot above, not from the objective alone.",
            "- Prefer the highest-priority open criterion with zero evidence.",
            "- Use available tools when fresh or artifact-backed evidence is needed; reuse existing artifacts only when they answer the open criterion.",
            "- After concrete research progress, call add_goal_evidence and link the exact criterion_id.",
            "- If the ledger is sufficient, call update_research_goal_status with a completion audit.",
            "- If progress is impossible, set a blocker/insufficient-evidence status instead of stopping silently.",
            "</goal-continuation>",
        ]
    )


def get_current_goal_context(session_id: str) -> tuple[str, str | None]:
    """Return active-goal context and goal id for a session.

    Args:
        session_id: Current chat/session id.

    Returns:
        Tuple of formatted context block and active goal id. Both are empty
        when no current goal exists.
    """
    if not session_id.strip():
        return "", None
    from src.goal.store import GoalStore

    snapshot = GoalStore().get_current_snapshot(session_id)
    if snapshot is None:
        return "", None
    return format_goal_context(snapshot), str(snapshot["goal"]["goal_id"])
