"""Read-only company-profile tool: key stats, estimates, and ownership.

Backed by the shared Yahoo Finance quoteSummary client
(:func:`backtest.loaders.yahoo_client.get_quote_summary`), which routes every
request through the throttled HTTP layer and handles the cookie+crumb
handshake. This tool only selects modules, projects the verbose Yahoo payload
into compact rows, and wraps the result in the project envelope.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from backtest.loaders.yahoo_client import get_quote_summary
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Section name (tool-facing) -> Yahoo quoteSummary module name.
_SECTION_MODULES: Dict[str, str] = {
    "key_stats": "defaultKeyStatistics",
    "financials": "financialData",
    "earnings_trend": "earningsTrend",
    "institution_ownership": "institutionOwnership",
    "insider_holders": "insiderHolders",
    "recommendation_trend": "recommendationTrend",
}
_ALL_SECTIONS = tuple(_SECTION_MODULES)

# Cap list-valued sections so a verbose payload cannot bloat the envelope.
_MAX_ROWS = 25


def _raw(value: Any) -> Any:
    """Unwrap a Yahoo ``{"raw":..,"fmt":..}`` cell to its numeric ``raw`` value.

    Args:
        value: A Yahoo scalar, which may be a plain value or a formatted dict.

    Returns:
        The ``raw`` member when ``value`` is a Yahoo formatted dict, the value
        itself when scalar, or ``None`` for an empty/absent cell.
    """
    if isinstance(value, dict):
        return value.get("raw")
    return value


def _pick(source: Dict[str, Any], fields: tuple[str, ...]) -> Dict[str, Any]:
    """Project selected Yahoo fields into a flat, raw-unwrapped row."""
    return {field: _raw(source.get(field)) for field in fields}


def _key_stats(module: Dict[str, Any]) -> Dict[str, Any]:
    """Shape the defaultKeyStatistics module into a compact row."""
    return _pick(
        module,
        (
            "enterpriseValue",
            "forwardPE",
            "trailingEps",
            "forwardEps",
            "pegRatio",
            "priceToBook",
            "profitMargins",
            "beta",
            "sharesOutstanding",
            "floatShares",
            "heldPercentInsiders",
            "heldPercentInstitutions",
        ),
    )


def _financials(module: Dict[str, Any]) -> Dict[str, Any]:
    """Shape the financialData module into a compact row."""
    return _pick(
        module,
        (
            "currentPrice",
            "targetMeanPrice",
            "targetHighPrice",
            "targetLowPrice",
            "recommendationKey",
            "numberOfAnalystOpinions",
            "totalRevenue",
            "revenueGrowth",
            "grossMargins",
            "operatingMargins",
            "returnOnEquity",
            "totalCash",
            "totalDebt",
        ),
    )


def _earnings_trend(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Shape the earningsTrend periods into per-period estimate rows."""
    rows: List[Dict[str, Any]] = []
    for entry in (module.get("trend") or [])[:_MAX_ROWS]:
        if not isinstance(entry, dict):
            continue
        eps = entry.get("earningsEstimate") or {}
        rev = entry.get("revenueEstimate") or {}
        rows.append(
            {
                "period": entry.get("period"),
                "end_date": entry.get("endDate"),
                "growth": _raw(entry.get("growth")),
                "eps_avg": _raw(eps.get("avg")),
                "eps_low": _raw(eps.get("low")),
                "eps_high": _raw(eps.get("high")),
                "eps_analysts": _raw(eps.get("numberOfAnalysts")),
                "revenue_avg": _raw(rev.get("avg")),
            }
        )
    return rows


def _institution_ownership(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Shape the institutionOwnership holders into per-holder rows."""
    rows: List[Dict[str, Any]] = []
    for entry in (module.get("ownershipList") or [])[:_MAX_ROWS]:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "organization": entry.get("organization"),
                "report_date": _raw(entry.get("reportDate")),
                "pct_held": _raw(entry.get("pctHeld")),
                "position": _raw(entry.get("position")),
                "value": _raw(entry.get("value")),
            }
        )
    return rows


def _insider_holders(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Shape the insiderHolders holders into per-insider rows."""
    rows: List[Dict[str, Any]] = []
    for entry in (module.get("holders") or [])[:_MAX_ROWS]:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "name": entry.get("name"),
                "relation": entry.get("relation"),
                "latest_transaction": entry.get("latestTransDate"),
                "position": _raw(entry.get("positionDirect")),
            }
        )
    return rows


