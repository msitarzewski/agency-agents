"""Stooq loader: free, no-auth US-equity EOD OHLCV via CSV download.

Stooq publishes free end-of-day bars from a plain CSV endpoint
(``https://stooq.com/q/d/l/``) with no API key. Like other free quote
providers it rate-limits by source IP and must be throttled, so every request
routes through :mod:`backtest.loaders._http` (shared per-host spacing + session
reuse) under the ``"stooq"`` host bucket.

API format:
  https://stooq.com/q/d/l/?s=aapl.us&d1=20240101&d2=20240131&i=d

Symbol convention (Vibe-Trading -> Stooq):
  * ``AAPL.US`` -> ``aapl.us`` (Stooq tickers are lowercase; the ``.US`` market
    suffix is kept, just lower-cased).

Response body is CSV ``Date,Open,High,Low,Close,Volume``. An unknown symbol or
empty window yields the literal ``"N/D"`` or an empty body, both treated as
"no data" for that symbol (skipped, never fatal to the batch).
"""

from __future__ import annotations

import io
import logging
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders._http import resolve_min_interval, throttled_get
from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_BASE_URL = "https://stooq.com/q/d/l/"
HOST_KEY = "stooq"

_MIN_INTERVAL_ENV = "VIBE_TRADING_STOOQ_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL_S = 0.6

# Stooq's CSV header columns mapped to our output field names.
_COLUMN_MAP = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
}
_OUTPUT_COLUMNS = ["open", "high", "low", "close", "volume"]


def _min_interval() -> float:
    """Resolve the per-call minimum spacing, honoring the env override."""
    return resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL_S)


def map_symbol(symbol: str) -> str:
    """Translate a Vibe-Trading symbol into Stooq's ticker convention.

    Args:
        symbol: Project-side symbol, e.g. ``AAPL.US``.

    Returns:
        The lower-cased Stooq ticker, e.g. ``aapl.us``.
    """
    return symbol.strip().lower()


def _compact_date(value: str) -> str:
    """Render a date string as Stooq's ``YYYYMMDD`` form."""
    return pd.Timestamp(value).strftime("%Y%m%d")


@register
class DataLoader:
    """Stooq US-equity EOD OHLCV loader (free, HTTP CSV, no auth)."""

    name = "stooq"
    markets = {"us_equity"}
    requires_auth = False

    def __init__(self) -> None:
        pass

    def is_available(self) -> bool:
        """Always available — uses plain throttled HTTP, no credentials."""
        return True

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch daily OHLCV bars for ``codes`` over ``[start_date, end_date]``.

        Args:
            codes: Project-side symbols (e.g. ``["AAPL.US", "MSFT.US"]``).
            start_date: Inclusive start date (``YYYY-MM-DD``).
            end_date: Inclusive end date (``YYYY-MM-DD``).
            interval: Bar size; only daily (``"1D"``) is supported by the
                endpoint and any other value is fetched as daily.
            fields: Unused — the CSV always carries the full OHLCV set.

        Returns:
            Mapping ``{symbol: DataFrame}`` for symbols that returned data. Each
            frame has a ``DatetimeIndex`` named ``trade_date`` and float columns
            ``open/high/low/close/volume`` in ascending date order. A symbol that
            errors or has no data is omitted, never aborting the batch.

        Raises:
            ValueError: If ``start_date > end_date`` or a date is unparseable.
        """
        validate_date_range(start_date, end_date)

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
                    fetch=lambda code=code: self._fetch_one(code, start_date, end_date),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:  # noqa: BLE001 - one bad symbol must not abort the batch
                logger.warning("stooq failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch and parse one symbol's CSV; ``None`` when Stooq has no data."""
        params = {
            "s": map_symbol(code),
            "d1": _compact_date(start_date),
            "d2": _compact_date(end_date),
            "i": "d",
        }
        response = throttled_get(
            _BASE_URL,
            host_key=HOST_KEY,
            min_interval=_min_interval(),
            params=params,
        )
        response.raise_for_status()
        return _parse_csv(response.text)


def _parse_csv(body: str) -> Optional[pd.DataFrame]:
    """Convert a Stooq EOD CSV body into our OHLCV frame, ``None`` on no data.

    Args:
        body: Raw CSV text ``Date,Open,High,Low,Close,Volume``. An empty body or
            the sentinel ``"N/D"`` (unknown symbol / empty window) means no data.

    Returns:
        A frame indexed by ``trade_date`` with float OHLCV columns sorted
        ascending, or ``None`` when the body carries no usable rows.
    """
    text = (body or "").strip()
    if not text or text.upper().startswith("N/D"):
        return None

    frame = pd.read_csv(io.StringIO(text))
    if frame.empty or "Date" not in frame.columns:
        return None

    rename = {col: _COLUMN_MAP[col] for col in _COLUMN_MAP if col in frame.columns}
    frame = frame.rename(columns=rename)
    if not all(col in frame.columns for col in _OUTPUT_COLUMNS):
        return None

    frame["trade_date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.dropna(subset=["trade_date"]).set_index("trade_date").sort_index()
    frame.index.name = "trade_date"

    for col in _OUTPUT_COLUMNS:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame[_OUTPUT_COLUMNS].dropna(subset=["open", "high", "low", "close"])
    if frame.empty:
        return None
    return frame.astype(float)
