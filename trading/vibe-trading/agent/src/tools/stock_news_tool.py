"""Read-only news tool: per-stock and global financial headlines.

Two public, no-auth news surfaces are wrapped behind one BaseTool contract:

* China A-share (and general China-market finance) headlines come from
  Eastmoney's free ``search-api`` news-list endpoint. Like every Eastmoney
  surface it rate-limits by source IP, so the request routes through the frozen,
  IP-throttled :mod:`backtest.loaders.eastmoney_client` rather than touching the
  host directly.
* US / HK have no free no-auth article feed here: the frozen
  :func:`backtest.loaders.yahoo_client.search` helper exposes only the search
  endpoint's instrument ``quotes`` (not its ``news`` array), so the tool returns
  honest related-instrument *matches* under a ``matches`` key — never instrument
  hits relabelled as articles.

The tool never re-implements provider plumbing and never issues an un-throttled
request: every outbound call goes through a frozen client.

Scopes:

* ``stock`` (default) — headlines for a single security named by ``code``.
* ``global`` — broad market headlines, no ``code`` required.

A failure for one upstream is reported as an error envelope; the tool never
raises out of :meth:`StockNewsTool.execute`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backtest.loaders import eastmoney_client, yahoo_client

from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Eastmoney free news search endpoint (JSON list of CMS articles). It is the
# same surface the site's search box calls; no auth, IP-throttled.
_EM_NEWS_URL = "https://search-api-web.eastmoney.com/search/jsonp"

# A-share / China-market suffixes that route to the Eastmoney news surface.
_EM_SUFFIXES = ("SH", "SZ", "BJ")
# Suffixes that route to Yahoo's search-news surface.
_YAHOO_SUFFIXES = ("US", "HK")

# Default broad-market query used when ``scope='global'`` carries no code.
_GLOBAL_QUERY = "财经"

# Bounds so a noisy upstream can never return an unbounded payload.
_DEFAULT_LIMIT = 20
_MAX_LIMIT = 50
# Per-article body trim so the envelope stays compact for the LLM.
_SNIPPET_CHARS = 280


def _clamp_limit(raw: Any) -> int:
    """Coerce a caller-supplied ``limit`` into the supported ``1.._MAX_LIMIT`` range.

    Args:
        raw: The raw ``limit`` value from the tool arguments (any type).

    Returns:
        An integer in ``[1, _MAX_LIMIT]``, falling back to ``_DEFAULT_LIMIT``
        when ``raw`` is missing or non-numeric.
    """
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    if value < 1:
        return 1
    return min(value, _MAX_LIMIT)


def _suffix_of(code: str) -> str:
    """Return the upper-cased exchange suffix of a symbol, or ``""`` when none."""
    if "." not in code:
        return ""
    return code.rpartition(".")[2].strip().upper()


def _bare_query(code: str) -> str:
    """Strip any exchange suffix to the bare code used as a news search term."""
    return code.strip().split(".", 1)[0].strip()


def _snippet(text: Any) -> str:
    """Trim an article body to a bounded plain-text snippet.

    Args:
        text: Raw body/summary value (any type).

    Returns:
        A whitespace-collapsed snippet capped at ``_SNIPPET_CHARS`` characters,
        or ``""`` when ``text`` is not a usable string.
    """
    if not isinstance(text, str):
        return ""
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SNIPPET_CHARS:
        return collapsed
    return collapsed[:_SNIPPET_CHARS].rstrip() + "…"


def _decode_jsonp(payload: Any) -> Any:
    """Decode an Eastmoney response that may arrive JSON or JSONP-wrapped.

    The search endpoint usually returns a JSON object, but can echo a
    ``callback(...)`` JSONP envelope. A single outer call wrapper is stripped
    before parsing.

    Args:
        payload: The decoded body from the throttled client (``dict`` already, or
            a raw ``str`` when JSONP-wrapped).

    Returns:
        The decoded object, or ``None`` when nothing parseable is found.
    """
    if isinstance(payload, dict):
        return payload
    if not isinstance(payload, str):
        return None
    start = payload.find("(")
    end = payload.rfind(")")
    inner = payload[start + 1 : end] if start != -1 and end > start else payload
    try:
        return json.loads(inner)
    except (ValueError, TypeError):
        return None


def _em_article(raw: dict[str, Any]) -> dict[str, Any]:
    """Project one Eastmoney CMS article into a compact, named record.

    Args:
        raw: A single article dict from ``result.cmsArticleWebOld``.

    Returns:
        A flat ``{title, url, source, published, snippet}`` record.
    """
    return {
        "title": _snippet(raw.get("title")),
        "url": raw.get("url"),
        "source": raw.get("mediaName"),
        "published": raw.get("date"),
        "snippet": _snippet(raw.get("content")),
    }


def _fetch_eastmoney_news(query: str, limit: int) -> list[dict[str, Any]]:
    """Fetch China-market news headlines for a query from Eastmoney.

    Args:
        query: Free-text search term (bare code or keyword).
        limit: Maximum number of articles to return.

    Returns:
        A capped list of compact article records; empty when none.

    Raises:
        requests.RequestException: Network failure, propagated to the caller.
        requests.HTTPError: Non-2xx response status.
        ValueError: Body is not valid JSON.
    """
    param = json.dumps(
        {
            "uid": "",
            "keyword": query,
            "type": ["cmsArticleWebOld"],
            "client": "web",
            "clientType": "web",
            "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "default", "pageIndex": 1, "pageSize": limit}},
        },
        ensure_ascii=False,
    )
    payload = eastmoney_client.get_json(
        _EM_NEWS_URL,
        params={"cb": "", "param": param, "_": "0"},
    )
    decoded = _decode_jsonp(payload)
    if not isinstance(decoded, dict):
        return []
    result = decoded.get("result")
    if not isinstance(result, dict):
        return []
    articles = result.get("cmsArticleWebOld")
    if not isinstance(articles, list):
        return []
    return [_em_article(a) for a in articles if isinstance(a, dict)][:limit]


def _yahoo_match(raw: dict[str, Any]) -> dict[str, Any]:
    """Project one Yahoo search match into a compact headline-style record.

    Yahoo's ``search`` helper returns instrument matches; each is surfaced as a
    related-instrument headline so callers get the symbol, name and exchange.

    Args:
        raw: A single quote dict from :func:`yahoo_client.search`.

    Returns:
        A flat ``{title, symbol, exchange, quote_type}`` record.
    """
    name = raw.get("shortname") or raw.get("longname") or raw.get("symbol")
    return {
        "title": _snippet(name),
        "symbol": raw.get("symbol"),
        "exchange": raw.get("exchange"),
        "quote_type": raw.get("quoteType"),
    }


def _fetch_yahoo_matches(query: str, limit: int) -> list[dict[str, Any]]:
    """Fetch US/HK related-instrument matches for a query via Yahoo search.

    Yahoo's public search endpoint also carries a ``news`` array, but the frozen
    :func:`yahoo_client.search` helper exposes only the instrument ``quotes``.
    Rather than mislabel those quotes as articles, this returns them honestly as
    related-instrument matches.

    Args:
        query: Free-text search term (bare ticker or keyword).
        limit: Maximum number of records to return.

    Returns:
        A capped list of compact instrument-match records; empty when none.

    Raises:
        requests.RequestException: Network/HTTP failure, propagated to caller.
    """
    matches = yahoo_client.search(query)
    return [_yahoo_match(m) for m in matches if isinstance(m, dict)][:limit]


class StockNewsTool(BaseTool):
    """Read-only per-stock and global financial news headlines."""

    name = "get_stock_news"
    description = (
        "Fetch recent financial news headlines, read-only and no auth. Markets: "
        "China A-share (SH/SZ/BJ) returns Eastmoney news ARTICLES "
        "(title/url/source/published/snippet) under 'articles'. US (.US) and Hong "
        "Kong (.HK) do NOT return news articles: Yahoo's public search surface "
        "yields related-instrument MATCHES (symbol/name/exchange/quote_type), "
        "returned under 'matches' (result_type='matches'), not 'articles'. Use "
        "scope 'stock' with a 'code', or scope 'global' (no code) for broad "
        "China-market finance articles. "
        'Example: {"code": "600519.SH", "scope": "stock", "limit": 10}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Symbol whose news to fetch, e.g. '600519.SH', 'AAPL.US', "
                    "'00700.HK'. Required when scope='stock'; ignored when "
                    "scope='global'. The exchange suffix selects the upstream: "
                    "SH/SZ/BJ -> Eastmoney, US/HK -> Yahoo Finance."
                ),
            },
            "scope": {
                "type": "string",
                "enum": ["stock", "global"],
                "description": (
                    "'stock' (default) for one security named by 'code'; "
                    "'global' for broad China-market finance headlines."
                ),
                "default": "stock",
            },
            "limit": {
                "type": "integer",
                "description": (
                    "Maximum number of headlines to return (1-50). Default 20."
                ),
                "default": _DEFAULT_LIMIT,
            },
        },
        "required": [],
    }

    def execute(self, **kwargs: Any) -> str:
        """Fetch news headlines for one stock or the broad market.

        Args:
            **kwargs: ``scope`` ('stock' | 'global', default 'stock'), ``code``
                (required when scope='stock'), and optional ``limit`` (1-50).

        Returns:
            A JSON string envelope. On success:
            ``{"ok": true, "market": <market>, "source": <source>,
            "data": {...}}``. On failure: ``{"ok": false, "error": "..."}``.
        """
        scope = kwargs.get("scope", "stock")
        if scope not in ("stock", "global"):
            return self._error(f"invalid scope: {scope!r}; expected 'stock' or 'global'")

        limit = _clamp_limit(kwargs.get("limit"))

        if scope == "global":
            return self._run_global(limit)
        return self._run_stock(kwargs.get("code"), limit)

    def _run_global(self, limit: int) -> str:
        """Fetch broad China-market headlines from Eastmoney.

        Args:
            limit: Maximum number of headlines.

        Returns:
            A success or error JSON envelope.
        """
        try:
            articles = _fetch_eastmoney_news(_GLOBAL_QUERY, limit)
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure as envelope
            logger.warning("global news fetch failed: %s", exc)
            return self._error(f"eastmoney news fetch failed: {exc}")
        return self._ok("global", "eastmoney", {"scope": "global", "articles": articles})

    def _run_stock(self, code_arg: Any, limit: int) -> str:
        """Fetch single-security headlines, routing by exchange suffix.

        Args:
            code_arg: Raw ``code`` argument (any type).
            limit: Maximum number of headlines.

        Returns:
            A success or error JSON envelope.
        """
        if not isinstance(code_arg, str) or not code_arg.strip():
            return self._error("missing required parameter: code (required when scope='stock')")

        code = code_arg.strip()
        suffix = _suffix_of(code)
        query = _bare_query(code)
        if not query:
            return self._error(f"invalid code: {code!r}")

        if suffix in _EM_SUFFIXES:
            return self._stock_via_eastmoney(code, query, limit)
        if suffix in _YAHOO_SUFFIXES:
            return self._stock_via_yahoo(code, query, limit)
        return self._error(
            f"unsupported market for code {code!r}; expected suffix in "
            f"{_EM_SUFFIXES + _YAHOO_SUFFIXES}"
        )

    def _stock_via_eastmoney(self, code: str, query: str, limit: int) -> str:
        """Fetch A-share headlines from Eastmoney for one code."""
        try:
            articles = _fetch_eastmoney_news(query, limit)
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure as envelope
            logger.warning("eastmoney news fetch failed for %s: %s", code, exc)
            return self._error(f"eastmoney news fetch failed: {exc}")
        return self._ok(
            "a_share", "eastmoney", {"scope": "stock", "code": code, "articles": articles}
        )

    def _stock_via_yahoo(self, code: str, query: str, limit: int) -> str:
        """Fetch US/HK related-instrument matches from Yahoo for one code.

        Yahoo's public ``search`` surface yields instrument matches, not news
        articles, so the payload is labelled ``matches`` (never ``articles``) to
        avoid passing instrument hits off as headlines.
        """
        market = "hk" if _suffix_of(code) == "HK" else "us"
        try:
            matches = _fetch_yahoo_matches(query, limit)
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure as envelope
            logger.warning("yahoo search fetch failed for %s: %s", code, exc)
            return self._error(f"yahoo search fetch failed: {exc}")
        return self._ok(
            market,
            "yahoo",
            {"scope": "stock", "code": code, "result_type": "matches", "matches": matches},
        )

    @staticmethod
    def _ok(market: str, source: str, data: dict[str, Any]) -> str:
        """Render a success envelope as a JSON string.

        Args:
            market: Market label (e.g. ``"a_share"``, ``"us"``, ``"global"``).
            source: Upstream provider name (``"eastmoney"`` or ``"yahoo"``).
            data: The payload mapping.

        Returns:
            ``{"ok": true, "market": ..., "source": ..., "data": ...}`` as JSON.
        """
        return json.dumps(
            {"ok": True, "market": market, "source": source, "data": data},
            ensure_ascii=False,
        )

    @staticmethod
    def _error(message: str) -> str:
        """Render a failure envelope as a JSON string.

        Args:
            message: Human-readable error text.

        Returns:
            ``{"ok": false, "error": message}`` as a JSON string.
        """
        return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
