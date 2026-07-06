"""Shared Yahoo Finance public-API client: chart, quote summary, options, search.

Yahoo Finance exposes several unauthenticated JSON endpoints (the same ones the
finance.yahoo.com site itself calls) that, like other free quote providers,
rate-limit by source IP and must be throttled. Every request here routes
through :mod:`backtest.loaders._http` so calls to ``query*.finance.yahoo.com``
share one process-wide minimum-spacing gate and a reused session.

The ``v10/finance/quoteSummary`` endpoint additionally requires a session
cookie plus a matching ``crumb`` token. This client fetches both lazily on the
first call that needs them and refreshes them once on a 401 (the documented
"crumb expired / unauthorized" signal), so callers never manage that handshake.

Symbol convention (Vibe-Trading -> Yahoo):
  * US ``AAPL.US`` -> ``AAPL`` (Yahoo carries US tickers bare)
  * HK ``00700.HK`` -> ``0700.HK`` (Yahoo drops the leading zero to 4 digits)
  * Anything else is passed through unchanged (e.g. ``BTC-USD``, ``^GSPC``).

This module is provider-specific glue only; it returns plain Python
dicts/lists so a downstream loader can map them into the project's OHLCV frame.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

import requests

from backtest.loaders._http import (
    DEFAULT_USER_AGENT,
    resolve_min_interval,
    throttled_get,
    throttled_get_json,
)

logger = logging.getLogger(__name__)

# All Yahoo endpoints share one throttle/session bucket so spacing is enforced
# across chart/quote/options/search regardless of which host alias is used.
HOST_KEY = "yahoo"

# Yahoo serves the same data from query1/query2; query2 is conventionally used
# for the crumb-gated endpoints. We keep the chart on query1 like the website.
_CHART_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
_QUOTE_SUMMARY_BASE = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"
_OPTIONS_BASE = "https://query2.finance.yahoo.com/v7/finance/options"
_SEARCH_BASE = "https://query2.finance.yahoo.com/v1/finance/search"
_CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"
# Hitting fc.yahoo.com first hands back the consent/session cookie the crumb
# endpoint then validates.
_COOKIE_URL = "https://fc.yahoo.com"

_MIN_INTERVAL_ENV = "VIBE_TRADING_YAHOO_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL_S = 0.6

# The columns Yahoo packs into indicators.quote[0], in our output field order.
_QUOTE_FIELDS = ("open", "high", "low", "close", "volume")


def _min_interval() -> float:
    """Resolve the per-call minimum spacing, honoring the env override."""
    return resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL_S)


def map_symbol(symbol: str) -> str:
    """Translate a Vibe-Trading symbol into Yahoo's ticker convention.

    Args:
        symbol: Project-side symbol, e.g. ``AAPL.US``, ``00700.HK``, ``BTC-USD``.

    Returns:
        The Yahoo ticker: ``.US`` suffix stripped; ``.HK`` codes normalized to
        a 4-digit base (``00700.HK`` -> ``0700.HK``); everything else unchanged.
    """
    cleaned = symbol.strip()
    upper = cleaned.upper()
    if upper.endswith(".US"):
        return cleaned[: -len(".US")]
    if upper.endswith(".HK"):
        base = cleaned[: -len(".HK")]
        digits = base.lstrip("0") or "0"
        return f"{digits.zfill(4)}.HK"
    return cleaned


class _CrumbStore:
    """Process-wide cookie jar + crumb token for the quoteSummary handshake.

    Holds a single :class:`requests.Session`-independent crumb string and the
    cookies returned by Yahoo's consent endpoint. Refreshing is serialized by a
    lock so a burst of concurrent callers performs the handshake at most once.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._crumb: Optional[str] = None
        self._cookies: Dict[str, str] = {}

    def get(self, *, force_refresh: bool = False) -> tuple[str, Dict[str, str]]:
        """Return ``(crumb, cookies)``, fetching them on first use or on refresh.

        Args:
            force_refresh: Discard any cached crumb/cookies and re-handshake.

        Returns:
            A tuple of the crumb token and the cookie mapping to send with the
            crumb-gated request.

        Raises:
            requests.RequestException: If the cookie or crumb fetch fails.
            ValueError: If Yahoo returns an empty crumb.
        """
        with self._lock:
            if force_refresh or self._crumb is None:
                self._crumb, self._cookies = self._handshake()
            return self._crumb, dict(self._cookies)

    def _handshake(self) -> tuple[str, Dict[str, str]]:
        cookie_resp = throttled_get(
            _COOKIE_URL,
            host_key=HOST_KEY,
            min_interval=_min_interval(),
        )
        cookies = requests.utils.dict_from_cookiejar(cookie_resp.cookies)
        crumb_resp = throttled_get(
            _CRUMB_URL,
            host_key=HOST_KEY,
            min_interval=_min_interval(),
            headers={"Cookie": _cookie_header(cookies)} if cookies else None,
        )
        crumb_resp.raise_for_status()
        crumb = (crumb_resp.text or "").strip()
        if not crumb:
            raise ValueError("Yahoo returned an empty crumb token")
        return crumb, cookies


