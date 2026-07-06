"""Financial Modeling Prep (FMP) loader: key-gated US-equity OHLCV via HTTP.

FMP exposes a daily historical-price endpoint that, like other free quote
providers, rate-limits by source IP and must be throttled. Every request here
routes through :mod:`backtest.loaders._http` so calls share one process-wide
minimum-spacing gate and a reused session.

API format (public, documented):
  https://financialmodelingprep.com/api/v3/historical-price-full/{SYMBOL}
    ?from=YYYY-MM-DD&to=YYYY-MM-DD&apikey=KEY

The JSON body is ``{"symbol": "AAPL", "historical": [{date, open, high, low,
close, volume}, ...]}`` in descending date order; an unknown symbol or empty
window yields an empty/absent ``historical`` array.

Auth: set ``FMP_API_KEY`` in the environment. Covers US equities only.
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

_API_KEY_ENV = "FMP_API_KEY"
_BASE_URL = "https://financialmodelingprep.com/api/v3/historical-price-full"

# Shared throttle/session bucket for every FMP request in this process.
_HOST_KEY = "fmp"
_MIN_INTERVAL_ENV = "VIBE_TRADING_FMP_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL_S = 0.3

# FMP daily bars carry these numeric fields; emitted in this column order.
_OHLCV_FIELDS = ("open", "high", "low", "close", "volume")


def _api_key() -> str:
    """Return the FMP API key from the environment, stripped (``""`` if unset)."""
    return os.getenv(_API_KEY_ENV, "").strip()


def _min_interval() -> float:
    """Resolve the per-call minimum spacing, honoring the env override."""
    return resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL_S)


def _fmp_symbol(code: str) -> str:
    """Translate a project symbol into FMP's bare-ticker convention.

    FMP carries US tickers bare, so a trailing ``.US`` suffix (the project's
    US-equity marker) is dropped; everything else is upper-cased and passed
    through unchanged.

    Args:
        code: Project-side symbol, e.g. ``AAPL`` or ``AAPL.US``.

    Returns:
        The FMP ticker (suffix stripped, upper-cased).
    """
    cleaned = code.strip().upper()
    if cleaned.endswith(".US"):
        cleaned = cleaned[: -len(".US")]
    return cleaned


@register
class DataLoader:
    """Financial Modeling Prep US-equity OHLCV loader (key-gated, HTTP)."""

    name = "fmp"
    markets = {"us_equity"}
    requires_auth = True

    def __init__(self) -> None:
        pass

    def is_available(self) -> bool:
        """Available when ``FMP_API_KEY`` is set to a non-empty value."""
        return bool(_api_key())

    def fetch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch daily OHLCV bars from FMP, one symbol at a time.

        A single failing symbol is logged and skipped so it never aborts the
        rest of the batch.

        Args:
            codes: Project symbols (e.g. ``["AAPL", "MSFT.US"]``).
            start_date: Inclusive start date, ``YYYY-MM-DD``.
            end_date: Inclusive end date, ``YYYY-MM-DD``.
            interval: Bar size; only ``"1D"`` is supported (others skipped).
            fields: Ignored — FMP returns a fixed OHLCV schema.

        Returns:
            Mapping ``{symbol: DataFrame(trade_date, open, high, low, close,
            volume)}`` for every symbol that returned non-empty data.

        Raises:
            ValueError: If ``start_date`` > ``end_date`` (via
                :func:`validate_date_range`).
        """
        validate_date_range(start_date, end_date)

        if interval != "1D":
            logger.warning("fmp only supports 1D bars; got interval=%r", interval)
            return {}

        if not self.is_available():
            logger.warning("fmp fetch skipped: %s not set", _API_KEY_ENV)
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
                    fetch=lambda code=code: self._fetch_one(code, start_date, end_date),
                )
                if df is not None and not df.empty:
                    result[code] = df
            except Exception as exc:
                logger.warning("fmp failed for %s: %s", code, exc)
        return result

    def _fetch_one(
        self, code: str, start_date: str, end_date: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch and parse one symbol's daily bars; ``None`` on no data.

        Args:
            code: Project symbol to fetch.
            start_date: Inclusive start date, ``YYYY-MM-DD``.
            end_date: Inclusive end date, ``YYYY-MM-DD``.

        Returns:
            An ascending OHLCV DataFrame indexed by ``trade_date``, or ``None``
            when FMP reports no bars for the symbol/window.

        Raises:
            RuntimeError: If the API key is missing at call time.
            requests.RequestException: Propagated from the HTTP layer.
        """
        api_key = _api_key()
        if not api_key:
            raise RuntimeError(f"{_API_KEY_ENV} is not set")

        symbol = _fmp_symbol(code)
        if not symbol:
            return None

        payload = throttled_get_json(
            f"{_BASE_URL}/{symbol}",
            host_key=_HOST_KEY,
            min_interval=_min_interval(),
            params={"from": start_date, "to": end_date, "apikey": api_key},
        )
        return _parse_historical(payload)


def _parse_historical(payload: Any) -> Optional[pd.DataFrame]:
    """Convert an FMP historical-price body into an ascending OHLCV frame.

    Args:
        payload: Decoded JSON body from the historical-price endpoint.

    Returns:
        DataFrame indexed by ``trade_date`` with float ``open/high/low/close/
        volume`` columns, or ``None`` when no usable rows are present.
    """
    historical = (payload or {}).get("historical") if isinstance(payload, dict) else None
    if not historical:
        return None

    rows = []
    for bar in historical:
        if not isinstance(bar, dict) or "date" not in bar:
            continue
        rows.append(
            {
                "trade_date": bar["date"],
                **{field: bar.get(field) for field in _OHLCV_FIELDS},
            }
        )

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    for field in _OHLCV_FIELDS:
        # Cast to float (not just to_numeric) so integer volume from the API
        # does not leave the column int64 and break the float-OHLCV contract.
        df[field] = pd.to_numeric(df[field], errors="coerce").astype(float)

    df = df.set_index("trade_date").sort_index()
    df = df[list(_OHLCV_FIELDS)].dropna(subset=["open", "high", "low", "close"])
    if df.empty:
        return None
    return df
