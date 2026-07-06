"""BaseTool wrappers for the durable hypothesis registry."""

from __future__ import annotations

import json
from typing import Any

from src.agent.tools import BaseTool
from src.hypotheses import HypothesisRegistry


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps({"status": "ok", **payload}, ensure_ascii=False)


def _error(exc: Exception) -> str:
    return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)


class CreateHypothesisTool(BaseTool):
    """Create a durable research hypothesis."""

    name = "create_hypothesis"
    description = (
        "Create a durable research hypothesis in the local registry. "
        "Research-only: does not place trades or call live trading APIs."
    )
    is_readonly = False
    repeatable = True
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short hypothesis title"},
            "thesis": {"type": "string", "description": "Research thesis/rationale"},
            "status": {
                "type": "string",
                "enum": ["exploring", "testing", "validated", "rejected", "monitoring"],
                "description": "Initial status, default exploring",
            },
            "universe": {"type": "string", "description": "Target universe or market"},
            "signal_definition": {"type": "string", "description": "Signal logic"},
            "data_sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Data sources used or expected",
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant Vibe-Trading skills",
            },
            "invalidation_notes": {"type": "string", "description": "Invalidation notes"},
        },
        "required": ["title", "thesis"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Create a hypothesis and return it as JSON."""
        try:
            hyp = HypothesisRegistry().create(
                title=str(kwargs.get("title", "")),
                thesis=str(kwargs.get("thesis", "")),
                status=str(kwargs.get("status", "exploring")),
                universe=str(kwargs.get("universe", "")),
                signal_definition=str(kwargs.get("signal_definition", "")),
                data_sources=kwargs.get("data_sources"),
                skills=kwargs.get("skills"),
                invalidation_notes=str(kwargs.get("invalidation_notes", "")),
            )
            return _ok({"hypothesis": hyp.to_dict()})
        except Exception as exc:
            return _error(exc)


class UpdateHypothesisTool(BaseTool):
    """Update fields and status for a durable research hypothesis."""

    name = "update_hypothesis"
    description = "Update a hypothesis, including lifecycle status and invalidation notes."
    is_readonly = False
    repeatable = True
    parameters = {
        "type": "object",
        "properties": {
            "hypothesis_id": {"type": "string", "description": "Hypothesis identifier"},
            "title": {"type": "string"},
            "thesis": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["exploring", "testing", "validated", "rejected", "monitoring"],
            },
            "universe": {"type": "string"},
            "signal_definition": {"type": "string"},
            "data_sources": {"type": "array", "items": {"type": "string"}},
            "skills": {"type": "array", "items": {"type": "string"}},
            "invalidation_notes": {"type": "string"},
        },
        "required": ["hypothesis_id"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Update a hypothesis and return it as JSON."""
        try:
            hypothesis_id = str(kwargs.pop("hypothesis_id", ""))
            updates = {key: value for key, value in kwargs.items() if value is not None}
            hyp = HypothesisRegistry().update(hypothesis_id, **updates)
            return _ok({"hypothesis": hyp.to_dict()})
        except Exception as exc:
            return _error(exc)


class LinkBacktestTool(BaseTool):
    """Link a backtest run card to a hypothesis."""

    name = "link_backtest"
    description = "Attach a run card or backtest run directory to a research hypothesis."
    is_readonly = False
    repeatable = True
    parameters = {
        "type": "object",
        "properties": {
            "hypothesis_id": {"type": "string", "description": "Hypothesis identifier"},
            "run_card_path": {"type": "string", "description": "Path to run_card.json"},
            "backtest_run_dir": {"type": "string", "description": "Backtest run directory"},
            "metrics": {"type": "object", "description": "Optional metrics summary"},
            "notes": {"type": "string", "description": "Optional link note"},
        },
        "required": ["hypothesis_id"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Link a backtest artifact and return the updated hypothesis."""
        try:
            hyp = HypothesisRegistry().link_backtest(
                str(kwargs.get("hypothesis_id", "")),
                run_card_path=str(kwargs.get("run_card_path", "")),
                backtest_run_dir=str(kwargs.get("backtest_run_dir", "")),
                metrics=kwargs.get("metrics"),
                notes=str(kwargs.get("notes", "")),
            )
            return _ok({"hypothesis": hyp.to_dict()})
        except Exception as exc:
            return _error(exc)


class SearchHypothesesTool(BaseTool):
    """Search durable research hypotheses."""

    name = "search_hypotheses"
    description = "Search hypotheses by text query and/or lifecycle status."
    repeatable = True
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Text query"},
            "status": {
                "type": "string",
                "enum": ["exploring", "testing", "validated", "rejected", "monitoring"],
                "description": "Optional status filter",
            },
            "limit": {"type": "integer", "description": "Max results, default 10"},
        },
        "required": [],
    }

    def execute(self, **kwargs: Any) -> str:
        """Search hypotheses and return matching records."""
        try:
            results = HypothesisRegistry().search(
                query=str(kwargs.get("query", "")),
                status=kwargs.get("status"),
                limit=int(kwargs.get("limit", 10)),
            )
            return _ok({"count": len(results), "hypotheses": [hyp.to_dict() for hyp in results]})
        except Exception as exc:
            return _error(exc)
