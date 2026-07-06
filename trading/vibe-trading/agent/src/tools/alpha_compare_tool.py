"""Agent tool: head-to-head comparison of hand-picked Alpha Zoo alphas.

Thin wrapper over :func:`src.factors.compare_runner.compare_alphas` — the same
core behind ``vibe-trading alpha compare`` (CLI) and ``POST /alpha/compare``
(Web UI). Auto-discovered and registered via ``BaseTool.__subclasses__()``.

Read-only: it computes IC/IR for the named alphas and ranks them; it writes no
files and places no orders.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.agent.tools import BaseTool
from src.factors.compare_runner import SORT_KEYS, compare_alphas


def _coerce_ids(raw: Any) -> list[str]:
    """Normalise the ``alpha_ids`` argument to a clean list of ids.

    Accepts a list (the contract) or a comma/space-separated string (LLMs
    occasionally inline the list), de-duplicating while preserving order.

    Args:
        raw: The ``alpha_ids`` value as supplied by the caller.

    Returns:
        Ordered, de-duplicated list of non-empty id strings.
    """
    items = re.split(r"[\s,]+", raw) if isinstance(raw, str) else (raw or [])
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        aid = str(item).strip()
        if aid and aid not in seen:
            seen.add(aid)
            out.append(aid)
    return out


class AlphaCompareTool(BaseTool):
    """Compare >= 2 named alphas head-to-head and rank them by an IC metric."""

    name = "alpha_compare"
    description = (
        "Compare a hand-picked set of Alpha Zoo alphas (alpha_ids, >= 2) "
        "head-to-head on a universe over a period. Benches only the named "
        "alphas — not the whole zoo — then ranks them by IC mean/std, IR, "
        "IC-positive ratio and sample count, with each alpha's gap to the "
        "leader. Returns the ranking + a winner; no per-stock per-date payloads."
    )
    parameters = {
        "type": "object",
        "properties": {
            "alpha_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "description": "Alpha ids to compare, e.g. ['alpha101_1', 'gtja191_5'].",
            },
            "universe": {
                "type": "string",
                "description": "csi300 | sp500 | btc-usdt.",
            },
            "period": {
                "type": "string",
                "description": "YYYY-YYYY or YYYY-MM-DD/YYYY-MM-DD.",
            },
            "sort": {
                "type": "string",
                "enum": list(SORT_KEYS),
                "default": "ir",
                "description": "Ranking metric (default ir).",
            },
        },
        "required": ["alpha_ids", "universe", "period"],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Run the comparison and return the JSON envelope.

        Args:
            **kwargs: ``alpha_ids`` (list[str]), ``universe`` (str),
                ``period`` (str), optional ``sort`` (str).

        Returns:
            JSON string — on success ``status="ok"`` with a ranking + winner;
            on failure ``status="error"`` with a message.
        """
        alpha_ids = _coerce_ids(kwargs.get("alpha_ids"))
        universe = str(kwargs.get("universe", "")).strip()
        period = str(kwargs.get("period", "")).strip()
        sort = str(kwargs.get("sort") or "ir").strip()

        if not universe or not period:
            return json.dumps(
                {"status": "error", "error": "universe and period are required"},
                ensure_ascii=False,
            )

        try:
            envelope = compare_alphas(alpha_ids, universe, period, sort=sort)
        except Exception as exc:  # noqa: BLE001 — surface a clean tool error
            return json.dumps(
                {"status": "error", "error": f"alpha compare failed: {exc}"},
                ensure_ascii=False,
            )
        return json.dumps(envelope, ensure_ascii=False, default=str)
