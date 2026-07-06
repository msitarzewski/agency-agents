"""Block-trade (大宗交易) lookup tool backed by the Eastmoney datacenter.

Eastmoney publishes every A-share block trade — negotiated off-book deals struck
at a premium or discount to the close — through its free, no-auth datacenter
report API (``RPT_DATA_BLOCKTRADE``). Each record carries the deal price and
volume, the discount/premium versus that session's close, and the buyer/seller
营业部 ("seats") that booked the trade. Block-trade flow is a watched signal for
institutional accumulation or distribution, so this read-only tool surfaces the
recent record list for a single A-share symbol.

Every request routes through the shared, throttled Eastmoney client
(:func:`backtest.loaders.eastmoney_client.get_json`) because Eastmoney
rate-limits by source IP; this tool never opens its own HTTP session.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

from backtest.loaders.eastmoney_client import get_json, resolve_secid
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney datacenter report endpoint + the block-trade report name.
_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_REPORT_NAME = "RPT_DATA_BLOCKTRADE"

# Report columns we request, mapped to our envelope keys. The report exposes the
# Chinese-named fields below; we never rename them in transit, only on output.
_FIELDS = (
    "TRADE_DATE,SECURITY_CODE,SECURITY_NAME_ABBR,CLOSE_PRICE,DEAL_PRICE,"
    "PREMIUM_RATIO,DEAL_VOLUME,DEAL_AMT,BUYER_NAME,SELLER_NAME"
)

# Bound the request and the returned payload so a wide window cannot blow up the
# context window. Eastmoney paginates; we pull one bounded page.
_MAX_RECORDS = 200
_MAX_DAYS = 365
_DEFAULT_DAYS = 30


def _resolve_code(symbol: str) -> str | None:
    """Validate an A-share symbol and extract its bare 6-digit code.

    The datacenter report filters by the plain ``SECURITY_CODE`` (no market
    prefix), but we route through :func:`resolve_secid` first so only genuine
    A-share symbols (``.SH`` / ``.SZ`` / ``.BJ``) are accepted; block trades do
    not exist for HK/US listings here.

    Args:
        symbol: Symbol such as ``"600519.SH"`` or ``"000001.SZ"``.

    Returns:
        The bare 6-digit code (e.g. ``"600519"``), or ``None`` when the symbol
        is not a resolvable A-share.
    """
    secid = resolve_secid(symbol)
    if not secid or "." not in secid:
        return None
    market = secid.split(".", 1)[0]
    if market not in ("0", "1"):  # 0=SZ/BJ, 1=SH; HK/US are not A-share blocks.
        return None
    code = symbol.rpartition(".")[0].strip().upper()
    return code or None


def _clamp_days(days: Any) -> int:
    """Coerce the ``days`` argument into the supported ``[1, _MAX_DAYS]`` range.

    Args:
        days: Caller-supplied lookback window; may be missing or malformed.

    Returns:
        A bounded integer day count, defaulting to ``_DEFAULT_DAYS``.
    """
    try:
        value = int(days)
    except (TypeError, ValueError):
        return _DEFAULT_DAYS
    if value < 1:
        return 1
    if value > _MAX_DAYS:
        return _MAX_DAYS
    return value


def _date_filter(code: str, start: date, end: date) -> str:
    """Build the report ``filter`` clause for one code over a date window.

    Args:
        code: Bare 6-digit security code.
        start: Inclusive lower bound.
        end: Inclusive upper bound.

    Returns:
        An Eastmoney report filter expression string.
    """
    return (
        f"(SECURITY_CODE=\"{code}\")"
        f"(TRADE_DATE>='{start.isoformat()}')"
        f"(TRADE_DATE<='{end.isoformat()}')"
    )


def _to_float(value: Any) -> float | None:
    """Best-effort float coercion that maps blanks/None to ``None``.

    Args:
        value: Raw report cell value.

    Returns:
        The float value, or ``None`` when the cell is empty or non-numeric.
    """
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Project one raw report row onto our stable, English-keyed shape.

    Args:
        raw: One ``result.data`` element from the datacenter response.

    Returns:
        A normalized record: trade date, deal price/volume/amount, the
        premium-vs-close ratio, and the buyer/seller seat names.
    """
    return {
        "trade_date": raw.get("TRADE_DATE"),
        "name": raw.get("SECURITY_NAME_ABBR"),
        "close_price": _to_float(raw.get("CLOSE_PRICE")),
        "deal_price": _to_float(raw.get("DEAL_PRICE")),
        "premium_ratio": _to_float(raw.get("PREMIUM_RATIO")),
        "deal_volume": _to_float(raw.get("DEAL_VOLUME")),
        "deal_amount": _to_float(raw.get("DEAL_AMT")),
        "buyer_seat": raw.get("BUYER_NAME"),
        "seller_seat": raw.get("SELLER_NAME"),
    }


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    """Pull the data rows out of a datacenter ``result`` envelope.

    Args:
        payload: Decoded JSON from the datacenter endpoint.

    Returns:
        The list of raw row dicts, or an empty list when the payload carries
        no data (an empty window is a valid, non-error result).
    """
    if not isinstance(payload, dict):
        return []
    result = payload.get("result")
    if not isinstance(result, dict):
        return []
    data = result.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


