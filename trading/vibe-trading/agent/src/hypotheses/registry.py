"""Pure-code durable research hypothesis registry.

The registry is intentionally small: local JSON storage, deterministic reads,
and no dependency on LLMs or live trading services.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HYPOTHESIS_STATUSES = (
    "exploring",
    "testing",
    "validated",
    "rejected",
    "monitoring",
)
_STATUS_SET = set(HYPOTHESIS_STATUSES)
_ENV_PATH = "VIBE_TRADING_HYPOTHESES_PATH"
_TOKEN_RE = re.compile(r"[a-zA-Z0-9]{2,}|[\u4e00-\u9fff]")


def default_hypotheses_path() -> Path:
    """Return the configured hypotheses JSON path.

    Returns:
        Env override path when ``VIBE_TRADING_HYPOTHESES_PATH`` is set,
        otherwise ``~/.vibe-trading/hypotheses.json``.
    """
    override = os.environ.get(_ENV_PATH, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".vibe-trading" / "hypotheses.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _new_hypothesis_id(title: str, created_at: str, existing_ids: set[str]) -> str:
    seed = f"{title.strip().lower()}|{created_at}"
    base = "hyp_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    if base not in existing_ids:
        return base
    idx = 2
    while f"{base}_{idx}" in existing_ids:
        idx += 1
    return f"{base}_{idx}"


def _validate_status(status: str) -> str:
    normalized = str(status).strip().lower()
    if normalized not in _STATUS_SET:
        allowed = ", ".join(HYPOTHESIS_STATUSES)
        raise ValueError(f"unknown hypothesis status '{status}'. Allowed: {allowed}")
    return normalized


@dataclass
class Hypothesis:
    """A research hypothesis tracked across analysis and backtests.

    Attributes:
        hypothesis_id: Stable registry identifier.
        title: Short human-readable title.
        thesis: Research thesis or rationale.
        status: Lifecycle status.
        universe: Target universe, market, or asset set.
        signal_definition: Signal logic in plain text.
        data_sources: Data sources expected or used.
        skills: Relevant Vibe-Trading skills.
        run_cards: Linked backtest/run-card artifacts.
        invalidation_notes: Notes describing rejection or invalidation logic.
        created_at: UTC creation timestamp.
        updated_at: UTC last update timestamp.
    """

    hypothesis_id: str
    title: str
    thesis: str
    status: str = "exploring"
    universe: str = ""
    signal_definition: str = ""
    data_sources: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    run_cards: list[dict[str, Any]] = field(default_factory=list)
    invalidation_notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the hypothesis to plain JSON-compatible data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Hypothesis":
        """Build a hypothesis from persisted JSON data.

        Args:
            data: Raw dictionary loaded from storage.

        Returns:
            Parsed hypothesis with defaults for missing MVP fields.
        """
        now = _utc_now()
        return cls(
            hypothesis_id=str(data.get("hypothesis_id", "")),
            title=str(data.get("title", "")),
            thesis=str(data.get("thesis", "")),
            status=_validate_status(str(data.get("status", "exploring"))),
            universe=str(data.get("universe", "")),
            signal_definition=str(data.get("signal_definition", "")),
            data_sources=_coerce_str_list(data.get("data_sources")),
            skills=_coerce_str_list(data.get("skills")),
            run_cards=list(data.get("run_cards") or data.get("backtests") or []),
            invalidation_notes=str(data.get("invalidation_notes", "")),
            created_at=str(data.get("created_at") or now),
            updated_at=str(data.get("updated_at") or data.get("created_at") or now),
        )


class HypothesisRegistry:
    """File-backed registry for research hypotheses."""

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the registry.

        Args:
            path: Optional storage path. Defaults to env override or
                ``~/.vibe-trading/hypotheses.json``.
        """
        self.path = path or default_hypotheses_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        title: str,
        thesis: str,
        status: str = "exploring",
        universe: str = "",
        signal_definition: str = "",
        data_sources: list[str] | None = None,
        skills: list[str] | None = None,
        invalidation_notes: str = "",
    ) -> Hypothesis:
        """Create and persist a new hypothesis.

        Args:
            title: Short hypothesis title.
            thesis: Research thesis or rationale.
            status: Initial lifecycle status.
            universe: Target market or asset universe.
            signal_definition: Signal logic.
            data_sources: Source names.
            skills: Related Vibe-Trading skills.
            invalidation_notes: Initial invalidation notes.

        Returns:
            Created hypothesis.

        Raises:
            ValueError: If title/thesis/status are invalid.
        """
        title = title.strip()
        thesis = thesis.strip()
        if not title:
            raise ValueError("title is required")
        if not thesis:
            raise ValueError("thesis is required")

        records = self.list()
        now = _utc_now()
        hyp = Hypothesis(
            hypothesis_id=_new_hypothesis_id(title, now, {h.hypothesis_id for h in records}),
            title=title,
            thesis=thesis,
            status=_validate_status(status),
            universe=universe.strip(),
            signal_definition=signal_definition.strip(),
            data_sources=_coerce_str_list(data_sources),
            skills=_coerce_str_list(skills),
            invalidation_notes=invalidation_notes.strip(),
            created_at=now,
            updated_at=now,
        )
        records.append(hyp)
        self._save(records)
        return hyp

    def update(
        self,
        hypothesis_id: str,
        *,
        title: str | None = None,
        thesis: str | None = None,
        status: str | None = None,
        universe: str | None = None,
        signal_definition: str | None = None,
        data_sources: list[str] | None = None,
        skills: list[str] | None = None,
        invalidation_notes: str | None = None,
    ) -> Hypothesis:
        """Update an existing hypothesis.

        Args:
            hypothesis_id: Registry identifier.
            title: Optional replacement title.
            thesis: Optional replacement thesis.
            status: Optional lifecycle status.
            universe: Optional replacement universe.
            signal_definition: Optional replacement signal definition.
            data_sources: Optional replacement source list.
            skills: Optional replacement skill list.
            invalidation_notes: Optional replacement invalidation notes.

        Returns:
            Updated hypothesis.

        Raises:
            KeyError: If the hypothesis does not exist.
            ValueError: If status is unknown.
        """
        records = self.list()
        hyp = self._find_required(records, hypothesis_id)
        if title is not None:
            hyp.title = title.strip()
        if thesis is not None:
            hyp.thesis = thesis.strip()
        if status is not None:
            hyp.status = _validate_status(status)
        if universe is not None:
            hyp.universe = universe.strip()
        if signal_definition is not None:
            hyp.signal_definition = signal_definition.strip()
        if data_sources is not None:
            hyp.data_sources = _coerce_str_list(data_sources)
        if skills is not None:
            hyp.skills = _coerce_str_list(skills)
        if invalidation_notes is not None:
            hyp.invalidation_notes = invalidation_notes.strip()
        hyp.updated_at = _utc_now()
        self._save(records)
        return hyp

    def link_backtest(
        self,
        hypothesis_id: str,
        *,
        run_card_path: str = "",
        backtest_run_dir: str = "",
        metrics: dict[str, Any] | None = None,
        notes: str = "",
    ) -> Hypothesis:
        """Link a run card or backtest artifact to a hypothesis.

        Args:
            hypothesis_id: Registry identifier.
            run_card_path: Optional path to a run_card.json.
            backtest_run_dir: Optional backtest run directory.
            metrics: Optional metrics summary.
            notes: Optional human note about the link.

        Returns:
            Updated hypothesis.

        Raises:
            KeyError: If the hypothesis does not exist.
            ValueError: If no run card or run directory is provided.
        """
        if not run_card_path and not backtest_run_dir:
            raise ValueError("run_card_path or backtest_run_dir is required")
        records = self.list()
        hyp = self._find_required(records, hypothesis_id)
        hyp.run_cards.append({
            "run_card_path": run_card_path,
            "backtest_run_dir": backtest_run_dir,
            "metrics": metrics or {},
            "notes": notes,
            "linked_at": _utc_now(),
        })
        hyp.updated_at = _utc_now()
        self._save(records)
        return hyp

    def search(
        self,
        *,
        query: str = "",
        status: str | None = None,
        limit: int = 10,
    ) -> list[Hypothesis]:
        """Search hypotheses by text and/or status.

        Args:
            query: Text query over title, thesis, universe, signal, sources,
                skills, notes, and links.
            status: Optional status filter.
            limit: Maximum results.

        Returns:
            Matching hypotheses ordered by score then most recently updated.

        Raises:
            ValueError: If status is unknown.
        """
        status_filter = _validate_status(status) if status else None
        query_tokens = _tokenize(query)
        scored: list[tuple[int, Hypothesis]] = []
        for hyp in self.list():
            if status_filter and hyp.status != status_filter:
                continue
            haystack = json.dumps(hyp.to_dict(), ensure_ascii=False, sort_keys=True)
            if not query_tokens:
                score = 1
            else:
                hay_tokens = _tokenize(haystack)
                score = len(query_tokens & hay_tokens)
            if score > 0:
                scored.append((score, hyp))
        scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
        return [hyp for _, hyp in scored[: max(1, min(int(limit), 100))]]

    def list(self) -> list[Hypothesis]:
        """Load all hypotheses from storage."""
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid hypotheses storage JSON: {self.path}") from exc
        if not isinstance(raw, list):
            raise ValueError("hypotheses storage must contain a JSON list")
        return [Hypothesis.from_dict(item) for item in raw if isinstance(item, dict)]

    def _save(self, records: list[Hypothesis]) -> None:
        payload = [hyp.to_dict() for hyp in sorted(records, key=lambda h: h.created_at)]
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self.path)

    @staticmethod
    def _find_required(records: list[Hypothesis], hypothesis_id: str) -> Hypothesis:
        for hyp in records:
            if hyp.hypothesis_id == hypothesis_id:
                return hyp
        raise KeyError(f"hypothesis not found: {hypothesis_id}")
