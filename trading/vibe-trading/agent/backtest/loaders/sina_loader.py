"""Sina Finance loader: free, no-auth US daily OHLCV via the JSONP K-line API.

Sina exposes US daily candles through a JSONP endpoint that wraps a JSON array
of ``{d,o,h,l,c,v}`` bars in a JavaScript variable assignment. We request it,
strip the JSONP wrapper, and reshape into the loader's standard OHLCV frame.

API format (JSONP)::

  https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/var%20x=/US_MinKService.getDailyK?symbol=AAPL

Like Eastmoney, Sina rate-limits by source IP, so every request routes through
the shared per-host throttle in :mod:`backtest.loaders._http`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders._http import resolve_min_interval, throttled_get
from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_BASE_URL = (
    "https://stock.finance.sina.com.cn/usstock/api/jsonp_v2.php/"
    "var%20x=/US_MinKService.getDailyK"
)
_HOST_KEY = "sina"
_MIN_INTERVAL_ENV = "VIBE_TRADING_SINA_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL = 0.5

# Sina wraps the payload as ``var x=([...]);`` — the JSON array sits inside an
# optional ``(...)``. Capture the outermost bracketed array, ignoring the
# assignment/paren scaffolding around it.
_JSONP_ARRAY_RE = re.compile(r"(\[.*\])", re.DOTALL)


def _is_us_equity(code: str) -> bool:
    """Return whether ``code`` is a US-equity symbol this loader handles."""
    return bool(code) and code.upper().endswith(".US")


def _to_sina_symbol(code: str) -> str:
    """Map an internal code to Sina's bare ticker (``"AAPL.US"`` -> ``"AAPL"``)."""
    return code.upper().rsplit(".", 1)[0]


def _strip_jsonp(raw: str) -> list:
    """Extract the JSON array embedded in Sina's JSONP wrapper.

    Args:
        raw: Raw response body, e.g. ``var x=([{"d":"2024-01-02",...}]);``.

    Returns:
        The decoded list of bar dicts.

    Raises:
        ValueError: If no JSON array can be located or decoded.
    """
    match = _JSONP_ARRAY_RE.search(raw.strip())
    if not match:
        raise ValueError("no JSON array found in Sina JSONP response")
    bars = json.loads(match.group(1))
    if not isinstance(bars, list):
        raise ValueError("Sina JSONP payload is not a list of bars")
    return bars


def _bars_to_frame(bars: list, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """Reshape Sina ``{d,o,h,l,c,v}`` bars into the standard OHLCV frame.

    Args:
        bars: List of per-day dicts with ``d/o/h/l/c/v`` keys.
        start_date: Inclusive window start (YYYY-MM-DD).
        end_date: Inclusive window end (YYYY-MM-DD).

    Returns:
        A DatetimeIndex (named ``trade_date``) frame with float columns
        ``open/high/low/close/volume`` clipped to the window, or ``None`` when
        no usable rows survive parsing.
    """
    rows = []
    for bar in bars:
        if not isinstance(bar, dict) or "d" not in bar:
            continue
        try:
            rows.append(
                {
                    "trade_date": bar["d"],
                    "open": float(bar["o"]),
                    "high": float(bar["h"]),
                    "low": float(bar["l"]),
                    "close": float(bar["c"]),
                    "volume": float(bar["v"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    if not rows:
        return None

    frame = pd.DataFrame(rows)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame = frame.set_index("trade_date").sort_index()
    frame = frame[["open", "high", "low", "close", "volume"]].dropna(
        subset=["open", "high", "low", "close"]
    )
    window = frame.loc[
        (frame.index >= pd.Timestamp(start_date))
        & (frame.index <= pd.Timestamp(end_date))
    ]
    return window if not window.empty else None


@register
class DataLoader:
    """Sina Finance US-equity daily OHLCV loader (free, HTTP/JSONP, no auth)."""

    name = "sina"
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
        """Fetch US daily OHLCV for each code; skip and log per-symbol failures.

        Args:
            codes: Symbols in ``TICKER.US`` form (e.g. ``"AAPL.US"``).
            start_date: Inclusive window start (YYYY-MM-DD).
            end_date: Inclusive window end (YYYY-MM-DD).
            interval: Bar interval; only daily (``"1D"``) is supported.
            fields: Ignored — the standard OHLCV columns are always returned.

        Returns:
            Mapping ``{code: DataFrame}`` for every code that yielded bars.

        Raises:
            ValueError: If ``interval`` is not daily or the date range is invalid.
        """
        if interval.upper() not in {"1D", "D", "DAY", "DAILY"}:
            raise ValueError(f"Unsupported interval {interval!r}; sina is daily-only")
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
            except Exception as exc:
                logger.warning("sina failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch and parse one symbol's daily bars, or ``None`` if non-US/empty."""
        if not _is_us_equity(code):
            return None

        symbol = _to_sina_symbol(code)
        response = throttled_get(
            _BASE_URL,
            host_key=_HOST_KEY,
            min_interval=resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL),
            params={"symbol": symbol},
            headers={"Referer": "https://stock.finance.sina.com.cn/"},
        )
        response.raise_for_status()
        bars = _strip_jsonp(response.text)
        return _bars_to_frame(bars, start_date, end_date)