class BlockTradesTool(BaseTool):
    """Recent A-share block trades (大宗交易): price, premium, volume, seats."""

    name = "get_block_trades"
    description = (
        "Fetch recent A-share block trades (大宗交易) for one symbol from the "
        "Eastmoney datacenter: per-deal price, volume, amount, the "
        "premium/discount versus that day's close, and the buyer/seller broker "
        "seats (营业部). Markets: China A-share only (.SH/.SZ/.BJ). Read-only. "
        'Example: get_block_trades(code="600519.SH", days=30).'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "A-share symbol with exchange suffix, e.g. '600519.SH', "
                    "'000001.SZ', or '830799.BJ'."
                ),
            },
            "days": {
                "type": "integer",
                "description": (
                    "Lookback window in calendar days ending today; clamped to "
                    f"[1, {_MAX_DAYS}]."
                ),
                "default": _DEFAULT_DAYS,
            },
        },
        "required": ["code"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Look up block trades for one symbol and return a JSON envelope.

        Args:
            **kwargs: ``code`` (required A-share symbol) and optional ``days``
                lookback window.

        Returns:
            A JSON string. On success:
            ``{"ok": true, "market": "china_a", "source": "eastmoney",
            "data": {"code", "days", "count", "records": [...]}}``. On failure:
            ``{"ok": false, "error": str}``.
        """
        symbol = str(kwargs.get("code") or "").strip()
        if not symbol:
            return json.dumps(
                {"ok": False, "error": "code is required"}, ensure_ascii=False
            )

        code = _resolve_code(symbol)
        if code is None:
            return json.dumps(
                {
                    "ok": False,
                    "error": (
                        f"{symbol!r} is not a resolvable A-share symbol "
                        "(use .SH/.SZ/.BJ)"
                    ),
                },
                ensure_ascii=False,
            )

        days = _clamp_days(kwargs.get("days", _DEFAULT_DAYS))
        end = datetime.now().date()
        start = end - timedelta(days=days - 1)

        try:
            payload = get_json(
                _DATACENTER_URL,
                params={
                    "reportName": _REPORT_NAME,
                    "columns": _FIELDS,
                    "filter": _date_filter(code, start, end),
                    "sortColumns": "TRADE_DATE",
                    "sortTypes": "-1",
                    "pageNumber": "1",
                    "pageSize": str(_MAX_RECORDS),
                    "source": "WEB",
                    "client": "WEB",
                },
            )
        except Exception as exc:  # noqa: BLE001 - surface upstream failure as envelope
            logger.warning("block-trade lookup failed for %s: %s", symbol, exc)
            return json.dumps(
                {"ok": False, "error": f"eastmoney request failed: {exc}"},
                ensure_ascii=False,
            )

        rows = _extract_rows(payload)
        records = [_normalize_record(row) for row in rows[:_MAX_RECORDS]]

        return json.dumps(
            {
                "ok": True,
                "market": "china_a",
                "source": "eastmoney",
                "data": {
                    "code": symbol,
                    "days": days,
                    "count": len(records),
                    "records": records,
                },
            },
            ensure_ascii=False,
        )
