"""Executor for persisted scheduled research jobs.

The executor polls :class:`ScheduledResearchJobStore`, dispatches due jobs via
an injected async callable, and persists lifecycle/next-run updates after each
attempt. Schedule math is intentionally pure and clock-injected so tests can
exercise it without sleeping or reading wall-clock time.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from src.scheduled_research.models import JobStatus, ScheduledResearchJob, validate_schedule
from src.scheduled_research.store import ScheduledResearchJobStore

logger = logging.getLogger(__name__)

DEFAULT_TICK_INTERVAL_MS = 60 * 1000
SCHEDULER_ENABLED_ENV = "VIBE_TRADING_ENABLE_SCHEDULER"

NowFn = Callable[[], int]
DispatchCallback = Callable[[ScheduledResearchJob], Awaitable[None]]

_TRUE_VALUES = {"1", "true", "yes", "on"}
# Search by day, not by minute, so an impossible date (e.g. Feb 31) fails fast
# instead of scanning years of minutes on the event loop. Four years covers any
# real recurrence, including a Feb-29 leap day.
_CRON_SEARCH_LIMIT_DAYS = 4 * 366 + 1
_CRON_BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))


def _now_ms() -> int:
    """Return current wall-clock time in epoch milliseconds."""
    return int(time.time() * 1000)


def scheduler_enabled_from_env(value: str | None = None) -> bool:
    """Return whether the scheduled-research executor should run.

    The feature is disabled by default. Pass *value* in tests to avoid mutating
    process environment.
    """
    raw = os.getenv(SCHEDULER_ENABLED_ENV, "") if value is None else value
    return raw.strip().lower() in _TRUE_VALUES


def is_due(job: ScheduledResearchJob, now_ms: int) -> bool:
    """Return whether *job* should fire at ``now_ms``.

    Cancelled and failed jobs are terminal and never re-dispatched; a failed
    job in particular keeps its old ``next_run_at`` (advancement may itself be
    what failed), so excluding it here prevents a re-dispatch loop every tick.
    Already-running jobs are left alone during live polling. Executor startup
    recovers stale persisted ``RUNNING`` jobs separately.
    """
    if job.status in {JobStatus.CANCELLED, JobStatus.RUNNING, JobStatus.FAILED}:
        return False
    return job.next_run_at <= now_ms


def next_due(schedule: str, after_ms: int) -> int:
    """Return the first due epoch-ms strictly after ``after_ms``.

    Supports the scheduled-research schedule format: a bare positive integer
    string for interval milliseconds, or a simplified 5-field cron expression
    interpreted in UTC.
    """
    validate_schedule(schedule)
    spec = schedule.strip()
    if spec.isdigit():
        return after_ms + int(spec)
    return _next_cron_due(spec, after_ms)


def _next_cron_due(schedule: str, after_ms: int) -> int:
    minutes, hours, doms, months, dows = (
        _parse_cron_field(part, low, high) for part, (low, high) in zip(schedule.split(), _CRON_BOUNDS)
    )
    start = datetime.fromtimestamp(after_ms / 1000.0, timezone.utc) + timedelta(milliseconds=1)
    # Round up to the next whole minute; cron has minute resolution.
    if start.second or start.microsecond:
        start = (start + timedelta(minutes=1)).replace(second=0, microsecond=0)

    day = start.replace(hour=0, minute=0, second=0, microsecond=0)
    for offset in range(_CRON_SEARCH_LIMIT_DAYS):
        candidate_day = day + timedelta(days=offset)
        if not _day_matches(candidate_day, doms, months, dows):
            continue
        for hour in sorted(hours) if hours is not None else range(24):
            for minute in sorted(minutes) if minutes is not None else range(60):
                fire = candidate_day.replace(hour=hour, minute=minute)
                if fire >= start:
                    return int(fire.timestamp() * 1000)
    raise ValueError(f"cron schedule has no matching time within search window: {schedule!r}")


def _parse_cron_field(part: str, low: int, high: int) -> set[int] | None:
    if part == "*":
        return None
    if part.startswith("*/"):
        step = int(part[2:])
        return set(range(low, high + 1, step))
    return {int(part)}


def _day_matches(dt: datetime, doms: set[int] | None, months: set[int] | None, dows: set[int] | None) -> bool:
    cron_day_of_week = (dt.weekday() + 1) % 7  # cron convention: Sunday == 0
    return (
        (doms is None or dt.day in doms)
        and (months is None or dt.month in months)
        and (dows is None or cron_day_of_week in dows)
    )


class ScheduledResearchExecutor:
    """Background poller that dispatches due scheduled research jobs."""

    def __init__(
        self,
        store: ScheduledResearchJobStore,
        dispatch: DispatchCallback,
        *,
        tick_interval_ms: int = DEFAULT_TICK_INTERVAL_MS,
        now_fn: NowFn = _now_ms,
        enabled: bool = True,
    ) -> None:
        """Initialize the executor.

        Args:
            store: Durable scheduled job store.
            dispatch: Async callable invoked once for each due job.
            tick_interval_ms: Poll interval for the background loop.
            now_fn: Injectable wall-clock source returning epoch milliseconds.
            enabled: When false, :meth:`start` and :meth:`stop` are no-ops.
        """
        self._store = store
        self._dispatch = dispatch
        self._tick_interval_ms = tick_interval_ms
        self._now_fn = now_fn
        self._enabled = enabled
        self._task: asyncio.Task | None = None
        self._wakeup: asyncio.Event | None = None
        self._stopping = False
        self._recovered_stale_running = False

    @property
    def is_running(self) -> bool:
        """Return whether the background loop task is active."""
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        """Start the background loop.

        Idempotent. When disabled, this is a no-op.
        """
        if not self._enabled or self.is_running:
            return
        self._stopping = False
        self.recover_stale_running()
        self._wakeup = asyncio.Event()
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run(), name="scheduled-research-executor")

    async def stop(self) -> None:
        """Stop the background loop and wait for it to finish.

        Idempotent. When disabled or not started, this is a no-op.
        """
        if not self._enabled:
            return
        task = self._task
        if task is None:
            return
        self._stopping = True
        if self._wakeup is not None:
            self._wakeup.set()
        # The set() above wakes a sleeping loop in the common case. Cancel as a
        # fallback so shutdown never blocks for a full tick if the wakeup raced
        # the loop's sleep, then await the task to let it unwind cleanly.
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def tick(self, now_ms: int | None = None) -> None:
        """Run one poll/dispatch pass.

        Args:
            now_ms: Optional explicit reference time. Defaults to ``now_fn``.
        """
        self.recover_stale_running()
        now = self._now_fn() if now_ms is None else now_ms
        jobs = sorted(
            (job for job in self._store.load().values() if is_due(job, now)),
            key=lambda job: job.next_run_at,
        )
        for job in jobs:
            await self._run_job(job, now)

    def recover_stale_running(self) -> int:
        """Reset jobs left ``RUNNING`` by a previous executor process.

        This runs at most once per executor instance. Jobs that become
        ``RUNNING`` after this recovery step are treated as live in-flight work
        and remain skipped by :func:`is_due`.
        """
        if self._recovered_stale_running:
            return 0

        jobs = self._store.load()
        recovered = 0
        for job in jobs.values():
            if job.status != JobStatus.RUNNING:
                continue
            job.status = JobStatus.PENDING
            recovered += 1
            logger.warning("recovering stale scheduled research job %s from running to pending", job.id)

        if recovered:
            self._store.save(jobs)
        self._recovered_stale_running = True
        return recovered

    async def _run(self) -> None:
        while not self._stopping:
            try:
                await self.tick(self._now_fn())
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error("scheduled research executor tick failed", exc_info=True)
            if self._stopping:
                break
            await self._sleep_or_wake(self._tick_interval_ms)

    async def _sleep_or_wake(self, sleep_ms: int) -> None:
        wakeup = self._wakeup
        if wakeup is None:
            await asyncio.sleep(sleep_ms / 1000.0)
            return
        # Re-check after re-entering: if stop() flipped _stopping and set the
        # event between the loop's check and here, return at once rather than
        # clearing the wakeup and blocking for a full tick on shutdown.
        if self._stopping:
            return
        wakeup.clear()
        try:
            await asyncio.wait_for(wakeup.wait(), timeout=sleep_ms / 1000.0)
        except asyncio.TimeoutError:
            pass

    async def _run_job(self, job: ScheduledResearchJob, now_ms: int) -> None:
        # The tick snapshot may be stale by the time we reach this job (an
        # earlier dispatch was awaited). Re-read and confirm identity before
        # marking it RUNNING so a job the user deleted or replaced in the
        # meantime is not resurrected or dispatched.
        current = self._store.get(job.id)
        if current is None or not self._same_record(current, job) or not is_due(current, now_ms):
            return
        job = current

        job.status = JobStatus.RUNNING
        self._store.upsert(job)

        try:
            await self._dispatch(job)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.error("scheduled research dispatch failed for job %s", job.id, exc_info=True)
            final_status = JobStatus.FAILED
        else:
            final_status = JobStatus.COMPLETED

        job.last_run_at = now_ms
        try:
            job.next_run_at = next_due(job.schedule, now_ms)
        except Exception:
            logger.error("scheduled research schedule advancement failed for job %s", job.id, exc_info=True)
            job.status = JobStatus.FAILED
            self._persist_completion(job)
            return

        job.status = final_status
        self._persist_completion(job)

    @staticmethod
    def _same_record(current: ScheduledResearchJob, job: ScheduledResearchJob) -> bool:
        """Return whether *current* is the same scheduled run we started.

        ``created_at`` is assigned once at creation, so a replacement POST for
        the same id (which the API stamps with a fresh ``created_at``) is
        distinguishable even when the schedule is unchanged.
        """
        return current.id == job.id and current.created_at == job.created_at

    def _persist_completion(self, job: ScheduledResearchJob) -> None:
        """Write a finished job back, unless it was changed during dispatch.

        Dispatch is awaited, so a concurrent DELETE or POST for the same id can
        land while a run is in flight. Reload first: if the record is gone the
        user cancelled it (do not resurrect), and if it is a different record
        (replaced via POST) let the new definition own its lifecycle. Only
        persist our completion when it still refers to the same scheduled run.
        """
        current = self._store.get(job.id)
        if current is None:
            logger.info("scheduled research job %s deleted during dispatch; skipping completion write", job.id)
            return
        if not self._same_record(current, job):
            logger.info("scheduled research job %s replaced during dispatch; skipping completion write", job.id)
            return
        self._store.upsert(job)
