"""Read-only financial-statements tool: three statements + key indicators.

Pulls a single stock's balance sheet, income statement, cash-flow statement, or
key per-period indicators from Eastmoney's free, no-auth datacenter report API,
picking the per-market report dataset from the symbol's market suffix:

* **A-share** (``.SH`` / ``.SZ`` / ``.BJ``) — Eastmoney's A-share F10 report
  datasets (``RPT_F10_FINANCE_*``), filtered on the dotted ``SECUCODE`` (e.g.
  ``600519.SH``). The legacy Sina ``quotes.sina.cn`` company-finance openapi
  returned a graceful-empty masking an upstream failure, so the A-share path now
  shares the Eastmoney transport with US/HK.
* **US** (``.US``) and **Hong Kong** (``.HK``) — Eastmoney's per-market F10
  financial-report datasets, filtered on the bare ``SECURITY_CODE``; ``indicators``
  reads the main-indicator dataset.

All requests go through :func:`backtest.loaders.eastmoney_client.get_json`
(Eastmoney bans bursting clients, so every call is throttled under
``host_key="eastmoney"``).

The tool is read-only and self-contained: ``execute`` returns a JSON-string
envelope and never raises for a recoverable per-request failure — a bad symbol
or a transient HTTP error is reported inside the envelope.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders.eastmoney_client import get_json, resolve_secid
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# --- Eastmoney datacenter report API --------------------------------------

# Eastmoney datacenter report API. The three statements and the main-indicator
# dataset are addressed by report name, which differs by market (A / US / HK).
_EM_REPORT_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

# (market_prefix_group, statement) -> Eastmoney report name. ``a`` covers the
# mainland exchanges (markets 0/1); ``us`` covers 105/106/107; ``hk`` covers 116.
_EM_REPORT_NAME: dict[str, dict[str, str]] = {
    "a": {
        "balance": "RPT_F10_FINANCE_GBALANCE",
        "income": "RPT_F10_FINANCE_GINCOME",
        "cashflow": "RPT_F10_FINANCE_GCASHFLOW",
        "indicators": "RPT_F10_FINANCE_MAINFINADATA",
    },
    "us": {
        "balance": "RPT_USF10_FN_BALANCE",
        "income": "RPT_USF10_FN_INCOME",
        "cashflow": "RPT_USF10_FN_CASHFLOW",
        "indicators": "RPT_USF10_FN_GMAININDICATOR",
    },
    "hk": {
        "balance": "RPT_HKF10_FN_BALANCE",
        "income": "RPT_HKF10_FN_INCOME",
        "cashflow": "RPT_HKF10_FN_CASHFLOW",
        "indicators": "RPT_HKF10_FN_GMAININDICATOR",
    },
}

# Eastmoney mainland A-share markets (SZ/BJ = 0, SH = 1), US markets
# (NASDAQ / NYSE / AMEX), and the HK market.
_EM_A_MARKETS = ("0", "1")
_EM_US_MARKETS = ("105", "106", "107")
_EM_HK_MARKET = "116"

# --- Shared limits / validation ------------------------------------------

_VALID_STATEMENTS = ("balance", "income", "cashflow", "indicators")
_VALID_PERIODS = ("annual", "quarter")

# Defensive caps so a payload can never blow up the LLM context.
_MAX_PERIODS = 40
_MAX_FIELDS_PER_PERIOD = 200


def _error(message: str) -> str:
    """Build the failure envelope as a JSON string.

    Args:
        message: Human-readable error description.

    Returns:
        A ``{"ok": false, "error": ...}`` JSON string.
    """
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _truncate_period(record: dict[str, Any]) -> dict[str, Any]:
    """Cap one period's field count so a single record stays context-safe.

    Args:
        record: A flat period dict (field name -> value).

    Returns:
        A new dict with at most :data:`_MAX_FIELDS_PER_PERIOD` items, preserving
        insertion order. The original is never mutated.
    """
    items = list(record.items())
    if len(items) <= _MAX_FIELDS_PER_PERIOD:
        return dict(items)
    return dict(items[:_MAX_FIELDS_PER_PERIOD])


def _cap_periods(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the most recent periods, each truncated to a safe field count.

    Args:
        periods: Period records as returned by the provider parser.

    Returns:
        A new list of at most :data:`_MAX_PERIODS` field-capped records.
    """
    capped = periods[:_MAX_PERIODS]
    return [_truncate_period(record) for record in capped]


