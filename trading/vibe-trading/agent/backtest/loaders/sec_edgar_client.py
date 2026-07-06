"""Shared SEC EDGAR REST client: ticker->CIK mapping + filings/facts fetch.

The U.S. SEC publishes free, no-auth JSON endpoints for company filings and
XBRL financial facts. Three public facts drive this module:

* ``https://www.sec.gov/files/company_tickers.json`` maps every reporting
  ticker to its numeric CIK (Central Index Key).
* ``https://data.sec.gov/submissions/CIK##########.json`` returns a company's
  recent filing index, keyed by the **zero-padded 10-digit** CIK.
* ``https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`` returns the
  full set of reported XBRL financial concepts for that same padded CIK.

SEC rate-limits by source IP and asks every client to send a descriptive
``User-Agent`` carrying a contact address; bursting without one earns a
temporary block. Every request therefore routes through the shared
:mod:`backtest.loaders._http` throttle under the ``"sec"`` host bucket, and the
UA defaults to a Vibe-Trading contact string overridable via
``VIBE_TRADING_SEC_UA``.

This module is a thin transport client, not a :class:`DataLoaderProtocol`
implementation: it returns raw decoded JSON for downstream loaders/tools to
shape. The ticker->CIK table is fetched once per process and memoized.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, Optional

from backtest.loaders._http import (
    DEFAULT_USER_AGENT,
    resolve_min_interval,
    throttled_get_json,
)

logger = logging.getLogger(__name__)

_HOST_KEY = "sec"
# SEC asks for no more than ~10 requests/second; 0.12s spacing keeps us well
# under that even with jitter, and is the floor mandated by the parcel contract.
_MIN_INTERVAL_DEFAULT = 0.12
_MIN_INTERVAL_ENV = "VIBE_TRADING_SEC_MIN_INTERVAL"

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

_UA_ENV = "VIBE_TRADING_SEC_UA"
# SEC's fair-access policy wants a real contact in the UA. Override via env to
# present your own address; this default keeps the client compliant out of box.
_DEFAULT_SEC_UA = f"Vibe-Trading/1.0 (contact: vibe-trading@example.com) {DEFAULT_USER_AGENT}"

# Process-wide memoized ticker->CIK map ("AAPL" -> "0000320193"), built lazily.
_TICKER_CACHE: Optional[Dict[str, str]] = None
_TICKER_CACHE_LOCK = threading.Lock()


def _min_interval() -> float:
    """Resolve the effective per-request spacing, never below the 0.12s floor."""
    return max(_MIN_INTERVAL_DEFAULT, resolve_min_interval(_MIN_INTERVAL_ENV, _MIN_INTERVAL_DEFAULT))


def _user_agent() -> str:
    """Return the compliant contact UA, honoring the ``VIBE_TRADING_SEC_UA`` override."""
    override = os.getenv(_UA_ENV)
    if override and override.strip():
        return override.strip()
    return _DEFAULT_SEC_UA


def _sec_get_json(url: str) -> Any:
    """GET ``url`` as JSON through the shared SEC-bucket throttle.

    Args:
        url: Fully-qualified SEC endpoint URL.

    Returns:
        The decoded JSON body (typically a ``dict``).

    Raises:
        requests.RequestException: On a non-2xx status or undecodable body,
            propagated unchanged for the caller to classify.
    """
    return throttled_get_json(
        url,
        host_key=_HOST_KEY,
        min_interval=_min_interval(),
        headers={"User-Agent": _user_agent(), "Accept": "application/json"},
    )


def _pad_cik(cik: str | int) -> str:
    """Normalize a CIK to the SEC's zero-padded 10-digit string form.

    Args:
        cik: A CIK as an int or a string that may already be padded or carry a
            leading ``"CIK"`` prefix.

    Returns:
        The CIK as exactly 10 digits, e.g. ``"0000320193"``.

    Raises:
        ValueError: If ``cik`` contains no digits.
    """
    digits = "".join(ch for ch in str(cik) if ch.isdigit())
    if not digits:
        raise ValueError(f"CIK has no digits: {cik!r}")
    return digits.zfill(10)


def _build_ticker_map(payload: Any) -> Dict[str, str]:
    """Build an uppercase ticker->padded-CIK map from the tickers payload.

    The SEC payload is a dict of positional string keys to records shaped like
    ``{"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}``. A
    malformed row is skipped rather than aborting the whole map.

    Args:
        payload: Decoded ``company_tickers.json`` body.

    Returns:
        Mapping of upper-cased ticker to zero-padded 10-digit CIK.
    """
    records = payload.values() if isinstance(payload, dict) else payload
    mapping: Dict[str, str] = {}
    for record in records or []:
        if not isinstance(record, dict):
            continue
        ticker = record.get("ticker")
        cik = record.get("cik_str", record.get("cik"))
        if not ticker or cik is None:
            continue
        try:
            mapping[str(ticker).strip().upper()] = _pad_cik(cik)
        except ValueError:
            logger.debug("skipping ticker row with bad CIK: %r", record)
    return mapping


def _ticker_map() -> Dict[str, str]:
    """Return the process-wide ticker->CIK map, fetching once and memoizing.

    Returns:
        Mapping of upper-cased ticker to zero-padded 10-digit CIK.

    Raises:
        requests.RequestException: If the one-time tickers fetch fails.
    """
    global _TICKER_CACHE
    if _TICKER_CACHE is not None:
        return _TICKER_CACHE
    with _TICKER_CACHE_LOCK:
        if _TICKER_CACHE is None:
            payload = _sec_get_json(_TICKERS_URL)
            _TICKER_CACHE = _build_ticker_map(payload)
    return _TICKER_CACHE


def cik_for(ticker: str) -> Optional[str]:
    """Resolve a ticker symbol to its zero-padded 10-digit CIK.

    Args:
        ticker: A U.S. equity ticker (case-insensitive), e.g. ``"AAPL"``.

    Returns:
        The padded CIK string (``"0000320193"``) or ``None`` when the ticker is
        empty or absent from the SEC table.

    Raises:
        requests.RequestException: If the one-time tickers fetch fails.
    """
    if not ticker or not ticker.strip():
        return None
    return _ticker_map().get(ticker.strip().upper())


def get_submissions(cik: str | int) -> Dict[str, Any]:
    """Fetch the filing-index ("submissions") JSON for a CIK.

    Args:
        cik: A CIK as int or string; padded to 10 digits internally.

    Returns:
        The decoded submissions document (company metadata + recent filings).

    Raises:
        ValueError: If ``cik`` contains no digits.
        requests.RequestException: On a non-2xx status or undecodable body.
    """
    return _sec_get_json(_SUBMISSIONS_URL.format(cik=_pad_cik(cik)))


def get_company_facts(cik: str | int) -> Dict[str, Any]:
    """Fetch the XBRL ``companyfacts`` JSON for a CIK.

    Args:
        cik: A CIK as int or string; padded to 10 digits internally.

    Returns:
        The decoded company-facts document (all reported XBRL concepts).

    Raises:
        ValueError: If ``cik`` contains no digits.
        requests.RequestException: On a non-2xx status or undecodable body.
    """
    return _sec_get_json(_COMPANY_FACTS_URL.format(cik=_pad_cik(cik)))


def _reset_ticker_cache_for_tests() -> None:
    """Clear the memoized ticker map. Test-only hook; never called in prod."""
    global _TICKER_CACHE
    with _TICKER_CACHE_LOCK:
        _TICKER_CACHE = None
