"""Finnhub loader: key-gated US-equity OHLCV via the public stock-candle API.

Finnhub (https://finnhub.io) serves daily stock candles from a single REST
endpoint, gated by a free API key passed as the ``token`` query parameter:

  https://finnhub.io/api/v1/stock/candle?symbol=AAPL&resolution=D&from=...&to=...&token=...

Like other free quote providers it rate-limits by source IP, so every request
routes through :func:`backtest.loaders._http.throttled_get_json` for per-host
spacing plus session reuse. The endpoint answers with parallel arrays
(``o``/``h``/``l``/``c``/``v`` plus epoch ``t``) and a status field ``s`` that
reads ``"ok"`` on a hit or ``"no_data"`` for an empty window.

Symbol convention (Vibe-Trading -> Finnhub):
  * US ``AAPL.US`` -> ``AAPL`` (Finnhub carries US tickers bare)
  * Anything else is passed through uppercased (e.g. a bare ``MSFT``).

No market data is ever persisted in the repo; settled ranges may be cached to
the user-home loader cache via :func:`cached_loader_fetch`.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd

from backtest.loaders._http import resolve_min_interval, throttled_get_json
from backtest.loaders.base import cached_loader_fetch, validate_date_range
from backtest.loaders.registry import register

logger = logging.getLogger(__name__)

_API_KEY_ENV = "FINNHUB_API_KEY"
_CANDLE_URL = "https://finnhub.io/api/v1/stock/candle"

# Throttle bucket + default minimum spacing (free tier is ~30 req/s but bursts
# get a 429; one shared bucket keeps the whole process polite).
_HOST_KEY = "finnhub"
_MIN_INTERVAL_ENV = "VIBE_TRADING_FINNHUB_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL_S = 0.4

# Only daily candles are wired here; Finnhub also exposes intraday resolutions
# but the project's us_equity fallback chain is daily-only.
_RESOLUTION = "D"

# Finnhub packs parallel arrays under these keys; ``t`` carries epoch seconds.
_FINNHUB_TO_OHLCV = {"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def _min_interval() -> float:
    """Resolve the per-call minimum spacing, honoring the env override."""
    return resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL_S)


def _to_finnhub_symbol(code: str) -> str:
    """Translate a project symbol into Finnhub's ticker convention.

    Args:
        code: Project-side symbol, e.g. ``AAPL.US`` or a bare ``MSFT``.

    Returns:
        The Finnhub ticker: the ``.US`` suffix stripped, otherwise the
        uppercased symbol unchanged.
    """
    upper = code.strip().upper()
    if upper.endswith(".US"):
        return upper[: -len(".US")]
    return upper


def _to_epoch_seconds(date_str: str, *, end_of_day: bool) -> int:
    """Convert a ``YYYY-MM-DD`` date to a UTC epoch-second bound.

    Args:
        date_str: Inclusive date string.
        end_of_day: When ``True`` push the instant to 23:59:59 so the day's
            bar falls inside Finnhub's inclusive ``[from, to]`` window.

    Returns:
        Epoch seconds (UTC) for the requested bound.
    """
    ts = pd.Timestamp(date_str).normalize()
    if end_of_day:
        ts = ts + pd.Timedelta(hours=23, minutes=59, seconds=59)
    return int(ts.value // 1_000_000_000)


def _rows_from_payload(payload: Any) -> List[Dict[str, Any]]:
    """Zip Finnhub's parallel candle arrays into ascending row dicts.

    Args:
        payload: Decoded JSON body from the stock-candle endpoint.

    Returns:
        Ascending list of ``{trade_date, open, high, low, close, volume}`` dicts
        where ``trade_date`` is the raw epoch-second ``int`` (normalized to a
        ``datetime64[ns]`` index later in :meth:`DataLoader._fetch_one`).
        Empty when the status is not ``"ok"`` or the timestamp array is missing,
        and per-bar gaps (a ``None`` in any OHLC slot) are skipped.
    """
    if not isinstance(payload, dict) or payload.get("s") != "ok":
        return []

    timestamps = payload.get("t") or []
    if not isinstance(timestamps, list):
        return []

    rows: List[Dict[str, Any]] = []
    for index, epoch in enumerate(timestamps):
        values = {
            field: _at(payload.get(key), index)
            for key, field in _FINNHUB_TO_OHLCV.items()
        }
        if any(values[field] is None for field in ("open", "high", "low", "close")):
            continue
        # Keep the raw epoch here; the resolution is normalized in one place
        # (``_fetch_one``) so the index dtype matches the other loaders.
        row: Dict[str, Any] = {"trade_date": int(epoch)}
        row.update({field: _to_float(values[field]) for field in _OHLCV_COLUMNS})
        rows.append(row)
    return rows


def _at(series: Any, index: int) -> Any:
    """Return ``series[index]`` when in range, else ``None``."""
    if isinstance(series, list) and 0 <= index < len(series):
        return series[index]
    return None


def _to_float(value: Any) -> Optional[float]:
    """Coerce a Finnhub numeric (or ``None``) to ``float``; ``None`` on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@register
