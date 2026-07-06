"""Read-only symbol-search tool: resolve a name/ticker to symbols + market.

Backed by three frozen, IP-throttled public-API clients so the agent never
hits a provider un-throttled and never re-implements transport plumbing:

* :mod:`backtest.loaders.eastmoney_client` — Eastmoney's free suggest endpoint
  matches Chinese/English names and tickers across A-shares (.SH/.SZ/.BJ),
  Hong Kong (.HK) and U.S. (.US) listings, each carrying a fully-qualified
  ``secid`` already in ``<market>.<code>`` form.
* :mod:`backtest.loaders.yahoo_client` — Yahoo's v1 search endpoint matches
  global tickers/company names (US, HK, crypto, indices, FX, ...).
* :mod:`backtest.loaders.sec_edgar_client` — the SEC company-tickers table
  enriches a resolved U.S. equity ticker with its zero-padded CIK.

The tool fans out across these sources, normalizes every hit into one compact
candidate row in the project's symbol convention, de-duplicates by symbol, and
caps the payload. A single failing source never aborts the others; its error is
recorded under ``sources`` and the surviving candidates still return.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from backtest.loaders import eastmoney_client, sec_edgar_client, yahoo_client
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney's free, no-auth suggest endpoint (the same one the quote site calls)
# returns multi-market candidates under ``QuotationCodeTable.Data`` with a
# ready-made ``QuoteID`` secid. Requests route through the frozen, throttled
# Eastmoney client; this is just the documented endpoint URL + query shape.
_EASTMONEY_SUGGEST_URL = "https://searchapi.eastmoney.com/api/suggest/get"

# Eastmoney market-number -> our symbol suffix. Anything else is left unmapped
# (those candidates are skipped rather than emitted with a wrong suffix).
_EASTMONEY_SUFFIX_BY_MARKET: Dict[str, str] = {
    "1": "SH",   # Shanghai
    "0": "SZ",   # Shenzhen / Beijing share the 0 prefix on Eastmoney
    "116": "HK",
    "105": "US",  # NASDAQ
    "106": "US",  # NYSE
    "107": "US",  # AMEX
}

# Coarse market label for the candidate row, keyed by symbol suffix.
_MARKET_BY_SUFFIX: Dict[str, str] = {
    "SH": "cn",
    "SZ": "cn",
    "BJ": "cn",
    "HK": "hk",
    "US": "us",
}

# Hard caps so a broad query cannot bloat the envelope.
_MAX_LIMIT = 25
_DEFAULT_LIMIT = 10
# Per-source fan-out ceiling before de-dup/merge keeps each provider bounded.
_PER_SOURCE_CAP = 25

# Sentinel for "no U.S. candidate, SEC was not consulted" so the caller can omit
# the ``sec_edgar`` source entry entirely.
_NO_US = "__no_us__"


class SymbolSearchTool(BaseTool):
    """Resolve a company name or ticker fragment to candidate symbols."""

    name = "search_symbol"
    description = (
        "Resolve a company name or ticker fragment to candidate trading symbols "
        "with their market, in the project's symbol convention (A-shares "
        "600519.SH, Hong Kong 00700.HK, U.S. AAPL.US, plus crypto/index/FX from "
        "Yahoo). Searches Eastmoney (China/HK/US names and tickers) and Yahoo "
        "(global) and, for U.S. equities, attaches the SEC CIK. Use this to turn "
        "an ambiguous name into a concrete symbol before calling get_market_data "
        'or get_sec_filings. Example: search_symbol(query="apple", limit=5).'
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Free-text company name or ticker fragment to resolve, e.g. "
                    "'apple', '贵州茅台', '茅台', 'AAPL', '00700'. Chinese and "
                    "English both accepted."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    f"Maximum number of merged candidates to return "
                    f"(1-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}."
                ),
                "default": _DEFAULT_LIMIT,
            },
        },
        "required": ["query"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Fan out across providers and return a merged candidate envelope.

        Args:
            **kwargs: ``query`` (str, required free-text name/ticker) and
                ``limit`` (int, optional; clamped to ``1.._MAX_LIMIT``).

        Returns:
            A JSON envelope string. On success:
            ``{"ok": true, "market": "multi", "source": "symbol_search",
            "data": {"query": str, "count": int, "candidates": [...],
            "sources": {<name>: "ok"|<error>}}}``. On failure (only when the
            query itself is invalid):
            ``{"ok": false, "error": str}``.
        """
        query = str(kwargs.get("query") or "").strip()
        if not query:
            return _error("'query' is required and must be a non-empty string")

        limit = _clamp_limit(kwargs.get("limit", _DEFAULT_LIMIT))

        candidates: List[Dict[str, Any]] = []
        sources: Dict[str, str] = {}

        em_hits, sources["eastmoney"] = _search_eastmoney(query)
        candidates.extend(em_hits)

        yh_hits, sources["yahoo"] = _search_yahoo(query)
        candidates.extend(yh_hits)

        merged = _merge_candidates(candidates)
        merged, sources["sec_edgar"] = _enrich_us_cik(merged)
        if sources["sec_edgar"] == _NO_US:
            del sources["sec_edgar"]
        merged = merged[:limit]

        return json.dumps(
            {
                "ok": True,
                "market": "multi",
                "source": "symbol_search",
                "data": {
                    "query": query,
                    "count": len(merged),
                    "candidates": merged,
                    "sources": sources,
                },
            },
            ensure_ascii=False,
        )


