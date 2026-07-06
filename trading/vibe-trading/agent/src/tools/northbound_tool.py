"""Northbound (Stock-Connect) net-flow tool backed by Eastmoney push2his.

Northbound flow is the net capital moving from Hong Kong into mainland China
A-shares through the Shanghai/Shenzhen Stock-Connect channels ("沪股通" and
"深股通"). Eastmoney publishes this as a free, no-auth time series through its
``push2his`` ``kamt`` (kapital-amount) endpoints. Every request routes through
the shared throttled Eastmoney client so we honor Eastmoney's per-IP rate limit
and never burst the host into a temporary ban.

This tool is read-only: it fetches the latest realtime net inflow plus a short
recent-daily history and returns them in the standard JSON envelope. It performs
no order placement and reaches no live trading endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders.eastmoney_client import get_json
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney kamt (Stock-Connect capital) endpoints. ``kamt/get`` carries the
# realtime snapshot for both connect channels; ``kamt.kline/get`` carries the
# daily net-inflow history.
_REALTIME_URL = "https://push2.eastmoney.com/api/qt/kamt/get"
_HISTORY_URL = "https://push2his.eastmoney.com/api/qt/kamt.kline/get"

# Default and ceiling for the recent-daily window. The history endpoint returns
# at most a few years of daily points; we cap to keep the payload bounded.
_DEFAULT_LOOKBACK_DAYS = 30
_MAX_LOOKBACK_DAYS = 250

# Realtime snapshot field selectors. Eastmoney's kamt realtime payload nests the
# two channels under ``data`` with ``s2n`` (south-to-north net inflow) figures
# per channel: ``hk2sh`` (Shanghai-Connect) and ``hk2sz`` (Shenzhen-Connect).
_REALTIME_FIELDS = "f1,f2,f3,f4,f51,f52,f54,f56"

# History field selectors: f51 date, f52 Shanghai net inflow, f54 Shenzhen net
# inflow (units: 10k CNY as published by Eastmoney).
_HISTORY_FIELDS1 = "f1,f3"
_HISTORY_FIELDS2 = "f51,f52,f54"


def _coerce_float(value: Any) -> float | None:
    """Coerce a raw Eastmoney numeric cell to ``float`` or ``None``.

    Args:
        value: Raw value from the payload (number, numeric string, or sentinel).

    Returns:
        The parsed float, or ``None`` when the cell is missing or not numeric
        (Eastmoney uses ``"-"`` for an absent figure).
    """
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_realtime(payload: Any) -> dict[str, float | None]:
    """Extract per-channel realtime net inflow from a kamt realtime payload.

    Args:
        payload: Decoded JSON from :data:`_REALTIME_URL`.

    Returns:
        Mapping with ``shanghai_connect``, ``shenzhen_connect`` and ``total``
        net inflow (10k CNY); each value is ``None`` when unavailable.
    """
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return {"shanghai_connect": None, "shenzhen_connect": None, "total": None}

    sh_block = data.get("hk2sh") if isinstance(data.get("hk2sh"), dict) else {}
    sz_block = data.get("hk2sz") if isinstance(data.get("hk2sz"), dict) else {}

    shanghai = _coerce_float(sh_block.get("netBuyAmt"))
    shenzhen = _coerce_float(sz_block.get("netBuyAmt"))
    total: float | None
    if shanghai is None and shenzhen is None:
        total = None
    else:
        total = (shanghai or 0.0) + (shenzhen or 0.0)

    return {
        "shanghai_connect": shanghai,
        "shenzhen_connect": shenzhen,
        "total": total,
    }


def _parse_history_row(raw: str) -> dict[str, Any] | None:
    """Parse one ``kamt.kline`` history row into a daily net-inflow dict.

    Column order follows :data:`_HISTORY_FIELDS2`: date, Shanghai net inflow,
    Shenzhen net inflow.

    Args:
        raw: One comma-joined row string from ``data.klines``.

    Returns:
        A dict ``{trade_date, shanghai_connect, shenzhen_connect, total}``, or
        ``None`` when the row is malformed.
    """
    parts = raw.split(",")
    if len(parts) < 3:
        return None
    shanghai = _coerce_float(parts[1])
    shenzhen = _coerce_float(parts[2])
    if shanghai is None and shenzhen is None:
        total: float | None = None
    else:
        total = (shanghai or 0.0) + (shenzhen or 0.0)
    return {
        "trade_date": parts[0],
        "shanghai_connect": shanghai,
        "shenzhen_connect": shenzhen,
        "total": total,
    }


def _parse_history(payload: Any, lookback_days: int) -> list[dict[str, Any]]:
    """Extract the most recent ``lookback_days`` daily net-inflow rows.

    Args:
        payload: Decoded JSON from :data:`_HISTORY_URL`.
        lookback_days: Number of trailing daily rows to keep.

    Returns:
        Ascending list of daily net-inflow dicts (empty when no rows).
    """
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return []
    klines = data.get("klines")
    if not isinstance(klines, list):
        return []

    rows: list[dict[str, Any]] = []
    for raw in klines:
        if not isinstance(raw, str):
            continue
        parsed = _parse_history_row(raw)
        if parsed is not None:
            rows.append(parsed)
    return rows[-lookback_days:]


def _clamp_lookback(value: Any) -> int:
    """Clamp a requested lookback to ``[1, _MAX_LOOKBACK_DAYS]``.

    Args:
        value: Raw ``lookback_days`` argument (any type the caller supplied).

    Returns:
        A valid lookback day count, defaulting on unparseable input.
    """
    try:
        days = int(value)
    except (TypeError, ValueError):
        return _DEFAULT_LOOKBACK_DAYS
    if days < 1:
        return 1
    if days > _MAX_LOOKBACK_DAYS:
        return _MAX_LOOKBACK_DAYS
    return days


class NorthboundFlowTool(BaseTool):
    """Fetch Northbound (Stock-Connect) net capital flow from Eastmoney."""

    name = "get_northbound_flow"
    description = (
        "MARKET-WIDE Northbound (Stock-Connect / 北向) net capital flow for the "
        "whole mainland China A-share market: the aggregate net inflow from Hong "
        "Kong, split into Shanghai-Connect (沪股通) and Shenzhen-Connect (深股通) "
        "channels (units: 10k CNY), as the latest realtime figure plus a recent "
        "daily history. This is a market-level total, NOT per-stock flow (for a "
        "given symbol's order-bucket inflow use get_fund_flow). Read-only; China "
        "A-share market only. Example: get_northbound_flow(lookback_days=10)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "lookback_days": {
                "type": "integer",
                "description": (
                    "Number of trailing trading days of daily net-inflow history "
                    f"to return, clamped to 1..{_MAX_LOOKBACK_DAYS}."
                ),
                "default": _DEFAULT_LOOKBACK_DAYS,
            },
        },
        "required": [],
    }

    def execute(self, **kwargs: Any) -> str:
        """Fetch realtime + recent-daily Northbound net flow as a JSON envelope.

        Args:
            **kwargs: Accepts ``lookback_days`` (int, default
                :data:`_DEFAULT_LOOKBACK_DAYS`).

        Returns:
            A JSON string envelope ``{"ok": true, "market": "China A",
            "source": "eastmoney", "data": {...}}`` on success, or
            ``{"ok": false, "error": str}`` on failure.
        """
        lookback_days = _clamp_lookback(kwargs.get("lookback_days", _DEFAULT_LOOKBACK_DAYS))

        try:
            realtime_payload = get_json(
                _REALTIME_URL,
                params={"fields": _REALTIME_FIELDS},
            )
            history_payload = get_json(
                _HISTORY_URL,
                params={
                    "fields1": _HISTORY_FIELDS1,
                    "fields2": _HISTORY_FIELDS2,
                    "klt": "101",
                    "lmt": str(_MAX_LOOKBACK_DAYS),
                },
            )
        except Exception as exc:  # noqa: BLE001 - surface as error envelope
            logger.warning("northbound flow fetch failed: %s", exc)
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

        realtime = _parse_realtime(realtime_payload)
        history = _parse_history(history_payload, lookback_days)

        envelope = {
            "ok": True,
            "market": "China A",
            "source": "eastmoney",
            "data": {
                "unit": "10k CNY",
                "lookback_days": lookback_days,
                "realtime": realtime,
                "history": history,
            },
        }
        return json.dumps(envelope, ensure_ascii=False)
