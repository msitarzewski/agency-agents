"""Alpha Vantage loader: US-equity daily OHLCV via the free key-gated REST API.

Alpha Vantage serves daily bars at ``/query?function=TIME_SERIES_DAILY`` and
gates access behind a free API key (env ``ALPHAVANTAGE_API_KEY``). The endpoint
rate-limits per IP, so every request routes through
:mod:`backtest.loaders._http` for per-host throttling and session reuse rather
than calling :mod:`requests` directly.

API format::

    https://www.alphavantage.co/query?function=TIME_SERIES_DAILY
        &symbol=AAPL&outputsize=full&apikey=<KEY>

The JSON payload nests the bars under ``"Time Series (Daily)"`` keyed by
``YYYY-MM-DD`` date strings, each mapping to numbered OHLCV fields
(``"1. open"`` .. ``"5. volume"``). Throttle/quota responses arrive as a plain
``"Note"`` / ``"Information"`` envelope, and bad symbols as ``"Error Message"``;
all three are surfaced as a transient-classified error so one symbol's failure
never aborts the batch.
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

_BASE_URL = "https://www.alphavantage.co/query"

# Throttle/session bucket shared by all Alpha Vantage calls. The free tier is
# quota-limited per key/IP, so requests are spaced out by default.
_HOST_KEY = "alphavantage"
_MIN_INTERVAL_ENV = "VIBE_TRADING_ALPHAVANTAGE_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL = 1.0

_API_KEY_ENV = "ALPHAVANTAGE_API_KEY"
# Env values that are present-but-meaningless and must be treated as absent.
_API_KEY_PLACEHOLDERS = {"", "your-alphavantage-api-key", "demo"}

# Bars live under this top-level key; the per-bar OHLCV fields are numbered.
_TIME_SERIES_KEY = "Time Series (Daily)"
_FIELD_MAP = {
    "open": "1. open",
    "high": "2. high",
    "low": "3. low",
    "close": "4. close",
    "volume": "5. volume",
}
_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def _resolve_api_key() -> str:
    """Return the configured Alpha Vantage API key, or empty when unset.

    Returns:
        The trimmed key, or ``""`` when the env var is absent or a placeholder.
    """
    key = os.getenv(_API_KEY_ENV, "").strip()
    return "" if key in _API_KEY_PLACEHOLDERS else key


def _min_interval() -> float:
    """Resolve the per-call minimum Alpha Vantage request spacing in seconds."""
    return resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL)


def _extract_provider_message(payload: object) -> Optional[str]:
    """Return any rate-limit / error envelope message from a payload.

    Alpha Vantage signals quota exhaustion and bad requests in-band with a 200
    status, using one of three string envelopes instead of the time series.

    Args:
        payload: The decoded JSON body.

    Returns:
        The envelope message when present, else ``None``.
    """
    if not isinstance(payload, dict):
        return None
    for key in ("Error Message", "Note", "Information"):
        message = payload.get(key)
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None


@register
class DataLoader:
    """Alpha Vantage US-equity daily OHLCV loader (key-gated REST, throttled)."""

    name = "alphavantage"
    markets = {"us_equity"}
    requires_auth = True

    def is_available(self) -> bool:
        """Available when a non-placeholder ``ALPHAVANTAGE_API_KEY`` is set."""
        return bool(_resolve_api_key())

    def __init__(self) -> None:
        pass

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch daily OHLCV bars for ``codes`` within ``[start_date, end_date]``.

        Args:
            codes: US-equity tickers (e.g. ``["AAPL", "MSFT"]``).
            start_date: Inclusive start date ``YYYY-MM-DD``.
            end_date: Inclusive end date ``YYYY-MM-DD``.
            interval: Bar interval; only ``"1D"`` (daily) is supported.
            fields: Ignored — the full OHLCV column set is always returned.

        Returns:
            Mapping ``{symbol: DataFrame}`` with a ``trade_date`` DatetimeIndex
            and float ``open/high/low/close/volume`` columns. Symbols that fail
            or carry no in-range bars are omitted.
        """
        validate_date_range(start_date, end_date)

        api_key = _resolve_api_key()
        if not api_key:
            logger.warning("alphavantage skipped: %s not set", _API_KEY_ENV)
            return {}

        result: Dict[str, pd.DataFrame] = {}
        for code in codes:
            try:
                df = cached_loader_fetch(
                    source=self.name,
                    symbol=code,
                    timeframe=interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=None,
                    fetch=lambda code=code: self._fetch_one(
                        code, start_date, end_date, api_key
                    ),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:  # noqa: BLE001 - one bad symbol must not abort the batch
                logger.warning("alphavantage failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str, api_key: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch and slice one symbol's daily bars into an OHLCV DataFrame.

        Args:
            code: US-equity ticker.
            start_date: Inclusive start date ``YYYY-MM-DD``.
            end_date: Inclusive end date ``YYYY-MM-DD``.
            api_key: Resolved Alpha Vantage API key.

        Returns:
            The in-range OHLCV DataFrame, or ``None`` when the payload carries
            no usable bars.

        Raises:
            ValueError: The provider returned a rate-limit / error envelope and
                no usable time series (a data-bearing payload that also carries
                an upsell note is parsed, not rejected).
            requests.RequestException: Network failure, propagated unchanged.
        """
        symbol = code.strip().upper()
        if not symbol:
            return None

        payload = throttled_get_json(
            _BASE_URL,
            host_key=_HOST_KEY,
            min_interval=_min_interval(),
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "full",
                "apikey": api_key,
            },
        )

        series = payload.get(_TIME_SERIES_KEY) if isinstance(payload, dict) else None
        if not isinstance(series, dict) or not series:
            # No usable series: a premium-upsell payload can carry both the data
            # key (empty/absent) and a Note/Information envelope, so only now —
            # with nothing to parse — do we surface the envelope as an error.
            message = _extract_provider_message(payload)
            if message is not None:
                raise ValueError(f"alphavantage rejected {symbol}: {message}")
            return None

        rows = [
            row
            for date, bar in series.items()
            if (row := _parse_bar(date, bar)) is not None
        ]
        if not rows:
            return None

        df = pd.DataFrame(rows)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.set_index("trade_date").sort_index()
        df = df[_OHLCV_COLUMNS].dropna(subset=["open", "high", "low", "close"])

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
        df = df.loc[(df.index >= start) & (df.index <= end)]
        return df


def _parse_bar(date: str, bar: object) -> Optional[dict]:
    """Parse one ``{date: {"1. open": ...}}`` entry into an OHLCV row dict.

    Args:
        date: The bar's ``YYYY-MM-DD`` date string.
        bar: The per-bar field mapping from the payload.

    Returns:
        A ``{trade_date, open, high, low, close, volume}`` dict, or ``None``
        when the entry is malformed or non-numeric.
    """
    if not isinstance(bar, dict):
        return None
    try:
        return {
            "trade_date": date,
            "open": float(bar[_FIELD_MAP["open"]]),
            "high": float(bar[_FIELD_MAP["high"]]),
            "low": float(bar[_FIELD_MAP["low"]]),
            "close": float(bar[_FIELD_MAP["close"]]),
            "volume": float(bar[_FIELD_MAP["volume"]]),
        }
    except (KeyError, TypeError, ValueError):
        return None
