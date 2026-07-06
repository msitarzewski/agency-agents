"""Tushare loader for A-share daily and intraday bars plus optional fundamentals.

Supports ``interval``: 1D (default) / 1m / 5m / 15m / 30m / 1H.
Minute data uses ``pro.stk_mins()`` (Tushare points >= 2000).
"""

import os
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders._symbol_utils import _is_etf_listed
from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register


TUSHARE_TOKEN_PLACEHOLDERS = {"", "your-tushare-token"}


def _is_index(code: str) -> bool:
    """Detect A-share index symbols (000xxx.SH, 000300.SH, 399xxx.SZ)."""
    upper = code.upper()
    if upper.endswith(".SH"):
        digits = upper.split(".")[0]
        return len(digits) == 6 and digits.isdigit() and digits.startswith("000")
    if upper.endswith(".SZ"):
        digits = upper.split(".")[0]
        return len(digits) == 6 and digits.isdigit() and digits.startswith("399")
    return False


def _is_hk_equity(code: str) -> bool:
    """Detect Hong Kong equity symbols (e.g. 00700.HK)."""
    return code.upper().endswith(".HK")


def _is_us_equity(code: str) -> bool:
    """Detect US equity symbols (e.g. AAPL.US)."""
    return code.upper().endswith(".US")


def _is_crypto(code: str) -> bool:
    """Detect crypto symbols (e.g. BTC-USDT, ETH/USDT)."""
    upper = code.upper()
    return upper.endswith("-USDT") or upper.endswith("/USDT")