def _clamp_limit(value: Any) -> int:
    """Coerce a requested count into the supported ``1.._MAX_LIMIT`` range."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    return max(1, min(n, _MAX_LIMIT))


def _search_eastmoney(query: str) -> tuple[List[Dict[str, Any]], str]:
    """Query Eastmoney's suggest endpoint and normalize the candidates.

    Args:
        query: Free-text name or ticker fragment.

    Returns:
        ``(candidates, status)`` where ``status`` is ``"ok"`` on success or a
        short error string when the source failed (candidates is then empty).
    """
    try:
        payload = eastmoney_client.get_json(
            _EASTMONEY_SUGGEST_URL,
            params={"input": query, "type": "14", "count": str(_PER_SOURCE_CAP)},
        )
    except Exception as exc:  # noqa: BLE001 - one source failing is non-fatal
        logger.warning("eastmoney suggest failed for %r: %s", query, exc)
        return [], f"eastmoney search failed: {exc}"

    rows = _eastmoney_data_rows(payload)
    candidates = [c for c in (_eastmoney_candidate(r) for r in rows) if c is not None]
    return candidates, "ok"


def _eastmoney_data_rows(payload: Any) -> List[Dict[str, Any]]:
    """Extract the ``QuotationCodeTable.Data`` rows from a suggest payload."""
    if not isinstance(payload, dict):
        return []
    table = payload.get("QuotationCodeTable")
    if not isinstance(table, dict):
        return []
    data = table.get("Data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _eastmoney_candidate(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map one Eastmoney suggest row to a normalized candidate, or ``None``.

    Eastmoney rows carry ``QuoteID`` (``<market>.<code>``), ``Code``, ``Name``,
    ``MktNum`` and ``SecurityTypeName``. A row whose market we cannot map to a
    project suffix is dropped rather than emitted with a wrong symbol.

    Args:
        row: One ``QuotationCodeTable.Data`` element.

    Returns:
        A candidate dict, or ``None`` when the row is unusable.
    """
    quote_id = row.get("QuoteID")
    market = ""
    code = str(row.get("Code") or "").strip()
    if isinstance(quote_id, str) and "." in quote_id:
        market, _, qid_code = quote_id.partition(".")
        code = code or qid_code.strip()
    else:
        market = str(row.get("MktNum") or "").strip()
    suffix = _EASTMONEY_SUFFIX_BY_MARKET.get(market)
    if not suffix or not code:
        return None

    symbol = _format_symbol(code, suffix)
    if symbol is None:
        return None
    name = str(row.get("Name") or "").strip() or None
    sec_type = str(row.get("SecurityTypeName") or "").strip() or None
    return {
        "symbol": symbol,
        "name": name,
        "market": _MARKET_BY_SUFFIX.get(suffix, suffix.lower()),
        "type": sec_type,
        "source": "eastmoney",
    }


def _format_symbol(code: str, suffix: str) -> Optional[str]:
    """Render a bare code + suffix into the project symbol convention.

    HK codes are zero-padded to five digits to match the loader/secid scheme.

    Args:
        code: Bare instrument code (e.g. ``"600519"``, ``"700"``, ``"AAPL"``).
        suffix: One of ``SH``/``SZ``/``BJ``/``HK``/``US``.

    Returns:
        The formatted symbol (``"600519.SH"``, ``"00700.HK"``, ``"AAPL.US"``),
        or ``None`` when the code is empty.
    """
    code = code.strip().upper()
    if not code:
        return None
    if suffix == "HK":
        return f"{code.zfill(5)}.HK"
    return f"{code}.{suffix}"


def _search_yahoo(query: str) -> tuple[List[Dict[str, Any]], str]:
    """Query Yahoo's search endpoint and normalize the quote candidates.

    Args:
        query: Free-text name or ticker fragment.

    Returns:
        ``(candidates, status)`` where ``status`` is ``"ok"`` on success or a
        short error string when the source failed (candidates is then empty).
    """
    try:
        quotes = yahoo_client.search(query)
    except Exception as exc:  # noqa: BLE001 - one source failing is non-fatal
        logger.warning("yahoo search failed for %r: %s", query, exc)
        return [], f"yahoo search failed: {exc}"

    candidates: List[Dict[str, Any]] = []
    for quote in quotes[:_PER_SOURCE_CAP]:
        candidate = _yahoo_candidate(quote)
        if candidate is not None:
            candidates.append(candidate)
    return candidates, "ok"


