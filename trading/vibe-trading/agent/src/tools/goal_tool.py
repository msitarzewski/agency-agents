"""Local agent tools for finance research goals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from src.agent.tools import BaseTool
from src.goal import AuditRow, EvidenceInput, GoalStatus, GoalStore, RiskTier, StaleGoalError
from src.goal.context import default_goal_criteria
from src.tools.path_utils import safe_run_dir


def _json_error(error: str, *, error_type: str = "validation") -> str:
    """Return a standard JSON error envelope."""
    return json.dumps(
        {"status": "error", "error_type": error_type, "error": error},
        ensure_ascii=False,
    )


def _coerce_string_list(value: Any) -> list[str]:
    """Coerce a JSON-schema array-or-string value to a string list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _coerce_audit_rows(value: Any) -> list[AuditRow]:
    """Coerce model/API-style audit rows into dataclasses."""
    if value in (None, ""):
        return []
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError("audit must be a list")

    rows: list[AuditRow] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("audit rows must be objects")
        criterion_id = str(item.get("criterion_id") or "").strip()
        result = str(item.get("result") or "").strip()
        if not criterion_id or not result:
            raise ValueError("audit rows require criterion_id and result")
        rows.append(
            AuditRow(
                criterion_id=criterion_id,
                result=result,
                evidence_ids=_coerce_string_list(item.get("evidence_ids")),
                notes=str(item.get("notes") or ""),
            )
        )
    return rows


def _sha256_file(path: Path) -> str:
    """Return the sha256 digest for a local artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _trace_fields_from_runtime(kwargs: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Resolve host-injected run metadata into ledger-verifiable evidence fields."""
    run_id = str(kwargs.get("run_id") or "").strip() or None
    artifact_path = str(kwargs.get("artifact_path") or "").strip() or None
    artifact_hash = str(kwargs.get("artifact_hash") or "").strip() or None

    run_dir_raw = str(kwargs.get("run_dir") or "").strip()
    run_dir: Path | None = None
    if run_dir_raw:
        run_dir = safe_run_dir(run_dir_raw)
        if run_id is None:
            run_id = run_dir.name

    artifact_candidate: Path | None = None
    if artifact_path:
        raw_path = Path(artifact_path).expanduser()
        if run_dir is not None and not raw_path.is_absolute():
            resolved = (run_dir / raw_path).resolve()
            try:
                resolved.relative_to(run_dir)
            except ValueError as exc:
                raise ValueError("artifact_path escapes the current run_dir") from exc
            artifact_candidate = resolved
            artifact_path = str(resolved)
        elif raw_path.is_absolute():
            artifact_candidate = raw_path.resolve()

    if artifact_candidate is not None and artifact_candidate.is_file() and not artifact_hash:
        artifact_hash = _sha256_file(artifact_candidate)

    return run_id, artifact_path, artifact_hash


