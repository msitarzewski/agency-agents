"""Regression tests for the P12-b okx.py parity fix — the OKX loader must
fail fast on a transient disconnect instead of silently dropping the symbol
or stalling ~max_pages*timeout.

Pre-fix: `_fetch_candles` called requests.get once per page with no retry and
no wall-clock budget. Post-fix: bounded retry on the transient
requests.RequestException family + a hard budget raising a clear TimeoutError;
the happy path still issues one request per page (no behavior change).
"""

from __future__ import annotations

import importlib

import pandas as pd
import pytest
import requests

import backtest.loaders.okx as okx
from backtest.loaders.base import DEFAULT_MAX_RETRIES
from backtest.loaders.okx import DataLoader

S = int(pd.Timestamp("2026-05-01").timestamp() * 1000)
E = int((pd.Timestamp("2026-05-05") + pd.Timedelta(days=1)).timestamp() * 1000)


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p


def _ok_page():
    # one short page (< _MAX_PER_PAGE) so the loop breaks after one call
    ts = int(pd.Timestamp("2026-05-02").timestamp() * 1000)
    return _Resp({"code": "0", "data": [[ts, "1", "2", "0.5", "1.5", "10", "0", "0", "1"]]})


class _Seq:
    def __init__(self, script):
        self.script = script
        self.calls = 0

    def __call__(self, *a, **k):
        item = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if isinstance(item, BaseException):
            raise item
        return item


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(okx.time, "sleep", lambda *_a, **_k: None)


def test_transient_then_success(monkeypatch):
    seq = _Seq([requests.ConnectionError("blip"), requests.ConnectionError("blip"), _ok_page()])
    monkeypatch.setattr(okx.requests, "get", seq)
    df = DataLoader()._fetch_candles("BTC-USDT", S, E, "1D", 20)
    assert seq.calls >= 3
    assert df is not None and not df.empty


def test_persistent_disconnect_is_bounded(monkeypatch):
    seq = _Seq([requests.ConnectionError("down")])
    monkeypatch.setattr(okx.requests, "get", seq)
    with pytest.raises(TimeoutError):
        DataLoader()._fetch_candles("BTC-USDT", S, E, "1D", 20)
    assert seq.calls == DEFAULT_MAX_RETRIES + 1  # bounded, not max_pages/forever


def test_non_network_error_not_retried(monkeypatch):
    seq = _Seq([KeyError("logic bug")])
    monkeypatch.setattr(okx.requests, "get", seq)
    with pytest.raises(KeyError):
        DataLoader()._fetch_candles("BTC-USDT", S, E, "1D", 20)
    assert seq.calls == 1


def test_happy_path_single_call(monkeypatch):
    seq = _Seq([_ok_page()])
    monkeypatch.setattr(okx.requests, "get", seq)
    df = DataLoader()._fetch_candles("BTC-USDT", S, E, "1D", 20)
    assert seq.calls == 1
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_wallclock_budget_enforced(monkeypatch):
    seq = iter([1000.0, 1000.0, 1_000_000.0])
    monkeypatch.setattr(okx.time, "monotonic", lambda: next(seq, 1_000_000.0))
    monkeypatch.setattr(okx.requests, "get", _Seq([requests.ConnectionError("slow")]))
    with pytest.raises(TimeoutError):
        DataLoader()._fetch_candles("BTC-USDT", S, E, "1D", 20)


def test_invalid_timeout_env_values_fall_back_on_reload(monkeypatch, caplog):
    monkeypatch.setenv("OKX_TIMEOUT_S", "abc")
    monkeypatch.setenv("OKX_FETCH_BUDGET_S", "nope")
    try:
        with caplog.at_level("WARNING", logger="backtest.loaders.base"):
            module = importlib.reload(okx)

        assert module._OKX_TIMEOUT == 15
        assert module._OKX_FETCH_BUDGET_S == 60.0
        assert "OKX_TIMEOUT_S" in caplog.text
        assert "OKX_FETCH_BUDGET_S" in caplog.text
    finally:
        monkeypatch.delenv("OKX_TIMEOUT_S", raising=False)
        monkeypatch.delenv("OKX_FETCH_BUDGET_S", raising=False)
        importlib.reload(okx)


def test_valid_timeout_env_values_are_honored_on_reload(monkeypatch):
    monkeypatch.setenv("OKX_TIMEOUT_S", "7")
    monkeypatch.setenv("OKX_FETCH_BUDGET_S", "2.5")
    try:
        module = importlib.reload(okx)

        assert module._OKX_TIMEOUT == 7
        assert module._OKX_FETCH_BUDGET_S == 2.5
    finally:
        monkeypatch.delenv("OKX_TIMEOUT_S", raising=False)
        monkeypatch.delenv("OKX_FETCH_BUDGET_S", raising=False)
        importlib.reload(okx)
