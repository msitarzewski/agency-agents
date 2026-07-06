"""Wall-clock scheduler for the live runtime (SPEC.md §7.5 #1).

Follows nanobot's ``cron/service.py`` shape: an asyncio timer that sleeps until
the earliest ``next_run_at`` across all jobs, fires the due jobs, advances each
fired job's ``next_run_at``, then re-sleeps. The sleep is **capped** at a
re-check interval (default 5 min) so a far-future job still wakes the loop
periodically — defending against wall-clock jumps, a job added while asleep, and
host suspend/resume drift.

Time is epoch-milliseconds throughout. Every pure decision helper takes
``now_ms`` explicitly (no wall-clock read inside) so scheduling logic is unit
testable without sleeping or freezing the clock. Only the async run loop reads
the real clock, via an injectable ``now_fn``.

The scheduler holds the live job set in memory and invokes an async
``on_fire(job)`` callback per due job; durability of the set is the
:class:`src.live.runtime.jobstore.JobStore`'s job, kept orthogonal here.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

#: Hard cap on how long the loop sleeps before re-checking, even when the next
#: job is far in the future. Bounds clock-drift / suspend-resume blind spots.
DEFAULT_MAX_RECHECK_MS = 5 * 60 * 1000

#: Default cadence applied when a job's ``schedule`` is a bare/empty/unknown
#: spec — the watch still fires on a sane interval rather than never.
DEFAULT_INTERVAL_MS = 60 * 1000

NowFn = Callable[[], int]
FireCallback = Callable[["Job"], Awaitable[None]]


def _now_ms() -> int:
    """Return the current wall-clock time in epoch milliseconds.

    Returns:
        Milliseconds since the Unix epoch.
    """
    return int(time.time() * 1000)


@dataclass
class Job:
    """A scheduled live-runtime job.

    ``next_run_at`` is mutable by design: the scheduler advances it in place
    after each fire (a frozen DTO would force a copy-and-reinsert per tick for
    no benefit, and the job's identity is its ``id``, not its run time). All
    other fields are treated as immutable after construction.

    Attributes:
        id: Stable unique identifier (also the key in the scheduler's set).
        next_run_at: Epoch-ms timestamp of the next scheduled fire. Mutated by
            the scheduler as the job recurs.
        schedule: Schedule spec. ``"interval:<ms>"`` recurs every ``<ms>``;
            ``"once"`` (or any unrecognized spec) fires a single time and is
            then removed. Higher-level market-hours / event triggers (SPEC #4)
            layer over this and are out of scope for this module.
        payload: Opaque, JSON-serializable application data carried with the
            job (e.g. mandate id / watch target). The scheduler never inspects
            it; it is round-tripped by the job store.
    """

    id: str
    next_run_at: int
    schedule: str
    payload: dict | None = field(default=None)

    def interval_ms(self) -> int | None:
        """Return the recurrence interval in ms, or ``None`` for one-shot jobs.

        Returns:
            The interval for an ``"interval:<ms>"`` schedule, ``None`` for a
            ``"once"`` schedule, and :data:`DEFAULT_INTERVAL_MS` for any other
            (non-empty) recognized-but-bare spec so a misconfigured job still
            watches on a sane cadence rather than silently never recurring.
        """
        spec = (self.schedule or "").strip().lower()
        if spec == "once":
            return None
        if spec.startswith("interval:"):
            raw = spec.split(":", 1)[1].strip()
            try:
                ms = int(raw)
            except ValueError:
                return DEFAULT_INTERVAL_MS
            return ms if ms > 0 else DEFAULT_INTERVAL_MS
        return DEFAULT_INTERVAL_MS


def earliest_next_run(jobs: list[Job]) -> int | None:
    """Return the smallest ``next_run_at`` across ``jobs``.

    Args:
        jobs: The current job set.

    Returns:
        The earliest scheduled fire time in epoch ms, or ``None`` when there
        are no jobs.
    """
    if not jobs:
        return None
    return min(job.next_run_at for job in jobs)


def due_jobs(jobs: list[Job], now_ms: int) -> list[Job]:
    """Return jobs whose ``next_run_at`` is at or before ``now_ms``.

    Args:
        jobs: The current job set.
        now_ms: The reference time in epoch ms.

    Returns:
        The due jobs, in ascending ``next_run_at`` order so the earliest-due
        fires first.
    """
    return sorted(
        (job for job in jobs if job.next_run_at <= now_ms),
        key=lambda job: job.next_run_at,
    )


def compute_sleep_ms(jobs: list[Job], now_ms: int, max_recheck_ms: int) -> int:
    """Compute how long the loop should sleep before its next check.

    Args:
        jobs: The current job set.
        now_ms: The reference time in epoch ms.
        max_recheck_ms: Hard upper bound on the returned sleep so a far-future
            job still wakes the loop periodically.

    Returns:
        A non-negative sleep duration in ms, clamped to ``[0, max_recheck_ms]``.
        Returns ``max_recheck_ms`` when there are no jobs (idle poll). Returns
        ``0`` when a job is already due so the loop fires it immediately.
    """
    earliest = earliest_next_run(jobs)
    if earliest is None:
        return max_recheck_ms
    delta = earliest - now_ms
    if delta <= 0:
        return 0
    return min(delta, max_recheck_ms)


def advance_after_fire(job: Job, now_ms: int) -> bool:
    """Advance a fired job's ``next_run_at``; report whether it should remain.

    Recurring jobs are re-scheduled one interval past ``now_ms`` (not past the
    old ``next_run_at``), so a job that fired late — because the host was
    suspended or the loop was busy — does not immediately re-fire a backlog of
    missed slots. One-shot jobs are not advanced.

    Args:
        job: The job that just fired. Mutated in place when recurring.
        now_ms: The time the job fired, in epoch ms.

    Returns:
        ``True`` if the job recurs and should stay in the set, ``False`` if it
        was one-shot and should be removed.
    """
    interval = job.interval_ms()
    if interval is None:
        return False
    job.next_run_at = now_ms + interval
    return True


class Scheduler:
    """Async wall-clock scheduler over an in-memory job set.

    Lifecycle: :meth:`start` spawns the loop task on the running event loop;
    :meth:`stop` cancels and awaits it. :meth:`add_job` / :meth:`remove_job`
    mutate the live set and wake the loop so a newly-added near-term job is not
    blocked behind a long sleep.

    The scheduler does not persist anything itself — pair it with a
    :class:`src.live.runtime.jobstore.JobStore` at the runner layer.

    Attributes:
        on_fire: Async callback invoked once per due job each tick.
    """

    def __init__(
        self,
        on_fire: FireCallback,
        *,
        max_recheck_ms: int = DEFAULT_MAX_RECHECK_MS,
        now_fn: NowFn = _now_ms,
    ) -> None:
        """Initialize the scheduler.

        Args:
            on_fire: Async callback invoked with each due :class:`Job`. An
                exception it raises is logged and swallowed so one bad job
                cannot kill the loop or starve its peers.
            max_recheck_ms: Cap on the loop's sleep (see
                :func:`compute_sleep_ms`).
            now_fn: Injectable wall-clock source returning epoch ms. Overridden
                in tests to make the loop deterministic.
        """
        self._on_fire = on_fire
        self._max_recheck_ms = max_recheck_ms
        self._now_fn = now_fn
        self._jobs: dict[str, Job] = {}
        self._task: asyncio.Task | None = None
        self._wakeup: asyncio.Event = asyncio.Event()
        self._stopping = False

    def jobs(self) -> list[Job]:
        """Return a snapshot list of the current jobs.

        Returns:
            A new list of the live :class:`Job` objects (the list is a copy;
            the jobs themselves are the live instances).
        """
        return list(self._jobs.values())

    def add_job(self, job: Job) -> None:
        """Add or replace a job and wake the loop.

        Args:
            job: The job to schedule. An existing job with the same ``id`` is
                replaced (idempotent re-registration on restart).
        """
        self._jobs[job.id] = job
        self._wakeup.set()

    def remove_job(self, job_id: str) -> bool:
        """Remove a job by id and wake the loop.

        Args:
            job_id: The id of the job to remove.

        Returns:
            ``True`` if a job was removed, ``False`` if no such job existed.
        """
        existed = self._jobs.pop(job_id, None) is not None
        if existed:
            self._wakeup.set()
        return existed

    def start(self) -> None:
        """Start the scheduler loop on the running event loop.

        Idempotent: calling :meth:`start` while already running is a no-op.

        Raises:
            RuntimeError: If there is no running event loop.
        """
        if self._task is not None and not self._task.done():
            return
        self._stopping = False
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run(), name="live-scheduler")

    async def stop(self) -> None:
        """Stop the scheduler loop and await its teardown.

        Idempotent: calling :meth:`stop` when not running is a no-op. Safe to
        call from within the same event loop the loop runs on.
        """
        self._stopping = True
        self._wakeup.set()
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _run(self) -> None:
        """Core loop: sleep until the earliest due job, fire it, repeat.

        Sleeps are interruptible by :attr:`_wakeup`, so ``add_job`` /
        ``remove_job`` / ``stop`` take effect immediately rather than after the
        current sleep expires.
        """
        while not self._stopping:
            now = self._now_fn()
            sleep_ms = compute_sleep_ms(self.jobs(), now, self._max_recheck_ms)
            if sleep_ms > 0:
                await self._sleep_or_wake(sleep_ms)
                if self._stopping:
                    break
                continue
            await self._fire_due(now)

    async def _sleep_or_wake(self, sleep_ms: int) -> None:
        """Sleep for ``sleep_ms`` or until woken by a set mutation / stop.

        Args:
            sleep_ms: Duration to sleep, in milliseconds.
        """
        self._wakeup.clear()
        try:
            await asyncio.wait_for(self._wakeup.wait(), timeout=sleep_ms / 1000.0)
        except asyncio.TimeoutError:
            pass

    async def _fire_due(self, now_ms: int) -> None:
        """Fire every job due at ``now_ms`` and reschedule/remove each.

        Args:
            now_ms: The reference time for due-ness, in epoch ms.
        """
        for job in due_jobs(self.jobs(), now_ms):
            try:
                await self._on_fire(job)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error("live scheduler on_fire failed for job %s", job.id, exc_info=True)
            keep = advance_after_fire(job, now_ms)
            if not keep:
                self._jobs.pop(job.id, None)
