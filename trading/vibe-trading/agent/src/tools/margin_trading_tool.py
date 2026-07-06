"""Read-only margin-trading (融资融券) balance tool backed by Eastmoney.

Eastmoney's public datacenter exposes the daily exchange-published
margin-financing / securities-lending (融资融券) figures for individual A-share
stocks: outstanding financing balance, financing buy amount, securities-lending
balance, and the combined RZRQ balance, one row per trading day. This tool reads
those rows through the shared throttled Eastmoney client so the agent can answer
"how leveraged is this stock?" without writing a raw scraping script.

The datacenter is rate-limited by source IP, so every request routes through
:func:`backtest.loaders.eastmoney_client.get_json` (per-host throttle + session
reuse). No credentials are required; the endpoint is read-only public data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders import eastmoney_client
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney datacenter report API. RPTA_WEB_RZRQ_GGMX is the per-stock daily
# margin-trading detail report (个股明细), filterable by SCODE (bare code).
_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_REPORT_NAME = "RPTA_WEB_RZRQ_GGMX"

# Per-bar columns we surface, mapped from the report's raw field names. The
# datacenter returns more columns than this; we keep the headline balances.
_FIELD_MAP: dict[str, str] = {
    "DATE": "trade_date",
    "RZYE": "financing_balance",
    "RZMRE": "financing_buy",
    "RZCHE": "financing_repay",
    "RQYE": "short_balance",
    "RQYL": "short_volume",
    "RZRQYE": "margin_total_balance",
}

# Hard caps so a pathological response can never blow up the LLM context.
_MAX_DAYS = 250
_DEFAULT_DAYS = 30


def _extract_code(symbol: str) -> str | None:
    """Reduce a user-supplied symbol to the bare A-share numeric code.

    Accepts ``"600519"``, ``"600519.SH"``, ``"sh600519"`` or ``"000001.SZ"`` and
    returns the six-digit code Eastmoney's ``SCODE`` filter expects. Margin
    trading is an A-share-only dataset, so non-A symbols return ``None``.

    Args:
        symbol: Caller-supplied stock identifier.

    Returns:
        The six-digit code, or ``None`` when no A-share code can be derived.
    """
    if not symbol:
        return None
    token = symbol.strip().upper()
    if "." in token:
        token = token.rpartition(".")[0]
    for prefix in ("SH", "SZ", "BJ"):
        if token.startswith(prefix):
            token = token[len(prefix) :]
    token = token.strip()
    if len(token) == 6 and token.isdigit():
        return token
    return None


def _clamp_days(days: Any) -> int:
    """Coerce the requested ``days`` to a sane integer within bounds.

    Args:
        days: Raw value from kwargs (may be ``None``, str, or int).

    Returns:
        An int in ``[1, _MAX_DAYS]``; falls back to ``_DEFAULT_DAYS`` on junk.
    """
    try:
        value = int(days)
    except (TypeError, ValueError):
        return _DEFAULT_DAYS
    if value <= 0:
        return _DEFAULT_DAYS
    return min(value, _MAX_DAYS)


def _to_float(value: Any) -> float | None:
    """Convert a raw cell to ``float``, returning ``None`` on missing/garbage."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Project one datacenter row onto our headline-balance schema.

    Args:
        raw: One element of the report's ``result.data`` list.

    Returns:
        A dict keyed by our field names; numeric cells become ``float`` or
        ``None``, the date is kept as the provider's ``YYYY-MM-DD`` string.
    """
    row: dict[str, Any] = {}
    for source_key, out_key in _FIELD_MAP.items():
        value = raw.get(source_key)
        if out_key == "trade_date":
            row[out_key] = str(value)[:10] if value else None
        else:
            row[out_key] = _to_float(value)
    return row


def _err(message: str) -> str:
    """Serialize a failure envelope."""
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


class MarginTradingTool(BaseTool):
    """Fetch daily A-share margin-financing / short-selling balances."""

    name = "get_margin_trading"
    description = (
        "Fetch an A-share stock's daily margin-trading (融资融券) balances from "
        "Eastmoney's public datacenter: outstanding financing balance, financing "
        "buy amount, securities-lending balance, and combined RZRQ balance, one "
        "row per trading day (most recent first). Read-only, no credentials, "
        "Mainland China A-shares only (SH/SZ). "
        'Example: get_margin_trading(code="600519.SH", days=30).'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "A-share stock code. Accepts a bare six-digit code "
                    '("600519"), a suffixed symbol ("600519.SH", "000001.SZ"), '
                    'or an exchange-prefixed form ("sh600519"). A-shares only.'
                ),
            },
            "days": {
                "type": "integer",
                "description": (
                    "Number of most-recent trading days to return. "
                    f"Default {_DEFAULT_DAYS}, capped at {_MAX_DAYS}."
                ),
                "default": _DEFAULT_DAYS,
            },
        },
        "required": ["code"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Fetch margin-trading rows and return a JSON envelope string.

        Args:
            **kwargs: ``code`` (required, str) and ``days`` (optional int).

        Returns:
            A JSON string. On success:
            ``{"ok": true, "market": "a_share", "source": "eastmoney",
            "data": {"code": str, "rows": [...]}}``. On failure:
            ``{"ok": false, "error": str}``.
        """
        code = _extract_code(kwargs.get("code", ""))
        if code is None:
            return _err(
                "Unsupported symbol: margin trading covers A-shares only "
                "(e.g. 600519.SH or 000001.SZ)."
            )
        days = _clamp_days(kwargs.get("days", _DEFAULT_DAYS))

        try:
            payload = eastmoney_client.get_json(
                _DATACENTER_URL,
                params={
                    "reportName": _REPORT_NAME,
                    "columns": "ALL",
                    "source": "WEB",
                    "filter": f'(SCODE="{code}")',
                    "sortColumns": "DATE",
                    "sortTypes": "-1",
                    "pageNumber": "1",
                    "pageSize": str(days),
                },
            )
        except Exception as exc:  # noqa: BLE001 - surface any provider failure as envelope
            logger.warning("eastmoney margin fetch failed for %s: %s", code, exc)
            return _err(f"Eastmoney margin request failed: {exc}")

        result = payload.get("result") if isinstance(payload, dict) else None
        data = result.get("data") if isinstance(result, dict) else None
        if not isinstance(data, list) or not data:
            return _err(f"No margin-trading data returned for {code}.")

        rows = [_normalize_row(item) for item in data if isinstance(item, dict)]
        rows = rows[:days]

        return json.dumps(
            {
                "ok": True,
                "market": "a_share",
                "source": "eastmoney",
                "data": {"code": code, "rows": rows},
            },
            ensure_ascii=False,
        )
