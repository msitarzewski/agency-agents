"""Tiingo loader: US-equity daily OHLCV via the Tiingo REST API (key-gated).

Tiingo serves end-of-day US-equity bars from a documented public endpoint:

  GET https://api.tiingo.com/tiingo/daily/{symbol}/prices
      ?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&token={KEY}

The response is a JSON array of per-day objects, each carrying ``date`` plus
``open``/``high``/``low``/``close``/``volume`` (and adjusted variants we ignore).
A token is required; it is read from the ``TIINGO_API_KEY`` environment variable
and is never hard-coded. Like every other ban-prone HTTP loader in this package,
all requests route through :mod:`backtest.loaders._http` for per-host throttling
and session reuse — Tiingo rate-limits by client and rejects unspaced bursts.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders._http import resolve_min_interval, throttled_get_json
from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.tiingo.com/tiingo/daily"

# Throttle/session bucket plus the per-provider minimum spacing override.
_HOST_KEY = "tiingo"
_MIN_INTERVAL_ENV = "VIBE_TRADING_TIINGO_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL = 0.5

_AUTH_ENV = "TIINGO_API_KEY"

# Placeholder values that must not count as a real key (mirrors how other
# key-gated loaders treat blank/example tokens as "not configured").
_KEY_PLACEHOLDERS = {"", "your_tiingo_api_key", "changeme", "xxx"}

# Target OHLCV schema, in column order.
_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def _resolve_key() -> str:
    """Return the configured Tiingo API key, or an empty string when unset.

    Returns:
        The trimmed ``TIINGO_API_KEY`` value, or ``""`` when absent or a known
        placeholder.
    """
    key = os.getenv(_AUTH_ENV, "").strip()
    return "" if key.lower() in _KEY_PLACEHOLDERS else key


def _to_tiingo_symbol(code: str) -> Optional[str]:
    """Map a project symbol to a Tiingo ticker, or ``None`` when unsupported.

    Args:
        code: Project symbol such as ``AAPL.US`` or ``AAPL``.

    Returns:
        The bare lower-cased ticker Tiingo expects (e.g. ``aapl``), or ``None``
        for symbols that are clearly not US equities (HK/crypto/A-share).
    """
    upper = code.strip().upper()
    if not upper:
        return None
    if upper.endswith(".US"):
        upper = upper[:-3]
    # Reject non-US market suffixes and crypto pairs outright.
    if "." in upper or "-" in upper:
        return None
    if not upper.isalnum():
        return None
    return upper.lower()


def _rows_to_frame(rows: List[dict]) -> Optional[pd.DataFrame]:
    """Convert Tiingo's per-day records into the normalized OHLCV frame.

    Args:
        rows: JSON array decoded from the prices endpoint; each item carries a
            ``date`` plus ``open``/``high``/``low``/``close``/``volume``.

    Returns:
        A DataFrame indexed by a ``trade_date`` :class:`~pandas.DatetimeIndex`
        with float ``open``/``high``/``low``/``close``/``volume`` columns, or
        ``None`` when no usable bar is present.
    """
    parsed: List[dict] = []
    for row in rows:
        date = row.get("date")
        if date is None:
            continue
        parsed.append(
            {
                "trade_date": date,
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
            }
        )
    if not parsed:
        return None

    frame = pd.DataFrame(parsed)
    # Tiingo stamps each bar with an ISO-8601 datetime (e.g.
    # "2024-01-02T00:00:00.000Z"); normalize to a tz-naive midnight index.
    index = pd.DatetimeIndex(pd.to_datetime(frame["trade_date"], utc=True, errors="coerce"))
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert(None)
    frame = frame.drop(columns=["trade_date"])
    frame.index = index.normalize()
    frame.index.name = "trade_date"

    frame = frame.apply(pd.to_numeric, errors="coerce")
    # Coerce every OHLCV column to float64 so the schema is uniform: integer
    # JSON volumes would otherwise land as int64, breaking downstream code that
    # assumes a single numeric dtype.
    frame = frame.astype("float64")
    frame["volume"] = frame["volume"].fillna(0.0)
    frame = frame.loc[:, _OHLCV_COLUMNS].sort_index()
    frame = frame.dropna(subset=["open", "high", "low", "close"])
    return frame if not frame.empty else None


@register
class DataLoader:
    """Fetch US-equity daily OHLCV bars from Tiingo (key-gated REST)."""

    name = "tiingo"
    markets = {"us_equity"}
    requires_auth = True

    def __init__(self) -> None:
        """Initialize the loader (no network or SDK touched at construction)."""
        pass

    def is_available(self) -> bool:
        """Return whether a usable Tiingo API key is configured."""
        return bool(_resolve_key())

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch OHLCV history keyed by the original project symbols.

        Each symbol is fetched independently so one failing ticker (bad symbol,
        transient HTTP error) never aborts the rest of the batch.

        Args:
            codes: Project symbols such as ``AAPL.US`` or ``MSFT``.
            start_date: Inclusive start date in ``YYYY-MM-DD`` format.
            end_date: Inclusive end date in ``YYYY-MM-DD`` format.
            interval: Backtest interval; only ``1D`` is served by this endpoint.
            fields: Ignored; included for interface compatibility.

        Returns:
            Mapping of input symbol to a normalized OHLCV DataFrame. Symbols
            with no usable data are omitted.

        Raises:
            ValueError: If ``start_date`` > ``end_date`` or dates are unparseable.
        """
        del fields
        validate_date_range(start_date, end_date)

        key = _resolve_key()
        if not key:
            logger.warning("tiingo skipped: %s not configured", _AUTH_ENV)
            return {}

        result: Dict[str, pd.DataFrame] = {}
        for code in codes:
            try:
                frame = cached_loader_fetch(
                    source=self.name,
                    symbol=code,
                    timeframe=interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=None,
                    fetch=lambda code=code: self._fetch_one(code, start_date, end_date, key),
                )
                if frame is not None and not frame.empty:
                    result[code] = frame
            except Exception as exc:  # noqa: BLE001 - one symbol must not kill the batch
                logger.warning("tiingo failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str, key: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch and normalize a single symbol's daily bars.

        Args:
            code: Original project symbol.
            start_date: Inclusive start date in ``YYYY-MM-DD`` format.
            end_date: Inclusive end date in ``YYYY-MM-DD`` format.
            key: Resolved Tiingo API key.

        Returns:
            Normalized OHLCV DataFrame, or ``None`` when the symbol is not a US
            equity or the endpoint returns no usable bars.
        """
        ticker = _to_tiingo_symbol(code)
        if ticker is None:
            return None

        url = f"{_BASE_URL}/{ticker}/prices"
        payload = throttled_get_json(
            url,
            host_key=_HOST_KEY,
            min_interval=resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL),
            params={
                "startDate": start_date,
                "endDate": end_date,
                "token": key,
            },
        )

        # The prices endpoint returns a JSON array; anything else is empty/error.
        if not isinstance(payload, list) or not payload:
            return None
        return _rows_to_frame(payload)