def _eastmoney_market_group(secid: str) -> str | None:
    """Classify an Eastmoney secid into the ``a``, ``us``, or ``hk`` report group.

    Args:
        secid: Eastmoney secid (e.g. ``"1.600519"``, ``"105.AAPL"`` or
            ``"116.00700"``).

    Returns:
        ``"a"``, ``"us"``, ``"hk"``, or ``None`` when the market prefix is
        unrecognized.
    """
    market = secid.split(".", 1)[0]
    if market in _EM_A_MARKETS:
        return "a"
    if market in _EM_US_MARKETS:
        return "us"
    if market == _EM_HK_MARKET:
        return "hk"
    return None


def _parse_eastmoney_periods(payload: Any) -> list[dict[str, Any]]:
    """Extract period records from an Eastmoney datacenter report payload.

    Eastmoney nests report rows under ``result.data`` as a list of flat dicts.
    Any other shape yields an empty list rather than raising.

    Args:
        payload: Decoded JSON from the datacenter report API.

    Returns:
        A list of flat period dicts (possibly empty).
    """
    if not isinstance(payload, dict):
        return []
    result = payload.get("result")
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _eastmoney_filter(group: str, code: str, secid: str) -> str:
    """Build the datacenter ``filter`` clause for one market group.

    The A-share F10 datasets key on the dotted ``SECUCODE`` (e.g.
    ``600519.SH``), whereas the US/HK datasets key on the bare ``SECURITY_CODE``
    carried in the secid (e.g. ``AAPL`` / ``00700``). No ``REPORT_TYPE`` clause
    is emitted: Eastmoney stores ``REPORT_TYPE`` as locale text (年报 / 一季报)
    or a ``2026/Q1`` string that differs by market and report, so a numeric
    filter matched zero rows. Period selection is done client-side instead
    (see :func:`_filter_by_period`).

    Args:
        group: Market group from :func:`_eastmoney_market_group`.
        code: Original Vibe-Trading symbol (e.g. ``"600519.SH"``).
        secid: Resolved Eastmoney secid (e.g. ``"1.600519"``).

    Returns:
        The Eastmoney ``filter`` query-parameter string.
    """
    if group == "a":
        return f'(SECUCODE="{code.upper()}")'
    bare_code = secid.split(".", 1)[1]
    return f'(SECURITY_CODE="{bare_code}")'


def _filter_by_period(
    periods: list[dict[str, Any]], period: str
) -> list[dict[str, Any]]:
    """Best-effort client-side period selection by report date.

    Eastmoney returns a mixed newest-first series (annual + interim reports).
    For ``annual`` we keep only fiscal-year-end rows (``REPORT_DATE`` ending
    ``-12-31``); if none match — e.g. a US issuer whose fiscal year does not end
    in December — we fall back to the full series rather than drop all data.
    ``quarter`` returns the full newest-first series unchanged.

    Args:
        periods: Period records (newest-first) from the report parser.
        period: ``"annual"`` or ``"quarter"``.

    Returns:
        The filtered list; never empty when ``periods`` is non-empty.
    """
    if period != "annual":
        return periods
    annual = [
        row
        for row in periods
        if str(row.get("REPORT_DATE", ""))[:10].endswith("-12-31")
    ]
    return annual or periods


def _fetch_eastmoney_statement(
    code: str, *, statement: str, period: str
) -> dict[str, Any]:
    """Fetch one A-share/US/HK statement from Eastmoney, shaped into a result dict.

    Args:
        code: Symbol (e.g. ``"600519.SH"``, ``"AAPL.US"`` or ``"00700.HK"``).
        statement: One of :data:`_VALID_STATEMENTS`.
        period: ``"annual"`` or ``"quarter"``.

    Returns:
        ``{"periods": [...]}`` on success or ``{"error": ...}`` on failure;
        never raises.
    """
    secid = resolve_secid(code)
    if secid is None:
        return {"error": "unresolvable symbol"}

    group = _eastmoney_market_group(secid)
    if group is None:
        return {"error": "symbol is not an A-share, US, or Hong Kong instrument"}

    params = {
        "reportName": _EM_REPORT_NAME[group][statement],
        "columns": "ALL",
        "filter": _eastmoney_filter(group, code, secid),
        "sortColumns": "REPORT_DATE",
        "sortTypes": "-1",
        "pageNumber": "1",
        "pageSize": str(_MAX_PERIODS),
        "source": "F10",
        "client": "PC",
    }
    try:
        payload = get_json(_EM_REPORT_URL, params=params)
    except Exception as exc:  # noqa: BLE001 - one bad fetch must not kill the call
        logger.warning("eastmoney statement fetch failed for %s: %s", code, exc)
        return {"error": str(exc)}

    periods = _filter_by_period(_parse_eastmoney_periods(payload), period)
    return {"periods": _cap_periods(periods)}


