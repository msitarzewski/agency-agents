"""Yahoo Finance loader: free, no-auth US/HK equity OHLCV via direct HTTP.

Wraps the shared :mod:`backtest.loaders.yahoo_client` (the public v8 chart
endpoint) rather than the ``yfinance`` package, so it pulls in no new
dependency and shares the process-wide throttle/session that keeps Yahoo from
IP-rate-limiting us. Covers US equities (``AAPL.US``) and HK equities
(``00700.HK``); the client maps each project symbol to Yahoo's ticker form.

The chart endpoint returns each bar's ``trade_date`` as an epoch-second
timestamp; this loader converts those to a tz-naive ``DatetimeIndex`` and clips
the ascending series to the requested inclusive date window.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders import yahoo_client
from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")

# Project interval -> Yahoo chart interval. Daily is the only granularity this
# loader exposes for equities; anything else falls back to lowercasing so an
# explicit ``5m``/``1h`` still reaches Yahoo unchanged.
_INTERVAL_MAP = {
    "1D": "1d",
    "1H": "1h",
    "1W": "1wk",
    "1M": "1mo",
}


def _is_us_or_hk(code: str) -> bool:
    """Return whether *code* is a US or HK equity symbol this loader handles."""
    return code.strip().upper().endswith((".US", ".HK"))


def _to_yahoo_interval(interval: str) -> str:
    """Map a project interval string to Yahoo's chart interval string.

    Args:
        interval: Backtest interval such as ``1D`` or ``1H``.

    Returns:
        Yahoo-compatible interval string (e.g. ``1d``).
    """
    normalized = str(interval or "1D").strip()
    return _INTERVAL_MAP.get(normalized.upper(), normalized.lower())


def _is_intraday_interval(interval: str) -> bool:
    """Return whether *interval* is finer than one day (minute/hour bars).

    Daily-and-coarser intervals (``1D``/``1W``/``1M``) carry no meaningful
    intraday time and must be midnight-indexed to align with every other
    loader's daily bars; minute/hour intervals keep their real timestamp.

    Project convention follows the interval map: a bare trailing ``M`` is a
    month (e.g. ``1M``) while a bare trailing lowercase ``m`` is a minute (e.g.
    ``5m``), so case is significant for that one suffix and is NOT folded.

    Args:
        interval: Backtest interval such as ``1D``, ``1H``, ``5m`` or ``30min``.

    Returns:
        ``True`` for minute/hour granularities, ``False`` for day/week/month.
    """
    raw = str(interval or "1D").strip()
    if not raw:
        return False
    lowered = raw.lower()
    # Multi-letter month forms ('mo'/'mth'/'mon') are daily-coarser.
    if lowered.endswith(("mo", "mth", "mon")):
        return False
    # Explicit minute spellings and hours are intraday.
    if lowered.endswith(("min", "h")):
        return True
    # Bare trailing letter: lowercase 'm' = minute (intraday), uppercase
    # 'M' = month (coarser), 'd'/'w' = day/week (coarser).
    return raw.endswith("m")


def _epoch_seconds(date_str: str) -> int:
    """Convert a ``YYYY-MM-DD`` date to UTC midnight epoch seconds.

    Computed from the parsed calendar date (not ``time.time()``) so the window
    is reproducible and independent of wall-clock fetch time.

    Args:
        date_str: Date string in ``YYYY-MM-DD`` form.

    Returns:
        Epoch seconds for that date's UTC midnight.
    """
    day = pd.Timestamp(date_str).normalize().date()
    moment = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    return int(moment.timestamp())


def _rows_to_frame(
    rows: List[dict], start_date: str, end_date: str, interval: str = "1D"
) -> pd.DataFrame:
    """Build the OHLCV frame from chart rows, clipped to the inclusive window.

    For daily-and-coarser intervals the DatetimeIndex is normalized to midnight
    so the dates line up with every other loader's midnight-indexed daily bars
    (Yahoo stamps daily bars at the US market-open epoch, e.g. 14:30 UTC, which
    would otherwise break fallback merge/join/dedup). Minute/hour intervals keep
    their real intraday timestamp.

    Args:
        rows: Ascending ``{trade_date(epoch s), open, high, low, close, volume}``
            dicts from :func:`yahoo_client.get_chart`.
        start_date: Inclusive window start (``YYYY-MM-DD``).
        end_date: Inclusive window end (``YYYY-MM-DD``).
        interval: Backtest interval such as ``1D`` or ``1H``; selects whether the
            index is normalized to midnight.

    Returns:
        DataFrame indexed by a tz-naive ``trade_date`` with float OHLCV columns,
        or an empty frame when no row carries usable OHLC.
    """
    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame(rows)
    index = pd.to_datetime(frame["trade_date"], unit="s", utc=True).dt.tz_convert(None)
    if not _is_intraday_interval(interval):
        index = index.dt.normalize()
    frame = frame.drop(columns=["trade_date"])
    frame.index = pd.DatetimeIndex(index)
    frame.index.name = "trade_date"

    for column in _OHLCV_COLUMNS:
        if column not in frame.columns:
            frame[column] = 0.0 if column == "volume" else pd.NA

    frame = frame.loc[:, list(_OHLCV_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    frame["volume"] = frame["volume"].fillna(0.0)
    frame = frame.dropna(subset=["open", "high", "low", "close"])

    lower = pd.Timestamp(start_date).normalize()
    upper = pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1)
    frame = frame[(frame.index >= lower) & (frame.index < upper)]
    return frame.astype(float).sort_index()


@register
class DataLoader:
    """Yahoo Finance US/HK equity OHLCV loader (free, direct HTTP, no auth)."""

    name = "yahoo"
    markets = {"us_equity", "hk_equity"}
    requires_auth = False

    def is_available(self) -> bool:
        """Always available — uses the throttled public HTTP client."""
        return True

    def __init__(self) -> None:
        """Initialize the loader (no credentials needed for public data)."""
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
        """Fetch OHLCV history keyed by the original project symbols.

        Args:
            codes: Project symbols such as ``AAPL.US`` and ``00700.HK``.
            start_date: Inclusive start date (``YYYY-MM-DD``).
            end_date: Inclusive end date (``YYYY-MM-DD``).
            interval: Backtest interval such as ``1D`` or ``1H``.
            fields: Ignored; included for interface compatibility.

        Returns:
            Mapping of input symbol to a normalized OHLCV DataFrame. A symbol
            that fails or returns no data is omitted; one failure never aborts
            the batch.
        """
        del fields
        if not codes:
            return {}
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
                    fetch=lambda code=code: self._fetch_one(
                        code, start_date, end_date, interval
                    ),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:
                logger.warning("yahoo failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str, interval: str
    ) -> Optional[pd.DataFrame]:
        """Fetch and normalize one symbol's chart, or ``None`` when unusable.

        Args:
            code: A single project symbol.
            start_date: Inclusive start date (``YYYY-MM-DD``).
            end_date: Inclusive end date (``YYYY-MM-DD``).
            interval: Backtest interval string.

        Returns:
            The OHLCV DataFrame for *code*, ``None`` if it is not a US/HK symbol
            or Yahoo returns no usable bars.
        """
        if not _is_us_or_hk(code):
            return None

        # period2 is exclusive on Yahoo; extend one day past end_date so the
        # final inclusive bar is fetched, then clip precisely in _rows_to_frame.
        period1 = _epoch_seconds(start_date)
        period2 = _epoch_seconds(end_date) + 86400

        rows = yahoo_client.get_chart(
            code,
            interval=_to_yahoo_interval(interval),
            period1=period1,
            period2=period2,
        )
        frame = _rows_to_frame(rows, start_date, end_date, interval)
        return frame if not frame.empty else None
