"""Regression tests for P12-b — the ccxt loader must fail fast instead of
hanging on a transient disconnect.

Pre-fix: `_fetch_one` called `exchange.fetch_ohlcv` with no per-call timeout,
no retry, and no wall-clock budget, so a flaky connection hung
`get_market_data` for 10+ minutes. Post-fix: bounded retry on the transient
`ccxt.NetworkError` family + a hard budget that raises a clear `TimeoutError`;
the happy path is unchanged (one call per page).
"""

from __future__ import annotations

import importlib

import pandas as pd
import pytest

import ccxt

import backtest.loaders.ccxt_loader as cl
from backtest.loaders.base import DEFAULT_MAX_RETRIES
from backtest.loaders.ccxt_loader import DataLoader

SINCE = int(pd.Timestamp("2026-05-01").timestamp() * 1000)
END = int((pd.Timestamp("2026-05-05") + pd.Timedelta(days=1)).timestamp() * 1000)


def _bars(n: int = 4) -> list:
    base = int(pd.Timestamp("2026-05-01").timestamp() * 1000)
    day = 86_400_000
    return [[base + i * day, 100 + i, 101 + i, 99 + i, 100 + i, 10 + i] for i in range(n)]


class _FakeEx:
    """Scripted exchange: each fetch_ohlcv call consumes the next script item;
    an Exception item is raised, a list item is returned."""

    def __init__(self, script: list) -> None:
        self.script = script
        self.calls = 0

    def fetch_ohlcv(self, symbol, timeframe, since=None, limit=None):
        item = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if isinstance(item, BaseException):
            raise item
        return item


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(cl.time, "sleep", lambda *_a, **_k: None)


def test_transient_networkerror_retried_then_succeeds():
    ex = _FakeEx([ccxt.NetworkError("blip"), ccxt.NetworkError("blip"), _bars(), []])
    df = DataLoader._fetch_one(ex, "BTC/USDT", "1d", SINCE, END)
    assert ex.calls >= 3
    assert df is not None and not df.empty


def test_persistent_disconnect_is_bounded_not_a_hang():
    """The old 10-min hang: now a bounded TimeoutError after a fixed budget."""
    ex = _FakeEx([ccxt.NetworkError("down")])  # always fails
    with pytest.raises(TimeoutError):
        DataLoader._fetch_one(ex, "BTC/USDT", "1d", SINCE, END)
    assert ex.calls == DEFAULT_MAX_RETRIES + 1  # bounded, not range(200)/forever


def test_non_network_error_is_not_retried():
    ex = _FakeEx([ccxt.ExchangeError("bad symbol")])
    with pytest.raises(ccxt.ExchangeError):
        DataLoader._fetch_one(ex, "BTC/USDT", "1d", SINCE, END)
    assert ex.calls == 1


def test_happy_path_single_call_unchanged():
    ex = _FakeEx([_bars(), []])
    df = DataLoader._fetch_one(ex, "BTC/USDT", "1d", SINCE, END)
    assert ex.calls == 1  # short page (< limit) -> exactly one call, as before
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_wallclock_budget_enforced(monkeypatch):
    seq = iter([1000.0, 1000.0, 1_000_000.0])  # deadline blown by the retry check
    monkeypatch.setattr(cl.time, "monotonic", lambda: next(seq, 1_000_000.0))
    ex = _FakeEx([ccxt.NetworkError("slow")])
    with pytest.raises(TimeoutError):
        DataLoader._fetch_one(ex, "BTC/USDT", "1d", SINCE, END)


def test_get_exchange_sets_explicit_timeout():
    ex = DataLoader()._get_exchange()
    assert ex.timeout == cl._CCXT_TIMEOUT_MS


def test_invalid_timeout_env_values_fall_back_on_reload(monkeypatch, caplog):
    monkeypatch.setenv("CCXT_TIMEOUT_MS", "abc")
    monkeypatch.setenv("CCXT_FETCH_BUDGET_S", "nope")
    try:
        with caplog.at_level("WARNING", logger="backtest.loaders.base"):
            module = importlib.reload(cl)

        assert module._CCXT_TIMEOUT_MS == 15_000
        assert module._CCXT_FETCH_BUDGET_S == 60.0
        assert "CCXT_TIMEOUT_MS" in caplog.text
        assert "CCXT_FETCH_BUDGET_S" in caplog.text
    finally:
        monkeypatch.delenv("CCXT_TIMEOUT_MS", raising=False)
        monkeypatch.delenv("CCXT_FETCH_BUDGET_S", raising=False)
        importlib.reload(cl)


def test_valid_timeout_env_values_are_honored_on_reload(monkeypatch):
    monkeypatch.setenv("CCXT_TIMEOUT_MS", "1234")
    monkeypatch.setenv("CCXT_FETCH_BUDGET_S", "2.5")
    try:
        module = importlib.reload(cl)

        assert module._CCXT_TIMEOUT_MS == 1234
        assert module._CCXT_FETCH_BUDGET_S == 2.5
    finally:
        monkeypatch.delenv("CCXT_TIMEOUT_MS", raising=False)
        monkeypatch.delenv("CCXT_FETCH_BUDGET_S", raising=False)
        importlib.reload(cl)
