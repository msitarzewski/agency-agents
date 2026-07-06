"""CCXT loader: unified crypto exchange data (100+ exchanges).

Uses the CCXT library to fetch OHLCV candles from any supported exchange.
Defaults to Binance; configurable via CCXT_EXCHANGE env var.
No API key required for public market data.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders.base import (
    cached_loader_fetch,
    check_budget,
    positive_env_float,
    positive_env_int,
    retry_with_budget,
    validate_date_range,
)
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1H": "1h", "4H": "4h", "1D": "1d",
}

# P12-b: ccxt had no request timeout and an unbounded paginated fetch with
# no retry budget, so a transient disconnect hung get_market_data for 10+
# minutes. Cap each HTTP call, bound transient retries, and enforce a hard
# wall-clock budget so the fetch fails fast instead of hanging. Retry
# scheduling is delegated to :mod:`backtest.loaders.base`.
_CCXT_TIMEOUT_MS = positive_env_int("CCXT_TIMEOUT_MS", 15_000)
_CCXT_FETCH_BUDGET_S = positive_env_float("CCXT_FETCH_BUDGET_S", 60.0)


def _first_proxy_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _ccxt_proxy_config() -> dict[str, str]:
    """Build CCXT proxy settings from conventional proxy environment variables."""
    all_proxy = _first_proxy_env("ALL_PROXY", "all_proxy")
    http_proxy = _first_proxy_env("HTTP_PROXY", "http_proxy") or all_proxy
    https_proxy = _first_proxy_env("HTTPS_PROXY", "https_proxy") or all_proxy or http_proxy

    proxies: dict[str, str] = {}
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy
    return proxies


@register
class DataLoader:
    """CCXT-backed crypto OHLCV loader (100+ exchanges)."""

    name = "ccxt"
    markets = {"crypto"}
    requires_auth = False

    def is_available(self) -> bool:
        """Available if ccxt is installed."""
        try:
            import ccxt  # noqa: F401
            return True
        except ImportError:
            return False

    def __init__(self) -> None:
        pass

    def _get_exchange(self):
        """Create exchange instance."""
        import ccxt
        exchange_id = os.getenv("CCXT_EXCHANGE", "binance").lower()
        exchange_cls = getattr(ccxt, exchange_id, None)
        if exchange_cls is None:
            logger.warning("Unknown CCXT exchange %s, falling back to binance", exchange_id)
            exchange_cls = ccxt.binance

        config = {"enableRateLimit": True, "timeout": _CCXT_TIMEOUT_MS}
        proxies = _ccxt_proxy_config()
        if proxies:
            config["proxies"] = proxies
        return exchange_cls(config)

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch crypto OHLCV via CCXT.

        Args:
            codes: Symbols like ``["BTC-USDT", "ETH-USDT"]``.
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            interval: Bar size.
            fields: Ignored.

        Returns:
            Mapping symbol -> OHLCV DataFrame.
        """
        validate_date_range(start_date, end_date)

        timeframe = _INTERVAL_MAP.get(interval, "1d")
        since_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
        end_ms = int((pd.Timestamp(end_date) + pd.Timedelta(days=1)).timestamp() * 1000)

        # Build the exchange lazily so a full cache hit never imports ccxt or
        # opens an exchange object.
        exchange_holder: Dict[str, object] = {}

        def get_exchange():
            if "exchange" not in exchange_holder:
                exchange_holder["exchange"] = self._get_exchange()
            return exchange_holder["exchange"]

        result: Dict[str, pd.DataFrame] = {}
        for code in codes:
            try:
                ccxt_symbol = code.replace("-", "/").upper()
                df = cached_loader_fetch(
                    source=self.name,
                    symbol=code,
                    timeframe=interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=None,
                    fetch=lambda ccxt_symbol=ccxt_symbol: self._fetch_one(
                        get_exchange(), ccxt_symbol, timeframe, since_ms, end_ms
                    ),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:
                logger.warning("CCXT failed for %s: %s", code, exc)
        return result

    @staticmethod
    def _fetch_one(
        exchange, symbol: str, timeframe: str, since_ms: int, end_ms: int,
    ) -> Optional[pd.DataFrame]:
        """Paginated OHLCV fetch for one symbol."""
        import ccxt

        all_rows: list = []
        cursor = since_ms
        limit = 1000
        deadline = time.monotonic() + _CCXT_FETCH_BUDGET_S
        label = f"ccxt fetch for {symbol}"

        for _ in range(200):
            check_budget(deadline, label, budget_s=_CCXT_FETCH_BUDGET_S)
            # ``ccxt.NetworkError`` covers RequestTimeout / DDoSProtection /
            # ExchangeNotAvailable — the transient family. Anything else
            # (e.g. ``ExchangeError`` for a bad symbol) is not retried.
            ohlcv = retry_with_budget(
                lambda: exchange.fetch_ohlcv(symbol, timeframe, since=cursor, limit=limit),
                transient=ccxt.NetworkError,
                deadline=deadline,
                label=label,
            )
            if not ohlcv:
                break
            all_rows.extend(ohlcv)
            last_ts = ohlcv[-1][0]
            if last_ts >= end_ms or len(ohlcv) < limit:
                break
            cursor = last_ts + 1

        if not all_rows:
            return None

        df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["trade_date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("trade_date").sort_index()

        start_dt = pd.Timestamp(since_ms, unit="ms")
        end_dt = pd.Timestamp(end_ms, unit="ms")
        df = df[(df.index >= start_dt) & (df.index < end_dt)]

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].dropna(
            subset=["open", "high", "low", "close"]
        )
        return df if not df.empty else None
