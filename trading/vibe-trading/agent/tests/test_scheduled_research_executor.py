"""Tests for the scheduled research executor."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest
from src.scheduled_research.executor import (
    ScheduledResearchExecutor,
    is_due,
    next_due,
    scheduler_enabled_from_env,
)
from src.scheduled_research.models import JobStatus, ScheduledResearchJob
from src.scheduled_research.store import ScheduledResearchJobStore


def _ms(year: int, month: int, day: int, hour: int, minute: int) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=timezone.utc).timestamp() * 1000)


def _store(tmp_path: Path) -> ScheduledResearchJobStore:
    return ScheduledResearchJobStore(path=tmp_path / "jobs.json")


def _job(
    job_id: str = "job-001",
    *,
    schedule: str = "1000",
    next_run_at: int = 0,
    status: JobStatus = JobStatus.PENDING,
    created_at: int = 0,
) -> ScheduledResearchJob:
    return ScheduledResearchJob(
        id=job_id,
        prompt=f"prompt for {job_id}",
        schedule=schedule,
        next_run_at=next_run_at,
        status=status,
        created_at=created_at,
    )


def test_interval_job_fires_and_persists_completion(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job(schedule="5000", next_run_at=1000))
    calls: list[tuple[str, JobStatus]] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append((job.id, job.status))

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(1500)

    asyncio.run(scenario())

    saved = store.get("job-001")
    assert saved is not None
    assert calls == [("job-001", JobStatus.RUNNING)]
    assert saved.status == JobStatus.COMPLETED
    assert saved.last_run_at == 1500
    assert saved.next_run_at == 6500


def test_cron_job_next_due_and_not_before_due_time(tmp_path: Path) -> None:
    store = _store(tmp_path)
    before_due = _ms(2026, 6, 20, 5, 59)
    due_at = _ms(2026, 6, 20, 6, 0)
    following_due = _ms(2026, 6, 20, 12, 0)
    assert next_due("0 */6 * * *", before_due) == due_at

    store.upsert(_job(schedule="0 */6 * * *", next_run_at=due_at))
    calls: list[str] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(due_at - 1)
        assert calls == []
        await executor.tick(due_at)

    asyncio.run(scenario())

    saved = store.get("job-001")
    assert saved is not None
    assert calls == ["job-001"]
    assert saved.status == JobStatus.COMPLETED
    assert saved.last_run_at == due_at
    assert saved.next_run_at == following_due


def test_dispatch_failure_marks_failed_and_tick_continues(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job("bad", next_run_at=10))
    store.upsert(_job("good", next_run_at=20))
    calls: list[str] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)
        if job.id == "bad":
            raise RuntimeError("boom")

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(100)

    asyncio.run(scenario())

    bad = store.get("bad")
    good = store.get("good")
    assert bad is not None
    assert good is not None
    assert calls == ["bad", "good"]
    assert bad.status == JobStatus.FAILED
    assert good.status == JobStatus.COMPLETED


def test_stale_running_job_recovers_to_pending_and_fires_on_next_tick(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job("stale", schedule="1000", next_run_at=10, status=JobStatus.RUNNING))
    calls: list[tuple[str, JobStatus]] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append((job.id, job.status))

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        assert executor.recover_stale_running() == 1
        recovered = store.get("stale")
        assert recovered is not None
        assert recovered.status == JobStatus.PENDING
        await executor.tick(100)

    asyncio.run(scenario())

    saved = store.get("stale")
    assert saved is not None
    assert calls == [("stale", JobStatus.RUNNING)]
    assert saved.status == JobStatus.COMPLETED
    assert saved.last_run_at == 100
    assert saved.next_run_at == 1100


def test_impossible_cron_marks_failed_and_tick_continues(tmp_path: Path) -> None:
    store = _store(tmp_path)
    now = _ms(2026, 2, 1, 0, 0)
    store.upsert(_job("bad", schedule="0 0 31 2 *", next_run_at=10))
    store.upsert(_job("good", schedule="1000", next_run_at=20))
    calls: list[str] = []

    with pytest.raises(ValueError):
        next_due("0 0 31 2 *", now)

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(now)

    asyncio.run(scenario())

    bad = store.get("bad")
    good = store.get("good")
    assert bad is not None
    assert good is not None
    assert calls == ["bad", "good"]
    assert bad.status == JobStatus.FAILED
    assert bad.last_run_at == now
    assert bad.next_run_at == 10
    assert good.status == JobStatus.COMPLETED


def test_cancelled_and_running_jobs_are_skipped(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job("cancelled", next_run_at=0, status=JobStatus.CANCELLED))
    store.upsert(_job("pending", next_run_at=0, status=JobStatus.PENDING))
    calls: list[str] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        assert executor.recover_stale_running() == 0
        store.upsert(_job("running", next_run_at=0, status=JobStatus.RUNNING))
        await executor.tick(100)

    asyncio.run(scenario())

    assert is_due(store.get("cancelled"), 100) is False  # type: ignore[arg-type]
    assert is_due(store.get("running"), 100) is False  # type: ignore[arg-type]
    assert calls == ["pending"]
    assert store.get("cancelled").status == JobStatus.CANCELLED  # type: ignore[union-attr]
    assert store.get("running").status == JobStatus.RUNNING  # type: ignore[union-attr]
    assert store.get("pending").status == JobStatus.COMPLETED  # type: ignore[union-attr]


def test_failed_job_is_not_redispatched(tmp_path: Path) -> None:
    store = _store(tmp_path)
    # A terminal FAILED job whose next_run_at is still in the past must not be
    # re-dispatched on the next tick (it would otherwise fire every poll).
    store.upsert(_job("failed", next_run_at=0, status=JobStatus.FAILED))
    calls: list[str] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(100)

    asyncio.run(scenario())

    assert is_due(store.get("failed"), 100) is False  # type: ignore[arg-type]
    assert calls == []
    assert store.get("failed").status == JobStatus.FAILED  # type: ignore[union-attr]


def test_job_deleted_during_dispatch_is_not_resurrected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job("job-001", schedule="1000", next_run_at=0))

    async def dispatch(job: ScheduledResearchJob) -> None:
        # Simulate a user DELETE landing while the run is in flight.
        store.delete(job.id)

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(100)

    asyncio.run(scenario())

    # The deleted job must not reappear after dispatch completes.
    assert store.get("job-001") is None


def test_job_replaced_during_dispatch_is_not_overwritten(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job("job-001", schedule="1000", next_run_at=0))

    async def dispatch(job: ScheduledResearchJob) -> None:
        # Simulate a user POST replacing the job mid-run. The API stamps a fresh
        # created_at on every create, which is how a replacement is told apart
        # from the in-flight original (even when the schedule is unchanged).
        store.upsert(_job("job-001", schedule="5000", next_run_at=900, created_at=999))

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(store, dispatch)
        await executor.tick(100)

    asyncio.run(scenario())

    saved = store.get("job-001")
    assert saved is not None
    # The replacement definition is preserved, not clobbered by the old run.
    assert saved.schedule == "5000"
    assert saved.next_run_at == 900
    assert saved.created_at == 999
    assert saved.status == JobStatus.PENDING


def test_restart_after_missed_window_honors_persisted_next_run_at(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job(schedule="5000", next_run_at=1000))
    calls: list[str] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)

    async def scenario() -> None:
        first = ScheduledResearchExecutor(store, dispatch)
        await first.tick(20_000)
        assert calls == ["job-001"]

        restarted = ScheduledResearchExecutor(store, dispatch)
        await restarted.tick(20_000)

    asyncio.run(scenario())

    saved = store.get("job-001")
    assert saved is not None
    assert calls == ["job-001"]
    assert saved.status == JobStatus.COMPLETED
    assert saved.last_run_at == 20_000
    assert saved.next_run_at == 25_000


def test_disabled_executor_start_stop_are_noops(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.upsert(_job(next_run_at=0))
    calls: list[str] = []

    async def dispatch(job: ScheduledResearchJob) -> None:
        calls.append(job.id)

    async def scenario() -> None:
        executor = ScheduledResearchExecutor(
            store,
            dispatch,
            tick_interval_ms=1,
            now_fn=lambda: 100,
            enabled=False,
        )
        executor.start()
        assert executor.is_running is False
        await executor.stop()

    asyncio.run(scenario())

    assert scheduler_enabled_from_env("") is False
    assert scheduler_enabled_from_env("true") is True
    assert calls == []
    assert store.get("job-001").status == JobStatus.PENDING  # type: ignore[union-attr]