def _yahoo_candidate(quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map one Yahoo search quote to a normalized candidate, or ``None``.

    Yahoo carries US tickers bare and HK tickers as ``0700.HK``. We translate
    those into the project convention (``AAPL.US`` / ``00700.HK``) and leave
    other instruments (crypto, indices, FX) on their native Yahoo symbol.

    Args:
        quote: One element of Yahoo search's ``quotes`` list.

    Returns:
        A candidate dict, or ``None`` when the quote has no symbol.
    """
    raw_symbol = str(quote.get("symbol") or "").strip()
    if not raw_symbol:
        return None
    symbol, market = _from_yahoo_symbol(raw_symbol, quote)
    name = (
        str(quote.get("shortname") or quote.get("longname") or "").strip() or None
    )
    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "type": str(quote.get("quoteType") or "").strip().lower() or None,
        "exchange": str(quote.get("exchange") or "").strip() or None,
        "source": "yahoo",
    }


def _from_yahoo_symbol(raw_symbol: str, quote: Dict[str, Any]) -> tuple[str, str]:
    """Translate a Yahoo symbol into the project convention + market label.

    Args:
        raw_symbol: The Yahoo-side symbol (e.g. ``AAPL``, ``0700.HK``, ``BTC-USD``).
        quote: The full Yahoo quote, used to distinguish a bare US equity from a
            crypto/index instrument via ``quoteType``.

    Returns:
        ``(symbol, market)`` in the project convention.
    """
    upper = raw_symbol.upper()
    if upper.endswith(".HK"):
        base = raw_symbol[: -len(".HK")].lstrip("0") or "0"
        return f"{base.zfill(5)}.HK", "hk"
    quote_type = str(quote.get("quoteType") or "").strip().upper()
    if quote_type == "EQUITY" and "." not in raw_symbol and "-" not in raw_symbol:
        return f"{upper}.US", "us"
    # Crypto, indices, FX, ETFs on non-HK exchanges: keep Yahoo's native symbol.
    return raw_symbol, "global"


def _merge_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """De-duplicate candidates by symbol, preserving first-seen order.

    When two sources resolve the same symbol the first hit wins and the second
    source name is appended to a ``also_from`` list so provenance is not lost.

    Args:
        candidates: Raw candidates from every source, in fan-out order.

    Returns:
        A de-duplicated candidate list (immutable inputs are copied, not mutated).
    """
    by_symbol: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for candidate in candidates:
        symbol = candidate.get("symbol")
        if not symbol:
            continue
        if symbol not in by_symbol:
            by_symbol[symbol] = dict(candidate)
            order.append(symbol)
            continue
        existing = by_symbol[symbol]
        other = candidate.get("source")
        if other and other != existing.get("source"):
            also = list(existing.get("also_from") or [])
            if other not in also:
                also.append(other)
            merged = dict(existing)
            merged["also_from"] = also
            # Backfill a missing name from the duplicate hit.
            if not merged.get("name") and candidate.get("name"):
                merged["name"] = candidate["name"]
            by_symbol[symbol] = merged
    return [by_symbol[sym] for sym in order]


def _enrich_us_cik(
    candidates: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], str]:
    """Return new candidates with a SEC CIK attached to U.S.-equity rows.

    Only ``.US`` equity symbols are looked up; the SEC table maps bare tickers
    to a zero-padded 10-digit CIK. A lookup failure stops further lookups and is
    reported via the status; resolved CIKs found before it still apply.

    Args:
        candidates: Merged candidate rows (left unmodified).

    Returns:
        ``(new_candidates, status)`` where ``status`` is :data:`_NO_US` when no
        U.S. equity was present, ``"ok"`` on a clean pass, or a short error
        string when a SEC lookup failed.
    """
    has_us = any(
        isinstance(c.get("symbol"), str) and c["symbol"].upper().endswith(".US")
        for c in candidates
    )
    if not has_us:
        return candidates, _NO_US

    status = "ok"
    out: List[Dict[str, Any]] = []
    for candidate in candidates:
        symbol = candidate.get("symbol")
        if status == "ok" and isinstance(symbol, str) and symbol.upper().endswith(".US"):
            ticker = symbol[: -len(".US")]
            try:
                cik = sec_edgar_client.cik_for(ticker)
            except Exception as exc:  # noqa: BLE001 - enrichment failure is non-fatal
                logger.warning("sec cik_for failed for %s: %s", ticker, exc)
                status = f"sec lookup failed: {exc}"
                out.append(candidate)
                continue
            if cik:
                out.append({**candidate, "cik": cik})
                continue
        out.append(candidate)
    return out, status


def _error(message: str) -> str:
    """Render a failure envelope as a JSON string."""
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
