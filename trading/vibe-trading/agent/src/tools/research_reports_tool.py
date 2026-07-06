"""Read-only tool: sell-side research reports + consensus EPS for A-shares.

Two free, no-auth disclosure feeds are stitched into one envelope:

* **Eastmoney reportapi** publishes the rolling list of broker research reports
  for a mainland A-share: report title, issuing brokerage, analyst, publish
  date, the broker's rating label, and that broker's per-year EPS / PE
  forecasts. This is the primary feed and drives the ``reports`` block.
* **THS** (同花顺, ``basic.10jqka.com.cn``) publishes a market *consensus* EPS
  forecast (the mean of analyst estimates) per forward fiscal year. THS rejects
  the bare requests User-Agent, so the call carries a desktop UA and a Referer
  and routes through the frozen IP-throttled HTTP layer under its own ``ths``
  host bucket. The consensus feed is best-effort: a THS failure degrades the
  ``consensus_eps`` block to an empty list and never aborts the report fetch.

Both feeds cover mainland A-shares only (``.SH`` / ``.SZ`` / ``.BJ``); any other
market returns an error envelope. Every outbound GET goes through the project's
throttled clients so the tool never hits a host un-throttled and never
re-implements provider plumbing.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders._http import (
    DEFAULT_USER_AGENT,
    resolve_min_interval,
    throttled_get,
)
from backtest.loaders.eastmoney_client import get_json, resolve_secid
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney research-report list endpoint. qType=0 selects individual-stock
# reports; the response carries a ``data`` array of one row per report.
_REPORT_LIST_URL = "https://reportapi.eastmoney.com/report/list"

# THS consensus-forecast endpoint. Returns per-forward-year mean analyst EPS.
_THS_CONSENSUS_URL = "https://basic.10jqka.com.cn/api/stock/profit_forecast/"
_THS_HOST_KEY = "ths"
_THS_MIN_INTERVAL_ENV = "VIBE_TRADING_THS_MIN_INTERVAL"
_THS_DEFAULT_MIN_INTERVAL = 1.0
_THS_TIMEOUT_S = 15.0

# A-share exchange suffixes these disclosures cover.
_A_SHARE_SUFFIXES = ("SH", "SZ", "BJ")

# Hard caps so a long history cannot bloat the payload.
_DEFAULT_LIMIT = 20
_MAX_LIMIT = 50


class ResearchReportsTool(BaseTool):
    """Fetch A-share sell-side research reports plus market consensus EPS."""

    name = "get_research_reports"
    description = (
        "Fetch mainland A-share sell-side research coverage: recent broker "
        "research reports (title, brokerage, analyst, publish date, rating) with "
        "each broker's per-year EPS and PE forecasts from Eastmoney, plus the "
        "market consensus (mean) EPS forecast per forward fiscal year from THS "
        "(同花顺). Markets: China A-shares only (.SH / .SZ / .BJ). "
        'Example: {"code": "600519.SH", "limit": 10}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "A-share symbol in <code>.<exchange> form, exchange suffix one "
                    "of SH / SZ / BJ (e.g. '600519.SH', '000001.SZ', '830799.BJ')."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    "Maximum number of most-recent research reports to return "
                    f"(1-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}."
                ),
                "default": _DEFAULT_LIMIT,
            },
        },
        "required": ["code"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Resolve the symbol, fetch reports + consensus, return a JSON envelope.

        Args:
            **kwargs: ``code`` (required A-share symbol) and optional ``limit``
                (report count cap).

        Returns:
            A JSON string envelope. On success:
            ``{"ok": true, "market": "CN", "source": "eastmoney+ths",
            "data": {"code", "reports": [...], "consensus_eps": [...]}}``.
            On failure: ``{"ok": false, "error": str}``.
        """
        code = kwargs.get("code")
        if not isinstance(code, str) or not code.strip():
            return _error("'code' is required and must be a non-empty A-share symbol")
        code = code.strip().upper()

        suffix = code.rpartition(".")[2]
        if suffix not in _A_SHARE_SUFFIXES:
            return _error(
                f"research reports are China A-share only (.SH/.SZ/.BJ); got '{code}'"
            )
        if resolve_secid(code) is None:
            return _error(f"could not resolve A-share symbol '{code}'")

        limit = _clamp_limit(kwargs.get("limit", _DEFAULT_LIMIT))

        try:
            payload = get_json(
                _REPORT_LIST_URL,
                params={
                    "code": _bare_code(code),
                    "qType": "0",
                    "pageSize": str(limit),
                    "pageNo": "1",
                },
            )
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure as envelope
            return _error(f"eastmoney report list request failed: {exc}")

        reports = _parse_reports(payload)

        # Consensus EPS is best-effort: a THS outage must not sink the reports.
        consensus_eps = _fetch_consensus_eps(code)

        if not reports and not consensus_eps:
            return _error(f"no research coverage found for '{code}'")

        return json.dumps(
            {
                "ok": True,
                "market": "CN",
                "source": "eastmoney+ths",
                "data": {
                    "code": code,
                    "reports": reports[:limit],
                    "consensus_eps": consensus_eps,
                },
            },
            ensure_ascii=False,
        )