def _classify_market(code: str) -> str | None:
    """Classify a symbol's suffix into ``a_share``, ``us``, ``hk``, or ``None``.

    Args:
        code: Symbol with a market suffix (e.g. ``"600519.SH"``, ``"AAPL.US"``).

    Returns:
        The market label, or ``None`` when the suffix is unrecognized.
    """
    suffix = code.rpartition(".")[2].strip().upper()
    if suffix in ("SH", "SZ", "BJ"):
        return "a_share"
    if suffix == "US":
        return "us"
    if suffix == "HK":
        return "hk"
    return None


class FinancialStatementsTool(BaseTool):
    """Fetch a stock's three financial statements or key per-period indicators."""

    name = "get_financial_statements"
    description = (
        "Fetch a single stock's financial statements: balance sheet, income "
        "statement, cash-flow statement, or key per-period indicators (margins, "
        "ROE, EPS, etc.). Markets: A-share (.SH/.SZ/.BJ), US (.US) and "
        "Hong Kong (.HK), all via Eastmoney. Reports come back newest-first as flat "
        "per-period rows. Use this to read fundamentals before building a "
        'valuation or screen. Example: {"code": "600519.SH", "statement": '
        '"income", "period": "annual"}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Single symbol with a market suffix, e.g. '600519.SH', "
                    "'000001.SZ', 'AAPL.US', or '00700.HK'."
                ),
            },
            "statement": {
                "type": "string",
                "enum": list(_VALID_STATEMENTS),
                "description": (
                    "Which report to fetch: 'balance' (balance sheet), 'income' "
                    "(income statement), 'cashflow' (cash-flow statement), or "
                    "'indicators' (key per-period indicators)."
                ),
                "default": "indicators",
            },
            "period": {
                "type": "string",
                "enum": list(_VALID_PERIODS),
                "description": (
                    "Reporting cadence: 'annual' (annual reports) or 'quarter' "
                    "(quarterly reports)."
                ),
                "default": "annual",
            },
        },
        "required": ["code"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Validate inputs, dispatch by market, and return a JSON envelope.

        Args:
            **kwargs: ``code`` (str, required), ``statement`` (one of balance|
                income|cashflow|indicators, default 'indicators'), ``period``
                (annual|quarter, default 'annual').

        Returns:
            A JSON string ``{"ok": true, "market": str, "source": str,
            "statement": str, "period": str, "data": {...}}`` when the fetch
            yields data, ``{"ok": false, "error": ...}`` when validation fails,
            or the same envelope with ``ok: false`` plus a top-level ``error``
            when the per-market fetch failed for every requested code (so a
            nested fetch error is never masked by a top-level ``ok: true``).
        """
        code = kwargs.get("code")
        if not isinstance(code, str) or not code.strip():
            return _error("code must be a non-empty symbol string")
        code = code.strip()

        statement = kwargs.get("statement", "indicators")
        if statement not in _VALID_STATEMENTS:
            return _error(f"statement must be one of {list(_VALID_STATEMENTS)}")

        period = kwargs.get("period", "annual")
        if period not in _VALID_PERIODS:
            return _error(f"period must be one of {list(_VALID_PERIODS)}")

        market = _classify_market(code)
        if market is None:
            return _error(
                "code must carry a supported suffix: .SH/.SZ/.BJ, .US, or .HK"
            )

        result = _fetch_eastmoney_statement(
            code, statement=statement, period=period
        )

        # The fetch failed for every requested code (here, the single ``code``)
        # iff its result carries an ``error``. Surface that as a top-level
        # ``ok: false`` so a nested failure is never masked by ``ok: true``.
        all_failed = "error" in result
        envelope: dict[str, Any] = {
            "ok": not all_failed,
            "market": market,
            "source": "eastmoney",
            "statement": statement,
            "period": period,
            "data": {code: result},
        }
        if all_failed:
            envelope["error"] = result["error"]
        return json.dumps(envelope, ensure_ascii=False)