class DataLoader:
    """Finnhub US-equity daily OHLCV loader (key-gated, throttled HTTP)."""

    name = "finnhub"
    markets = {"us_equity"}
    requires_auth = True

    def __init__(self) -> None:
        """Initialize the loader without touching the network or credentials.

        Construction never raises on a missing key; availability is reported
        separately via :meth:`is_available` so the fallback chain can keep
        walking when the key is absent.
        """
        pass

    def is_available(self) -> bool:
        """Return whether a Finnhub API key is present in the environment."""
        return bool(os.getenv(_API_KEY_ENV))

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch daily OHLCV history keyed by the original project symbols.

        Each symbol is fetched independently through the opt-in loader cache;
        a single failing symbol is logged and skipped so it never aborts the
        batch.

        Args:
            codes: Project symbols such as ``AAPL.US``.
            start_date: Inclusive start date in ``YYYY-MM-DD`` format.
            end_date: Inclusive end date in ``YYYY-MM-DD`` format.
            interval: Backtest interval; only daily (``1D``) is supported.
            fields: Ignored; included for interface compatibility.

        Returns:
            Mapping of input symbol to a DataFrame indexed by a ``trade_date``
            :class:`~pandas.DatetimeIndex` with float ``open``/``high``/``low``/
            ``close``/``volume`` columns. Symbols without data are omitted.

        Raises:
            ValueError: If ``start_date`` > ``end_date``.
        """
        del fields
        validate_date_range(start_date, end_date)

        api_key = os.getenv(_API_KEY_ENV)
        if not api_key:
            logger.warning("finnhub fetch skipped: %s not set", _API_KEY_ENV)
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
            except Exception as exc:  # noqa: BLE001 - one symbol must not abort the batch
                logger.warning("finnhub failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str, api_key: str
    ) -> Optional[pd.DataFrame]:
        """Fetch and normalize one symbol's daily candles.

        Args:
            code: Project-side symbol.
            start_date: Inclusive start date (``YYYY-MM-DD``).
            end_date: Inclusive end date (``YYYY-MM-DD``).
            api_key: Finnhub API token for the ``token`` query parameter.

        Returns:
            A normalized OHLCV DataFrame, or ``None`` when Finnhub reports no
            usable data for the window.
        """
        payload = throttled_get_json(
            _CANDLE_URL,
            host_key=_HOST_KEY,
            min_interval=_min_interval(),
            params={
                "symbol": _to_finnhub_symbol(code),
                "resolution": _RESOLUTION,
                "from": _to_epoch_seconds(start_date, end_of_day=False),
                "to": _to_epoch_seconds(end_date, end_of_day=True),
                "token": api_key,
            },
        )

        rows = _rows_from_payload(payload)
        if not rows:
            return None

        df = pd.DataFrame(rows)
        # Epoch seconds -> nanosecond-resolution DatetimeIndex so the index
        # dtype (``datetime64[ns]``) stays consistent with the other loaders
        # rather than collapsing to the second resolution pandas infers from a
        # ``unit="s"`` conversion.
        df["trade_date"] = pd.to_datetime(df["trade_date"], unit="s").astype(
            "datetime64[ns]"
        )
        df = df.set_index("trade_date").sort_index()
        df = df[_OHLCV_COLUMNS].astype(float).dropna(
            subset=["open", "high", "low", "close"]
        )
        return df
