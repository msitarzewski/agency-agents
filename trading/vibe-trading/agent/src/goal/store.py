"""SQLite-backed store for finance research goals."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar

from src.goal.models import (
    AuditRow,
    EvidenceInput,
    EvidenceRecord,
    GoalClaim,
    GoalCriterion,
    GoalRecord,
    GoalStatus,
    RiskTier,
    StaleGoalError,
)
from src.goal.policy import normalize_required_text, reject_live_execution_objective
from src.tools.path_utils import safe_document_path, safe_run_id

_DEFAULT_DB_PATH = Path.home() / ".vibe-trading" / "sessions.db"
_DB_PATH_ENV = "VIBE_TRADING_GOAL_DB_PATH"

_CURRENT_STATUSES = {
    GoalStatus.ACTIVE,
    GoalStatus.PAUSED,
    GoalStatus.WAITING_USER,
    GoalStatus.NEEDS_REFRESH,
    GoalStatus.INSUFFICIENT_EVIDENCE,
    GoalStatus.COMPLIANCE_BLOCKED,
    GoalStatus.BUDGET_LIMITED,
}

_COMPLETION_RESULTS = {
    "satisfied",
    "satisfied_with_caveat",
    "not_applicable_user_accepted",
}


def _now_iso() -> str:
    return datetime.now().isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_loads(value: str | None, default: object) -> object:
    if not value:
        return default
    return json.loads(value)


def _default_db_path() -> Path:
    """Return the configured goal ledger database path."""
    raw_path = os.getenv(_DB_PATH_ENV, "").strip()
    if raw_path:
        return Path(raw_path).expanduser()
    return _DEFAULT_DB_PATH


def _to_json_dict(value: object) -> dict:
    data = asdict(value)
    for key, item in list(data.items()):
        if isinstance(item, Enum):
            data[key] = item.value
    return data


F = TypeVar("F", bound=Callable)


def _synchronized(method: F) -> F:
    """Serialize access to the shared SQLite connection."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


