"""Read-only full-market screener backed by the Eastmoney client.

Eastmoney publishes a free, no-auth full-market quote list via the push2
``clist`` endpoint. Given a market universe selector (``fs``) it returns one row
per listed instrument with the latest price plus the common ranking metrics —
percent change, traded volume, turnover value (amount) and turnover rate — and
serves them already sorted server-side by a chosen field (``fid``). This tool
wraps that endpoint to answer "what are today's biggest movers / most-traded
names" questions across A-share, US and Hong Kong markets without writing raw
provider scripts.

Every request routes through :mod:`backtest.loaders.eastmoney_client` so it
goes through the shared per-host throttle (Eastmoney rate-limits by IP and
temporarily bans bursting clients). The result payload is capped so a full
market list can never blow up the LLM context.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders.eastmoney_client import get_json
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney push2 full-market quote list endpoint.
_CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"

# Per-market universe selectors (``fs``). A-share covers the SH/SZ main+ChiNext
# boards plus the Beijing exchange; US covers NASDAQ/NYSE/AMEX; HK covers the
# main-board and GEM equity markets.
_MARKET_FS: dict[str, str] = {
    "a": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
    "us": "m:105,m:106,m:107",
    "hk": "m:116,m:113,m:114,m:115,m:128",
}

# Sort-key -> Eastmoney field id. f3 = change percent, f5 = traded volume (lots),
# f6 = turnover value / amount (currency), f8 = turnover rate (percent).
_SORT_FID: dict[str, str] = {
    "change_pct": "f3",
    "volume": "f5",
    "amount": "f6",
    "turnover": "f8",
}

# Column selectors requested from the endpoint, in no particular order; values
# are read out by name from each row dict below.
_FIELDS = "f2,f3,f4,f5,f6,f8,f12,f14"

# Defensive caps so a full-market response can never blow up the LLM context.
_MAX_TOP_N = 100
_DEFAULT_TOP_N = 30


def _error(message: str) -> str:
    """Build the failure envelope as a JSON string.

    Args:
        message: Human-readable error description.

    Returns:
        A ``{"ok": false, "error": ...}`` JSON string.
    """
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _num(value: Any) -> float | None:
    """Coerce one Eastmoney numeric cell to ``float``.

    Eastmoney sends ``"-"`` (or sometimes ``-`` as an int sentinel) for cells
    with no value (e.g. a halted name's turnover rate). Those become ``None``
    rather than a misleading zero.

    Args:
        value: Raw cell value from the row dict.

    Returns:
        The value as a float, or ``None`` when it is a sentinel / unparseable.
    """
    if value is None or value == "-":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _shape_row(raw: Any) -> dict[str, Any] | None:
    """Shape one clist row dict into a normalized screener record.

    Args:
        raw: One element of ``data.diff`` (a per-instrument dict keyed by the
            Eastmoney field ids requested in :data:`_FIELDS`).

    Returns:
        A dict ``{code, name, price, change_pct, change, volume, amount,
        turnover_rate}``, or ``None`` when the row carries no usable code.
    """
    if not isinstance(raw, dict):
        return None
    code = raw.get("f12")
    if not code:
        return None
    return {
        "code": str(code),
        "name": str(raw.get("f14", "")),
        "price": _num(raw.get("f2")),
        "change_pct": _num(raw.get("f3")),
        "change": _num(raw.get("f4")),
        "volume": _num(raw.get("f5")),
        "amount": _num(raw.get("f6")),
        "turnover_rate": _num(raw.get("f8")),
    }


def _screen_market(market: str, *, sort_by: str, top_n: int) -> list[dict[str, Any]]:
    """Fetch the ``top_n`` instruments of ``market`` ranked by ``sort_by``.

    Args:
        market: One of :data:`_MARKET_FS` keys (``a`` / ``us`` / ``hk``).
        sort_by: One of :data:`_SORT_FID` keys.
        top_n: Number of rows to request (already validated/capped).

    Returns:
        A list of shaped row dicts (already server-side sorted descending),
        possibly empty when the payload carries no rows.

    Raises:
        requests.RequestException: Network failure, propagated to the caller.
        requests.HTTPError: Non-2xx response status.
        ValueError: Body is not valid JSON.
    """
    payload = get_json(
        _CLIST_URL,
        params={
            "pn": "1",
            "pz": str(top_n),
            "po": "1",  # descending
            "fid": _SORT_FID[sort_by],
            "fs": _MARKET_FS[market],
            "fields": _FIELDS,
        },
    )
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return []
    diff = data.get("diff")
    # push2 clist returns ``diff`` either as a list or, on some hosts, a dict
    # keyed by index; normalize both to a list of row dicts.
    if isinstance(diff, dict):
        diff = list(diff.values())
    if not isinstance(diff, list):
        return []

    rows: list[dict[str, Any]] = []
    for raw in diff:
        shaped = _shape_row(raw)
        if shaped is not None:
            rows.append(shaped)
    return rows[:top_n]


class MarketScreenerTool(BaseTool):
    """Rank a full market's listed instruments by change%, volume or turnover."""

    name = "screen_market"
    description = (
        "Screen a whole market's listed instruments and return the top names "
        "ranked by a chosen metric: percent change, traded volume, turnover "
        "value (amount) or turnover rate. Use this to find today's biggest "
        "movers or most-actively-traded names without fetching every symbol. "
        "Markets: A-share ('a'), US ('us'), Hong Kong ('hk'). "
        'Example: {"market": "a", "sort_by": "change_pct", "top_n": 20}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "market": {
                "type": "string",
                "enum": ["a", "us", "hk"],
                "description": (
                    "Market universe to screen: 'a' = China A-share "
                    "(SH/SZ/ChiNext/Beijing), 'us' = US (NASDAQ/NYSE/AMEX), "
                    "'hk' = Hong Kong."
                ),
            },
            "sort_by": {
                "type": "string",
                "enum": ["change_pct", "volume", "amount", "turnover"],
                "description": (
                    "Ranking metric, sorted descending: 'change_pct' = percent "
                    "change, 'volume' = traded volume, 'amount' = turnover value "
                    "in currency, 'turnover' = turnover rate (percent)."
                ),
                "default": "change_pct",
            },
            "top_n": {
                "type": "integer",
                "description": (
                    f"Number of top-ranked instruments to return (1-{_MAX_TOP_N})."
                ),
                "default": _DEFAULT_TOP_N,
            },
        },
        "required": ["market"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Validate inputs, screen the market, and return a JSON envelope.

        Args:
            **kwargs: ``market`` (str, required, one of a/us/hk), ``sort_by``
                (str, default "change_pct"), ``top_n`` (int, default 30).

        Returns:
            A JSON string ``{"ok": true, "market": <market>, "source":
            "eastmoney", "data": {"market": <market>, "sort_by": <sort_by>,
            "rows": [...]}}`` on success, or ``{"ok": false, "error": ...}`` on
            a validation or request failure. The row list nests under ``data``
            so the envelope matches every other tool's ``data:{...}`` shape.
        """
        market = kwargs.get("market")
        if not isinstance(market, str) or market not in _MARKET_FS:
            return _error(f"market must be one of {list(_MARKET_FS)}")

        sort_by = kwargs.get("sort_by", "change_pct")
        if sort_by not in _SORT_FID:
            return _error(f"sort_by must be one of {list(_SORT_FID)}")

        top_n = kwargs.get("top_n", _DEFAULT_TOP_N)
        if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
            return _error("top_n must be a positive integer")
        top_n = min(top_n, _MAX_TOP_N)

        try:
            rows = _screen_market(market, sort_by=sort_by, top_n=top_n)
        except Exception as exc:  # noqa: BLE001 - surface as the error envelope
            logger.warning("market screen failed for %s/%s: %s", market, sort_by, exc)
            return _error(str(exc))

        envelope = {
            "ok": True,
            "market": market,
            "source": "eastmoney",
            "data": {
                "market": market,
                "sort_by": sort_by,
                "rows": rows,
            },
        }
        return json.dumps(envelope, ensure_ascii=False)
