"""Tests for the durable live-runtime job store (src/live/runtime/jobstore.py,
SPEC.md §7.5 #1).

The store is exercised purely through its public API + the filesystem (the
runtime root is redirected to a tmp dir). Focus: atomic save round-trips, a
SIGKILL mid-write can never truncate the real store, a corrupt store is
quarantined and refuses an empty start, and a genuinely-missing store is the
only blank-start path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.live import paths
from src.live.runtime.jobstore import (
    CorruptJobStoreError,
    JobStore,
    runtime_dir,
)
from src.live.runtime.scheduler import Job


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live runtime root at an isolated tmp dir."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def _job(jid: str = "j1", next_run_at: int = 1000, schedule: str = "interval:60000") -> Job:
    return Job(id=jid, next_run_at=next_run_at, schedule=schedule, payload={"watch": jid})


def test_missing_store_loads_empty(live_runtime: Path) -> None:
    store = JobStore()
    assert not store.path.exists()
    assert store.load() == []


def test_save_then_load_roundtrips(live_runtime: Path) -> None:
    store = JobStore()
    jobs = [_job("a", 1000), _job("b", 2000, "once")]
    store.save(jobs)

    loaded = store.load()
    assert [j.id for j in loaded] == ["a", "b"]
    assert loaded[0].next_run_at == 1000
    assert loaded[1].schedule == "once"
    assert loaded[0].payload == {"watch": "a"}


def test_save_creates_runtime_dir_private(live_runtime: Path) -> None:
    store = JobStore()
    store.save([_job()])
    assert runtime_dir().is_dir()
    # The store file itself was written 0600 (best-effort; POSIX only).
    if os.name == "posix":
        assert (os.stat(store.path).st_mode & 0o777) == 0o600


def test_save_is_atomic_no_temp_left_behind(live_runtime: Path) -> None:
    store = JobStore()
    store.save([_job()])
    leftovers = list(runtime_dir().glob(".*tmp"))
    assert leftovers == [], f"temp files leaked: {leftovers}"


def test_save_overwrites_in_place(live_runtime: Path) -> None:
    store = JobStore()
    store.save([_job("a", 1000)])
    store.save([_job("a", 9999), _job("c", 1)])
    loaded = {j.id: j for j in store.load()}
    assert set(loaded) == {"a", "c"}
    assert loaded["a"].next_run_at == 9999


def test_sigkill_mid_write_leaves_old_store_intact(
    live_runtime: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crash during the write (modeled as os.replace raising) must leave the
    previously-committed store fully readable, never a truncated file."""
    store = JobStore()
    store.save([_job("a", 1000)])

    real_replace = os.replace

    def boom(src, dst, *a, **k):
        # Simulate SIGKILL after the temp is written + fsync'd but before the
        # atomic rename lands.
        raise OSError("simulated crash before rename")

    monkeypatch.setattr("src.live.runtime.jobstore.os.replace", boom)
    with pytest.raises(OSError):
        store.save([_job("a", 7777), _job("b", 2)])
    monkeypatch.setattr("src.live.runtime.jobstore.os.replace", real_replace)

    # Old store survives untouched — the half-written attempt never replaced it.
    loaded = {j.id: j for j in store.load()}
    assert set(loaded) == {"a"}
    assert loaded["a"].next_run_at == 1000


def test_corrupt_store_quarantined_and_refuses_empty_start(live_runtime: Path) -> None:
    store = JobStore()
    store.save([_job("a", 1000)])
    store.path.write_text("{ this is not valid json", encoding="utf-8")

    with pytest.raises(CorruptJobStoreError) as exc_info:
        store.load()

    err = exc_info.value
    # Quarantine file exists and the original is gone (renamed aside).
    assert err.quarantined.exists()
    assert err.quarantined.name.startswith("jobs.json.corrupt-")
    assert not store.path.exists()


def test_corrupt_wrong_shape_also_refuses(live_runtime: Path) -> None:
    store = JobStore()
    store.path.parent.mkdir(parents=True, exist_ok=True)
    # Valid JSON but not the expected envelope.
    store.path.write_text(json.dumps({"nope": []}), encoding="utf-8")
    with pytest.raises(CorruptJobStoreError):
        store.load()


def test_corrupt_bad_job_field_refuses(live_runtime: Path) -> None:
    store = JobStore()
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_text(
        json.dumps({"jobs": [{"id": "a", "next_run_at": "not-an-int", "schedule": "once"}]}),
        encoding="utf-8",
    )
    with pytest.raises(CorruptJobStoreError):
        store.load()


def test_explicit_path_is_honored(tmp_path: Path) -> None:
    custom = tmp_path / "nested" / "store.json"
    store = JobStore(path=custom)
    store.save([_job("a", 5)])
    assert custom.is_file()
    assert JobStore(path=custom).load()[0].id == "a"