class _GoalToolBase(BaseTool):
    """Shared helpers for local goal tools."""

    repeatable = True

    def __init__(
        self,
        *,
        default_session_id: str | None = None,
        store: GoalStore | None = None,
        event_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        """Initialize a local goal tool.

        Args:
            default_session_id: Session id injected by the host runtime.
            store: Optional store override for tests.
            event_callback: Optional host callback for live UI updates.
        """
        self._default_session_id = default_session_id
        self._store = store or GoalStore()
        self._event_callback = event_callback

    def _session_id(self, kwargs: dict[str, Any]) -> str | None:
        value = str(kwargs.get("session_id") or self._default_session_id or "").strip()
        return value or None

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Best-effort host event emission for goal mutations."""
        if self._event_callback is None:
            return
        try:
            self._event_callback(event_type, data)
        except Exception:
            return


class StartResearchGoalTool(_GoalToolBase):
    """Start or replace the current research-only goal."""

    name = "start_research_goal"
    description = (
        "Start or replace the current finance research goal for this session. "
        "Use for long-running research tasks, multi-step market analysis, or "
        "evidence-driven conclusions. Research-only; live trading objectives are rejected."
    )
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session id. Omit when the host runtime injected the current session.",
            },
            "objective": {
                "type": "string",
                "description": "Research-only goal objective.",
            },
            "criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional acceptance criteria. Defaults to the finance research checklist.",
            },
            "risk_tier": {
                "type": "string",
                "enum": [
                    "research_general",
                    "market_specific_short_term",
                    "personalized_advice_or_position_sizing",
                ],
                "description": "Research risk tier. Live trading/execution is not supported.",
            },
            "token_budget": {"type": "integer", "description": "Optional positive token budget."},
            "turn_budget": {"type": "integer", "description": "Optional positive turn budget."},
            "time_budget_seconds": {"type": "integer", "description": "Optional positive wall-clock budget."},
        },
        "required": ["objective"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Start a research goal.

        Args:
            **kwargs: Tool arguments from the model.

        Returns:
            JSON envelope with the goal snapshot or an error.
        """
        session_id = self._session_id(kwargs)
        if not session_id:
            return _json_error("session_id is required")

        try:
            criteria = _coerce_string_list(kwargs.get("criteria")) or default_goal_criteria()
            goal = self._store.replace_goal(
                session_id=session_id,
                objective=str(kwargs.get("objective", "")),
                criteria=criteria,
                source="agent_tool",
                protocol="thesis_review",
                risk_tier=RiskTier(str(kwargs.get("risk_tier") or RiskTier.RESEARCH_GENERAL.value)),
                token_budget=kwargs.get("token_budget"),
                turn_budget=kwargs.get("turn_budget"),
                time_budget_seconds=kwargs.get("time_budget_seconds"),
            )
            snapshot = self._store.get_goal_snapshot(goal.goal_id)
            if snapshot is not None:
                self._emit("goal.created", {"goal": snapshot["goal"]})
            return json.dumps({"status": "ok", "snapshot": snapshot}, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            return _json_error(str(exc))


class UpdateResearchGoalStatusTool(_GoalToolBase):
    """Move the current research goal to another lifecycle status."""

    name = "update_research_goal_status"
    description = (
        "Update the current finance research goal status. Use this to complete, "
        "cancel, block, pause, or mark a goal as needing more evidence after an audit. "
        "Completion requires an audit row for every required criterion with verified evidence."
    )
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session id. Omit when the host runtime injected the current session.",
            },
            "goal_id": {"type": "string", "description": "Optional goal id. Defaults to the current goal."},
            "expected_goal_id": {
                "type": "string",
                "description": "Optional stale-write guard. Defaults to goal_id.",
            },
            "status": {
                "type": "string",
                "enum": [status.value for status in GoalStatus],
                "description": "Next lifecycle status.",
            },
            "audit": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "criterion_id": {"type": "string"},
                        "result": {
                            "type": "string",
                            "enum": [
                                "satisfied",
                                "satisfied_with_caveat",
                                "not_applicable_user_accepted",
                                "unsatisfied",
                            ],
                        },
                        "evidence_ids": {"type": "array", "items": {"type": "string"}},
                        "notes": {"type": "string"},
                    },
                    "required": ["criterion_id", "result"],
                },
                "description": "Criterion audit rows, required when status is complete.",
            },
            "recap": {"type": "string", "description": "Optional concise status recap."},
        },
        "required": ["status"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Update the current research goal status.

        Args:
            **kwargs: Tool arguments from the model.

        Returns:
            JSON envelope with the updated goal snapshot or an error.
        """
        session_id = self._session_id(kwargs)
        if not session_id:
            return _json_error("session_id is required")
        try:
            snapshot = self._store.get_current_snapshot(session_id)
            goal_id = str(kwargs.get("goal_id") or "").strip()
            if not goal_id:
                if snapshot is None:
                    return _json_error("no current goal for this session", error_type="not_found")
                goal_id = str(snapshot["goal"]["goal_id"])
            expected_goal_id = str(kwargs.get("expected_goal_id") or goal_id).strip()
            status = GoalStatus(str(kwargs.get("status") or "").strip())
            self._store.update_status(
                session_id=session_id,
                goal_id=goal_id,
                expected_goal_id=expected_goal_id,
                status=status,
                audit=_coerce_audit_rows(kwargs.get("audit")),
                recap=str(kwargs.get("recap") or "").strip() or None,
            )
            updated = self._store.get_goal_snapshot(goal_id)
            if updated is not None:
                self._emit("goal.updated", {"goal": updated["goal"], "snapshot": updated})
            return json.dumps({"status": "ok", "snapshot": updated}, ensure_ascii=False)
        except StaleGoalError as exc:
            return _json_error(str(exc), error_type="stale_goal")
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return _json_error(str(exc))


class GetResearchGoalTool(_GoalToolBase):
    """Read the current research goal snapshot."""

    name = "get_research_goal"
    description = "Read the current finance research goal, criteria, claims, and latest evidence."
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session id. Omit when the host runtime injected the current session.",
            },
        },
        "required": [],
    }

    def execute(self, **kwargs: Any) -> str:
        """Return the current goal snapshot.

        Args:
            **kwargs: Optional session_id.

        Returns:
            JSON envelope with the current goal snapshot or a not_found error.
        """
        session_id = self._session_id(kwargs)
        if not session_id:
            return _json_error("session_id is required")
        try:
            snapshot = self._store.get_current_snapshot(session_id)
        except ValueError as exc:
            return _json_error(str(exc))
        if snapshot is None:
            return _json_error("no current goal for this session", error_type="not_found")
        return json.dumps({"status": "ok", "snapshot": snapshot}, ensure_ascii=False)


class AddGoalEvidenceTool(_GoalToolBase):
    """Attach evidence to the current research goal."""

    name = "add_goal_evidence"
    description = (
        "Attach a concise evidence note, artifact reference, or tool result to the current "
        "research goal. Prefer linking evidence to a criterion by criterion_id or criterion_index."
    )
    is_readonly = False
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session id. Omit when the host runtime injected the current session.",
            },
            "goal_id": {"type": "string", "description": "Optional goal id. Defaults to the current goal."},
            "expected_goal_id": {
                "type": "string",
                "description": "Optional stale-write guard. Defaults to goal_id.",
            },
            "criterion_id": {"type": "string", "description": "Criterion id to satisfy."},
            "criterion_index": {
                "type": "integer",
                "description": "1-based criterion index, used when criterion_id is not known.",
            },
            "claim_id": {"type": "string", "description": "Optional claim id."},
            "text": {"type": "string", "description": "Evidence note or artifact summary."},
            "run_id": {"type": "string", "description": "Optional local run id that produced this evidence."},
            "run_dir": {
                "type": "string",
                "description": "Optional host-injected current run directory. Omit unless provided by the runtime.",
            },
            "tool_call_id": {"type": "string", "description": "Optional tool call id for traceability."},
            "source_provider": {"type": "string", "description": "Data or tool provider."},
            "source_type": {"type": "string", "description": "Source type, e.g. backtest, market_data, manual_note."},
            "source_uri": {"type": "string", "description": "Optional source URI."},
            "symbol_universe": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Symbols covered by the evidence.",
            },
            "benchmark": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Benchmarks used by the evidence.",
            },
            "timeframe": {"type": "string", "description": "Evidence timeframe."},
            "method": {"type": "string", "description": "Method used to produce the evidence."},
            "artifact_path": {"type": "string", "description": "Optional local artifact path."},
            "artifact_hash": {"type": "string", "description": "Optional sha256 for artifact_path."},
            "data_as_of": {"type": "string", "description": "Timestamp/date the data is current as of."},
            "confidence": {"type": "string", "description": "Optional confidence label."},
            "caveat": {"type": "string", "description": "Optional caveat."},
        },
        "required": ["text"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Append evidence to a goal.

        Args:
            **kwargs: Tool arguments from the model.

        Returns:
            JSON envelope with the evidence row and updated snapshot.
        """
        session_id = self._session_id(kwargs)
        if not session_id:
            return _json_error("session_id is required")
        try:
            snapshot = self._store.get_current_snapshot(session_id)
            if snapshot is None:
                return _json_error("no current goal for this session", error_type="not_found")

            goal_id = str(kwargs.get("goal_id") or snapshot["goal"]["goal_id"])
            expected_goal_id = str(kwargs.get("expected_goal_id") or goal_id)
            criterion_id = str(kwargs.get("criterion_id") or "").strip() or None
            if criterion_id is None and kwargs.get("criterion_index") is not None:
                index = int(kwargs["criterion_index"])
                criteria = snapshot.get("criteria") or []
                if index < 1 or index > len(criteria):
                    return _json_error(f"criterion_index out of range: {index}")
                criterion_id = str(criteria[index - 1]["criterion_id"])
            run_id, artifact_path, artifact_hash = _trace_fields_from_runtime(kwargs)

            record = self._store.append_evidence(
                session_id=session_id,
                goal_id=goal_id,
                expected_goal_id=expected_goal_id,
                evidence=EvidenceInput(
                    criterion_id=criterion_id,
                    claim_id=str(kwargs.get("claim_id") or "").strip() or None,
                    text=str(kwargs.get("text", "")),
                    run_id=run_id,
                    tool_call_id=str(kwargs.get("tool_call_id") or "").strip() or None,
                    source_provider=str(kwargs.get("source_provider") or "agent_tool"),
                    source_type=str(kwargs.get("source_type") or "tool_note"),
                    source_uri=str(kwargs.get("source_uri") or "").strip() or None,
                    symbol_universe=_coerce_string_list(kwargs.get("symbol_universe")),
                    benchmark=_coerce_string_list(kwargs.get("benchmark")),
                    timeframe=str(kwargs.get("timeframe") or "").strip() or None,
                    method=str(kwargs.get("method") or "").strip() or None,
                    artifact_path=artifact_path,
                    artifact_hash=artifact_hash,
                    data_as_of=str(kwargs.get("data_as_of") or "").strip() or None,
                    confidence=str(kwargs.get("confidence") or "").strip() or None,
                    caveat=str(kwargs.get("caveat") or "").strip() or None,
                ),
            )
            updated = self._store.get_goal_snapshot(goal_id)
            self._emit(
                "goal.evidence",
                {"evidence": record.__dict__, "goal_id": goal_id},
            )
            return json.dumps(
                {"status": "ok", "evidence": record.__dict__, "snapshot": updated},
                ensure_ascii=False,
            )
        except StaleGoalError as exc:
            return _json_error(str(exc), error_type="stale_goal")
        except (TypeError, ValueError) as exc:
            return _json_error(str(exc))
