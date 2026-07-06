"""Read-only tool: FRED macroeconomic time series (St. Louis Fed).

The Federal Reserve Bank of St. Louis publishes hundreds of thousands of
economic time series — CPI, unemployment, GDP, federal funds rate, Treasury
yields, money supply and the like — through its FRED REST API. Each series is
addressed by a short uppercase ``series_id`` (e.g. ``CPIAUCSL`` for headline
CPI, ``UNRATE`` for the unemployment rate, ``DGS10`` for the 10-year Treasury
yield).

This tool fetches the observations of a single series over an optional date
window and returns them as a normalized envelope. The FRED API requires a free
``api_key``; the tool reads it from the ``FRED_API_KEY`` environment variable
and is silently excluded from the registry when that key is absent, so the
agent never sees a tool it cannot call. Every outbound GET routes through the
project's IP-throttled HTTP layer under the ``fred`` host bucket so the API is
never hit un-throttled.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from backtest.loaders._http import resolve_min_interval, throttled_get_json
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# FRED series-observations endpoint. The response carries an ``observations``
# array of ``{date, value}`` records (value is a string; "." marks a gap).
_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"

_FRED_HOST_KEY = "fred"
_FRED_MIN_INTERVAL_ENV = "VIBE_TRADING_FRED_MIN_INTERVAL"
_FRED_DEFAULT_MIN_INTERVAL = 0.6
_FRED_TIMEOUT_S = 15.0

# Hard cap on returned observations so a long daily series cannot bloat the
# payload. The most recent observations are kept when the cap is exceeded.
_DEFAULT_LIMIT = 2000
_MAX_LIMIT = 5000

# FRED's sentinel for a missing value within an otherwise valid series.
_MISSING_VALUE = "."


class FredMacroTool(BaseTool):
    """Fetch a single FRED macroeconomic time series from the St. Louis Fed."""

    name = "get_macro_series"
    description = (
        "Fetch a FRED macroeconomic time series from the St. Louis Fed: dated "
        "observations of indicators such as CPI (CPIAUCSL), unemployment "
        "(UNRATE), real GDP (GDPC1), the federal funds rate (FEDFUNDS), or the "
        "10-year Treasury yield (DGS10). Markets: US / global macroeconomic "
        "data. Requires a free FRED API key (FRED_API_KEY). "
        'Example: {"series_id": "CPIAUCSL", "start_date": "2020-01-01", '
        '"end_date": "2024-12-31"}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "series_id": {
                "type": "string",
                "description": (
                    "FRED series identifier, a short uppercase code such as "
                    "'CPIAUCSL', 'UNRATE', 'GDPC1', 'FEDFUNDS' or 'DGS10'."
                ),
            },
            "start_date": {
                "type": "string",
                "description": (
                    "Inclusive start of the observation window, YYYY-MM-DD. "
                    "Omit for the full available history."
                ),
            },
            "end_date": {
                "type": "string",
                "description": (
                    "Inclusive end of the observation window, YYYY-MM-DD. "
                    "Omit for observations through the latest available date."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    "Maximum number of most-recent observations to return "
                    f"(1-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}."
                ),
                "default": _DEFAULT_LIMIT,
            },
        },
        "required": ["series_id"],
    }

    @classmethod
    def check_available(cls) -> bool:
        """Available only when a FRED API key is configured.

        Returns:
            ``True`` when ``FRED_API_KEY`` is set in the environment, otherwise
            ``False`` so the tool is silently excluded from the registry.
        """
        return bool(os.getenv("FRED_API_KEY"))

    def execute(self, **kwargs: Any) -> str:
        """Fetch one FRED series and return a JSON envelope.

        Args:
            **kwargs: ``series_id`` (required FRED code), optional ``start_date``
                / ``end_date`` (inclusive YYYY-MM-DD bounds) and optional
                ``limit`` (observation count cap).

        Returns:
            A JSON string envelope. On success:
            ``{"ok": true, "market": "US", "source": "fred",
            "data": {"series_id", "observations": [{"date", "value"}, ...],
            "count"}}``. On failure: ``{"ok": false, "error": str}``.
        """
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            return _error("FRED_API_KEY is not configured")

        series_id = kwargs.get("series_id")
        if not isinstance(series_id, str) or not series_id.strip():
            return _error("'series_id' is required and must be a non-empty string")
        series_id = series_id.strip().upper()

        params: dict[str, str] = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
        }
        start_date = _clean_date(kwargs.get("start_date"))
        if start_date is not None:
            params["observation_start"] = start_date
        end_date = _clean_date(kwargs.get("end_date"))
        if end_date is not None:
            params["observation_end"] = end_date

        try:
            payload = throttled_get_json(
                _OBSERVATIONS_URL,
                host_key=_FRED_HOST_KEY,
                min_interval=resolve_min_interval(
                    _FRED_MIN_INTERVAL_ENV, _FRED_DEFAULT_MIN_INTERVAL
                ),
                params=params,
                timeout=_FRED_TIMEOUT_S,
            )
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure as envelope
            return _error(f"fred observations request failed: {exc}")

        observations = _parse_observations(payload)
        if not observations:
            return _error(f"no observations found for series '{series_id}'")

        limit = _clamp_limit(kwargs.get("limit", _DEFAULT_LIMIT))
        # Keep the most recent observations when the cap is exceeded; FRED serves
        # oldest-first, so the tail holds the newest records.
        capped = observations[-limit:]

        return json.dumps(
            {
                "ok": True,
                "market": "US",
                "source": "fred",
                "data": {
                    "series_id": series_id,
                    "observations": capped,
                    "count": len(capped),
                },
            },
            ensure_ascii=False,
        )


def _parse_observations(payload: Any) -> list[dict]:
    """Extract dated observations from a FRED observations payload.

    Args:
        payload: Decoded FRED JSON; rows live under the ``observations`` array,
            each a ``{date, value}`` record where ``value`` is a string and a
            lone ``"."`` marks a missing reading.

    Returns:
        A list of ``{date, value}`` dicts in served (oldest-first) order, with
        ``value`` coerced to ``float`` or ``None`` for gaps. Empty when the
        payload carries no usable rows.
    """
    if not isinstance(payload, dict):
        return []
    rows = payload.get("observations")
    if not isinstance(rows, list):
        return []

    out: list[dict] = []
    for row in rows:
        record = _normalize_observation(row)
        if record is not None:
            out.append(record)
    return out


def _normalize_observation(row: Any) -> dict | None:
    """Map one raw FRED observation row to our record, or ``None`` if unusable.

    A row with no date carries no anchor and is dropped; a single bad row never
    aborts the batch.

    Args:
        row: One element of the FRED ``observations`` array.

    Returns:
        ``{"date": str, "value": float | None}`` or ``None``.
    """
    if not isinstance(row, dict):
        return None
    date = _clean_date(row.get("date"))
    if date is None:
        return None
    return {"date": date, "value": _to_number(row.get("value"))}


def _clamp_limit(value: Any) -> int:
    """Coerce a requested observation count into the supported range."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    return max(1, min(n, _MAX_LIMIT))


def _clean_date(value: Any) -> str | None:
    """Trim a date cell to its ``YYYY-MM-DD`` form, or ``None`` when absent/blank."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().split(" ", 1)[0]


def _to_number(value: Any) -> float | None:
    """Coerce a FRED value cell to ``float``, or ``None`` for gaps / non-numerics.

    FRED encodes a missing reading as the string ``"."``; that and any other
    non-numeric cell map to ``None`` so downstream consumers see an explicit gap.
    """
    if value is None or value == "" or value == _MISSING_VALUE:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _error(message: str) -> str:
    """Render a failure envelope as a JSON string."""
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
