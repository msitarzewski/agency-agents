"""BaoStock loader: free, no-auth A-share data via TCP protocol.

BaoStock (http://baostock.com) uses its own TCP protocol (not HTTP),
bypassing CDN IP blocks that affect HTTP-based data sources like
eastmoney.com.  Completely free, no API token required.

Covers: A-shares (SH/SZ), does NOT cover HK/US/crypto.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)


def _is_a_share(code: str) -> bool:
    # Support both baostock native format (sh.601398) and tushare-style suffix (601398.SH)
    code_lower = code.lower()
    return (
        code_lower.startswith(("sh.", "sz."))
        or code.upper().endswith((".SZ", ".SH"))
    )


@register
class DataLoader:
    """BaoStock A-share OHLCV loader (free, TCP protocol, no auth)."""

    name = "baostock"
    markets = {"a_share"}
    requires_auth = False

    def is_available(self) -> bool:
        """Available if baostock is installed."""
        try:
            import baostock  # noqa: F401
            return True
        except ImportError:
            return False

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
        """Fetch OHLCV data via BaoStock.

        Args:
            codes: Symbol list (e.g. ["601595.SH", "000001.SZ"]).
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.
            interval: Bar size (only 1D supported).
            fields: Ignored.

        Returns:
            Mapping symbol -> OHLCV DataFrame.
        """
        validate_date_range(start_date, end_date)

        import baostock as bs
        lg = bs.login()
        if lg.error_code != "0":
            logger.error("baostock login failed: %s", lg.error_msg)
            return {}

        result: Dict[str, pd.DataFrame] = {}
        try:
            for code in codes:
                try:
                    df = cached_loader_fetch(
                        source=self.name,
                        symbol=code,
                        timeframe=interval,
                        start_date=start_date,
                        end_date=end_date,
                        fields=None,
                        fetch=lambda code=code: self._fetch_one(bs, code, start_date, end_date),
                    )
                    if df is not None and not df.empty:
                        result[code] = df
                except Exception as exc:
                    logger.warning("baostock failed for %s: %s", code, exc)
        finally:
            bs.logout()

        return result

    def _fetch_one(
        self, bs, code: str, start_date: str, end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch a single A-share symbol."""
        if not _is_a_share(code):
            return None

        # Support baostock native format (sh.601398 / sz.000001)
        # and tushare-style suffix (601398.SH / 000001.SZ)
        code_lower = code.lower()
        if code_lower.startswith("sh.") or code_lower.startswith("sz."):
            bs_code = code_lower
        else:
            parts = code.upper().split(".")
            symbol = parts[0]
            suffix = parts[1] if len(parts) > 1 else ""
            if suffix == "SH":
                bs_code = f"sh.{symbol}"
            elif suffix == "SZ":
                bs_code = f"sz.{symbol}"
            else:
                return None

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2",  # 前复权
        )

        if rs.error_code != "0":
            logger.warning("baostock query failed for %s: %s", code, rs.error_msg)
            return None

        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume", "amount"])
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.rename(columns={"date": "trade_date"})
        df = df.set_index("trade_date").sort_index()
        df = df[["open", "high", "low", "close", "volume"]].dropna(
            subset=["open", "high", "low", "close"]
        )
        return df
