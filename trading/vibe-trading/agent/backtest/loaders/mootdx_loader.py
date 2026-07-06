"""Mootdx loader: A-share OHLCV via TCP-direct 通达信 servers (no IP ban).

Mootdx (https://github.com/mootdx/mootdx) talks the native 通达信 binary
protocol over TCP and is not subject to the HTTP scraping rate limits that
periodically break the akshare → East Money path. Public market data only,
no token required, no per-IP throttling.

Scope: A-share OHLCV only (沪/深/京 auto-detected from symbol). Mootdx's
extended-market endpoint (futures/options) is upstream-broken as of
v0.11.7 — falls through to tushare/akshare for those markets.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

# Mootdx frequency codes (see mootdx.consts).
_INTRADAY_FREQ: dict[str, int] = {
    "1m": 8,
    "5m": 0,
    "15m": 1,
    "30m": 2,
    "1H": 3,
}
_DAILY_FREQ: dict[str, int] = {
    "1D": 4,
    "1W": 5,
    "1M": 6,
}

# bars() returns one page of N rows ending at the latest bar. Pages older
# than this need to be requested with ``start=offset_into_history``. We cap
# pagination at MAX_PAGES so a wildly out-of-range request can't grind for
# minutes against the TDX server.
_BARS_PAGE = 800
_MAX_PAGES = 25  # 25 × 800 = 20 000 bars (~10y daily, ~5y 1H, ~3mo 1m)


def _is_a_share(code: str) -> bool:
    """Accept either explicit `.SH/.SZ/.BJ` suffix or bare 6-digit ticker."""
    upper = code.upper()
    if upper.endswith((".SH", ".SZ", ".BJ")):
        return True
    return len(code) == 6 and code.isdigit()


def _is_bj(code: str) -> bool:
    """Detect 北交所 symbols. Mootdx std factory does not serve BJ data
    (get_k_data raises KeyError, bars() returns empty), so the loader logs
    a warning and skips these instead of silently returning nothing."""
    upper = code.upper()
    if upper.endswith(".BJ"):
        return True
    # 4xxxxx / 8xxxxx are BJ prefixes (bare 6-digit form).
    return len(code) == 6 and code.isdigit() and code[0] in ("4", "8")


@register
class DataLoader:
    """Mootdx-backed A-share OHLCV loader (TCP-direct, no auth)."""

    name = "mootdx"
    markets = {"a_share"}
    requires_auth = False

    def __init__(self) -> None:
        self._client = None

    def is_available(self) -> bool:
        """Available if mootdx is installed."""
        try:
            import mootdx  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_client(self):
        if self._client is None:
            from mootdx.quotes import Quotes
            self._client = Quotes.factory(market="std")
        return self._client

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch A-share OHLCV via mootdx.

        Args:
            codes: Symbol list. `.SH/.SZ/.BJ` suffix or bare 6-digit
                tickers; non-A-share symbols are silently skipped.
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.
            interval: One of ``1m / 5m / 15m / 30m / 1H / 1D / 1W / 1M``.
            fields: Ignored.

        Returns:
            Mapping symbol -> OHLCV DataFrame.

        Raises:
            ValueError: If ``interval`` is not in the supported set.
        """
        validate_date_range(start_date, end_date)
        if interval not in _DAILY_FREQ and interval not in _INTRADAY_FREQ:
            raise ValueError(
                f"Unsupported interval for mootdx: {interval!r}. "
                f"Supported: {sorted(_DAILY_FREQ) + sorted(_INTRADAY_FREQ)}"
            )

        result: Dict[str, pd.DataFrame] = {}
        for code in codes:
            if not _is_a_share(code):
                logger.debug("mootdx: skipping non-A-share symbol %s", code)
                continue
            if _is_bj(code):
                logger.warning(
                    "mootdx: 北交所 (%s) not supported upstream; use akshare/tushare",
                    code,
                )
                continue
            try:
                df = cached_loader_fetch(
                    source=self.name,
                    symbol=code,
                    timeframe=interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=None,
                    fetch=lambda code=code: self._fetch_one(code, start_date, end_date, interval),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:
                logger.warning("mootdx failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str, interval: str,
    ) -> Optional[pd.DataFrame]:
        symbol = code.split(".")[0]
        client = self._get_client()

        # Daily has a native date-range API; intraday and weekly/monthly
        # only expose offset-from-latest, so we page back through history
        # until the first row of the page is older than start_date.
        if interval == "1D":
            df = client.get_k_data(code=symbol, start_date=start_date, end_date=end_date)
            return self._normalize_daily(df)

        freq = _DAILY_FREQ.get(interval) or _INTRADAY_FREQ[interval]
        return self._fetch_bars_paginated(client, symbol, freq, start_date, end_date)

    @staticmethod
    def _fetch_bars_paginated(
        client, symbol: str, freq: int, start_date: str, end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Walk backward through ``bars()`` pages until the requested
        window is covered, then clip and concatenate.

        Mootdx ``bars()`` returns the latest ``_BARS_PAGE`` rows by default;
        ``start=N`` skips the newest N rows. We page until the oldest row
        in a page is at or before ``start_date``, or until ``_MAX_PAGES``
        is exhausted (very old or thinly-traded symbols).
        """
        start_ts = pd.Timestamp(start_date)
        chunks: list[pd.DataFrame] = []
        for page in range(_MAX_PAGES):
            df = client.bars(
                symbol=symbol,
                frequency=freq,
                start=page * _BARS_PAGE,
                offset=_BARS_PAGE,
            )
            if df is None or df.empty:
                break
            chunks.append(df)
            first_dt = pd.to_datetime(df["datetime"].iloc[0])
            if first_dt <= start_ts:
                break
        else:
            logger.warning(
                "mootdx: %s %s pagination hit cap (%d pages) without reaching %s",
                symbol, freq, _MAX_PAGES, start_date,
            )
        if not chunks:
            return None
        combined = pd.concat(chunks, ignore_index=False)
        return DataLoader._normalize_bars(combined, start_date, end_date)

    @staticmethod
    def _normalize_daily(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Normalize `get_k_data()` output to the OHLCV contract.

        get_k_data returns columns ``[open, close, high, low, vol, amount,
        date, code]`` with ``date`` as the index name.
        """
        if df is None or df.empty:
            return None
        out = df.rename(columns={"vol": "volume"}).copy()
        out.index = pd.to_datetime(out.index)
        out.index.name = "trade_date"
        for col in ("open", "high", "low", "close", "volume"):
            out[col] = pd.to_numeric(out[col], errors="coerce")
        out = out[["open", "high", "low", "close", "volume"]].dropna(
            subset=["open", "high", "low", "close"]
        )
        return out.sort_index() if not out.empty else None

    @staticmethod
    def _normalize_bars(
        df: Optional[pd.DataFrame], start_date: str, end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Normalize `bars()` output and clip to the requested window.

        bars() returns ``[open, close, high, low, vol, amount, year, month,
        day, hour, minute, datetime, volume]`` with a datetime index.
        ``volume`` (lowercase, last column) is the canonical share count;
        ``vol`` is a historical alias kept by mootdx for compatibility.
        """
        if df is None or df.empty:
            return None
        out = df.copy()
        if "datetime" in out.columns:
            out["trade_date"] = pd.to_datetime(out["datetime"])
            out = out.set_index("trade_date")
        else:
            out.index = pd.to_datetime(out.index)
            out.index.name = "trade_date"
        out = out.sort_index()
        for col in ("open", "high", "low", "close", "volume"):
            out[col] = pd.to_numeric(out[col], errors="coerce")
        out = out[["open", "high", "low", "close", "volume"]].dropna(
            subset=["open", "high", "low", "close"]
        )
        # Inclusive end-of-day so a `2025-02-01` window keeps the 15:00 bar.
        end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        out = out.loc[pd.Timestamp(start_date):end_ts]
        return out if not out.empty else None
