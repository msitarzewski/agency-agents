"""Tests for the live-runtime scheduler (src/live/runtime/scheduler.py,
SPEC.md §7.5 #1).

Two layers:
* pure decision helpers (``earliest_next_run`` / ``due_jobs`` /
  ``compute_sleep_ms`` / ``advance_after_fire``) — no clock, ``now_ms`` passed
  in, fully deterministic.
* the async ``Scheduler`` loop — driven with ``asyncio.run`` (house style; no
  pytest-asyncio in this repo) and a controllable ``now_fn`` so a job fires
  without real sleeping.
"""

from __future__ import annotations

import asyncio

from src.live.runtime.scheduler import (
    DEFAULT_INTERVAL_MS,
    DEFAULT_MAX_RECHECK_MS,
    Job,
    Scheduler,
    advance_after_fire,
    compute_sleep_ms,
    due_jobs,
    earliest_next_run,
)


def _job(jid: str, next_run_at: int, schedule: str = "interval:1000") -> Job:
    return Job(id=jid, next_run_at=next_run_at, schedule=schedule)


# ---- Job.interval_ms ------------------------------------------------------


def test_interval_ms_parses_interval_spec() -> None:
    assert _job("a", 0, "interval:5000").interval_ms() == 5000


def test_interval_ms_once_is_none() -> None:
    assert _job("a", 0, "once").interval_ms() is None


def test_interval_ms_bad_or_bare_spec_defaults() -> None:
    assert _job("a", 0, "interval:nope").interval_ms() == DEFAULT_INTERVAL_MS
    assert _job("a", 0, "interval:-5").interval_ms() == DEFAULT_INTERVAL_MS
    assert _job("a", 0, "weird").interval_ms() == DEFAULT_INTERVAL_MS
    assert _job("a", 0, "").interval_ms() == DEFAULT_INTERVAL_MS


# ---- pure decision helpers ------------------------------------------------


def test_earliest_next_run() -> None:
    assert earliest_next_run([]) is None
    assert earliest_next_run([_job("a", 30), _job("b", 10), _job("c", 20)]) == 10


def test_due_jobs_ordered_ascending() -> None:
    jobs = [_job("a", 30), _job("b", 10), _job("c", 20), _job("d", 100)]
    due = due_jobs(jobs, now_ms=25)
    assert [j.id for j in due] == ["b", "c"]


def test_compute_sleep_ms_no_jobs_polls_at_cap() -> None:
    assert compute_sleep_ms([], now_ms=0, max_recheck_ms=DEFAULT_MAX_RECHECK_MS) == DEFAULT_MAX_RECHECK_MS


def test_compute_sleep_ms_far_future_is_capped() -> None:
    jobs = [_job("a", 10_000_000)]
    assert compute_sleep_ms(jobs, now_ms=0, max_recheck_ms=5000) == 5000


def test_compute_sleep_ms_near_term_returns_delta() -> None:
    jobs = [_job("a", 800)]
    assert compute_sleep_ms(jobs, now_ms=300, max_recheck_ms=5000) == 500


def test_compute_sleep_ms_due_now_is_zero() -> None:
    jobs = [_job("a", 100)]
    assert compute_sleep_ms(jobs, now_ms=200, max_recheck_ms=5000) == 0


def test_advance_after_fire_recurring_reschedules_past_now() -> None:
    job = _job("a", next_run_at=100, schedule="interval:1000")
    # Fired late at now=5000; next run should be now+interval, not 100+interval,
    # so a backlog of missed slots does not stampede.
    keep = advance_after_fire(job, now_ms=5000)
    assert keep is True
    assert job.next_run_at == 6000


def test_advance_after_fire_once_is_removed() -> None:
    job = _job("a", next_run_at=100, schedule="once")
    keep = advance_after_fire(job, now_ms=5000)
    assert keep is False
    assert job.next_run_at == 100  # untouched


# ---- async Scheduler loop -------------------------------------------------


def test_scheduler_fires_due_job_then_removes_oneshot() -> None:
    fired: list[str] = []

    async def on_fire(job: Job) -> None:
        fired.append(job.id)

    # now_fn returns a fixed time well past the job's next_run_at so the loop
    # treats it as due immediately (sleep_ms == 0) — no real waiting.
    async def scenario() -> None:
        sched = Scheduler(on_fire, now_fn=lambda: 10_000)
        sched.add_job(Job(id="x", next_run_at=0, schedule="once"))
        sched.start()
        # Yield until the one-shot has fired and self-removed.
        for _ in range(100):
            await asyncio.sleep(0)
            if fired and not sched.jobs():
                break
        await sched.stop()

    asyncio.run(scenario())
    assert fired == ["x"]


def test_scheduler_recurring_job_stays_and_advances() -> None:
    fired: list[str] = []

    async def on_fire(job: Job) -> None:
        fired.append(job.id)

    async def scenario() -> None:
        sched = Scheduler(on_fire, now_fn=lambda: 10_000)
        sched.add_job(Job(id="r", next_run_at=0, schedule="interval:1000"))
        sched.start()
        for _ in range(100):
            await asyncio.sleep(0)
            if fired:
                break
        # Job advanced to now+interval == 11000 and remains scheduled.
        assert [j.id for j in sched.jobs()] == ["r"]
        assert sched.jobs()[0].next_run_at == 11_000
        await sched.stop()

    asyncio.run(scenario())
    assert fired and fired[0] == "r"


def test_scheduler_on_fire_exception_does_not_kill_loop() -> None:
    calls: list[str] = []

    async def on_fire(job: Job) -> None:
        calls.append(job.id)
        raise RuntimeError("boom")

    async def scenario() -> None:
        sched = Scheduler(on_fire, now_fn=lambda: 10_000)
        sched.add_job(Job(id="bad", next_run_at=0, schedule="once"))
        sched.start()
        for _ in range(100):
            await asyncio.sleep(0)
            if calls and not sched.jobs():
                break
        # Loop survived the raising callback and still removed the one-shot.
        assert sched._task is not None and not sched._task.done()
        await sched.stop()

    asyncio.run(scenario())
    assert calls == ["bad"]


def test_scheduler_remove_job_and_idempotent_add() -> None:
    async def on_fire(job: Job) -> None:  # pragma: no cover - never fires here
        pass

    async def scenario() -> None:
        sched = Scheduler(on_fire, now_fn=lambda: 0)
        sched.add_job(Job(id="a", next_run_at=10**12, schedule="once"))
        sched.add_job(Job(id="a", next_run_at=10**13, schedule="once"))  # replace
        assert len(sched.jobs()) == 1
        assert sched.jobs()[0].next_run_at == 10**13
        assert sched.remove_job("a") is True
        assert sched.remove_job("a") is False
        assert sched.jobs() == []

    asyncio.run(scenario())


def test_scheduler_stop_is_idempotent_when_not_started() -> None:
    async def on_fire(job: Job) -> None:  # pragma: no cover
        pass

    async def scenario() -> None:
        sched = Scheduler(on_fire)
        await sched.stop()  # never started — must be a no-op
        await sched.stop()

    asyncio.run(scenario())