@register
class DataLoader:
    """Tushare-backed OHLCV loader."""

    name = "tushare"
    markets = {"a_share", "futures", "fund"}
    requires_auth = True

    def is_available(self) -> bool:
        """Available when TUSHARE_TOKEN is set."""
        return os.getenv("TUSHARE_TOKEN", "").strip() not in TUSHARE_TOKEN_PLACEHOLDERS

    def __init__(self) -> None:
        """Initialize Tushare pro API."""
        import tushare as ts

        token = os.getenv("TUSHARE_TOKEN", "")
        self.api = ts.pro_api(token)

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        interval: str = "1D",
    ) -> Dict[str, pd.DataFrame]:
        """Fetch A-share bars via Tushare API.

        Args:
            codes: Stock codes (e.g. ``000001.SZ``).
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            fields: Extra fundamental columns (daily only).
            interval: Bar size (1D/1m/5m/15m/30m/1H), default ``1D``.

        Returns:
            Mapping code -> OHLCV DataFrame.
        """
        validate_date_range(start_date, end_date)

        if interval != "1D":
            return self._fetch_minutes(codes, start_date, end_date, interval)

        sd = start_date.replace("-", "")
        ed = end_date.replace("-", "")
        cache_fields = list(fields or [])
        result: Dict[str, pd.DataFrame] = {}

        # Every code goes through the opt-in cache helper, which is a direct
        # passthrough when the cache is disabled. Fundamentals are merged inside
        # the cached unit so a cached entry already carries its extra columns.
        for code in codes:
            def _fetch_one(code: str = code) -> Optional[pd.DataFrame]:
                try:
                    df = self._fetch_daily_frame(code, sd, ed)
                    if df is None:
                        return None
                    merged = self._merge_basic_fields(
                        {code: df}, [code], start_date, end_date, cache_fields
                    )
                    return merged.get(code)
                except Exception as exc:
                    print(f"[WARN] failed to fetch {code}: {exc}")
                    return None

            df = cached_loader_fetch(
                source=self.name,
                symbol=code,
                timeframe="1D",
                start_date=start_date,
                end_date=end_date,
                fields=cache_fields,
                fetch=_fetch_one,
            )
            if df is not None and not df.empty:
                result[code] = df

        return result

    def _fetch_daily_frame(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch and normalize one daily OHLCV frame, routing by symbol type."""
        if _is_us_equity(code) or _is_crypto(code):
            print(f"[WARN] tushare does not support {code} (US/crypto); skipping")
            return None

        if _is_etf_listed(code):
            endpoint_name = "fund_daily"
            df = self.api.fund_daily(ts_code=code, start_date=start_date, end_date=end_date)
        elif _is_index(code):
            endpoint_name = "index_daily"
            df = self.api.index_daily(ts_code=code, start_date=start_date, end_date=end_date)
        elif _is_hk_equity(code):
            endpoint_name = "hk_daily"
            df = self.api.hk_daily(ts_code=code, start_date=start_date, end_date=end_date)
        else:
            endpoint_name = "daily"
            df = self.api.daily(ts_code=code, start_date=start_date, end_date=end_date)

        if df is None or df.empty:
            print(f"[WARN] tushare returned empty for {code} via {endpoint_name}")
            return None
        df = df.sort_values("trade_date")
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.set_index("trade_date")
        df = df.rename(columns={"vol": "volume"})
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        ohlcv = df[["open", "high", "low", "close", "volume"]].dropna(
            subset=["open", "high", "low", "close"]
        )
        return ohlcv

    def _merge_basic_fields(
        self,
        result: Dict[str, pd.DataFrame],
        codes: List[str],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]],
    ) -> Dict[str, pd.DataFrame]:
        """Merge fundamental columns from daily_basic API.

        Args:
            result: Existing OHLCV frames.
            codes: All requested codes.
            start_date: Start date.
            end_date: End date.
            fields: Extra column names from daily_basic.

        Returns:
            Updated result map.
        """
        if not fields:
            return result

        sd = start_date.replace("-", "")
        ed = end_date.replace("-", "")
        active_codes = [c for c in codes if c in result]

        for code in active_codes:
            if (
                _is_etf_listed(code)
                or _is_index(code)
                or _is_hk_equity(code)
                or _is_us_equity(code)
                or _is_crypto(code)
            ):
                # daily_basic is stock-only; skip fundamental enrichment for non-stock symbols
                continue
            try:
                basic = self.api.daily_basic(
                    ts_code=code,
                    start_date=sd,
                    end_date=ed,
                    fields="ts_code,trade_date," + ",".join(fields),
                )
                if basic is not None and not basic.empty:
                    basic["trade_date"] = pd.to_datetime(basic["trade_date"])
                    basic = basic.set_index("trade_date").sort_index()
                    for f in fields:
                        if f in basic.columns:
                            result[code][f] = basic[f]
            except Exception as exc:
                print(f"[WARN] daily_basic for {code} failed: {exc}")

        return result

    def _fetch_minutes(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        interval: str,
    ) -> Dict[str, pd.DataFrame]:
        """Intraday bars via stk_mins.

        Args:
            codes: Stock codes.
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            interval: Minute bar (1m/5m/15m/30m/1H).

        Returns:
            Mapping code -> DataFrame.
        """
        freq_map = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1H": "60min"}
        freq = freq_map.get(interval)
        if not freq:
            print(f"[ERROR] unsupported Tushare interval: {interval}")
            return {}

        sd = start_date.replace("-", "")
        ed = end_date.replace("-", "")
        result: Dict[str, pd.DataFrame] = {}

        for code in codes:
            if _is_etf_listed(code):
                # tushare has no fund_mins endpoint; ETF intraday is unavailable
                print(f"[WARN] tushare does not support intraday data for {code} (ETF); skipping")
                continue
            if _is_index(code) or _is_hk_equity(code) or _is_us_equity(code) or _is_crypto(code):
                sym_type = (
                    "index" if _is_index(code)
                    else "HK" if _is_hk_equity(code)
                    else "US" if _is_us_equity(code)
                    else "crypto"
                )
                print(f"[WARN] tushare does not support intraday data for {code} ({sym_type}); skipping")
                continue
            try:
                df = self.api.stk_mins(ts_code=code, freq=freq, start_date=sd, end_date=ed)
                if df is None or df.empty:
                    print(f"[WARN] empty Tushare minute data: {code} (points >= 2000 required)")
                    continue
                df = df.sort_values("trade_time")
                df["trade_date"] = pd.to_datetime(df["trade_time"])
                df = df.set_index("trade_date")
                df = df.rename(columns={"vol": "volume"})
                for col in ["open", "high", "low", "close", "volume"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                ohlcv = df[["open", "high", "low", "close", "volume"]].dropna(
                    subset=["open", "high", "low", "close"]
                )
                result[code] = ohlcv
            except Exception as exc:
                print(f"[WARN] failed to fetch minute data {code}: {exc}")
        return result
