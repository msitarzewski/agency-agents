"""DataLoader Protocol, shared exceptions, retry helpers, and loader cache.

The retry/budget helpers are the canonical pattern for any loader that calls
a flaky external API: a wall-clock deadline plus a small backoff schedule
applied only to a declared transient exception class. New loaders should
import :func:`check_budget` and :func:`retry_with_budget` rather than
re-implementing the loop.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Callable, Protocol, TypeVar, runtime_checkable

import pandas as pd

logger = logging.getLogger(__name__)


class NoAvailableSourceError(Exception):
    """Raised when no data source is available for a given market."""


def validate_date_range(start_date: str, end_date: str) -> None:
    """Validate that start_date <= end_date.

    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).

    Raises:
        ValueError: If dates are invalid or start > end.
    """
    try:
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
    except Exception as exc:
        raise ValueError(f"Invalid date format: start={start_date!r}, end={end_date!r}") from exc
    if start > end:
        raise ValueError(f"start_date ({start_date}) > end_date ({end_date})")


def validate_ohlc(frame: pd.DataFrame, *, strategy: str = "drop") -> pd.DataFrame:
    """Drop, flag, or reject bars that violate OHLC invariants.

    Loaders only drop NaN rows, so structurally dirty bars — ``high < low``,
    a non-positive price, or a high/low that fails to bracket open/close —
    flow straight into the backtest and surface downstream as NaN/inf metrics
    that break the strict (``allow_nan=False``) JSON serializers. This is the
    canonical loader-boundary check; call it after the existing ``dropna`` so a
    single sanity pass guards every source.

    Args:
        frame: OHLCV frame with at least ``open``/``high``/``low``/``close``
            columns. NaN handling is left to the caller's ``dropna``.
        strategy: ``"drop"`` (remove offending rows, default), ``"warn"``
            (log and keep), or ``"raise"`` (raise on any violation).

    Returns:
        The frame with invalid rows removed (``"drop"``) or unchanged
        (``"warn"``). A frame that is empty or lacks OHLC columns is returned
        as-is.

    Raises:
        ValueError: ``strategy="raise"`` and at least one bar is invalid.
    """
    required = ("open", "high", "low", "close")
    if frame.empty or not all(col in frame.columns for col in required):
        return frame

    open_, high, low, close = (frame[c] for c in required)
    invalid = (
        (high < low)
        | (high < open_)
        | (high < close)
        | (low > open_)
        | (low > close)
        | (open_ <= 0)
        | (high <= 0)
        | (low <= 0)
        | (close <= 0)
    )
    n_invalid = int(invalid.sum())
    if n_invalid == 0:
        return frame

    if strategy == "raise":
        raise ValueError(f"{n_invalid} bar(s) violate OHLC invariants")
    if strategy == "warn":
        logger.warning("OHLC validation: %d bar(s) violate invariants (kept)", n_invalid)
        return frame
    logger.warning("OHLC validation: dropping %d invalid bar(s)", n_invalid)
    return frame[~invalid]


# ---------------------------------------------------------------------------
# Bounded retry / budget helpers (shared by ccxt_loader, okx, and any future
# loader calling a flaky external API).
# ---------------------------------------------------------------------------

DEFAULT_BACKOFF: tuple[float, ...] = (0.5, 1.5, 4.0)
DEFAULT_MAX_RETRIES = 3


def positive_env_int(name: str, default: int) -> int:
    """Read a positive integer env var, warning and falling back on invalid values."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("invalid %s=%r, using default %s", name, raw, default)
        return default
    if value <= 0:
        logger.warning("non-positive %s=%r, using default %s", name, raw, default)
        return default
    return value


