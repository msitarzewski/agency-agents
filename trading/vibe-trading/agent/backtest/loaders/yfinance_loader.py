"""yfinance-backed loader for HK/US equity OHLCV data."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Union

import pandas as pd
import yfinance as yf

from backtest.loaders.base import (
    loader_cache_get,
    loader_cache_put,
    validate_date_range,
    validate_ohlc,
)
from backtest.loaders.registry import register

_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]
_COLUMN_RENAMES = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}
_INTERVAL_MAP = {
    "1D": "1d",
    "1H": "1h",
    "4H": "1h",
}


def _to_yfinance_symbol(code: str) -> str:
    """Convert project symbols into yfinance symbols.

    Args:
        code: Project symbol, for example ``AAPL.US`` or ``700.HK``.

    Returns:
        yfinance-compatible symbol.
    """
    upper = code.strip().upper()
    if upper.endswith(".US"):
        return upper[:-3]
    if upper.endswith(".HK"):
        digits = upper[:-3]
        width = max(4, len(digits))
        return f"{digits.zfill(width)}.HK"
    # Crypto: BTC-USDT -> BTC-USD, ETH-USDT -> ETH-USD, etc.
    if upper.endswith("-USDT"):
        return upper[:-5] + "-USD"
    if upper.endswith("-USDC"):
        return upper[:-5] + "-USD"
    return upper


def _to_yfinance_interval(interval: str) -> str:
    """Map project interval strings to yfinance interval strings.

    Args:
        interval: Backtest interval such as ``1D`` or ``5m``.

    Returns:
        yfinance interval string.
    """
    normalized = str(interval or "1D").strip()
    return _INTERVAL_MAP.get(normalized, normalized.lower())


def _to_yfinance_exclusive_end(end_date: str) -> str:
    """Convert the project-inclusive end date to yfinance's exclusive end."""
    return (pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def _download_history(
    tickers: Union[List[str], str],
    start_date: str,
    end_date: str,
    interval: str,
) -> pd.DataFrame:
    """Download raw historical data via yfinance.

    Args:
        tickers: One or more yfinance symbols.
        start_date: Inclusive start date string.
        end_date: End date string passed directly to yfinance.
        interval: yfinance interval string.

    Returns:
        Raw dataframe from ``yf.download``.
    """
    return yf.download(
        tickers,
        start=start_date,
        end=end_date,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )


def _flatten_columns(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Flatten any leftover multi-index columns after symbol selection.

    Args:
        frame: Price dataframe.
        symbol: yfinance symbol used for column cleanup.

    Returns:
        Dataframe with flat string columns.
    """
    if not isinstance(frame.columns, pd.MultiIndex):
        return frame

    cleaned_columns = []
    for column in frame.columns:
        pieces = [str(part) for part in column if str(part) and str(part).upper() != symbol.upper()]
        cleaned_columns.append(pieces[-1] if pieces else str(column[-1]))
    flattened = frame.copy()
    flattened.columns = cleaned_columns
    return flattened


def _extract_symbol_frame(frame: pd.DataFrame, symbol: str, total_symbols: int) -> pd.DataFrame:
    """Extract a single symbol slice from a raw yfinance dataframe.

    Args:
        frame: Raw dataframe returned by ``yf.download``.
        symbol: yfinance symbol to extract.
        total_symbols: Number of unique symbols requested.

    Returns:
        A single-symbol dataframe or an empty dataframe when unavailable.
    """
    if frame.empty:
        return pd.DataFrame()

    if not isinstance(frame.columns, pd.MultiIndex):
        if total_symbols == 1:
            return frame.copy()
        return pd.DataFrame()

    for level in range(frame.columns.nlevels):
        if symbol in frame.columns.get_level_values(level):
            selected = frame.xs(symbol, axis=1, level=level, drop_level=True)
            return _flatten_columns(selected.copy(), symbol)
    return pd.DataFrame()


def _normalize_frame(frame: pd.DataFrame, requested_interval: str) -> pd.DataFrame:
    """Normalize raw yfinance data into the backtest OHLCV schema.

    Args:
        frame: Raw or symbol-scoped yfinance dataframe.
        requested_interval: Original backtest interval.

    Returns:
        Normalized OHLCV dataframe indexed by ``trade_date``.
    """
    if frame.empty:
        return pd.DataFrame(columns=_OHLCV_COLUMNS)

    normalized = _flatten_columns(frame.copy(), "")
    normalized = normalized.rename(columns=_COLUMN_RENAMES)

    for column in _OHLCV_COLUMNS:
        if column not in normalized.columns:
            if column == "volume":
                normalized[column] = 0.0
            else:
                return pd.DataFrame(columns=_OHLCV_COLUMNS)

    normalized = normalized.loc[:, _OHLCV_COLUMNS].copy()
    normalized = normalized.apply(pd.to_numeric, errors="coerce")

    index = pd.DatetimeIndex(pd.to_datetime(normalized.index))
    if getattr(index, "tz", None) is not None:
        index = index.tz_localize(None)
    normalized.index = index
    normalized.index.name = "trade_date"
    normalized = normalized.sort_index()
    normalized["volume"] = normalized["volume"].fillna(0.0)
    normalized = normalized.dropna(subset=["open", "high", "low", "close"])
    normalized = validate_ohlc(normalized)

    if requested_interval == "4H" and not normalized.empty:
        normalized = normalized.resample("4h").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        normalized = normalized.dropna(subset=["open", "high", "low", "close"])
        normalized.index.name = "trade_date"

    return normalized


@register
class DataLoader:
    """Fetch HK/US equity bars from Yahoo Finance via yfinance."""

    name = "yfinance"
    markets = {"us_equity", "hk_equity", "crypto"}
    requires_auth = False

    def is_available(self) -> bool:
        """Always available (free public data, no auth)."""
        return True

    def __init__(self) -> None:
        """Initialize the loader.

        yfinance is a free public-data wrapper and does not require credentials.
        """
        pass

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        fields: Optional[List[str]] = None,
        interval: str = "1D",
    ) -> Dict[str, pd.DataFrame]:
        """Fetch OHLCV history keyed by the original project symbols.

        Args:
            codes: Project symbols such as ``AAPL.US`` and ``700.HK``.
            start_date: Start date in ``YYYY-MM-DD`` format.
            end_date: End date in ``YYYY-MM-DD`` format.
            fields: Ignored for yfinance; included for interface compatibility.
            interval: Backtest interval such as ``1D`` or ``1H``.

        Returns:
            Mapping of input symbol to normalized OHLCV dataframe.
        """
        del fields
        if not codes:
            return {}
        validate_date_range(start_date, end_date)

        requested_interval = str(interval or "1D").strip()
        yf_interval = _to_yfinance_interval(requested_interval)
        yf_end_date = _to_yfinance_exclusive_end(end_date)

        symbol_groups: Dict[str, List[str]] = defaultdict(list)
        for code in codes:
            symbol_groups[_to_yfinance_symbol(code)].append(code)

        unique_symbols = list(symbol_groups.keys())
        results: Dict[str, pd.DataFrame] = {}

        # Serve cached symbols first so a fully-cached request skips the bulk
        # download entirely; only uncached symbols hit the network.
        pending: List[str] = []
        for symbol in unique_symbols:
            cached = loader_cache_get(
                source=self.name,
                symbol=symbol,
                timeframe=requested_interval,
                start_date=start_date,
                end_date=end_date,
                fields=None,
            )
            if cached is not None:
                for original_code in symbol_groups[symbol]:
                    results[original_code] = cached.copy()
            else:
                pending.append(symbol)

        if not pending:
            return results

        try:
            bulk_data = _download_history(pending, start_date, yf_end_date, yf_interval)
        except Exception as exc:
            print(f"[WARN] yfinance bulk download failed for {pending}: {exc}")
            bulk_data = pd.DataFrame()

        for symbol in pending:
            try:
                symbol_frame = _extract_symbol_frame(bulk_data, symbol, len(pending))
                if symbol_frame.empty:
                    symbol_frame = _download_history(symbol, start_date, yf_end_date, yf_interval)

                normalized = _normalize_frame(symbol_frame, requested_interval)
                if normalized.empty:
                    print(f"[WARN] yfinance returned no usable data for {symbol}")
                    continue

                loader_cache_put(
                    source=self.name,
                    symbol=symbol,
                    timeframe=requested_interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=None,
                    frame=normalized,
                )
                for original_code in symbol_groups[symbol]:
                    results[original_code] = normalized.copy()
            except Exception as exc:
                print(f"[WARN] Failed to fetch data for {symbol}: {exc}")
                continue

        return results