def _cookie_header(cookies: Dict[str, str]) -> str:
    """Render a cookie mapping as a single ``Cookie:`` header value."""
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


# One shared crumb/cookie store for the whole process.
_CRUMB_STORE = _CrumbStore()


def get_chart(
    symbol: str,
    *,
    interval: str = "1d",
    period1: Optional[int] = None,
    period2: Optional[int] = None,
    range_: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch OHLCV bars from the v8 chart endpoint as ascending rows.

    Either supply a ``range_`` (e.g. ``"1y"``, ``"max"``) or a
    ``period1``/``period2`` epoch-second window; ``range_`` wins when both are
    given. Yahoo returns parallel timestamp/indicator arrays which this function
    zips into row dicts, dropping any bar whose OHLC is incomplete (Yahoo emits
    ``null`` for non-trading slots).

    Args:
        symbol: Project-side symbol (mapped via :func:`map_symbol`).
        interval: Bar size accepted by Yahoo (``1d``, ``1h``, ``5m``, ...).
        period1: Inclusive start as epoch seconds, or ``None``.
        period2: Exclusive end as epoch seconds, or ``None``.
        range_: Relative range string; takes precedence over period1/period2.

    Returns:
        Ascending list of ``{trade_date, open, high, low, close, volume}`` dicts
        (``trade_date`` is the bar's epoch-second timestamp). Empty when Yahoo
        reports no data for the symbol/window.

    Raises:
        requests.RequestException: On a network/HTTP failure.
        ValueError: If Yahoo reports an error for the symbol or the payload is
            structurally unusable.
    """
    yahoo_symbol = map_symbol(symbol)
    params: Dict[str, Any] = {"interval": interval}
    if range_:
        params["range"] = range_
    else:
        if period1 is not None:
            params["period1"] = int(period1)
        if period2 is not None:
            params["period2"] = int(period2)

    payload = throttled_get_json(
        f"{_CHART_BASE}/{yahoo_symbol}",
        host_key=HOST_KEY,
        min_interval=_min_interval(),
        params=params,
    )
    return _parse_chart(payload, yahoo_symbol)


def _parse_chart(payload: Any, yahoo_symbol: str) -> List[Dict[str, Any]]:
    """Convert a v8 chart payload into ascending OHLCV row dicts."""
    chart = (payload or {}).get("chart") or {}
    error = chart.get("error")
    if error:
        description = error.get("description") if isinstance(error, dict) else error
        raise ValueError(f"Yahoo chart error for {yahoo_symbol}: {description}")

    results = chart.get("result") or []
    if not results:
        return []
    result = results[0] or {}

    timestamps = result.get("timestamp") or []
    quotes = (((result.get("indicators") or {}).get("quote")) or [{}])[0] or {}

    rows: List[Dict[str, Any]] = []
    for index, ts in enumerate(timestamps):
        values = {field: _at(quotes.get(field), index) for field in _QUOTE_FIELDS}
        # A non-trading slot leaves OHLC null; skip rather than emit a NaN bar.
        if any(values[field] is None for field in ("open", "high", "low", "close")):
            continue
        row: Dict[str, Any] = {"trade_date": ts}
        row.update({field: _to_float(values[field]) for field in _QUOTE_FIELDS})
        rows.append(row)
    return rows


def _at(series: Any, index: int) -> Any:
    """Return ``series[index]`` when in range, else ``None``."""
    if isinstance(series, list) and 0 <= index < len(series):
        return series[index]
    return None


def _to_float(value: Any) -> Optional[float]:
    """Coerce a Yahoo numeric (or ``None``) to ``float``, ``None`` on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_quote_summary(symbol: str, modules: List[str]) -> Dict[str, Any]:
    """Fetch v10 quoteSummary modules, handling the cookie+crumb handshake.

    On a 401 (expired/invalid crumb) the crumb and cookies are refreshed once
    and the request is retried; a second 401 propagates.

    Args:
        symbol: Project-side symbol (mapped via :func:`map_symbol`).
        modules: Yahoo module names, e.g. ``["price", "summaryDetail"]``.

    Returns:
        The ``quoteSummary.result[0]`` mapping, or ``{}`` when Yahoo returns no
        result for the symbol.

    Raises:
        requests.RequestException: On a non-401 HTTP failure or a second 401.
        ValueError: If Yahoo reports an error for the symbol.
    """
    yahoo_symbol = map_symbol(symbol)
    modules_param = ",".join(modules)

    payload = _quote_summary_request(yahoo_symbol, modules_param, force_refresh=False)
    return _parse_quote_summary(payload, yahoo_symbol)


def _quote_summary_request(
    yahoo_symbol: str, modules_param: str, *, force_refresh: bool
) -> Any:
    """Issue one crumb-gated quoteSummary GET, retrying once on a 401."""
    crumb, cookies = _CRUMB_STORE.get(force_refresh=force_refresh)
    headers = {"Cookie": _cookie_header(cookies)} if cookies else None
    response = throttled_get(
        f"{_QUOTE_SUMMARY_BASE}/{yahoo_symbol}",
        host_key=HOST_KEY,
        min_interval=_min_interval(),
        params={"modules": modules_param, "crumb": crumb},
        headers=headers,
    )
    if response.status_code == 401 and not force_refresh:
        logger.info("Yahoo quoteSummary 401 for %s; refreshing crumb", yahoo_symbol)
        return _quote_summary_request(yahoo_symbol, modules_param, force_refresh=True)
    response.raise_for_status()
    return response.json()


def _parse_quote_summary(payload: Any, yahoo_symbol: str) -> Dict[str, Any]:
    """Extract the first quoteSummary result, raising on a reported error."""
    summary = (payload or {}).get("quoteSummary") or {}
    error = summary.get("error")
    if error:
        description = error.get("description") if isinstance(error, dict) else error
        raise ValueError(f"Yahoo quoteSummary error for {yahoo_symbol}: {description}")
    results = summary.get("result") or []
    if not results:
        return {}
    return results[0] or {}


def get_options(symbol: str, *, expiration: Optional[int] = None) -> Dict[str, Any]:
    """Fetch the v7 option chain for a symbol, handling the cookie+crumb handshake.

    Like ``v10/quoteSummary``, the ``v7/finance/options`` endpoint now rejects
    bare requests with HTTP 401 and demands the same session cookie plus a
    matching ``crumb`` token. This routes through the shared
    :data:`_CRUMB_STORE` handshake and, on a 401 (expired/invalid crumb),
    refreshes the crumb once and retries; a second 401 propagates.

    Args:
        symbol: Project-side symbol (mapped via :func:`map_symbol`).
        expiration: Optional expiration as epoch seconds; omit for the nearest.

    Returns:
        The ``optionChain.result[0]`` mapping (expirationDates, strikes, the
        calls/puts arrays for the chosen expiry), or ``{}`` when none.

    Raises:
        requests.RequestException: On a non-401 HTTP failure or a second 401.
        ValueError: If Yahoo reports an error for the symbol.
    """
    yahoo_symbol = map_symbol(symbol)
    payload = _options_request(yahoo_symbol, expiration, force_refresh=False)
    return _parse_options(payload, yahoo_symbol)


def _options_request(
    yahoo_symbol: str, expiration: Optional[int], *, force_refresh: bool
) -> Any:
    """Issue one crumb-gated v7 options GET, retrying once on a 401."""
    crumb, cookies = _CRUMB_STORE.get(force_refresh=force_refresh)
    headers = {"Cookie": _cookie_header(cookies)} if cookies else None
    params: Dict[str, Any] = {"crumb": crumb}
    if expiration is not None:
        params["date"] = int(expiration)
    response = throttled_get(
        f"{_OPTIONS_BASE}/{yahoo_symbol}",
        host_key=HOST_KEY,
        min_interval=_min_interval(),
        params=params,
        headers=headers,
    )
    if response.status_code == 401 and not force_refresh:
        logger.info("Yahoo options 401 for %s; refreshing crumb", yahoo_symbol)
        return _options_request(yahoo_symbol, expiration, force_refresh=True)
    response.raise_for_status()
    return response.json()


def _parse_options(payload: Any, yahoo_symbol: str) -> Dict[str, Any]:
    """Extract the first optionChain result, raising on a reported error."""
    chain = (payload or {}).get("optionChain") or {}
    error = chain.get("error")
    if error:
        description = error.get("description") if isinstance(error, dict) else error
        raise ValueError(f"Yahoo options error for {yahoo_symbol}: {description}")
    results = chain.get("result") or []
    if not results:
        return {}
    return results[0] or {}


def search(query: str) -> List[Dict[str, Any]]:
    """Look up matching instruments via the v1 search endpoint.

    Args:
        query: Free-text query (ticker fragment or company name).

    Returns:
        The ``quotes`` list (each a dict with ``symbol``, ``shortname``,
        ``exchange``, ``quoteType``, ...), or an empty list when none match.

    Raises:
        requests.RequestException: On a network/HTTP failure.
    """
    payload = throttled_get_json(
        _SEARCH_BASE,
        host_key=HOST_KEY,
        min_interval=_min_interval(),
        params={"q": query},
    )
    quotes = (payload or {}).get("quotes") or []
    return [quote for quote in quotes if isinstance(quote, dict)]
