"""Unit tests for the shared loader retry/budget helpers.

The ccxt + okx integration tests already exercise these helpers via their
real loaders; these tests pin the helper semantics directly so future
loaders that adopt :func:`retry_with_budget` and :func:`check_budget`
inherit the same guarantees:

- Happy path runs ``fn`` exactly once.
- Transient exceptions retry up to ``max_retries + 1`` total attempts,
  then are wrapped in ``TimeoutError`` with the original as ``__cause__``.
- Non-transient exceptions propagate immediately, unchanged.
- A deadline crossed mid-retry aborts before exhausting attempts.
- ``check_budget`` raises iff the deadline has passed.
- A short remaining budget is never overspent by ``backoff``.
"""

from __future__ import annotations

import datetime as dt
import sys
import time
from types import SimpleNamespace

import pandas as pd
import pytest

import backtest.loaders.base as base
from backtest.loaders.base import (
    DEFAULT_BACKOFF,
    DEFAULT_MAX_RETRIES,
    LOADER_CACHE_ENV,
    cached_loader_fetch,
    check_budget,
    loader_cache_get,
    loader_cache_path,
    loader_cache_put,
    loader_cache_range_is_final,
    make_loader_cache_key,
    retry_with_budget,
)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Keep retry tests instant + deterministic."""
    monkeypatch.setattr(base.time, "sleep", lambda *_a, **_k: None)


class _Transient(Exception):
    pass


class _Fatal(Exception):
    pass


def _scripted(*outcomes):
    """Return a fn() that walks through scripted outcomes (return value or raise)."""
    state = {"i": 0}

    def fn():
        i = state["i"]
        state["i"] += 1
        outcome = outcomes[min(i, len(outcomes) - 1)]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    fn.state = state  # type: ignore[attr-defined]
    return fn


def test_happy_path_single_call():
    fn = _scripted("ok")
    deadline = time.monotonic() + 60
    assert retry_with_budget(fn, transient=_Transient, deadline=deadline, label="x") == "ok"
    assert fn.state["i"] == 1


def test_transient_retried_then_succeeds():
    fn = _scripted(_Transient("blip"), _Transient("blip"), "ok")
    deadline = time.monotonic() + 60
    assert retry_with_budget(fn, transient=_Transient, deadline=deadline, label="x") == "ok"
    assert fn.state["i"] == 3


def test_persistent_transient_exhausts_then_timeouts():
    fn = _scripted(_Transient("down"))
    deadline = time.monotonic() + 60
    with pytest.raises(TimeoutError) as ei:
        retry_with_budget(fn, transient=_Transient, deadline=deadline, label="myfetch")
    assert fn.state["i"] == DEFAULT_MAX_RETRIES + 1  # bounded
    # Original exception preserved as cause for diagnosability.
    assert isinstance(ei.value.__cause__, _Transient)
    assert "myfetch" in str(ei.value)
    assert "attempt(s)" in str(ei.value)


def test_non_transient_propagates_unchanged():
    fn = _scripted(_Fatal("logic bug"))
    deadline = time.monotonic() + 60
    with pytest.raises(_Fatal):  # NOT wrapped in TimeoutError
        retry_with_budget(fn, transient=_Transient, deadline=deadline, label="x")
    assert fn.state["i"] == 1


def test_deadline_crossed_mid_retry_aborts(monkeypatch):
    """A wall-clock deadline already past abort the retry on the first
    post-failure budget check, before max_retries is exhausted."""
    # ``monotonic`` always returns a value far past the deadline, so the
    # remaining-budget gate fires on the first transient failure.
    monkeypatch.setattr(base.time, "monotonic", lambda: 1_000_000.0)
    fn = _scripted(_Transient("slow"))
    with pytest.raises(TimeoutError):
        retry_with_budget(fn, transient=_Transient, deadline=2000.0, label="x")
    assert fn.state["i"] == 1  # aborted before any retry


def test_multi_transient_tuple():
    """Tuple of transient classes is supported (matches except T1|T2 semantics)."""

    class _A(Exception):
        pass

    class _B(Exception):
        pass

    fn = _scripted(_A("a"), _B("b"), "ok")
    deadline = time.monotonic() + 60
    assert retry_with_budget(fn, transient=(_A, _B), deadline=deadline, label="x") == "ok"


def test_backoff_shorter_than_retries_rejected():
    """Defensive: misconfigured backoff is rejected at call time, not silently
    indexed out of range mid-retry."""
    with pytest.raises(ValueError, match="backoff has"):
        retry_with_budget(
            _scripted("ok"),
            transient=_Transient,
            deadline=time.monotonic() + 60,
            label="x",
            max_retries=5,
            backoff=DEFAULT_BACKOFF,  # only 3 entries
        )


def test_check_budget_passes_before_deadline():
    check_budget(time.monotonic() + 60, "x")  # no raise


def test_check_budget_raises_past_deadline():
    with pytest.raises(TimeoutError, match="myfetch"):
        check_budget(time.monotonic() - 1, "myfetch", budget_s=60)


def test_check_budget_message_includes_budget_when_provided():
    with pytest.raises(TimeoutError, match="60s budget"):
        check_budget(time.monotonic() - 1, "label", budget_s=60.0)


def test_check_budget_message_omits_budget_when_absent():
    with pytest.raises(TimeoutError) as ei:
        check_budget(time.monotonic() - 1, "label")
    assert "budget" in str(ei.value)
    assert "0s" not in str(ei.value)  # don't print "0s budget" by accident


@pytest.fixture
def fake_duckdb(monkeypatch):
    """Install a tiny DuckDB stand-in so cache tests stay dependency-light."""

    class _Connection:
        def __init__(self):
            self._tables = {}
            self._frame = None

        def register(self, name, frame):
            self._tables[name] = frame.copy()

        def execute(self, sql):
            path = _first_sql_string(sql)
            if sql.strip().upper().startswith("COPY "):
                self._tables["cache_frame"].to_pickle(path)
                return self
            self._frame = pd.read_pickle(path)
            return self

        def fetchdf(self):
            return self._frame.copy()

        def close(self):
            pass

    def _first_sql_string(sql):
        start = sql.index("'") + 1
        end = sql.index("'", start)
        return sql[start:end].replace("''", "'")

    monkeypatch.setitem(
        sys.modules,
        "duckdb",
        SimpleNamespace(connect=lambda database=":memory:": _Connection()),
    )


def _cache_frame(value: float = 1.0) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "open": [value],
            "high": [value + 1],
            "low": [value - 1],
            "close": [value + 0.5],
            "volume": [100],
        },
        index=pd.DatetimeIndex(["2025-01-02"], name="trade_date"),
    )
    return frame


def test_loader_cache_disabled_by_default_bypasses_home(tmp_path, monkeypatch):
    monkeypatch.delenv(LOADER_CACHE_ENV, raising=False)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    calls = {"count": 0}
    frame = _cache_frame()

    def fetch():
        calls["count"] += 1
        return frame

    out = cached_loader_fetch(
        source="tushare",
        symbol="000001.SZ",
        timeframe="1D",
        start_date="2025-01-01",
        end_date="2025-01-03",
        fields=None,
        fetch=fetch,
    )

    assert calls["count"] == 1
    pd.testing.assert_frame_equal(out, frame)
    assert not (home / ".vibe-trading").exists()


def test_loader_cache_key_partitions_source_symbol_timeframe_date_and_fields():
    base_args = {
        "source": "tushare",
        "symbol": "000001.SZ",
        "timeframe": "1D",
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
        "fields": ["pe"],
    }
    key = make_loader_cache_key(**base_args)

    assert make_loader_cache_key(**{**base_args, "source": "akshare"}) != key
    assert make_loader_cache_key(**{**base_args, "symbol": "600519.SH"}) != key
    assert make_loader_cache_key(**{**base_args, "timeframe": "1H"}) != key
    assert make_loader_cache_key(**{**base_args, "start_date": "2024-12-31"}) != key
    assert make_loader_cache_key(**{**base_args, "end_date": "2025-01-04"}) != key
    assert make_loader_cache_key(**{**base_args, "fields": ["pb"]}) != key


def test_loader_cache_happy_path_writes_then_reuses(
    tmp_path,
    monkeypatch,
    fake_duckdb,
):
    monkeypatch.setenv(LOADER_CACHE_ENV, "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    calls = {"count": 0}
    frame = _cache_frame()

    def fetch():
        calls["count"] += 1
        return frame.copy()

    kwargs = {
        "source": "tushare",
        "symbol": "000001.SZ",
        "timeframe": "1D",
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
        "fields": ["pe"],
    }
    first = cached_loader_fetch(**kwargs, fetch=fetch)
    second = cached_loader_fetch(**kwargs, fetch=fetch)

    assert calls["count"] == 1
    pd.testing.assert_frame_equal(first, frame)
    pd.testing.assert_frame_equal(second, frame)
    assert loader_cache_path(**kwargs).is_file()
    assert str(loader_cache_path(**kwargs)).startswith(str(tmp_path / ".vibe-trading" / "cache"))


def test_loader_cache_corrupt_entry_falls_back_to_live_fetch(
    tmp_path,
    monkeypatch,
    fake_duckdb,
):
    monkeypatch.setenv(LOADER_CACHE_ENV, "true")
    monkeypatch.setenv("HOME", str(tmp_path))
    kwargs = {
        "source": "tushare",
        "symbol": "000001.SZ",
        "timeframe": "1D",
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
        "fields": [],
    }
    cache_path = loader_cache_path(**kwargs)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text("not a parquet file", encoding="utf-8")
    base._loader_cache_metadata_path(cache_path).write_text(
        '{"index_columns":["trade_date"],"index_names":["trade_date"],"version":1}',
        encoding="utf-8",
    )
    calls = {"count": 0}
    frame = _cache_frame()

    def fetch():
        calls["count"] += 1
        return frame

    out = cached_loader_fetch(**kwargs, fetch=fetch)

    assert calls["count"] == 1
    pd.testing.assert_frame_equal(out, frame)


def test_tushare_daily_fetch_uses_opt_in_cache_for_bars_and_fields(
    tmp_path,
    monkeypatch,
    fake_duckdb,
):
    monkeypatch.setenv(LOADER_CACHE_ENV, "yes")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TUSHARE_TOKEN", "test-token")

    class _FakeApi:
        def __init__(self):
            self.daily_calls = 0
            self.daily_basic_calls = 0

        def daily(self, ts_code, start_date, end_date):
            self.daily_calls += 1
            return pd.DataFrame(
                {
                    "ts_code": [ts_code, ts_code],
                    "trade_date": ["20250103", "20250102"],
                    "open": [2.0, 1.0],
                    "high": [3.0, 2.0],
                    "low": [1.0, 0.5],
                    "close": [2.5, 1.5],
                    "vol": [200, 100],
                }
            )

        def daily_basic(self, ts_code, start_date, end_date, fields):
            self.daily_basic_calls += 1
            return pd.DataFrame(
                {
                    "ts_code": [ts_code, ts_code],
                    "trade_date": ["20250102", "20250103"],
                    "pe": [10.0, 11.0],
                }
            )

    api = _FakeApi()
    monkeypatch.setitem(sys.modules, "tushare", SimpleNamespace(pro_api=lambda token: api))

    from backtest.loaders.tushare import DataLoader

    loader = DataLoader()
    first = loader.fetch(["000001.SZ"], "2025-01-01", "2025-01-03", fields=["pe"])
    second = loader.fetch(["000001.SZ"], "2025-01-01", "2025-01-03", fields=["pe"])

    assert api.daily_calls == 1
    assert api.daily_basic_calls == 1
    pd.testing.assert_frame_equal(first["000001.SZ"], second["000001.SZ"])
    assert list(first["000001.SZ"].columns) == ["open", "high", "low", "close", "volume", "pe"]


def test_loader_cache_range_is_final_only_for_settled_past():
    today = dt.date.today()
    yesterday = (today - dt.timedelta(days=1)).isoformat()
    tomorrow = (today + dt.timedelta(days=1)).isoformat()

    assert loader_cache_range_is_final(yesterday) is True
    assert loader_cache_range_is_final(today.isoformat()) is False
    assert loader_cache_range_is_final(tomorrow) is False
    # An unparseable end date is conservatively treated as not cacheable.
    assert loader_cache_range_is_final("not-a-date") is False


def test_loader_cache_skips_unsettled_today_range(tmp_path, monkeypatch):
    """A range ending today must never be cached: its last bar is still forming."""
    monkeypatch.setenv(LOADER_CACHE_ENV, "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    today = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=5)).isoformat()
    kwargs = {
        "source": "okx",
        "symbol": "BTC-USDT",
        "timeframe": "1D",
        "start_date": start,
        "end_date": today,
        "fields": None,
    }

    loader_cache_put(**kwargs, frame=_cache_frame())

    assert loader_cache_get(**kwargs) is None
    assert not loader_cache_path(**kwargs).exists()
    assert not (tmp_path / ".vibe-trading").exists()


def test_loader_cache_real_duckdb_round_trip(tmp_path, monkeypatch):
    """Exercise the real duckdb -> parquet -> duckdb path (CI mocks duckdb elsewhere)."""
    pytest.importorskip("duckdb")
    monkeypatch.setenv(LOADER_CACHE_ENV, "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    frame = _cache_frame()
    kwargs = {
        "source": "yfinance",
        "symbol": "AAPL.US",
        "timeframe": "1D",
        "start_date": "2025-01-01",
        "end_date": "2025-01-03",
        "fields": None,
    }

    assert loader_cache_get(**kwargs) is None  # cold miss
    loader_cache_put(**kwargs, frame=frame)
    restored = loader_cache_get(**kwargs)

    assert restored is not None
    assert loader_cache_path(**kwargs).is_file()
    assert restored.index.name == "trade_date"
    # The cache preserves columns name and per-level index dtype, so a real
    # duckdb round-trip is byte-identical to the source frame.
    pd.testing.assert_frame_equal(restored, frame)


def test_yfinance_loader_serves_second_fetch_from_cache(tmp_path, monkeypatch, fake_duckdb):
    """A batch loader (yfinance) must skip its bulk download on a full cache hit."""
    monkeypatch.setenv(LOADER_CACHE_ENV, "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import backtest.loaders.yfinance_loader as yfl

    calls = {"n": 0}

    def fake_download(tickers, start_date, end_date, interval):
        calls["n"] += 1
        return pd.DataFrame(
            {
                "Open": [1.0, 2.0],
                "High": [1.5, 2.5],
                "Low": [0.5, 1.5],
                "Close": [1.2, 2.2],
                "Volume": [100, 200],
            },
            index=pd.DatetimeIndex(["2025-01-02", "2025-01-03"], name="Date"),
        )

    monkeypatch.setattr(yfl, "_download_history", fake_download)

    loader = yfl.DataLoader()
    first = loader.fetch(["AAPL.US"], "2025-01-01", "2025-01-03")
    second = loader.fetch(["AAPL.US"], "2025-01-01", "2025-01-03")

    assert calls["n"] == 1  # second fetch is served from cache, no re-download
    assert "AAPL.US" in first and "AAPL.US" in second
    pd.testing.assert_frame_equal(first["AAPL.US"], second["AAPL.US"])