def positive_env_float(name: str, default: float) -> float:
    """Read a positive float env var, warning and falling back on invalid values."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning("invalid %s=%r, using default %s", name, raw, default)
        return default
    if value <= 0:
        logger.warning("non-positive %s=%r, using default %s", name, raw, default)
        return default
    return value


def check_budget(deadline: float, label: str, budget_s: float | None = None) -> None:
    """Raise :class:`TimeoutError` if the monotonic clock has crossed ``deadline``.

    Use this between pages of a paginated fetch to fail fast instead of
    grinding through more requests once the wall-clock budget is gone.

    Args:
        deadline: ``time.monotonic()`` instant past which we abort.
        label: Free-form label used in the exception message
            (e.g. ``"ccxt fetch for BTC/USDT"``).
        budget_s: Original budget in seconds, included verbatim in the
            message when present.
    """
    if time.monotonic() > deadline:
        suffix = f" exceeded {budget_s:.0f}s budget" if budget_s is not None else " exceeded budget"
        raise TimeoutError(f"{label}{suffix}")


_T = TypeVar("_T")


def retry_with_budget(
    fn: Callable[[], _T],
    *,
    transient: type[BaseException] | tuple[type[BaseException], ...],
    deadline: float,
    label: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: tuple[float, ...] = DEFAULT_BACKOFF,
) -> _T:
    """Call ``fn`` with a bounded retry budget on declared transient errors.

    Between attempts sleeps ``min(backoff[attempt], remaining_budget)`` so a
    short remaining budget never spends the full backoff. The terminal
    transient failure — whether ``max_retries`` is exhausted OR the deadline
    has passed — is wrapped in :class:`TimeoutError`, preserving the original
    exception as ``__cause__``. Anything not in ``transient`` propagates
    unchanged on the first occurrence (we never retry an exception class
    the caller didn't opt in to).

    Args:
        fn: Zero-arg callable producing the result.
        transient: Exception class(es) considered transient and retryable.
        deadline: ``time.monotonic()`` instant past which retries are aborted.
        label: Free-form label used in the TimeoutError message
            (e.g. ``"OKX fetch for BTC-USDT"``).
        max_retries: Additional attempts after the first call. Total
            attempts = ``max_retries + 1``.
        backoff: Per-retry sleep seconds. Must have at least
            ``max_retries`` entries.

    Returns:
        Whatever ``fn`` returns.

    Raises:
        ValueError: ``backoff`` is shorter than ``max_retries``.
        TimeoutError: All retries exhausted or the deadline crossed.
        Any non-transient exception: Propagated unchanged from ``fn``.
    """
    if len(backoff) < max_retries:
        raise ValueError(
            f"backoff has {len(backoff)} entries; need >= max_retries ({max_retries})"
        )
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except transient as exc:
            remaining = deadline - time.monotonic()
            if attempt == max_retries or remaining <= 0:
                raise TimeoutError(
                    f"{label} failed after {attempt + 1} attempt(s): {exc}"
                ) from exc
            time.sleep(min(backoff[attempt], max(0.0, remaining)))
    raise AssertionError("unreachable: retry loop must return or raise")  # pragma: no cover


# ---------------------------------------------------------------------------
# Opt-in local loader cache.
# ---------------------------------------------------------------------------

LOADER_CACHE_ENV = "VIBE_TRADING_DATA_CACHE"
_LOADER_CACHE_TRUE_VALUES = {"1", "true", "yes", "on"}
# Bump when the key payload or on-disk layout changes so stale entries are
# simply never matched (old files become unreachable garbage, safe to delete).
_LOADER_CACHE_VERSION = 2


def loader_cache_enabled() -> bool:
    """Return whether the local market-data cache is explicitly enabled."""
    return os.getenv(LOADER_CACHE_ENV, "").strip().lower() in _LOADER_CACHE_TRUE_VALUES


def make_loader_cache_key(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    fields: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Build a stable content-addressed key for one loader payload."""
    payload = _loader_cache_payload(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def loader_cache_path(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    fields: list[str] | tuple[str, ...] | None = None,
) -> Path:
    """Return the parquet cache path for one loader payload."""
    key = make_loader_cache_key(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    source_dir = _sanitize_cache_segment(source)
    return Path.home() / ".vibe-trading" / "cache" / "loaders" / source_dir / f"{key}.parquet"


def loader_cache_range_is_final(end_date: str) -> bool:
    """Return whether ``end_date`` is settled enough to cache.

    The key is content-addressed on ``end_date`` but not on wall-clock fetch
    time, so caching a range whose last bar is still forming (``end_date`` today
    or in the future) would pin a provisional bar and serve it on every later
    run. Only fully-elapsed days (strictly before today) are cacheable.
    """
    try:
        end = pd.Timestamp(end_date).normalize().date()
    except Exception:  # noqa: BLE001 - an unparseable date is treated as not cacheable
        return False
    return end < dt.date.today()


def loader_cache_get(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    fields: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame | None:
    """Return a cached DataFrame for one payload, or ``None`` on any miss.

    Misses include: cache disabled, range not yet settled, entry absent, or a
    corrupt entry. A corrupt entry is non-fatal — the caller falls back to the
    live provider.
    """
    if not loader_cache_enabled() or not loader_cache_range_is_final(end_date):
        return None
    cache_path = loader_cache_path(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    return _read_loader_cache_frame(cache_path)


def loader_cache_put(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    fields: list[str] | tuple[str, ...] | None,
    frame: pd.DataFrame | None,
) -> None:
    """Write one non-empty DataFrame to the cache; a no-op when not cacheable.

    Skips a disabled cache, an unsettled range, and empty/non-DataFrame results.
    Write failures are swallowed so a fetch never fails because of the cache.
    """
    if not loader_cache_enabled() or not loader_cache_range_is_final(end_date):
        return
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return
    cache_path = loader_cache_path(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    _write_loader_cache_frame(cache_path, frame)


def cached_loader_fetch(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    fields: list[str] | tuple[str, ...] | None,
    fetch: Callable[[], pd.DataFrame | None],
) -> pd.DataFrame | None:
    """Fetch one DataFrame through the opt-in local cache.

    Convenience wrapper over :func:`loader_cache_get` / :func:`loader_cache_put`
    for the common per-symbol loader loop: return the cached frame when present,
    otherwise call ``fetch`` and cache a non-empty result. Cache read/write
    failures are non-fatal and fall back to ``fetch``.
    """
    cached = loader_cache_get(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    if cached is not None:
        return cached

    frame = fetch()
    loader_cache_put(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        frame=frame,
    )
    return frame


def _loader_cache_payload(
    *,
    source: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    fields: list[str] | tuple[str, ...] | None,
) -> dict[str, object]:
    return {
        "version": _LOADER_CACHE_VERSION,
        "source": str(source),
        "symbol": str(symbol),
        "timeframe": str(timeframe),
        "start_date": _normalize_cache_date(start_date),
        "end_date": _normalize_cache_date(end_date),
        "fields": [str(field) for field in (fields or ())],
    }


def _normalize_cache_date(value: str) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _sanitize_cache_segment(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip().lower())
    return cleaned or "unknown"


def _loader_cache_metadata_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(cache_path.suffix + ".json")


def _read_loader_cache_frame(cache_path: Path) -> pd.DataFrame | None:
    if not cache_path.is_file():
        return None

    metadata_path = _loader_cache_metadata_path(cache_path)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - local cache miss is non-fatal
        logger.warning("loader cache metadata read failed for %s: %s", cache_path.name, exc)
        return None

    con = None
    try:
        import duckdb

        con = duckdb.connect(database=":memory:")
        frame = con.execute(
            f"SELECT * FROM read_parquet({_duckdb_sql_string(cache_path)})"
        ).fetchdf()
    except Exception as exc:  # noqa: BLE001 - corrupt cache falls back to provider
        logger.warning("loader cache read failed for %s: %s", cache_path.name, exc)
        return None
    finally:
        if con is not None:
            con.close()

    index_columns = metadata.get("index_columns") or []
    if index_columns:
        missing = [column for column in index_columns if column not in frame.columns]
        if missing:
            logger.warning("loader cache %s missing index column(s): %s", cache_path.name, missing)
            return None
        frame = frame.set_index(index_columns)
        frame.index.names = metadata.get("index_names") or index_columns
        frame = _restore_cache_index_dtypes(frame, metadata.get("index_dtypes"))
    frame.columns.name = metadata.get("columns_name")
    return frame


def _restore_cache_index_dtypes(frame: pd.DataFrame, index_dtypes: object) -> pd.DataFrame:
    """Best-effort restore of the per-level index dtypes recorded at write time.

    Cosmetic and non-fatal: duckdb parquet may rewrite datetime resolution, so
    we cast each level back to its original dtype. A failed cast leaves the
    duckdb-provided dtype rather than failing the read.
    """
    if not isinstance(index_dtypes, list) or frame.index.nlevels != len(index_dtypes):
        return frame
    try:
        if frame.index.nlevels == 1:
            frame.index = frame.index.astype(index_dtypes[0])
        else:
            for level, dtype in enumerate(index_dtypes):
                frame.index = frame.index.set_levels(
                    frame.index.levels[level].astype(dtype), level=level
                )
    except Exception:  # noqa: BLE001 - index dtype restore is cosmetic
        logger.debug("loader cache index dtype restore skipped: %s", index_dtypes)
    return frame


def _write_loader_cache_frame(cache_path: Path, frame: pd.DataFrame) -> None:
    metadata_path = _loader_cache_metadata_path(cache_path)
    # pid + uuid so two concurrent writers of the same key never share a tmp
    # path; os.replace then swaps each file in atomically.
    unique = f"{os.getpid()}.{uuid.uuid4().hex}"
    tmp_path = cache_path.with_name(f"{cache_path.name}.{unique}.tmp")
    tmp_metadata_path = metadata_path.with_name(f"{metadata_path.name}.{unique}.tmp")

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_frame, metadata = _frame_for_loader_cache(frame)

        import duckdb

        con = duckdb.connect(database=":memory:")
        try:
            con.register("cache_frame", cache_frame)
            con.execute(f"COPY cache_frame TO {_duckdb_sql_string(tmp_path)} (FORMAT PARQUET)")
        finally:
            con.close()

        tmp_metadata_path.write_text(
            json.dumps(metadata, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(tmp_path, cache_path)
        os.replace(tmp_metadata_path, metadata_path)
    except Exception as exc:  # noqa: BLE001 - cache write failures should not fail fetches
        logger.warning("loader cache write failed for %s: %s", cache_path.name, exc)
        for path in (tmp_path, tmp_metadata_path):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def _frame_for_loader_cache(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    cache_frame = frame.copy()
    original_index_names = list(cache_frame.index.names)
    columns_name = cache_frame.columns.name
    index_dtypes = [
        str(cache_frame.index.get_level_values(level).dtype)
        for level in range(cache_frame.index.nlevels)
    ]
    index_columns = _cache_index_columns(cache_frame)
    cache_frame.index = cache_frame.index.set_names(index_columns)
    metadata: dict[str, object] = {
        "version": _LOADER_CACHE_VERSION,
        "index_columns": index_columns,
        "index_names": original_index_names,
        # Preserve the columns-axis name (e.g. yfinance leaves "Price") and the
        # per-level index dtypes so a cached frame round-trips byte-identical to
        # a freshly fetched one (duckdb parquet otherwise rewrites datetime
        # resolution, e.g. [s] -> [us]).
        "columns_name": None if columns_name is None else str(columns_name),
        "index_dtypes": index_dtypes,
    }
    return cache_frame.reset_index(), metadata


def _cache_index_columns(frame: pd.DataFrame) -> list[str]:
    columns = {str(column) for column in frame.columns}
    used: set[str] = set()
    index_columns: list[str] = []
    for pos, name in enumerate(frame.index.names):
        base = str(name) if name is not None else f"__vibe_loader_index_{pos}__"
        candidate = base
        suffix = 1
        while candidate in columns or candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        index_columns.append(candidate)
        used.add(candidate)
    return index_columns


def _duckdb_sql_string(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


@runtime_checkable
class DataLoaderProtocol(Protocol):
    """Interface that every data source loader must satisfy."""

    name: str
    markets: set[str]
    requires_auth: bool

    def is_available(self) -> bool:
        """Check whether this data source is usable (token present, network ok, etc.)."""
        ...

    def fetch(
        self,
        codes: list[str],
        start_date: str,
        end_date: str,
        *,
        interval: str = "1D",
        fields: list[str] | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch OHLCV data.

        Returns:
            Mapping ``{symbol: DataFrame(trade_date, open, high, low, close, volume)}``.
        """
        ...
