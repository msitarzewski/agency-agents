"""Shadow Account BaseTool wrappers (auto-discovered by `src.tools` registry).

Four tools, all thin — business logic lives in `src.shadow_account`:
    extract_shadow_strategy → extractor.extract_shadow_profile
    run_shadow_backtest     → backtester.run_shadow_backtest
    render_shadow_report    → reporter.render_shadow_report
    scan_shadow_signals     → scanner.scan_today_signals
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import date, timedelta
from typing import Any

from src.agent.tools import BaseTool
from src.tools.path_utils import safe_user_path
from src.shadow_account import (
    extract_shadow_profile,
    load_profile,
    render_shadow_report,
    run_shadow_backtest,
    save_profile,
)
from src.shadow_account.backtester import load_cached_result
from src.shadow_account.scanner import scan_today_signals

logger = logging.getLogger(__name__)


def _err(message: str, **extra: Any) -> str:
    return json.dumps({"status": "error", "error": message, **extra}, ensure_ascii=False)


def _ok(**payload: Any) -> str:
    return json.dumps({"status": "ok", **payload}, ensure_ascii=False, default=str)


def _validate_optional_journal_path(raw: Any) -> str | None:
    """Validate a journal_path kwarg that may be missing/empty.

    Returns the resolved path string, or None when the caller didn't pass
    one. Raises ValueError (already the contract of `safe_user_path`) when
    the path escapes the user envelope.
    """
    if not raw:
        return None
    return str(safe_user_path(raw))


# ---------------- Tool 1: extract ----------------

class ExtractShadowStrategyTool(BaseTool):
    """Extract a Shadow Account profile from a user's trade journal."""

    name = "extract_shadow_strategy"
    description = (
        "Extract implicit trading rules from the user's profitable roundtrips "
        "and produce a Shadow Account profile (3-5 human-readable if-then rules). "
        "Run `analyze_trade_journal` first if the journal hasn't been parsed. "
        "Returns shadow_id + rules preview; profile is persisted to "
        "~/.vibe-trading/shadow_accounts/."
    )
    parameters = {
        "type": "object",
        "properties": {
            "journal_path": {
                "type": "string",
                "description": "Path to the CSV/Excel broker export (同花顺/东方财富/富途/generic).",
            },
            "min_support": {
                "type": "integer",
                "description": "Minimum profitable roundtrips required to back one rule.",
                "default": 3,
            },
            "max_rules": {
                "type": "integer",
                "description": "Maximum number of rules to return (typically 3-5).",
                "default": 5,
            },
        },
        "required": ["journal_path"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        journal_path = kwargs.get("journal_path")
        if not journal_path:
            return _err("journal_path is required")
        try:
            journal_path = str(safe_user_path(journal_path))
        except ValueError as exc:
            return _err(str(exc))
        try:
            profile = extract_shadow_profile(
                journal_path,
                min_support=int(kwargs.get("min_support", 3)),
                max_rules=int(kwargs.get("max_rules", 5)),
            )
        except (FileNotFoundError, ValueError) as exc:
            return _err(str(exc))
        except Exception as exc:  # pragma: no cover — defensive
            logger.exception("extract_shadow_strategy failed")
            return _err(f"unexpected error: {exc}")

        save_profile(profile)
        rules_preview = [
            {
                "rule_id": r.rule_id,
                "human_text": r.human_text,
                "support_count": r.support_count,
                "coverage_rate": r.coverage_rate,
                "holding_days_range": list(r.holding_days_range),
            }
            for r in profile.rules
        ]
        return _ok(
            shadow_id=profile.shadow_id,
            profile_text=profile.profile_text,
            source_market=profile.source_market,
            profitable_roundtrips=profile.profitable_roundtrips,
            total_roundtrips=profile.total_roundtrips,
            typical_holding_days=list(profile.typical_holding_days),
            rules=rules_preview,
        )


# ---------------- Tool 2: backtest ----------------

class RunShadowBacktestTool(BaseTool):
    """Run multi-market backtest for an extracted Shadow Account."""

    name = "run_shadow_backtest"
    description = (
        "Run a multi-market backtest (A股/港股/美股/crypto) on a Shadow Account "
        "profile and compute delta-PnL attribution vs the user's realized trades. "
        "Requires `extract_shadow_strategy` to have been run first."
    )
    parameters = {
        "type": "object",
        "properties": {
            "shadow_id": {"type": "string", "description": "Shadow ID returned by extract_shadow_strategy."},
            "window_start": {
                "type": "string",
                "description": "Backtest window start (ISO date). Default: today - 1y.",
            },
            "window_end": {
                "type": "string",
                "description": "Backtest window end (ISO date). Default: today.",
            },
            "markets": {
                "type": "array",
                "items": {"type": "string", "enum": ["china_a", "hk", "us", "crypto"]},
                "description": "Markets to include. Default: all four.",
            },
            "journal_path": {
                "type": "string",
                "description": "Original journal path (enables attribution). Optional.",
            },
        },
        "required": ["shadow_id"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        shadow_id = kwargs.get("shadow_id")
        if not shadow_id:
            return _err("shadow_id is required")
        try:
            profile = load_profile(shadow_id)
        except FileNotFoundError as exc:
            return _err(str(exc))

        today = date.today()
        window_end = kwargs.get("window_end") or today.isoformat()
        window_start = kwargs.get("window_start") or (today - timedelta(days=365)).isoformat()
        markets = tuple(kwargs.get("markets") or ("china_a", "hk", "us", "crypto"))

        try:
            journal_path = _validate_optional_journal_path(kwargs.get("journal_path"))
        except ValueError as exc:
            return _err(str(exc))
        try:
            result = run_shadow_backtest(
                profile,
                window_start=window_start,
                window_end=window_end,
                markets=markets,
                journal_path=journal_path,
            )
        except ValueError as exc:
            return _err(str(exc))
        except Exception as exc:  # pragma: no cover — defensive
            logger.exception("run_shadow_backtest failed")
            return _err(f"unexpected error: {exc}")

        return _ok(
            shadow_id=result.shadow_id,
            window=[window_start, window_end],
            markets=list(markets),
            per_market=result.per_market,
            combined=result.combined,
            shadow_total_pnl=result.shadow_total_pnl,
            real_total_pnl=result.real_total_pnl,
            delta_pnl=result.delta_pnl,
            attribution=asdict(result.attribution),
            equity_points=len(result.equity_curves.get("combined", [])),
        )


# ---------------- Tool 3: render ----------------

class RenderShadowReportTool(BaseTool):
    """Render a Shadow Account PDF report from a completed backtest."""

    name = "render_shadow_report"
    description = (
        "Generate the Shadow Account PDF (8 sections + charts) for a shadow_id. "
        "Requires a backtest to have been run; otherwise the report renders "
        "with empty metrics. Returns paths to html/pdf + structured JSON."
    )
    parameters = {
        "type": "object",
        "properties": {
            "shadow_id": {"type": "string"},
            "include_today_signals": {"type": "boolean", "default": True},
            "window_start": {"type": "string"},
            "window_end": {"type": "string"},
            "journal_path": {"type": "string"},
        },
        "required": ["shadow_id"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        shadow_id = kwargs.get("shadow_id")
        if not shadow_id:
            return _err("shadow_id is required")
        try:
            profile = load_profile(shadow_id)
        except FileNotFoundError as exc:
            return _err(str(exc))

        try:
            journal_path = _validate_optional_journal_path(kwargs.get("journal_path"))
        except ValueError as exc:
            return _err(str(exc))

        result = load_cached_result(profile.shadow_id)
        if result is None:
            today = date.today()
            window_end = kwargs.get("window_end") or today.isoformat()
            window_start = kwargs.get("window_start") or (today - timedelta(days=365)).isoformat()
            try:
                result = run_shadow_backtest(
                    profile,
                    window_start=window_start,
                    window_end=window_end,
                    journal_path=journal_path,
                )
            except Exception as exc:  # pragma: no cover — defensive
                logger.warning("backtest failed during report render: %s", exc)
                from src.shadow_account.models import AttributionBreakdown, ShadowBacktestResult
                result = ShadowBacktestResult(
                    shadow_id=profile.shadow_id,
                    per_market={}, combined={"error": str(exc)}, equity_curves={},
                    attribution=AttributionBreakdown(
                        missed_signals_pnl=0.0, noise_trades_pnl=0.0, early_exit_pnl=0.0,
                        late_exit_pnl=0.0, overtrading_pnl=0.0, counterfactual_trades=(),
                    ),
                    shadow_total_pnl=0.0, real_total_pnl=0.0, delta_pnl=0.0,
                )

        today_signals = (
            scan_today_signals(profile) if kwargs.get("include_today_signals", True) else []
        )
        report = render_shadow_report(profile, result, today_signals=today_signals)
        payload = {
            "shadow_id": profile.shadow_id,
            "html_path": report["html_path"],
            "pdf_path": report["pdf_path"],
            "engine": report["engine"],
            "delta_pnl": result.delta_pnl,
            "report_url": f"/shadow-reports/{profile.shadow_id}",
        }
        if report["pdf_path"]:
            payload["pdf_url"] = f"/shadow-reports/{profile.shadow_id}?format=pdf"
        return _ok(**payload)


# ---------------- Tool 4: scan ----------------

class ScanShadowSignalsTool(BaseTool):
    """Scan the market for symbols matching a Shadow Account's rules (research only)."""

    name = "scan_shadow_signals"
    description = (
        "List today's symbols that fall within the Shadow Account's entry "
        "cadence (research use only — not a trade recommendation)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "shadow_id": {"type": "string"},
            "date": {
                "type": "string",
                "description": "ISO YYYY-MM-DD target date. Default: today.",
            },
            "per_market": {"type": "integer", "default": 3},
        },
        "required": ["shadow_id"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        shadow_id = kwargs.get("shadow_id")
        if not shadow_id:
            return _err("shadow_id is required")
        try:
            profile = load_profile(shadow_id)
        except FileNotFoundError as exc:
            return _err(str(exc))

        target = kwargs.get("date") or None
        per_market = int(kwargs.get("per_market", 3))
        signals = scan_today_signals(profile, target_date=target, per_market=per_market)
        return _ok(
            shadow_id=profile.shadow_id,
            target_date=target or "today",
            matches=signals,
            disclaimer="Research use only - not investment advice.",
        )