def _recommendation_trend(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Shape the recommendationTrend periods into per-period rating rows."""
    rows: List[Dict[str, Any]] = []
    for entry in (module.get("trend") or [])[:_MAX_ROWS]:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "period": entry.get("period"),
                "strong_buy": entry.get("strongBuy"),
                "buy": entry.get("buy"),
                "hold": entry.get("hold"),
                "sell": entry.get("sell"),
                "strong_sell": entry.get("strongSell"),
            }
        )
    return rows


# Section name -> (yahoo module name, shaper). One entry per supported section.
_SHAPERS = {
    "key_stats": _key_stats,
    "financials": _financials,
    "earnings_trend": _earnings_trend,
    "institution_ownership": _institution_ownership,
    "insider_holders": _insider_holders,
    "recommendation_trend": _recommendation_trend,
}


def _resolve_sections(sections: Optional[List[str]]) -> List[str]:
    """Validate the requested sections, defaulting to all when omitted.

    Args:
        sections: Requested section names, or ``None`` for every section.

    Returns:
        An ordered, de-duplicated list of valid section names.

    Raises:
        ValueError: If any requested name is not a supported section.
    """
    if not sections:
        return list(_ALL_SECTIONS)
    resolved: List[str] = []
    for name in sections:
        key = str(name).strip().lower()
        if key not in _SECTION_MODULES:
            raise ValueError(
                f"unknown section '{name}'; valid: {', '.join(_ALL_SECTIONS)}"
            )
        if key not in resolved:
            resolved.append(key)
    return resolved


def _market_for(ticker: str) -> str:
    """Classify a ticker into a coarse market label for the envelope."""
    return "hk" if ticker.strip().upper().endswith(".HK") else "us"


class StockProfileTool(BaseTool):
    """Company profile: key stats, analyst estimates, and ownership."""

    name = "get_stock_profile"
    description = (
        "Fetch a read-only company profile for a US or Hong Kong listing from "
        "Yahoo Finance: valuation key statistics, analyst price targets and "
        "earnings/revenue estimates, institutional and insider ownership, and "
        "the analyst recommendation trend. Use this for fundamentals and "
        "consensus context, not for OHLCV price bars (use get_market_data). "
        'Example: get_stock_profile(ticker="AAPL.US", '
        'sections=["key_stats", "financials"]).'
    )
    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": (
                    "US or HK symbol. US uses a bare or .US suffix (AAPL or "
                    "AAPL.US); HK uses a zero-padded .HK code (00700.HK)."
                ),
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(_ALL_SECTIONS),
                },
                "description": (
                    "Which profile sections to return. One or more of: "
                    "key_stats, financials, earnings_trend, "
                    "institution_ownership, insider_holders, "
                    "recommendation_trend. Defaults to all sections."
                ),
                "default": list(_ALL_SECTIONS),
            },
        },
        "required": ["ticker"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Fetch and shape the requested profile sections for one ticker.

        Args:
            **kwargs: ``ticker`` (str, required) and ``sections`` (list[str],
                optional; defaults to all sections).

        Returns:
            A JSON envelope string. On success:
            ``{"ok": true, "market": str, "source": "yahoo",
            "data": {"ticker": str, "sections": {<name>: <shaped>}}}``.
            On failure: ``{"ok": false, "error": str}``.
        """
        ticker = str(kwargs.get("ticker") or "").strip()
        if not ticker:
            return self._error("ticker is required")

        try:
            sections = _resolve_sections(kwargs.get("sections"))
        except ValueError as exc:
            return self._error(str(exc))

        modules = [_SECTION_MODULES[name] for name in sections]
        try:
            summary = get_quote_summary(ticker, modules)
        except Exception as exc:  # noqa: BLE001 - surface upstream as envelope
            logger.warning("get_stock_profile failed for %s: %s", ticker, exc)
            return self._error(f"yahoo quoteSummary request failed: {exc}")

        shaped: Dict[str, Any] = {}
        for name in sections:
            module = summary.get(_SECTION_MODULES[name]) or {}
            shaped[name] = _SHAPERS[name](module if isinstance(module, dict) else {})

        return json.dumps(
            {
                "ok": True,
                "market": _market_for(ticker),
                "source": "yahoo",
                "data": {"ticker": ticker, "sections": shaped},
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _error(message: str) -> str:
        """Render a failure envelope as a JSON string."""
        return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