def _bare_code(code: str) -> str:
    """Return the numeric stock code without its exchange suffix."""
    return code.rpartition(".")[0]


def _clamp_limit(value: Any) -> int:
    """Coerce a requested report count into the supported ``1.._MAX_LIMIT`` range."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    return max(1, min(n, _MAX_LIMIT))


def _parse_reports(payload: Any) -> list[dict]:
    """Extract per-report records from an Eastmoney reportapi payload.

    Args:
        payload: Decoded reportapi JSON; rows live under the ``data`` array.

    Returns:
        A list of normalized report dicts (newest first as served), empty when
        the payload carries no usable rows.
    """
    if not isinstance(payload, dict):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []

    reports: list[dict] = []
    for row in rows:
        record = _normalize_report(row)
        if record is not None:
            reports.append(record)
    return reports


def _normalize_report(row: Any) -> dict | None:
    """Map one raw reportapi row to our report record, or ``None`` if unusable.

    A row carrying neither a title nor a publish date holds no signal and is
    dropped; a single bad row never aborts the batch.

    Args:
        row: One element of the reportapi ``data`` array.

    Returns:
        ``{title, brokerage, analyst, publish_date, rating, eps_forecast,
        pe_forecast}`` or ``None``.
    """
    if not isinstance(row, dict):
        return None
    title = _clean_text(row.get("title"))
    publish_date = _clean_date(row.get("publishDate"))
    if title is None and publish_date is None:
        return None
    return {
        "title": title,
        "brokerage": _clean_text(row.get("orgSName")) or _clean_text(row.get("orgName")),
        "analyst": _clean_text(row.get("researcher")),
        "publish_date": publish_date,
        "rating": _clean_text(row.get("emRatingName")) or _clean_text(row.get("sRatingName")),
        "eps_forecast": {
            "this_year": _to_number(row.get("predictThisYearEps")),
            "next_year": _to_number(row.get("predictNextYearEps")),
        },
        "pe_forecast": {
            "this_year": _to_number(row.get("predictThisYearPe")),
            "next_year": _to_number(row.get("predictNextYearPe")),
        },
    }


def _fetch_consensus_eps(code: str) -> list[dict]:
    """Fetch THS consensus (mean) EPS forecast per forward fiscal year.

    Best-effort: any network/parse failure is logged and degraded to an empty
    list so the primary report fetch is never aborted by a THS outage. THS
    rejects the bare requests UA, so the call presents a desktop browser UA and
    a Referer and is spaced under its own ``ths`` host bucket.

    Args:
        code: A-share symbol such as ``"600519.SH"``.

    Returns:
        A list of ``{fiscal_year, consensus_eps}`` dicts ordered as served,
        empty when THS returns nothing usable or the request fails.
    """
    try:
        response = throttled_get(
            _THS_CONSENSUS_URL,
            host_key=_THS_HOST_KEY,
            min_interval=resolve_min_interval(
                _THS_MIN_INTERVAL_ENV, _THS_DEFAULT_MIN_INTERVAL
            ),
            params={"code": _bare_code(code)},
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Referer": "https://basic.10jqka.com.cn/",
            },
            timeout=_THS_TIMEOUT_S,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:  # noqa: BLE001 - consensus is best-effort
        logger.warning("ths consensus eps fetch failed for %s: %s", code, exc)
        return []
    return _parse_consensus_eps(payload)


def _parse_consensus_eps(payload: Any) -> list[dict]:
    """Extract per-year consensus EPS rows from a THS forecast payload.

    THS wraps its rows under ``data`` (a list of per-forward-year records, each
    carrying a fiscal year and a mean EPS estimate). Field naming varies, so we
    probe a small set of known key aliases for each value.

    Args:
        payload: Decoded THS JSON.

    Returns:
        A list of ``{fiscal_year, consensus_eps}`` dicts, empty when no usable
        row is present.
    """
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []

    out: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        year = _clean_text(_first(row, ("year", "fiscal_year", "report_year")))
        eps = _to_number(_first(row, ("eps", "avg_eps", "predict_eps", "forecast_eps")))
        if year is None and eps is None:
            continue
        out.append({"fiscal_year": year, "consensus_eps": eps})
    return out


def _first(row: dict, keys: tuple[str, ...]) -> Any:
    """Return the first present, non-empty value among ``keys`` in ``row``."""
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def _clean_text(value: Any) -> str | None:
    """Trim a string cell, or ``None`` when absent/blank/non-string."""
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed or None


def _clean_date(value: Any) -> str | None:
    """Trim a timestamp cell to its ``YYYY-MM-DD`` date, or ``None``."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().split(" ", 1)[0]


def _to_number(value: Any) -> float | None:
    """Coerce a cell to ``float``, or ``None`` when absent/non-numeric."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _error(message: str) -> str:
    """Render a failure envelope as a JSON string."""
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
