"""Lockup-expiry (限售解禁) tool backed by the Eastmoney datacenter API.

Chinese A-share restricted shares come off lockup on scheduled dates; a large
upcoming unlock can pressure a stock as newly tradable supply hits the market.
This tool surfaces both the historical unlock schedule and the upcoming window
(default 90 days) for a single A-share code, or a market-wide upcoming-unlock
calendar when no code is given.

All requests reuse the shared, per-host-throttled Eastmoney client
(:mod:`backtest.loaders.eastmoney_client`); Eastmoney rate-limits by source IP
and temporarily bans bursting callers, so this module never issues an
un-throttled GET. It only knows Eastmoney's ``RPT_LIFT_STOCK`` report layout,
not any loader's DataFrame conventions.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

from backtest.loaders import eastmoney_client
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney datacenter report endpoint + the restricted-share unlock report.
_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_REPORT_NAME = "RPT_LIFT_STOCK"

# Per-bar columns requested from the report, in our display order.
_COLUMNS = (
    "SECURITY_CODE,SECURITY_NAME_ABBR,FREE_DATE,FREE_SHARES_TYPE,"
    "FREE_SHARES,CURRENT_FREE_SHARES,ABLE_FREE_SHARES,LIFT_MARKET_CAP,"
    "FREE_RATIO,TOTAL_RATIO"
)

# Defaults / hard caps. Eastmoney's pageSize is generous, but we cap the
# returned payload so a market-wide query can never flood the agent context.
_DEFAULT_HORIZON_DAYS = 90
_MAX_HORIZON_DAYS = 365
_MAX_RECORDS = 200
_PAGE_SIZE = 200


def _today() -> date:
    """Return today's date (indirection kept for test monkeypatching)."""
    return datetime.now().date()


def _compact(d: date) -> str:
    """Format a date as Eastmoney's ``YYYY-MM-DD`` filter literal."""
    return d.strftime("%Y-%m-%d")


def _clamp_horizon(horizon_days: Any) -> int:
    """Coerce a caller horizon into ``[1, _MAX_HORIZON_DAYS]`` days.

    Args:
        horizon_days: Caller-supplied value of any type.

    Returns:
        A valid integer horizon, falling back to the default on bad input.
    """
    try:
        value = int(horizon_days)
    except (TypeError, ValueError):
        return _DEFAULT_HORIZON_DAYS
    if value < 1:
        return 1
    return min(value, _MAX_HORIZON_DAYS)


def _normalize_code(code: str) -> str | None:
    """Reduce a Vibe-Trading symbol to its bare 6-digit A-share code.

    Accepts ``"600519"``, ``"600519.SH"``, ``"000001.SZ"`` and similar; the
    Eastmoney report keys on the bare numeric code regardless of exchange.

    Args:
        code: Caller-supplied symbol.

    Returns:
        The bare 6-digit code, or ``None`` when it is not a 6-digit A-share code.
    """
    bare = code.strip().split(".", 1)[0]
    if len(bare) == 6 and bare.isdigit():
        return bare
    return None


def _build_filter(code: str | None, start: date, end: date) -> str:
    """Compose the Eastmoney ``filter`` clause for the query.

    Args:
        code: Bare 6-digit code, or ``None`` for a market-wide calendar.
        start: Inclusive earliest unlock date for the upcoming window.
        end: Inclusive latest unlock date for the upcoming window.

    Returns:
        The Eastmoney filter expression string.
    """
    if code is not None:
        # Whole history for one code: no date bound, report sorts by date.
        return f'(SECURITY_CODE="{code}")'
    return f"(FREE_DATE>='{_compact(start)}')(FREE_DATE<='{_compact(end)}')"


def _select_sort(code: str | None) -> tuple[str, str]:
    """Pick sort column + direction for the query.

    Single-code history reads newest-first; the market calendar reads
    soonest-first so the nearest unlocks lead.
    """
    if code is not None:
        return "FREE_DATE", "-1"
    return "FREE_DATE", "1"


