"""Alpha-Zoo browse tool: list / get / health on the frozen Registry contract.

A single agent-facing tool with an ``action`` discriminator (list_alphas /
get_alpha / health) rather than three separate tools — keeps the LLM tool
catalogue compact and avoids teaching three near-identical surfaces.

Source-code bodies of alphas are intentionally NOT exposed here: payloads
get large, and the CLI/inspection path handles that case. The agent gets
metadata only.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 500

# Fields surfaced to the agent for get_alpha. Excludes raw source — caller
# uses a dedicated inspection path for that.
_META_FIELDS_EXPOSED = (
    "nickname",
    "theme",
    "formula_latex",
    "columns_required",
    "extras_required",
    "requires_sector",
    "universe",
    "frequency",
    "decay_horizon",
    "min_warmup_bars",
    "notes",
)


def _err(msg: str) -> str:
    return json.dumps({"status": "error", "error": msg}, ensure_ascii=False)


def _ok(result: Any) -> str:
    return json.dumps({"status": "ok", "result": result}, ensure_ascii=False)


def _get_registry() -> Any:
    """Lazy-import Registry so this tool's import never triggers a zoo scan
    until the agent actually calls it."""
    from src.factors.registry import Registry  # local import; intentional

    return Registry()


def _alpha_summary(registry: Any, alpha_id: str) -> dict[str, Any]:
    alpha = registry.get(alpha_id)
    meta = alpha.meta or {}
    out: dict[str, Any] = {"id": alpha.id, "zoo": alpha.zoo}
    for field in _META_FIELDS_EXPOSED:
        if field in meta:
            out[field] = meta[field]
    return out


def _action_list(
    registry: Any,
    *,
    zoo: str | None,
    theme: str | None,
    universe: str | None,
    limit: int,
) -> dict[str, Any]:
    all_ids = registry.list(zoo=zoo, theme=theme, universe=universe)
    total = len(all_ids)
    truncated = total > limit
    items = [_alpha_summary(registry, aid) for aid in all_ids[:limit]]
    return {
        "total": total,
        "returned": len(items),
        "truncated": truncated,
        "filters": {"zoo": zoo, "theme": theme, "universe": universe},
        "items": items,
    }


def _action_get(registry: Any, alpha_id: str) -> dict[str, Any]:
    return _alpha_summary(registry, alpha_id)


def _action_health(registry: Any) -> dict[str, Any]:
    return registry.health()


def run_alpha_zoo(**kwargs: Any) -> dict[str, Any]:
    """Module-level entry returning a parsed envelope (dict, not JSON string).

    Mirrors ``run_alpha_bench`` so CLI handlers can call without round-trip.
    """
    action = kwargs.get("action")
    if action not in {"list_alphas", "get_alpha", "health"}:
        return {
            "status": "error",
            "error": f"action must be list_alphas|get_alpha|health, got {action!r}",
        }

    try:
        registry = _get_registry()
    except Exception as exc:
        logger.exception("Registry construction failed")
        return {"status": "error", "error": f"registry init failed: {exc}"}

    try:
        if action == "list_alphas":
            limit_raw = kwargs.get("limit", _DEFAULT_LIMIT)
            try:
                limit = int(limit_raw)
            except (TypeError, ValueError):
                return {"status": "error", "error": f"limit must be int, got {limit_raw!r}"}
            if limit <= 0:
                return {"status": "error", "error": "limit must be > 0"}
            limit = min(limit, _MAX_LIMIT)
            result = _action_list(
                registry,
                zoo=kwargs.get("zoo"),
                theme=kwargs.get("theme"),
                universe=kwargs.get("universe"),
                limit=limit,
            )
        elif action == "get_alpha":
            alpha_id = kwargs.get("alpha_id")
            if not alpha_id or not isinstance(alpha_id, str):
                return {"status": "error", "error": "get_alpha requires alpha_id (string)"}
            try:
                result = _action_get(registry, alpha_id)
            except KeyError as exc:
                return {"status": "error", "error": str(exc)}
        else:  # health
            result = _action_health(registry)
    except Exception as exc:
        logger.exception("alpha_zoo action %s failed", action)
        return {"status": "error", "error": f"{action} failed: {exc}"}

    return {"status": "ok", "result": result}


class AlphaZooTool(BaseTool):
    """Browse the bundled alpha zoo: list_alphas / get_alpha / health."""

    name = "alpha_zoo"
    description = (
        "Browse the bundled alpha zoo. action=list_alphas filters by zoo/theme/universe; "
        "action=get_alpha returns one alpha's metadata (no source body); "
        "action=health reports registry load status (loaded / failed / errors)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list_alphas", "get_alpha", "health"],
                "description": "Which registry operation to run.",
            },
            "alpha_id": {
                "type": "string",
                "description": "Required when action=get_alpha.",
            },
            "zoo": {
                "type": "string",
                "description": "Optional zoo filter for list_alphas (e.g. gtja191, kakushadze101).",
            },
            "theme": {
                "type": "string",
                "description": "Optional theme filter (momentum, reversal, volume, ...).",
            },
            "universe": {
                "type": "string",
                "description": "Optional universe filter (equity_us, equity_cn, crypto, ...).",
            },
            "limit": {
                "type": "integer",
                "default": _DEFAULT_LIMIT,
                "description": f"Cap on returned items (default {_DEFAULT_LIMIT}, max {_MAX_LIMIT}).",
            },
        },
        "required": ["action"],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        envelope = run_alpha_zoo(**kwargs)
        return json.dumps(envelope, ensure_ascii=False)
