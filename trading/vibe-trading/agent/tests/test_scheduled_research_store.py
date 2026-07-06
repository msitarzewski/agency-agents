"""Tests for the scheduled research job store.

Covers: happy-path CRUD, atomic persistence, invalid schedule rejection,
idempotent upsert, and empty-store behaviour.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from src.scheduled_research.models import JobStatus, ScheduledResearchJob, validate_schedule
from src.scheduled_research.store import CorruptStoreError, ScheduledResearchJobStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(
    job_id: str = "job-001",
    prompt: str = "analyse AAPL momentum",
    schedule: str = "60000",
) -> ScheduledResearchJob:
    now = int(time.time() * 1000)
    return ScheduledResearchJob(
        id=job_id,
        prompt=prompt,
        schedule=schedule,
        next_run_at=now + 60_000,
        status=JobStatus.PENDING,
        created_at=now,
    )


# ---------------------------------------------------------------------------
# validate_schedule unit tests
# ---------------------------------------------------------------------------


class TestValidateSchedule:
    def test_accepts_interval_ms(self) -> None:
        validate_schedule("60000")

    def test_accepts_cron_string(self) -> None:
        validate_schedule("0 */6 * * *")

    def test_accepts_cron_with_plain_numbers(self) -> None:
        validate_schedule("30 8 * * 1")

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("")

    def test_rejects_zero_interval(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("0")

    def test_rejects_negative_interval(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("-1000")

    def test_rejects_malformed_cron(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("* * * *")  # only 4 fields

    def test_rejects_non_numeric_cron_field(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("abc * * * *")

    def test_rejects_cron_with_invalid_step(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("*/0 * * * *")  # step of 0 is not allowed

    def test_rejects_out_of_range_minute(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("99 * * * *")  # minute > 59

    def test_rejects_out_of_range_hour(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("0 25 * * *")  # hour > 23

    def test_rejects_zero_day_of_month(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("0 0 0 * *")  # day-of-month is 1-31

    def test_rejects_out_of_range_step(self) -> None:
        with pytest.raises(ValueError):
            validate_schedule("*/99 * * * *")  # minute step > 59

    def test_accepts_boundary_values(self) -> None:
        validate_schedule("59 23 31 12 6")  # all field maxima


# ---------------------------------------------------------------------------
# Store CRUD tests
# ---------------------------------------------------------------------------


class TestScheduledResearchJobStore:
    def test_empty_store_returns_empty_list(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        assert store.list_jobs() == []

    def test_load_missing_file_returns_empty_dict(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        assert store.load() == {}

    def test_upsert_then_list(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        job = _make_job()
        store.upsert(job)
        result = store.list_jobs()
        assert len(result) == 1
        assert result[0].id == job.id
        assert result[0].status == JobStatus.PENDING

    def test_get_returns_job(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        job = _make_job()
        store.upsert(job)
        fetched = store.get(job.id)
        assert fetched is not None
        assert fetched.id == job.id
        assert fetched.prompt == job.prompt

    def test_get_missing_returns_none(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        assert store.get("nonexistent") is None

    def test_delete_removes_job(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        job = _make_job()
        store.upsert(job)
        removed = store.delete(job.id)
        assert removed is True
        assert store.get(job.id) is None

    def test_delete_missing_returns_false(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        assert store.delete("ghost") is False

    def test_idempotent_upsert_replaces_not_duplicates(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        job = _make_job()
        store.upsert(job)
        updated = ScheduledResearchJob(
            id=job.id,
            prompt="updated prompt",
            schedule=job.schedule,
            next_run_at=job.next_run_at,
            status=JobStatus.COMPLETED,
            created_at=job.created_at,
        )
        store.upsert(updated)
        jobs = store.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].prompt == "updated prompt"
        assert jobs[0].status == JobStatus.COMPLETED

    def test_filter_by_status(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        pending = _make_job("p1")
        completed = ScheduledResearchJob(
            id="c1",
            prompt="done",
            schedule="60000",
            status=JobStatus.COMPLETED,
            next_run_at=int(time.time() * 1000),
            created_at=int(time.time() * 1000),
        )
        store.upsert(pending)
        store.upsert(completed)
        pending_only = store.list_jobs(status="pending")
        assert len(pending_only) == 1
        assert pending_only[0].id == "p1"

    def test_list_honours_limit(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        for i in range(5):
            store.upsert(_make_job(f"job-{i:03d}"))
        assert len(store.list_jobs(limit=3)) == 3

    def test_upsert_rejects_malformed_schedule(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        bad_job = ScheduledResearchJob(
            id="bad",
            prompt="x",
            schedule="not-a-schedule",
            next_run_at=int(time.time() * 1000),
            created_at=int(time.time() * 1000),
        )
        with pytest.raises(ValueError):
            store.upsert(bad_job)

    def test_corrupt_store_raises_and_quarantines(self, tmp_path: Path) -> None:
        store_path = tmp_path / "jobs.json"
        store_path.write_text("{{not valid json}}", encoding="utf-8")
        store = ScheduledResearchJobStore(path=store_path)
        with pytest.raises(CorruptStoreError) as exc_info:
            store.load()
        assert not store_path.exists(), "original corrupt file should be gone"
        assert exc_info.value.quarantined.exists(), "quarantined file must exist"

    def test_atomic_write_cleans_up_temp_on_success(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        store.upsert(_make_job())
        # Verify no leftover .tmp files after a successful write
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"unexpected temp files: {tmp_files}"

    def test_persisted_data_round_trips(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        job = _make_job("rt-001", schedule="0 */4 * * *")
        store.upsert(job)

        # Open a fresh store instance to simulate restart
        store2 = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        fetched = store2.get("rt-001")
        assert fetched is not None
        assert fetched.prompt == job.prompt
        assert fetched.schedule == "0 */4 * * *"

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        store = ScheduledResearchJobStore(path=tmp_path / "jobs.json")
        cron_job = _make_job("cron-1", schedule="*/30 * * * *")
        store.upsert(cron_job)
        assert store.get("cron-1") is not None