def _to_float(value: Any) -> float | None:
    """Best-effort float coercion; ``None`` for missing/garbage values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _shape_record(raw: Any) -> dict[str, Any] | None:
    """Project one Eastmoney report row into our compact record shape.

    Args:
        raw: One element of ``result.data``.

    Returns:
        A normalized record dict, or ``None`` when the row is unusable.
    """
    if not isinstance(raw, dict):
        return None
    code = raw.get("SECURITY_CODE")
    free_date = raw.get("FREE_DATE")
    if not code or not free_date:
        return None
    return {
        "code": str(code),
        "name": raw.get("SECURITY_NAME_ABBR"),
        "free_date": str(free_date)[:10],
        "share_type": raw.get("FREE_SHARES_TYPE"),
        "free_shares": _to_float(raw.get("FREE_SHARES")),
        "able_free_shares": _to_float(raw.get("ABLE_FREE_SHARES")),
        "lift_market_cap": _to_float(raw.get("LIFT_MARKET_CAP")),
        "free_ratio": _to_float(raw.get("FREE_RATIO")),
        "total_ratio": _to_float(raw.get("TOTAL_RATIO")),
    }


def _extract_rows(payload: Any) -> list[dict]:
    """Pull the ``result.data`` list out of a datacenter payload.

    Args:
        payload: Decoded JSON from the datacenter endpoint.

    Returns:
        The raw record list, or an empty list when absent.
    """
    if not isinstance(payload, dict):
        return []
    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    data = result.get("data")
    return data if isinstance(data, list) else []


def _fetch_lockups(code: str | None, horizon_days: int) -> list[dict]:
    """Fetch and normalize lockup-expiry records from Eastmoney.

    Args:
        code: Bare 6-digit code, or ``None`` for a market-wide calendar.
        horizon_days: Upcoming-window length in days (used only when ``code``
            is ``None``).

    Returns:
        Normalized records (capped at :data:`_MAX_RECORDS`).

    Raises:
        requests.RequestException: Network failure from the shared client.
        requests.HTTPError: Non-2xx response status.
        ValueError: Body is not valid JSON.
    """
    start = _today()
    end = start + timedelta(days=horizon_days)
    sort_column, sort_type = _select_sort(code)

    payload = eastmoney_client.get_json(
        _DATACENTER_URL,
        params={
            "reportName": _REPORT_NAME,
            "columns": _COLUMNS,
            "filter": _build_filter(code, start, end),
            "sortColumns": sort_column,
            "sortTypes": sort_type,
            "pageNumber": "1",
            "pageSize": str(_PAGE_SIZE),
            "source": "WEB",
            "client": "WEB",
        },
    )

    records: list[dict] = []
    for raw in _extract_rows(payload):
        shaped = _shape_record(raw)
        if shaped is not None:
            records.append(shaped)
        if len(records) >= _MAX_RECORDS:
            break
    return records


def get_lockup_expiry(code: str | None, horizon_days: int) -> str:
    """Query A-share lockup-expiry (限售解禁) data from Eastmoney.

    Args:
        code: A-share symbol (``"600519"`` or ``"600519.SH"``); ``None`` or
            empty yields a market-wide upcoming-unlock calendar.
        horizon_days: Upcoming-window length in days for the market calendar,
            clamped to ``[1, 365]``.

    Returns:
        A JSON-string envelope ``{"ok": true, "market": "a_share",
        "source": "eastmoney", "data": {...}}`` on success, or
        ``{"ok": false, "error": str}`` on failure.
    """
    horizon = _clamp_horizon(horizon_days)
    bare_code: str | None = None
    if code and code.strip():
        bare_code = _normalize_code(code)
        if bare_code is None:
            return json.dumps(
                {
                    "ok": False,
                    "error": (
                        f"unrecognized A-share code {code!r}; expected a 6-digit "
                        "code such as '600519' or '600519.SH'"
                    ),
                },
                ensure_ascii=False,
            )

    try:
        records = _fetch_lockups(bare_code, horizon)
    except Exception as exc:  # noqa: BLE001 - surface any upstream failure cleanly
        logger.warning("get_lockup_expiry failed (code=%s): %s", bare_code, exc)
        return json.dumps(
            {"ok": False, "error": f"eastmoney lockup query failed: {exc}"},
            ensure_ascii=False,
        )

    scope = "single_code" if bare_code is not None else "market_calendar"
    data: dict[str, Any] = {
        "scope": scope,
        "count": len(records),
        "records": records,
    }
    if bare_code is not None:
        data["code"] = bare_code
    else:
        data["horizon_days"] = horizon
        data["as_of"] = _compact(_today())
    if len(records) >= _MAX_RECORDS:
        data["truncated"] = True

    return json.dumps(
        {"ok": True, "market": "a_share", "source": "eastmoney", "data": data},
        ensure_ascii=False,
    )


class LockupExpiryTool(BaseTool):
    """Surface Chinese A-share restricted-share unlock (限售解禁) schedules."""

    name = "get_lockup_expiry"
    description = (
        "Fetch Chinese A-share lockup-expiry (restricted-share unlock, 限售解禁) "
        "data from Eastmoney. Pass a 6-digit A-share code (e.g. '600519' or "
        "'600519.SH') to get that stock's full historical unlock schedule, or "
        "omit the code to get a market-wide calendar of upcoming unlocks within "
        "the next horizon_days. A large near-term unlock adds tradable supply "
        "and often pressures the stock. Example: "
        '{"code": "600519.SH"} or {"horizon_days": 30}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "A-share symbol: 6-digit code, optionally suffixed "
                    "(e.g. '600519', '600519.SH', '000001.SZ'). Omit for a "
                    "market-wide upcoming-unlock calendar."
                ),
            },
            "horizon_days": {
                "type": "integer",
                "description": (
                    "Length of the upcoming-unlock window in days for the "
                    "market-wide calendar; clamped to [1, 365]. Ignored when "
                    "code is given (full history is returned instead)."
                ),
                "default": _DEFAULT_HORIZON_DAYS,
            },
        },
        "required": [],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Execute the lockup-expiry query and return a JSON envelope."""
        return get_lockup_expiry(
            kwargs.get("code"),
            kwargs.get("horizon_days", _DEFAULT_HORIZON_DAYS),
        )
