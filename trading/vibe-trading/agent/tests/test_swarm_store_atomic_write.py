"""Regression tests for P13 — SwarmStore atomic write/read must survive the
Windows concurrent-access race (os.replace WinError 5/32) deterministically.

The behaviour tests drive the public ``SwarmStore`` API with a fake
``os.replace`` and therefore run on BOTH pre- and post-fix code:
- pre-fix ``_atomic_write`` calls replace once -> a single transient failure
  propagates and ``update_run`` raises (test FAILS).
- post-fix it retries the WinError-scoped transient -> ``update_run`` lands
  (test PASSES).

A non-transient error must still raise immediately (no masking), the budget
is bounded, and POSIX behaviour is unchanged (a plain OSError without
``winerror`` is never treated as transient).
"""

from __future__ import annotations

import os

import pytest

import src.swarm.store as store_mod
from src.swarm.models import SwarmRun
from src.swarm.store import SwarmStore


def _winerr(code: int) -> PermissionError:
    e = PermissionError(f"simulated WinError {code}")
    e.winerror = code  # set even off-Windows so the test is deterministic
    return e


def _run(rid: str = "r") -> SwarmRun:
    return SwarmRun(id=rid, preset_name="demo", created_at="2026-01-01T00:00:00Z")


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Keep retry tests instant + deterministic.
    monkeypatch.setattr(store_mod.time, "sleep", lambda *_a, **_k: None)


def test_replace_retries_transient_winerror_then_succeeds(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    store.create_run(_run())

    real = os.replace
    calls = {"n": 0}

    def flaky(src, dst, *a, **k):
        calls["n"] += 1
        if calls["n"] <= 3:  # fail the first 3 attempts with WinError 5
            raise _winerr(5)
        return real(src, dst, *a, **k)

    monkeypatch.setattr(store_mod.os, "replace", flaky)

    upd = _run()
    upd.final_report = "RETRIED-OK"
    store.update_run(upd)  # pre-fix: raises on first WinError; post-fix: retries

    assert calls["n"] >= 4
    assert store.load_run("r").final_report == "RETRIED-OK"


def test_non_transient_error_reraises_immediately(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    store.create_run(_run())
    calls = {"n": 0}

    def boom(src, dst, *a, **k):
        calls["n"] += 1
        raise _winerr(2)  # ERROR_FILE_NOT_FOUND — NOT in the transient set

    monkeypatch.setattr(store_mod.os, "replace", boom)
    with pytest.raises(OSError):
        store.update_run(_run())
    assert calls["n"] == 1, "non-transient must not be retried (no masking)"


def test_transient_budget_is_bounded(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    store.create_run(_run())
    calls = {"n": 0}

    def always(src, dst, *a, **k):
        calls["n"] += 1
        raise _winerr(32)  # ERROR_SHARING_VIOLATION, forever

    monkeypatch.setattr(store_mod.os, "replace", always)
    with pytest.raises(OSError):
        store.update_run(_run())
    assert calls["n"] == store_mod._REPLACE_ATTEMPTS


def test_load_run_retries_transient_read_then_parses(tmp_path, monkeypatch):
    store = SwarmStore(base_dir=tmp_path)
    store.create_run(_run())

    real_validate = SwarmRun.model_validate_json
    calls = {"n": 0}

    def flaky_validate(data, *a, **k):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise ValueError("simulated partial-read / parse mid-replace")
        return real_validate(data, *a, **k)

    monkeypatch.setattr(store_mod.SwarmRun, "model_validate_json", staticmethod(flaky_validate))
    got = store.load_run("r")
    assert got is not None and got.id == "r"
    assert calls["n"] >= 3


def test_load_run_missing_is_fast_none(tmp_path, monkeypatch):
    """Fast not-found path must stay immediate (guards get_run_result(bogus))."""
    store = SwarmStore(base_dir=tmp_path)

    def fail_read(*a, **k):
        raise AssertionError("read_text must not be called for a missing run")

    monkeypatch.setattr(store_mod.SwarmRun, "model_validate_json", staticmethod(lambda *a, **k: fail_read()))
    assert store.load_run("does-not-exist") is None


def test_posix_oserror_is_not_treated_transient():
    """POSIX no-op guard: a plain OSError (no winerror) is never transient,
    so off-Windows the retry loop runs exactly once — no behavior change."""
    from src.swarm.store import _is_transient_windows_error

    assert _is_transient_windows_error(OSError("posix")) is False
    assert _is_transient_windows_error(_winerr(13)) is False
    assert _is_transient_windows_error(_winerr(5)) is True
