"""Local data loader: reads CSV, Parquet, and DuckDB files from user config.

Configuration lives at ``~/.vibe-trading/data-bridge/config.yaml``.
Each entry maps a symbol to a data file with optional column-name overrides,
date format, and (for DuckDB) an SQL query.

Example config::

    sources:
      - symbol: "AAPL.US"
        type: csv
        path: "~/data/aapl_2024.csv"
        columns:
          date: "Date"
          open: "Open"
          high: "High"
          low: "Low"
          close: "Close"
          volume: "Volume"
        date_format: "%Y-%m-%d"

      - symbol: "BTC-USDT"
        type: parquet
        path: "~/data/btc.parquet"

      - symbol: "MYINDEX"
        type: duckdb
        db_path: "~/data/market.duckdb"
        query: "SELECT * FROM prices WHERE ticker = 'MYINDEX'"
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from backtest.loaders.base import cached_loader_fetch, validate_date_range, validate_ohlc
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path.home() / ".vibe-trading" / "data-bridge"
_CONFIG_PATH = _CONFIG_DIR / "config.yaml"

_DEFAULT_COLUMNS = {
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}


def _load_config() -> dict[str, Any] | None:
    if not _CONFIG_PATH.exists():
        return None
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _normalize_columns(
    df: pd.DataFrame,
    col_map: dict[str, str],
    date_fmt: str | None,
) -> pd.DataFrame | None:
    rename: dict[str, str] = {}
    for std_name, src_name in col_map.items():
        if std_name == "date":
            continue
        if src_name in df.columns:
            rename[src_name] = std_name
    df = df.rename(columns=rename)

    required = {"open", "high", "low", "close"}
    if not required.issubset(df.columns):
        return None

    date_col = col_map.get("date", "date")
    if date_col not in df.columns:
        return None

    if date_fmt:
        df["trade_date"] = pd.to_datetime(df[date_col], format=date_fmt, errors="coerce")
    else:
        df["trade_date"] = pd.to_datetime(df[date_col], errors="coerce")
    # Drop any timezone so the tz-naive date-range filter in ``_fetch_one`` never
    # raises "Invalid comparison between tz-aware and tz-naive" (which was caught
    # and swallowed into a silently empty result for tz-aware parquet/CSV inputs).
    if getattr(df["trade_date"].dt, "tz", None) is not None:
        df["trade_date"] = df["trade_date"].dt.tz_localize(None)
    df = df.dropna(subset=["trade_date"])
    df = df.set_index("trade_date").sort_index()

    ohlcv_cols: list[str] = ["open", "high", "low", "close"]
    if "volume" in df.columns:
        ohlcv_cols.append("volume")

    df = df[ohlcv_cols]
    for col in ohlcv_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = validate_ohlc(df)
    for col in ohlcv_cols:
        df[col] = df[col].astype("float64")

    if "volume" not in df.columns:
        df["volume"] = 0.0

    return df


def _read_csv(path: str, col_map: dict[str, str], date_fmt: str | None) -> pd.DataFrame | None:
    df = pd.read_csv(path)
    return _normalize_columns(df, col_map, date_fmt)


def _read_parquet(path: str, col_map: dict[str, str], date_fmt: str | None) -> pd.DataFrame | None:
    df = pd.read_parquet(path)
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        if date_fmt is None and col_map.get("date", "date") not in df.columns:
            col_map = dict(col_map)
            col_map["date"] = df.columns[0]
    return _normalize_columns(df, col_map, date_fmt)


def _read_duckdb(
    db_path: str, query: str, col_map: dict[str, str], date_fmt: str | None
) -> pd.DataFrame | None:
    import duckdb

    with duckdb.connect(db_path, read_only=True) as conn:
        df = conn.execute(query).df()
    return _normalize_columns(df, col_map, date_fmt)


_READERS = {
    "csv": _read_csv,
    "parquet": _read_parquet,
    "duckdb": _read_duckdb,
}


@register
class DataLoader:
    """Config-driven local data loader for CSV, Parquet, and DuckDB."""

    name = "local"
    markets = {"us_equity", "a_share", "hk_equity", "crypto", "futures", "forex", "macro", "fund"}
    requires_auth = False

    def __init__(self) -> None:
        self._config: dict[str, Any] | None = None
        self._source_by_symbol: dict[str, dict[str, Any]] = {}

    def is_available(self) -> bool:
        """Return True when the YAML config file exists and has sources."""
        config = _load_config()
        if config is None:
            return False
        sources = config.get("sources")
        return isinstance(sources, list) and len(sources) > 0

    def _ensure_config(self) -> None:
        if self._config is not None:
            return
        self._config = _load_config() or {}
        self._source_by_symbol = {}
        for entry in self._config.get("sources", []):
            symbol = entry.get("symbol", "").strip()
            if symbol:
                self._source_by_symbol[symbol] = entry

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch OHLCV data for each code from configured local sources.

        Args:
            codes: Symbol list, optionally prefixed with ``local:``.
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.
            interval: Bar size (all intervals supported if data contains them).
            fields: Ignored.

        Returns:
            Mapping clean_symbol -> OHLCV DataFrame.
        """
        validate_date_range(start_date, end_date)
        self._ensure_config()

        result: Dict[str, pd.DataFrame] = {}
        for code in codes:
            clean = code.split(":", 1)[1] if code.startswith("local:") else code
            entry = self._source_by_symbol.get(clean)
            if entry is None:
                logger.warning("local loader: no config entry for symbol %s", clean)
                continue
            try:
                df = cached_loader_fetch(
                    source=self.name,
                    symbol=clean,
                    timeframe=interval,
                    start_date=start_date,
                    end_date=end_date,
                    fields=None,
                    fetch=lambda c=clean: self._fetch_one(c, start_date, end_date),
                )
                if df is not None and not df.empty:
                    result[clean] = df
            except Exception as exc:
                logger.warning("local loader failed for %s: %s", clean, exc)

        return result

    def _fetch_one(
        self, symbol: str, start_date: str, end_date: str,
    ) -> pd.DataFrame | None:
        entry = self._source_by_symbol.get(symbol)
        if entry is None:
            return None

        src_type: str = entry.get("type", "csv").strip().lower()
        reader = _READERS.get(src_type)
        if reader is None:
            logger.warning("local loader: unsupported type %r for symbol %s", src_type, symbol)
            return None

        col_map: dict[str, str] = dict(_DEFAULT_COLUMNS)
        user_cols = entry.get("columns")
        if isinstance(user_cols, dict):
            for k, v in user_cols.items():
                if isinstance(v, str):
                    col_map[k] = v

        date_fmt: str | None = None
        user_fmt = entry.get("date_format")
        if isinstance(user_fmt, str) and user_fmt.strip():
            date_fmt = user_fmt.strip()

        if src_type == "duckdb":
            db_path = str(Path(entry.get("db_path", "")).expanduser())
            query = entry.get("query", "").strip()
            if not db_path or not query:
                logger.warning(
                    "local loader: missing db_path or query for duckdb symbol %s", symbol
                )
                return None
            df = _read_duckdb(db_path, query, col_map, date_fmt)
        else:
            path = entry.get("path", "").strip()
            if not path:
                logger.warning("local loader: missing path for symbol %s", symbol)
                return None
            expanded = str(Path(path).expanduser())
            df = reader(expanded, col_map, date_fmt)

        if df is None:
            return None

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
        df = df[(df.index >= start) & (df.index <= end)]
        if df.empty:
            return None
        return df
