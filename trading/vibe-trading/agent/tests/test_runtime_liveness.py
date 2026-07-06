"""Tests for live-runtime runner liveness (src/live/runtime/liveness.py,
SPEC.md §7.5 #3).

Heartbeat write/read, the alive predicate against a staleness threshold, and
the stale-runner reaper (borrowed from the swarm reaper shape). All time is
injected via ``now_ms`` so the tests are deterministic and never sleep; the
runtime root is redirected to a tmp dir.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.live import paths
from src.live.runtime import liveness
from src.live.runtime.liveness import (
    DEFAULT_STALENESS_MS,
    heartbeats_dir,
    is_runner_alive,
    last_tick,
    reap_stale,
    write_heartbeat,
)


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live runtime root at an isolated tmp dir."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def test_write_then_read_roundtrips(live_runtime: Path) -> None:
    written = write_heartbeat("runner-1", now_ms=123_456)
    assert written == 123_456
    assert last_tick("runner-1") == 123_456


def test_last_tick_missing_is_none(live_runtime: Path) -> None:
    assert last_tick("never-ran") is None


def test_write_is_atomic_no_temp_left(live_runtime: Path) -> None:
    write_heartbeat("r", now_ms=1)
    leftovers = list(heartbeats_dir().glob(".*tmp"))
    assert leftovers == []


def test_is_runner_alive_fresh(live_runtime: Path) -> None:
    write_heartbeat("r", now_ms=1_000_000)
    assert is_runner_alive("r", now_ms=1_000_000 + DEFAULT_STALENESS_MS) is True


def test_is_runner_alive_stale(live_runtime: Path) -> None:
    write_heartbeat("r", now_ms=1_000_000)
    assert is_runner_alive("r", now_ms=1_000_000 + DEFAULT_STALENESS_MS + 1) is False


def test_is_runner_alive_missing_is_false(live_runtime: Path) -> None:
    assert is_runner_alive("ghost", now_ms=0) is False


def test_unreadable_heartbeat_is_not_alive(live_runtime: Path) -> None:
    write_heartbeat("r", now_ms=1000)
    # Corrupt the file: a non-integer body reads as no-signal (fail-closed).
    liveness.heartbeat_path("r").write_text("not-a-number", encoding="utf-8")
    assert last_tick("r") is None
    assert is_runner_alive("r", now_ms=1000) is False


def test_invalid_runner_id_rejected_on_write(live_runtime: Path) -> None:
    with pytest.raises(ValueError):
        write_heartbeat("../escape", now_ms=0)
    with pytest.raises(ValueError):
        write_heartbeat("a/b", now_ms=0)
    with pytest.raises(ValueError):
        write_heartbeat("   ", now_ms=0)


def test_invalid_runner_id_reads_as_none(live_runtime: Path) -> None:
    # last_tick swallows the ValueError -> no signal.
    assert last_tick("../escape") is None


def test_reap_stale_removes_only_stale(live_runtime: Path) -> None:
    now = 10_000_000
    write_heartbeat("fresh", now_ms=now)
    write_heartbeat("stale", now_ms=now - DEFAULT_STALENESS_MS - 1)

    reaped = reap_stale(now_ms=now)
    assert reaped == ["stale"]
    # Fresh heartbeat survives; stale sentinel is gone.
    assert last_tick("fresh") == now
    assert last_tick("stale") is None


def test_reap_stale_empty_when_no_dir(live_runtime: Path) -> None:
    assert reap_stale(now_ms=0) == []


def test_reap_stale_nothing_when_all_fresh(live_runtime: Path) -> None:
    now = 5_000
    write_heartbeat("a", now_ms=now)
    write_heartbeat("b", now_ms=now)
    assert reap_stale(now_ms=now) == []
    assert last_tick("a") == now
    assert last_tick("b") == now
