"""Read-only sector / concept board tool backed by the Eastmoney client.

Eastmoney publishes a free, no-auth board taxonomy that groups A-shares into
industry sectors (行业板块) and thematic concept boards (概念板块). This tool
exposes two read-only views over that taxonomy:

* **Membership** — given a stock ``code``, list the industry / concept boards
  that stock belongs to. Served by the push2 ``slist`` endpoint, addressed by
  the same ``secid`` scheme used for klines.
* **Ranking** — with ``mode="ranking"``, rank the industry boards themselves by
  intraday percent change. Served by the push2 ``clist`` endpoint over the
  industry-board universe (``fs=m:90+t:2``).

Both endpoints route through :mod:`backtest.loaders.eastmoney_client` so every
request goes through the shared per-host throttle (Eastmoney rate-limits by IP
and bans bursting clients). Membership covers A-shares (``.SH`` / ``.SZ`` /
``.BJ``); ranking is the A-share board universe.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders.eastmoney_client import get_json, resolve_secid
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney push2 board endpoints. ``slist`` returns the boards one stock
# belongs to; ``clist`` enumerates / ranks a board universe.
_MEMBERSHIP_URL = "https://push2.eastmoney.com/api/qt/slist/get"
_RANKING_URL = "https://push2.eastmoney.com/api/qt/clist/get"

# Field selectors. f12 = board/security code, f14 = name, f3 = change percent,
# f2 = latest price, f104/f105 = up/down constituent counts (ranking only).
_MEMBERSHIP_FIELDS = "f12,f13,f14,f3,f2"
_RANKING_FIELDS = "f12,f14,f3,f2,f104,f105,f128,f140"

# Industry-board universe selector for the ranking view (m:90 = board market,
# t:2 = industry board sub-type). Sort by f3 (change percent), descending.
_RANKING_FS = "m:90+t:2"

# Defensive caps so a payload can never blow up the LLM context.
_MAX_RANKING = 100
_DEFAULT_RANKING = 30
_VALID_MODES = ("membership", "ranking")


def _error(message: str) -> str:
    """Build the failure envelope as a JSON string.

    Args:
        message: Human-readable error description.

    Returns:
        A ``{"ok": false, "error": ...}`` JSON string.
    """
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _as_float(value: Any) -> float | None:
    """Coerce an Eastmoney numeric cell to ``float``, or ``None`` if unusable.

    Eastmoney emits ``"-"`` for missing numerics; those map to ``None``.

    Args:
        value: Raw cell value from a push2 row.

    Returns:
        The float value, or ``None`` when the cell is missing / non-numeric.
    """
    if value is None or value == "-" or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_membership_row(row: Any) -> dict[str, Any] | None:
    """Parse one ``slist`` diff row into a labelled board-membership dict.

    Args:
        row: One element of ``data.diff`` (a dict keyed by ``f12``/``f14``/...).

    Returns:
        A dict ``{board_code, board_name, change_pct, price}``, or ``None`` when
        the row lacks an identifiable board code/name.
    """
    if not isinstance(row, dict):
        return None
    board_code = row.get("f12")
    board_name = row.get("f14")
    if not board_code or not board_name:
        return None
    return {
        "board_code": str(board_code),
        "board_name": str(board_name),
        "change_pct": _as_float(row.get("f3")),
        "price": _as_float(row.get("f2")),
    }


def _parse_ranking_row(row: Any) -> dict[str, Any] | None:
    """Parse one ``clist`` diff row into a labelled board-ranking dict.

    Args:
        row: One element of ``data.diff`` (a dict keyed by ``f12``/``f14``/...).

    Returns:
        A dict ``{board_code, board_name, change_pct, index, leader, up_count,
        down_count}``, or ``None`` when the row lacks a board code/name.
    """
    if not isinstance(row, dict):
        return None
    board_code = row.get("f12")
    board_name = row.get("f14")
    if not board_code or not board_name:
        return None
    leader = row.get("f140")
    return {
        "board_code": str(board_code),
        "board_name": str(board_name),
        "change_pct": _as_float(row.get("f3")),
        "index": _as_float(row.get("f2")),
        "up_count": _as_float(row.get("f104")),
        "down_count": _as_float(row.get("f105")),
        "leader": str(leader) if leader and leader != "-" else None,
    }


def _diff_rows(payload: Any) -> list:
    """Extract the ``data.diff`` row list from a push2 payload, defensively.

    Args:
        payload: Decoded JSON from a push2 board endpoint.

    Returns:
        The list of diff rows, or ``[]`` when the payload carries none.
    """
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return []
    diff = data.get("diff")
    if isinstance(diff, dict):
        # Some push2 responses key diff rows by string index instead of a list.
        return list(diff.values())
    if isinstance(diff, list):
        return diff
    return []


def _fetch_membership(code: str) -> str:
    """Fetch the industry / concept boards one stock belongs to.

    Args:
        code: Vibe-Trading A-share symbol (e.g. ``"600519.SH"``).

    Returns:
        A JSON envelope string with the resolved boards, or an error envelope
        when the symbol is unresolvable or the request fails.
    """
    secid = resolve_secid(code)
    if secid is None:
        return _error(f"unresolvable symbol: {code}")

    try:
        payload = get_json(
            _MEMBERSHIP_URL,
            params={
                "secid": secid,
                "spt": "3",
                "pi": "0",
                "pz": "100",
                "fields": _MEMBERSHIP_FIELDS,
                "fltt": "2",
                "po": "1",
            },
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean error envelope
        logger.warning("sector membership fetch failed for %s: %s", code, exc)
        return _error(f"membership request failed: {exc}")

    boards = [
        parsed
        for parsed in (_parse_membership_row(r) for r in _diff_rows(payload))
        if parsed is not None
    ]
    envelope = {
        "ok": True,
        "market": "stock",
        "source": "eastmoney",
        "mode": "membership",
        "data": {"code": code, "secid": secid, "boards": boards},
    }
    return json.dumps(envelope, ensure_ascii=False)


def _fetch_ranking(limit: int) -> str:
    """Fetch the industry-board ranking by intraday percent change.

    Args:
        limit: Number of top boards to keep (already validated and capped).

    Returns:
        A JSON envelope string with the ranked boards, or an error envelope when
        the request fails.
    """
    try:
        payload = get_json(
            _RANKING_URL,
            params={
                "fs": _RANKING_FS,
                "fields": _RANKING_FIELDS,
                "pn": "1",
                "pz": str(limit),
                "po": "1",
                "fid": "f3",
                "fltt": "2",
            },
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean error envelope
        logger.warning("sector ranking fetch failed: %s", exc)
        return _error(f"ranking request failed: {exc}")

    boards = [
        parsed
        for parsed in (_parse_ranking_row(r) for r in _diff_rows(payload))
        if parsed is not None
    ]
    if len(boards) > limit:
        boards = boards[:limit]
    envelope = {
        "ok": True,
        "market": "stock",
        "source": "eastmoney",
        "mode": "ranking",
        "data": {"boards": boards},
    }
    return json.dumps(envelope, ensure_ascii=False)


class SectorInfoTool(BaseTool):
    """Look up sector / concept board membership for a stock, or rank boards."""

    name = "get_sector_info"
    description = (
        "Look up Chinese A-share sector / concept board info via Eastmoney "
        "(free, no auth). Two modes: (1) membership — given a stock 'code' "
        "(e.g. 600519.SH / 000001.SZ / .BJ), list the industry and concept "
        "boards it belongs to; (2) ranking — set mode='ranking' to rank "
        "industry boards by today's percent change (with up/down constituent "
        "counts and the leading stock). Use this to map a stock to its sectors "
        "or to see which sectors are hot today. Market: A-share stocks. "
        'Example: {"code": "600519.SH"} or {"mode": "ranking", "limit": 20}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "A-share stock symbol with market suffix, e.g. '600519.SH', "
                    "'000001.SZ', '430139.BJ'. Required when mode='membership' "
                    "(the default); ignored when mode='ranking'."
                ),
            },
            "mode": {
                "type": "string",
                "enum": ["membership", "ranking"],
                "description": (
                    "'membership' (default) lists the boards a stock belongs to "
                    "and requires 'code'. 'ranking' ranks industry boards by "
                    "today's percent change and ignores 'code'."
                ),
                "default": "membership",
            },
            "limit": {
                "type": "integer",
                "description": (
                    "For mode='ranking', number of top boards to return "
                    f"(1-{_MAX_RANKING}). Ignored for mode='membership'. "
                    f"Default {_DEFAULT_RANKING}."
                ),
                "default": _DEFAULT_RANKING,
            },
        },
        "required": [],
    }

    def execute(self, **kwargs: Any) -> str:
        """Dispatch to the membership or ranking view and return a JSON envelope.

        Args:
            **kwargs: ``mode`` ("membership"|"ranking", default "membership"),
                ``code`` (str, required for membership), ``limit`` (int, default
                30, used by ranking).

        Returns:
            A JSON string ``{"ok": true, "market": "stock", "source":
            "eastmoney", "mode": ..., "data": {...}}`` on success, or
            ``{"ok": false, "error": ...}`` on a validation / request failure.
        """
        mode = kwargs.get("mode", "membership")
        if mode not in _VALID_MODES:
            return _error(f"mode must be one of {list(_VALID_MODES)}")

        if mode == "ranking":
            limit = kwargs.get("limit", _DEFAULT_RANKING)
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                return _error("limit must be a positive integer")
            return _fetch_ranking(min(limit, _MAX_RANKING))

        code = kwargs.get("code")
        if not isinstance(code, str) or not code.strip():
            return _error("code must be a non-empty string for mode='membership'")
        return _fetch_membership(code.strip())