class GoalStore:
    """SQLite-backed store for finance research goals."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize the goal store.

        Args:
            db_path: SQLite database path. When omitted,
                ``VIBE_TRADING_GOAL_DB_PATH`` can override the default.
        """
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        """Create goal tables and indexes if they do not exist."""
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    ui_summary TEXT NOT NULL,
                    source TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    risk_tier TEXT NOT NULL,
                    token_budget INTEGER,
                    tokens_used INTEGER NOT NULL DEFAULT 0,
                    turn_budget INTEGER,
                    turns_used INTEGER NOT NULL DEFAULT 0,
                    time_budget_seconds INTEGER,
                    time_used_seconds INTEGER NOT NULL DEFAULT 0,
                    budget_wrapup_sent INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    recap TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_goals_one_current_per_session
                    ON goals(session_id)
                    WHERE status IN (
                        'active',
                        'paused',
                        'waiting_user',
                        'needs_refresh',
                        'insufficient_evidence',
                        'compliance_blocked',
                        'budget_limited'
                    );

                CREATE TABLE IF NOT EXISTS goal_claims (
                    claim_id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
                );

                CREATE INDEX IF NOT EXISTS idx_goal_claims_goal
                    ON goal_claims(goal_id, status);

                CREATE TABLE IF NOT EXISTS goal_criteria (
                    criterion_id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    required INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'pending',
                    freshness_requirement TEXT,
                    protocol_step TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
                );

                CREATE INDEX IF NOT EXISTS idx_goal_criteria_goal
                    ON goal_criteria(goal_id, status);

                CREATE TABLE IF NOT EXISTS goal_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    criterion_id TEXT,
                    claim_id TEXT,
                    evidence_type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tool_call_id TEXT,
                    run_id TEXT,
                    source_provider TEXT,
                    source_type TEXT,
                    source_uri TEXT,
                    symbol_universe_json TEXT NOT NULL DEFAULT '[]',
                    benchmark_json TEXT NOT NULL DEFAULT '[]',
                    timeframe TEXT,
                    method TEXT,
                    assumptions_json TEXT NOT NULL DEFAULT '{}',
                    artifact_path TEXT,
                    artifact_hash TEXT,
                    retrieved_at TEXT NOT NULL,
                    data_as_of TEXT,
                    freshness_status TEXT NOT NULL DEFAULT 'unknown',
                    verification_status TEXT NOT NULL DEFAULT 'unverified',
                    confidence TEXT,
                    caveat TEXT,
                    contradicts_claim_ids_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
                );

                CREATE INDEX IF NOT EXISTS idx_goal_evidence_goal
                    ON goal_evidence(goal_id, created_at);

                CREATE TABLE IF NOT EXISTS goal_audits (
                    audit_id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    result TEXT NOT NULL,
                    rows_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
                );
                """
            )
            if self._conn.execute("PRAGMA user_version").fetchone()[0] < 1:
                self._conn.execute("PRAGMA user_version=1")
            self._conn.commit()

    @contextmanager
    def _write_transaction(self):
        """Open an immediate write transaction for cross-connection safety."""
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()

    @_synchronized
    def replace_goal(
        self,
        *,
        session_id: str,
        objective: str,
        criteria: list[str],
        ui_summary: str = "",
        source: str = "api",
        protocol: str = "thesis_review",
        risk_tier: RiskTier = RiskTier.RESEARCH_GENERAL,
        token_budget: int | None = None,
        turn_budget: int | None = None,
        time_budget_seconds: int | None = None,
    ) -> GoalRecord:
        """Supersede the current goal and create a new active goal.

        Args:
            session_id: Owning session id.
            objective: Research objective.
            criteria: Required criteria generated by the finance protocol.
            ui_summary: Optional compact summary.
            source: Source of goal creation.
            protocol: Finance research protocol name.
            risk_tier: Risk classification.
            token_budget: Optional token budget.
            turn_budget: Optional turn budget.
            time_budget_seconds: Optional wall-clock budget.

        Returns:
            The newly active goal.

        Raises:
            ValueError: If objective or criteria are empty.
        """
        session_id = normalize_required_text(session_id, "session_id")
        objective = normalize_required_text(objective, "goal objective")
        reject_live_execution_objective(objective)
        if risk_tier is RiskTier.LIVE_TRADING_OR_EXECUTION:
            raise ValueError("live trading or execution goals are not supported")
        cleaned_criteria = [item.strip() for item in criteria if item.strip()]
        if not cleaned_criteria:
            raise ValueError("at least one goal criterion is required")
        for criterion in cleaned_criteria:
            reject_live_execution_objective(criterion)
        budgets = {
            "token_budget": token_budget,
            "turn_budget": turn_budget,
            "time_budget_seconds": time_budget_seconds,
        }
        for name, value in budgets.items():
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")

        now = _now_iso()
        goal_id = _id("goal")
        summary = ui_summary.strip() or objective[:80]
        current_values = [status.value for status in _CURRENT_STATUSES]
        placeholders = ",".join("?" for _ in current_values)

        with self._write_transaction():
            self._conn.execute(
                f"""
                UPDATE goals
                SET status = ?, updated_at = ?, completed_at = COALESCE(completed_at, ?)
                WHERE session_id = ? AND status IN ({placeholders})
                """,
                [GoalStatus.SUPERSEDED.value, now, now, session_id, *current_values],
            )
            self._conn.execute(
                """
                INSERT INTO goals (
                    goal_id, session_id, status, objective, ui_summary, source,
                    protocol, risk_tier, token_budget, turn_budget,
                    time_budget_seconds, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal_id,
                    session_id,
                    GoalStatus.ACTIVE.value,
                    objective,
                    summary,
                    source,
                    protocol,
                    risk_tier.value,
                    token_budget,
                    turn_budget,
                    time_budget_seconds,
                    now,
                    now,
                ),
            )
            self._conn.execute(
                """
                INSERT INTO goal_claims (
                    claim_id, goal_id, session_id, claim_type, text,
                    status, created_at, updated_at
                )
                VALUES (?, ?, ?, 'thesis', ?, 'active', ?, ?)
                """,
                (_id("claim"), goal_id, session_id, objective, now, now),
            )
            for index, text in enumerate(cleaned_criteria):
                self._conn.execute(
                    """
                    INSERT INTO goal_criteria (
                        criterion_id, goal_id, session_id, text, required,
                        status, protocol_step, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, 1, 'pending', ?, ?, ?)
                    """,
                    (
                        _id("crit"),
                        goal_id,
                        session_id,
                        text,
                        f"step_{index + 1}",
                        now,
                        now,
                    ),
                )

        goal = self.get_goal(goal_id)
        if goal is None:
            raise RuntimeError("created goal could not be reloaded")
        return goal

    @_synchronized
    def update_goal(
        self,
        *,
        session_id: str,
        goal_id: str,
        expected_goal_id: str,
        objective: str | None = None,
        ui_summary: str | None = None,
    ) -> GoalRecord:
        """Edit mutable goal metadata without superseding the active goal.

        Args:
            session_id: Owning session id.
            goal_id: Goal being mutated.
            expected_goal_id: Stale-write guard captured by the caller.
            objective: Optional replacement research objective.
            ui_summary: Optional compact display summary.

        Returns:
            Updated goal record.

        Raises:
            StaleGoalError: If the goal is stale or not current.
            ValueError: If the new objective is empty or unsafe.
        """
        with self._write_transaction():
            goal = self._require_mutable_goal(session_id, goal_id, expected_goal_id)
            session_id = goal.session_id
            goal_id = goal.goal_id
            next_objective = goal.objective
            if objective is not None:
                next_objective = normalize_required_text(objective, "goal objective")
                reject_live_execution_objective(next_objective)
            next_summary = goal.ui_summary
            if ui_summary is not None:
                next_summary = ui_summary.strip() or next_objective[:80]
            elif objective is not None and goal.ui_summary == goal.objective[:80]:
                next_summary = next_objective[:80]
            now = _now_iso()
            self._conn.execute(
                """
                UPDATE goals
                SET objective = ?, ui_summary = ?, updated_at = ?
                WHERE goal_id = ? AND session_id = ?
                """,
                (next_objective, next_summary, now, goal_id, session_id),
            )
            if objective is not None:
                self._conn.execute(
                    """
                    UPDATE goal_claims
                    SET text = ?, updated_at = ?
                    WHERE goal_id = ? AND session_id = ?
                        AND claim_type = 'thesis'
                        AND status = 'active'
                    """,
                    (next_objective, now, goal_id, session_id),
                )

        updated = self.get_goal(goal_id)
        if updated is None:
            raise RuntimeError("updated goal could not be reloaded")
        return updated

    @_synchronized
    def get_goal(self, goal_id: str) -> GoalRecord | None:
        """Return a goal by id."""
        row = self._conn.execute(
            "SELECT * FROM goals WHERE goal_id = ?",
            (normalize_required_text(goal_id, "goal_id"),),
        ).fetchone()
        return self._goal_from_row(row) if row else None

    @_synchronized
    def get_current_goal(self, session_id: str) -> GoalRecord | None:
        """Return the current goal for a session."""
        current_values = [status.value for status in _CURRENT_STATUSES]
        session_id = normalize_required_text(session_id, "session_id")
        placeholders = ",".join("?" for _ in current_values)
        row = self._conn.execute(
            f"""
            SELECT * FROM goals
            WHERE session_id = ? AND status IN ({placeholders})
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [session_id, *current_values],
        ).fetchone()
        return self._goal_from_row(row) if row else None

    @_synchronized
    def list_criteria(self, goal_id: str) -> list[GoalCriterion]:
        """Return criteria for a goal."""
        rows = self._conn.execute(
            """
            SELECT * FROM goal_criteria
            WHERE goal_id = ?
            ORDER BY
                CASE
                    WHEN protocol_step GLOB 'step_[0-9]*' THEN CAST(substr(protocol_step, 6) AS INTEGER)
                    ELSE 2147483647
                END,
                created_at,
                criterion_id
            """,
            (normalize_required_text(goal_id, "goal_id"),),
        ).fetchall()
        return [self._criterion_from_row(row) for row in rows]

    @_synchronized
    def list_claims(self, goal_id: str) -> list[GoalClaim]:
        """Return claims for a goal."""
        rows = self._conn.execute(
            """
            SELECT * FROM goal_claims
            WHERE goal_id = ?
            ORDER BY created_at, claim_id
            """,
            (normalize_required_text(goal_id, "goal_id"),),
        ).fetchall()
        return [self._claim_from_row(row) for row in rows]

    @_synchronized
    def list_evidence(self, goal_id: str, limit: int | None = None) -> list[EvidenceRecord]:
        """Return evidence rows for a goal."""
        goal_id = normalize_required_text(goal_id, "goal_id")
        if limit is not None and limit <= 0:
            raise ValueError("evidence limit must be positive")
        if limit is not None:
            rows = self._conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM goal_evidence
                    WHERE goal_id = ?
                    ORDER BY created_at DESC, evidence_id DESC
                    LIMIT ?
                )
                ORDER BY created_at, evidence_id
                """,
                (goal_id, limit),
            ).fetchall()
            return [self._evidence_from_row(row) for row in rows]
        rows = self._conn.execute(
            """
            SELECT * FROM goal_evidence
            WHERE goal_id = ?
            ORDER BY created_at, evidence_id
            """,
            (goal_id,),
        ).fetchall()
        return [self._evidence_from_row(row) for row in rows]

    @_synchronized
    def count_evidence(self, goal_id: str) -> int:
        """Return the total evidence row count for a goal."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM goal_evidence WHERE goal_id = ?",
            (normalize_required_text(goal_id, "goal_id"),),
        ).fetchone()
        return int(row[0]) if row else 0

    @_synchronized
    def delete_session_goals(self, session_id: str) -> int:
        """Delete all goal ledger rows for a session.

        Args:
            session_id: Session whose goal ledger should be removed.

        Returns:
            Number of goal rows deleted.
        """
        session_id = normalize_required_text(session_id, "session_id")
        with self._write_transaction():
            row = self._conn.execute(
                "SELECT COUNT(*) FROM goals WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            count = int(row[0]) if row else 0
            for table in (
                "goal_audits",
                "goal_evidence",
                "goal_criteria",
                "goal_claims",
                "goals",
            ):
                self._conn.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))
        return count

    @_synchronized
    def get_current_snapshot(self, session_id: str) -> dict | None:
        """Return the current goal plus ledger rows for a session."""
        goal = self.get_current_goal(session_id)
        if goal is None:
            return None
        return self.get_goal_snapshot(goal.goal_id)

    @_synchronized
    def get_goal_snapshot(self, goal_id: str, evidence_limit: int | None = 50) -> dict | None:
        """Return a JSON-safe goal snapshot."""
        goal = self.get_goal(goal_id)
        if goal is None:
            return None
        evidence = self.list_evidence(goal.goal_id, limit=evidence_limit)
        return {
            "goal": _to_json_dict(goal),
            "claims": [_to_json_dict(item) for item in self.list_claims(goal.goal_id)],
            "criteria": [_to_json_dict(item) for item in self.list_criteria(goal.goal_id)],
            "evidence": [_to_json_dict(item) for item in evidence],
            "evidence_count": self.count_evidence(goal.goal_id),
        }

    @_synchronized
    def append_evidence(
        self,
        *,
        session_id: str,
        goal_id: str,
        expected_goal_id: str,
        evidence: EvidenceInput,
    ) -> EvidenceRecord:
        """Append traceable evidence after stale-goal validation.

        Args:
            session_id: Owning session id.
            goal_id: Goal being mutated.
            expected_goal_id: Goal id captured at the start of the agent turn.
            evidence: Evidence payload.

        Returns:
            Persisted evidence record.

        Raises:
            StaleGoalError: If the expected goal id does not match or goal is not current.
            ValueError: If evidence text is empty or references an unknown criterion.
        """
        evidence_id = _id("ev")
        with self._write_transaction():
            goal = self._require_mutable_goal(session_id, goal_id, expected_goal_id)
            session_id = goal.session_id
            goal_id = goal.goal_id
            text = evidence.text.strip()
            if not text:
                raise ValueError("evidence text cannot be empty")
            if evidence.criterion_id is not None:
                self._require_criterion(goal.goal_id, evidence.criterion_id)
            if evidence.claim_id is not None:
                self._require_claim(goal.goal_id, evidence.claim_id)

            now = _now_iso()
            freshness_status = "fresh" if evidence.data_as_of else "unknown"
            verification_status = self._verification_status(evidence)
            self._conn.execute(
                """
                INSERT INTO goal_evidence (
                    evidence_id, goal_id, session_id, criterion_id, claim_id,
                    evidence_type, text, tool_call_id, run_id, source_provider,
                    source_type, source_uri, symbol_universe_json, benchmark_json,
                    timeframe, method, assumptions_json, artifact_path,
                    artifact_hash, retrieved_at, data_as_of, freshness_status,
                    verification_status, confidence, caveat,
                    contradicts_claim_ids_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    goal_id,
                    session_id,
                    evidence.criterion_id,
                    evidence.claim_id,
                    evidence.evidence_type,
                    text,
                    evidence.tool_call_id,
                    evidence.run_id,
                    evidence.source_provider,
                    evidence.source_type,
                    evidence.source_uri,
                    _json_dumps(evidence.symbol_universe),
                    _json_dumps(evidence.benchmark),
                    evidence.timeframe,
                    evidence.method,
                    _json_dumps(evidence.assumptions),
                    evidence.artifact_path,
                    evidence.artifact_hash,
                    now,
                    evidence.data_as_of,
                    freshness_status,
                    verification_status,
                    evidence.confidence,
                    evidence.caveat,
                    _json_dumps(evidence.contradicts_claim_ids),
                    now,
                ),
            )
            if evidence.criterion_id is not None:
                self._conn.execute(
                    """
                    UPDATE goal_criteria
                    SET status = 'covered', updated_at = ?
                    WHERE goal_id = ? AND session_id = ? AND criterion_id = ?
                        AND status IN ('pending', 'open', 'unsatisfied')
                    """,
                    (now, goal_id, session_id, evidence.criterion_id),
                )

        record = self._get_evidence(evidence_id)
        if record is None:
            raise RuntimeError("created evidence could not be reloaded")
        return record

    @_synchronized
    def update_status(
        self,
        *,
        session_id: str,
        goal_id: str,
        expected_goal_id: str,
        status: GoalStatus,
        audit: list[AuditRow] | None = None,
        recap: str | None = None,
    ) -> GoalRecord:
        """Update a goal status with stale-goal and completion validation."""
        with self._write_transaction():
            goal = self._require_mutable_goal(session_id, goal_id, expected_goal_id)
            session_id = goal.session_id
            goal_id = goal.goal_id
            if status is GoalStatus.COMPLETE:
                self._validate_completion_audit(goal, audit or [])

            now = _now_iso()
            completed_at = now if status in {
                GoalStatus.COMPLETE,
                GoalStatus.BLOCKED,
                GoalStatus.CANCELLED,
                GoalStatus.SUPERSEDED,
                GoalStatus.USAGE_LIMITED,
            } else None
            self._conn.execute(
                """
                UPDATE goals
                SET status = ?, updated_at = ?, completed_at = COALESCE(?, completed_at),
                    recap = COALESCE(?, recap)
                WHERE goal_id = ? AND session_id = ?
                """,
                (status.value, now, completed_at, recap, goal_id, session_id),
            )
            if audit:
                self._conn.execute(
                    """
                    INSERT INTO goal_audits (
                        audit_id, goal_id, session_id, audit_type, result,
                        rows_json, created_at
                    )
                    VALUES (?, ?, ?, 'completion', ?, ?, ?)
                    """,
                    (
                        _id("audit"),
                        goal_id,
                        session_id,
                        status.value,
                        _json_dumps([row.__dict__ for row in audit]),
                        now,
                    ),
                )
            if audit and status is GoalStatus.COMPLETE:
                for row in audit:
                    self._conn.execute(
                        """
                        UPDATE goal_criteria
                        SET status = ?, updated_at = ?
                        WHERE goal_id = ? AND session_id = ? AND criterion_id = ?
                        """,
                        (row.result, now, goal_id, session_id, row.criterion_id),
                    )

        updated = self.get_goal(goal_id)
        if updated is None:
            raise RuntimeError("updated goal could not be reloaded")
        return updated

    @_synchronized
    def account_usage(
        self,
        *,
        session_id: str,
        goal_id: str,
        expected_goal_id: str,
        token_delta: int = 0,
        time_delta_seconds: int = 0,
        turn_delta: int = 0,
    ) -> GoalRecord:
        """Account usage and move the goal to budget_limited if needed."""
        if min(token_delta, time_delta_seconds, turn_delta) < 0:
            raise ValueError("usage deltas must be non-negative")

        with self._write_transaction():
            goal = self._require_mutable_goal(session_id, goal_id, expected_goal_id)
            session_id = goal.session_id
            goal_id = goal.goal_id
            tokens_used = goal.tokens_used + token_delta
            time_used_seconds = goal.time_used_seconds + time_delta_seconds
            turns_used = goal.turns_used + turn_delta
            crosses_budget = (
                (goal.token_budget is not None and tokens_used >= goal.token_budget)
                or (
                    goal.time_budget_seconds is not None
                    and time_used_seconds >= goal.time_budget_seconds
                )
                or (goal.turn_budget is not None and turns_used >= goal.turn_budget)
            )
            next_status = GoalStatus.BUDGET_LIMITED if crosses_budget else goal.status
            now = _now_iso()
            self._conn.execute(
                """
                UPDATE goals
                SET tokens_used = ?, time_used_seconds = ?, turns_used = ?,
                    status = ?, updated_at = ?
                WHERE goal_id = ? AND session_id = ?
                """,
                (
                    tokens_used,
                    time_used_seconds,
                    turns_used,
                    next_status.value,
                    now,
                    goal_id,
                    session_id,
                ),
            )

        updated = self.get_goal(goal_id)
        if updated is None:
            raise RuntimeError("usage-updated goal could not be reloaded")
        return updated

    def _require_mutable_goal(
        self,
        session_id: str,
        goal_id: str,
        expected_goal_id: str,
    ) -> GoalRecord:
        if expected_goal_id != goal_id:
            raise StaleGoalError("expected_goal_id does not match target goal")
        session_id = normalize_required_text(session_id, "session_id")
        goal_id = normalize_required_text(goal_id, "goal_id")
        goal = self.get_goal(goal_id)
        if goal is None or goal.session_id != session_id:
            raise StaleGoalError("goal is not available for this session")
        if goal.status not in _CURRENT_STATUSES:
            raise StaleGoalError(f"goal status {goal.status.value!r} is not mutable")
        current = self.get_current_goal(session_id)
        if current is None or current.goal_id != goal_id:
            raise StaleGoalError("goal is not current for this session")
        return goal

    @staticmethod
    def _verification_status(evidence: EvidenceInput) -> str:
        """Return whether evidence has a traceable local artifact/run source."""
        if evidence.artifact_path:
            try:
                artifact = safe_document_path(evidence.artifact_path)
            except ValueError:
                artifact = None
            if artifact and artifact.is_file():
                if GoalStore._artifact_hash_matches(artifact, evidence.artifact_hash):
                    return "verified"
        if evidence.run_id:
            try:
                run_dir = safe_run_id(evidence.run_id)
            except ValueError:
                run_dir = None
            if run_dir and run_dir.is_dir():
                return "verified"
        return "unverified"

    @staticmethod
    def _artifact_hash_matches(path: Path, expected_hash: str | None) -> bool:
        if not expected_hash:
            return False
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return False
        return digest == expected_hash.lower().removeprefix("sha256:")

    def _require_criterion(self, goal_id: str, criterion_id: str) -> GoalCriterion:
        row = self._conn.execute(
            """
            SELECT * FROM goal_criteria
            WHERE goal_id = ? AND criterion_id = ?
            """,
            (goal_id, criterion_id),
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown criterion_id: {criterion_id}")
        return self._criterion_from_row(row)

    def _require_claim(self, goal_id: str, claim_id: str) -> GoalClaim:
        row = self._conn.execute(
            """
            SELECT * FROM goal_claims
            WHERE goal_id = ? AND claim_id = ?
            """,
            (goal_id, claim_id),
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown claim_id: {claim_id}")
        return self._claim_from_row(row)

    def _validate_completion_audit(
        self,
        goal: GoalRecord,
        audit: list[AuditRow],
    ) -> None:
        criteria = self.list_criteria(goal.goal_id)
        rows_by_criterion = {row.criterion_id: row for row in audit}
        for criterion in criteria:
            if not criterion.required:
                continue
            row = rows_by_criterion.get(criterion.criterion_id)
            if row is None:
                raise ValueError(f"missing audit row for criterion {criterion.criterion_id}")
            if row.result not in _COMPLETION_RESULTS:
                raise ValueError(f"criterion {criterion.criterion_id} is not satisfied")
            if row.result in {"satisfied", "satisfied_with_caveat"} and not row.evidence_ids:
                raise ValueError("complete goals require verified evidence")
            if row.result == "not_applicable_user_accepted" and not row.notes.strip():
                raise ValueError("not-applicable criteria require acceptance notes")
            has_verified_evidence = False
            for evidence_id in row.evidence_ids:
                evidence = self._get_evidence(evidence_id)
                if evidence is None or evidence.goal_id != goal.goal_id:
                    raise ValueError(f"unknown evidence_id: {evidence_id}")
                if evidence.criterion_id != criterion.criterion_id:
                    raise ValueError(
                        f"evidence {evidence_id} does not match criterion {criterion.criterion_id}"
                    )
                if evidence.verification_status == "verified":
                    has_verified_evidence = True
            if row.result in {"satisfied", "satisfied_with_caveat"} and not has_verified_evidence:
                raise ValueError("complete goals require verified evidence")

    def _get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        row = self._conn.execute(
            "SELECT * FROM goal_evidence WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()
        return self._evidence_from_row(row) if row else None

    @staticmethod
    def _goal_from_row(row: sqlite3.Row) -> GoalRecord:
        return GoalRecord(
            goal_id=row["goal_id"],
            session_id=row["session_id"],
            status=GoalStatus(row["status"]),
            objective=row["objective"],
            ui_summary=row["ui_summary"],
            source=row["source"],
            protocol=row["protocol"],
            risk_tier=RiskTier(row["risk_tier"]),
            token_budget=row["token_budget"],
            tokens_used=row["tokens_used"],
            turn_budget=row["turn_budget"],
            turns_used=row["turns_used"],
            time_budget_seconds=row["time_budget_seconds"],
            time_used_seconds=row["time_used_seconds"],
            budget_wrapup_sent=bool(row["budget_wrapup_sent"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
            recap=row["recap"],
        )

    @staticmethod
    def _criterion_from_row(row: sqlite3.Row) -> GoalCriterion:
        return GoalCriterion(
            criterion_id=row["criterion_id"],
            goal_id=row["goal_id"],
            session_id=row["session_id"],
            text=row["text"],
            required=bool(row["required"]),
            status=row["status"],
            freshness_requirement=row["freshness_requirement"],
            protocol_step=row["protocol_step"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _claim_from_row(row: sqlite3.Row) -> GoalClaim:
        return GoalClaim(
            claim_id=row["claim_id"],
            goal_id=row["goal_id"],
            session_id=row["session_id"],
            claim_type=row["claim_type"],
            text=row["text"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _evidence_from_row(row: sqlite3.Row) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=row["evidence_id"],
            goal_id=row["goal_id"],
            session_id=row["session_id"],
            criterion_id=row["criterion_id"],
            claim_id=row["claim_id"],
            evidence_type=row["evidence_type"],
            text=row["text"],
            tool_call_id=row["tool_call_id"],
            run_id=row["run_id"],
            source_provider=row["source_provider"],
            source_type=row["source_type"],
            source_uri=row["source_uri"],
            symbol_universe=list(_json_loads(row["symbol_universe_json"], [])),
            benchmark=list(_json_loads(row["benchmark_json"], [])),
            timeframe=row["timeframe"],
            method=row["method"],
            assumptions=dict(_json_loads(row["assumptions_json"], {})),
            artifact_path=row["artifact_path"],
            artifact_hash=row["artifact_hash"],
            retrieved_at=row["retrieved_at"],
            data_as_of=row["data_as_of"],
            freshness_status=row["freshness_status"],
            verification_status=row["verification_status"],
            confidence=row["confidence"],
            caveat=row["caveat"],
            contradicts_claim_ids=list(_json_loads(row["contradicts_claim_ids_json"], [])),
            created_at=row["created_at"],
        )
