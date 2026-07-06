"""Tests for agent.progress (heartbeat + structured progress emission)."""

from __future__ import annotations

import logging
import threading
import time

import pytest

from src.agent.progress import (
    HeartbeatTimer,
    ProgressEvent,
    _get_emitter,
    _set_emitter,
    emit_progress,
)


# ---------- ProgressEvent ---------------------------------------------------


def test_progress_event_to_dict_round_trip() -> None:
    """to_dict returns every public field with rounded elapsed_s."""
    e = ProgressEvent(
        tool="run_backtest",
        stage="loading",
        current=3,
        total=10,
        message="page 3",
        elapsed_s=1.23456,
    )
    d = e.to_dict()
    assert d["tool"] == "run_backtest"
    assert d["stage"] == "loading"
    assert d["current"] == 3
    assert d["total"] == 10
    assert d["message"] == "page 3"
    assert d["elapsed_s"] == 1.23
    assert "ts" in d


def test_progress_event_is_immutable() -> None:
    """frozen dataclass forbids field reassignment."""
    e = ProgressEvent(stage="x")
    with pytest.raises(Exception):
        e.stage = "y"  # type: ignore[misc]


# ---------- emit_progress ---------------------------------------------------


def test_emit_progress_noop_without_emitter() -> None:
    """emit_progress must silently no-op when nothing is listening."""
    # Ensure no leftover emitter from another test.
    _set_emitter(None)
    assert _get_emitter() is None
    emit_progress("nope", message="should not raise")
    # Still no emitter installed.
    assert _get_emitter() is None


def test_emit_progress_routes_to_active_emitter() -> None:
    """Installed emitter receives a ProgressEvent with the supplied fields."""
    captured: list[ProgressEvent] = []
    _set_emitter(captured.append)
    try:
        emit_progress("loading", current=2, total=5, message="halfway")
    finally:
        _set_emitter(None)

    assert len(captured) == 1
    assert captured[0].stage == "loading"
    assert captured[0].current == 2
    assert captured[0].total == 5
    assert captured[0].message == "halfway"
    # Tool name is filled by the agent loop, not the tool itself.
    assert captured[0].tool == ""


def test_emit_progress_swallows_emitter_errors() -> None:
    """A failing emitter must not propagate out of a tool."""
    def _boom(_ev: ProgressEvent) -> None:
        raise RuntimeError("emitter is angry")

    _set_emitter(_boom)
    try:
        # Should not raise.
        emit_progress("danger")
    finally:
        _set_emitter(None)


def test_set_emitter_is_thread_local() -> None:
    """Each thread gets its own emitter slot."""
    other_captured: list[ProgressEvent] = []

    def _other_thread() -> None:
        # No emitter installed on this thread.
        emit_progress("from_other")  # no-op
        assert _get_emitter() is None
        # Install a thread-local emitter.
        _set_emitter(other_captured.append)
        emit_progress("other_active")
        _set_emitter(None)

    main_captured: list[ProgressEvent] = []
    _set_emitter(main_captured.append)
    try:
        t = threading.Thread(target=_other_thread)
        t.start()
        t.join()
        emit_progress("main_still_here")
    finally:
        _set_emitter(None)

    # Main thread's emitter must not have received the other thread's event.
    assert [e.stage for e in main_captured] == ["main_still_here"]
    assert [e.stage for e in other_captured] == ["other_active"]


# ---------- HeartbeatTimer --------------------------------------------------


def test_heartbeat_timer_emits_ticks_until_exit() -> None:
    """Timer ticks ~every interval seconds and stops on context exit."""
    ticks: list[dict] = []
    # interval is clamped to 0.5 minimum, so sleep ~1.4s to fit two ticks.
    with HeartbeatTimer("dummy_tool", interval=0.5, emit=ticks.append):
        time.sleep(1.4)
    assert len(ticks) >= 2
    assert all(t["tool"] == "dummy_tool" for t in ticks)
    assert all(isinstance(t["elapsed_s"], (int, float)) for t in ticks)
    # Elapsed must be monotonic non-decreasing.
    elapsed = [t["elapsed_s"] for t in ticks]
    assert elapsed == sorted(elapsed)


def test_heartbeat_timer_clamps_short_interval() -> None:
    """Intervals below 0.5s are clamped to avoid CPU thrash."""
    timer = HeartbeatTimer("x", interval=0.01, emit=lambda d: None)
    assert timer._interval >= 0.5  # implementation detail but worth pinning


def test_heartbeat_timer_logs_warning_when_clamped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Clamping a sub-0.5s interval emits exactly one warning record."""
    with caplog.at_level(logging.WARNING, logger="src.agent.progress"):
        HeartbeatTimer("x", interval=0.01, emit=lambda d: None)
    clamp_records = [
        r for r in caplog.records if "clamped" in r.getMessage()
    ]
    assert len(clamp_records) == 1
    assert clamp_records[0].levelno == logging.WARNING


def test_heartbeat_timer_no_warning_when_interval_ok(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A valid interval (>= 0.5s) must not log the clamp warning."""
    with caplog.at_level(logging.WARNING, logger="src.agent.progress"):
        HeartbeatTimer("x", interval=1.5, emit=lambda d: None)
    assert not any("clamped" in r.getMessage() for r in caplog.records)


def test_heartbeat_timer_swallows_emit_errors() -> None:
    """A failing emit callback must not crash the heartbeat thread."""
    raised = threading.Event()

    def _boom(_d: dict) -> None:
        raised.set()
        raise RuntimeError("nope")

    with HeartbeatTimer("x", interval=0.3, emit=_boom):
        time.sleep(0.7)
    # The callback was invoked at least once and didn't bring the thread down.
    assert raised.is_set()


def test_heartbeat_timer_no_ticks_when_exits_before_interval() -> None:
    """Quick tool calls don't emit any heartbeat tick."""
    ticks: list[dict] = []
    with HeartbeatTimer("fast", interval=2.0, emit=ticks.append):
        time.sleep(0.05)
    assert ticks == []
