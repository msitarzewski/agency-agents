"""Unit tests for the persistent live-trading runner (SPEC.md §7.5 #2, #7).

The runner is exercised with all external dependencies stubbed — no live agent,
no broker, no real audit ledger — so these tests assert pure control flow:

* tick ordering (halt → expiry → reconcile → invoke → audit),
* halt aborts before anything else,
* proactive expiry trips a stop AND never reaches the agent invocation,
* a reconcile-unsafe / reconcile-error report aborts (no auto-resend, §8 #5),
* the mandate is pinned inline in the prompt the runner constructs.

pytest-asyncio is not a dependency here, so the single async entry
(:meth:`LiveRunner.run_once`) is driven via :func:`asyncio.run`.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import pytest

from src.live.mandate.model import (
    AssetClass,
    ConsentMeta,
    HardCaps,
    InstrumentType,
    Mandate,
    UniverseConstraint,
    MANDATE_SCHEMA_VERSION,
)
from src.live.runtime.runner import (
    LiveRunner,
    TICK_ERROR,
    TICK_EXPIRED,
    TICK_HALTED,
    TICK_INVOKED,
    TICK_NO_MANDATE,
    TICK_RECONCILE_ERROR,
    TICK_RECONCILE_UNSAFE,
    _mandate_is_expired,
    _parse_expiry,
    _pin_mandate_prompt,
    _report_is_unsafe,
)

BROKER = "robinhood"
_FIXED_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Fixtures / stubs
# --------------------------------------------------------------------------- #


def _make_mandate(*, expires_at: str) -> Mandate:
    """Build a minimal valid mandate with a caller-chosen ``expires_at``."""
    return Mandate(
        schema_version=MANDATE_SCHEMA_VERSION,
        hard_caps=HardCaps(
            account_funding_usd=10_000.0,
            max_order_notional_usd=750.0,
            max_total_exposure_usd=5_000.0,
            max_leverage=1.0,
            allowed_instruments=(InstrumentType.EQUITY, InstrumentType.ETF),
            max_trades_per_day=5,
        ),
        universe=UniverseConstraint(
            asset_classes=(AssetClass.US_EQUITY,),
            min_market_cap_usd=1_000_000_000.0,
            min_avg_daily_volume_usd=5_000_000.0,
            exclude_symbols=("GME", "AMC"),
        ),
        consent=ConsentMeta(
            created_at="2026-06-01T00:00:00Z",
            consent_token_sha256="deadbeef",
            broker=BROKER,
            account_ref="acct-xyz",
            expires_at=expires_at,
        ),
    )


def _future_expiry() -> str:
    return (_FIXED_NOW + timedelta(days=30)).isoformat().replace("+00:00", "Z")


def _past_expiry() -> str:
    return (_FIXED_NOW - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")


class _SafeReport:
    """A reconcile report that reports a clean, safe-to-trade state."""

    safe_to_trade = True


class _UnsafeReport:
    """A reconcile report that flags an unsafe / ambiguous state."""

    safe_to_trade = False


class _OrderTracker:
    """Records the order in which the runner reaches each tick stage."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.audits: list[dict[str, Any]] = []
        self.agent_prompts: list[str] = []
        self.tripped: list[dict[str, Any]] = []

    def halt_flag(self, broker: str | None) -> bool:
        self.calls.append("halt")
        return False

    def load_mandate(self, broker: str) -> Mandate | None:
        self.calls.append("mandate")
        return _make_mandate(expires_at=_future_expiry())

    def reconcile(self, broker, read_positions, read_balance, read_open_orders):
        self.calls.append("reconcile")
        return _SafeReport()

    async def agent_caller(self, session_id: str, prompt: str) -> Mapping[str, Any]:
        self.calls.append("invoke")
        self.agent_prompts.append(prompt)
        return {"status": "success", "content": "held"}

    def write_audit(self, event) -> Mapping[str, Any]:
        self.calls.append("audit")
        record = {"audit_id": event.audit_id, "kind": event.kind, "outcome": event.outcome}
        self.audits.append(record)
        return record

    def trip_halt(self, by: str, reason: str, broker: str | None = None):
        self.tripped.append({"by": by, "reason": reason, "broker": broker})


def _read_stub() -> list:
    return []


def _build_runner(tracker: _OrderTracker, **overrides) -> LiveRunner:
    """Build a runner wired entirely to the tracker stubs, with overrides."""
    kwargs: dict[str, Any] = dict(
        agent_caller=tracker.agent_caller,
        reconcile_fn=tracker.reconcile,
        read_positions=_read_stub,
        read_balance=_read_stub,
        read_open_orders=_read_stub,
        clock=lambda: _FIXED_NOW,
        load_mandate_fn=tracker.load_mandate,
        write_audit_fn=tracker.write_audit,
        halt_flag_fn=tracker.halt_flag,
        trip_halt_fn=tracker.trip_halt,
        session_id="live-test",
    )
    kwargs.update(overrides)
    return LiveRunner(BROKER, **kwargs)


# --------------------------------------------------------------------------- #
# Pure-helper tests
# --------------------------------------------------------------------------- #


def test_parse_expiry_handles_z_suffix() -> None:
    parsed = _parse_expiry("2026-06-28T00:00:00Z")
    assert parsed == datetime(2026, 6, 28, tzinfo=timezone.utc)


def test_parse_expiry_handles_offset() -> None:
    parsed = _parse_expiry("2026-06-28T00:00:00+00:00")
    assert parsed == datetime(2026, 6, 28, tzinfo=timezone.utc)


def test_parse_expiry_unparseable_is_none() -> None:
    assert _parse_expiry("not-a-date") is None
    assert _parse_expiry("") is None


def test_mandate_expired_failclosed_on_bad_expiry() -> None:
    mandate = _make_mandate(expires_at="garbage")
    assert _mandate_is_expired(mandate, _FIXED_NOW) is True


def test_mandate_not_expired_in_future() -> None:
    mandate = _make_mandate(expires_at=_future_expiry())
    assert _mandate_is_expired(mandate, _FIXED_NOW) is False


def test_report_is_unsafe_defensive() -> None:
    assert _report_is_unsafe(None) is True
    assert _report_is_unsafe(_SafeReport()) is False
    assert _report_is_unsafe(_UnsafeReport()) is True

    class _Ambiguous:
        ambiguous = True

    assert _report_is_unsafe(_Ambiguous()) is True

    class _Unknown:
        pass

    assert _report_is_unsafe(_Unknown()) is True  # fail-closed on unknown shape


def test_pin_mandate_prompt_includes_full_mandate() -> None:
    mandate = _make_mandate(expires_at=_future_expiry())
    prompt = _pin_mandate_prompt(BROKER, mandate, _FIXED_NOW)
    # Hard caps and universe pinned inline (survives loop.py compaction).
    assert "750.0" in prompt  # max order notional
    assert "5000.0" in prompt  # max total exposure
    assert "Max trades per UTC day: 5" in prompt
    assert "equity, etf" in prompt
    assert "us_equity" in prompt
    assert "GME, AMC" in prompt  # exclude list
    assert BROKER in prompt


# --------------------------------------------------------------------------- #
# run_once control-flow tests
# --------------------------------------------------------------------------- #


def test_happy_path_tick_ordering() -> None:
    tracker = _OrderTracker()
    runner = _build_runner(tracker)
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_INVOKED
    assert result["agent_result"] == {"status": "success", "content": "held"}
    # Order: halt → mandate → reconcile → invoke → audit.
    assert tracker.calls == ["halt", "mandate", "reconcile", "invoke", "audit"]
    # Mandate was pinned into the prompt actually sent to the agent.
    assert tracker.agent_prompts and "Max trades per UTC day: 5" in tracker.agent_prompts[0]


def test_halt_aborts_before_anything_else() -> None:
    tracker = _OrderTracker()
    runner = _build_runner(tracker, halt_flag_fn=lambda broker: True)
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_HALTED
    # No mandate load, no reconcile, no invoke — only the halt audit.
    assert tracker.calls == ["audit"]
    assert tracker.audits[0]["kind"] == "halt_tripped"
    assert not tracker.agent_prompts


def test_no_mandate_aborts_with_block() -> None:
    tracker = _OrderTracker()
    runner = _build_runner(tracker, load_mandate_fn=lambda broker: None)
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_NO_MANDATE
    assert tracker.calls == ["halt", "audit"]
    assert not tracker.agent_prompts


def test_proactive_expiry_trips_stop_and_never_invokes() -> None:
    tracker = _OrderTracker()
    runner = _build_runner(
        tracker,
        load_mandate_fn=lambda broker: _make_mandate(expires_at=_past_expiry()),
    )
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_EXPIRED
    # Authority was cut: a per-broker halt was tripped.
    assert tracker.tripped == [
        {
            "by": "file",
            "reason": "mandate expired — proactive runner stop",
            "broker": BROKER,
        }
    ]
    # Expiry acted on BEFORE reconcile/invoke; the agent is never reached.
    assert "reconcile" not in tracker.calls
    assert "invoke" not in tracker.calls
    assert not tracker.agent_prompts
    assert tracker.audits[-1]["kind"] == "halt_tripped"


def test_reconcile_unsafe_aborts_no_resend() -> None:
    tracker = _OrderTracker()
    runner = _build_runner(tracker, reconcile_fn=lambda *a: _UnsafeReport())
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_RECONCILE_UNSAFE
    # Reached reconcile but NOT invoke — no auto-resend on ambiguous state.
    assert "invoke" not in tracker.calls
    assert not tracker.agent_prompts
    assert tracker.audits[-1]["kind"] == "breach"


def test_reconcile_error_is_failclosed() -> None:
    tracker = _OrderTracker()

    def _boom(*_a):
        raise RuntimeError("broker read timeout")

    runner = _build_runner(tracker, reconcile_fn=_boom)
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_RECONCILE_ERROR
    assert "invoke" not in tracker.calls
    assert not tracker.agent_prompts


def test_agent_invocation_error_is_audited() -> None:
    tracker = _OrderTracker()

    async def _boom(session_id: str, prompt: str):
        raise RuntimeError("agent crashed")

    runner = _build_runner(tracker, agent_caller=_boom)
    result = asyncio.run(runner.run_once())

    assert result["outcome"] == TICK_ERROR
    assert result["reason"] == "agent crashed"
    assert tracker.audits[-1]["kind"] == "breach"
    assert tracker.audits[-1]["outcome"] == "error"


def test_expired_mandate_never_reaches_invoke_even_if_reconcile_safe() -> None:
    # Regression guard for the §7.5 #7 invariant: expiry precedes reconcile.
    tracker = _OrderTracker()
    runner = _build_runner(
        tracker,
        load_mandate_fn=lambda broker: _make_mandate(expires_at=_past_expiry()),
        reconcile_fn=lambda *a: _SafeReport(),
    )
    result = asyncio.run(runner.run_once())
    assert result["outcome"] == TICK_EXPIRED
    # load_mandate_fn is overridden with a lambda that does not record the
    # "mandate" marker, so calls reflect: halt check -> (lambda load) -> expiry
    # -> audit. The invariant under test is that reconcile/invoke never run.
    assert tracker.calls == ["halt", "audit"]
    assert "reconcile" not in tracker.calls
    assert "invoke" not in tracker.calls


# --------------------------------------------------------------------------- #
# run_loop (resume-via-recompute) tests
# --------------------------------------------------------------------------- #


class _FakeJob:
    def __init__(self, job_id: str) -> None:
        self.id = job_id
        self.next_run_at = 0
        self.schedule = None


class _FakeScheduler:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.jobs: list[Any] = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def add_job(self, job) -> None:
        self.jobs.append(job)

    def remove_job(self, job_id: str) -> None:
        self.jobs = [j for j in self.jobs if j.id != job_id]


def test_run_loop_recomputes_and_starts() -> None:
    tracker = _OrderTracker()
    sched = _FakeScheduler()
    runner = _build_runner(tracker, scheduler=sched)
    runner.run_loop(jobs=[_FakeJob("watch-1")])

    assert sched.started is True
    assert [j.id for j in sched.jobs] == ["watch-1"]


def test_run_loop_refuses_without_mandate() -> None:
    tracker = _OrderTracker()
    sched = _FakeScheduler()
    runner = _build_runner(tracker, scheduler=sched, load_mandate_fn=lambda b: None)
    runner.run_loop(jobs=[_FakeJob("watch-1")])

    assert sched.started is False
    assert sched.jobs == []


def test_run_loop_refuses_when_expired_and_trips() -> None:
    tracker = _OrderTracker()
    sched = _FakeScheduler()
    runner = _build_runner(
        tracker,
        scheduler=sched,
        load_mandate_fn=lambda b: _make_mandate(expires_at=_past_expiry()),
    )
    runner.run_loop()

    assert sched.started is False
    assert tracker.tripped  # proactive stop tripped on a dead mandate at boot


def test_run_loop_requires_scheduler() -> None:
    tracker = _OrderTracker()
    runner = _build_runner(tracker)  # no scheduler injected
    with pytest.raises(RuntimeError):
        runner.run_loop()


def test_run_loop_synthesizes_jobs_from_triggers() -> None:
    # No explicit jobs, no durable store entries -> the runner must recompute its
    # watch cadence from the injected triggers (R3) so it actually wakes, instead
    # of starting an empty scheduler that never fires (the C3 integration gap).
    from src.live.runtime.triggers import Trigger

    tracker = _OrderTracker()
    sched = _FakeScheduler()

    class _EmptyStore:
        def load(self):
            return []

        def save(self, jobs):
            self.saved = list(jobs)

    store = _EmptyStore()
    runner = _build_runner(
        tracker,
        scheduler=sched,
        triggers=[Trigger.market("us_equity"), Trigger.interval(30_000)],
        job_store=store,
    )
    runner.run_loop()  # no explicit jobs

    assert sched.started is True
    assert len(sched.jobs) == 2  # market watch-job + interval job
    assert all(j.schedule.startswith("interval:") for j in sched.jobs)
    assert getattr(store, "saved", None) is not None  # synthesized jobs persisted


def test_market_watch_cadence_is_operator_configurable() -> None:
    # The MARKET watch cadence is no longer a hardcoded constant — it is an
    # injectable operational knob (default 60s). A custom value flows into the
    # synthesized job's interval schedule.
    from src.live.runtime.triggers import Trigger

    tracker = _OrderTracker()
    sched = _FakeScheduler()

    class _EmptyStore:
        def load(self):
            return []

        def save(self, jobs):
            pass

    runner = _build_runner(
        tracker,
        scheduler=sched,
        triggers=[Trigger.market("us_equity")],
        job_store=_EmptyStore(),
        market_watch_ms=15_000,
    )
    runner.run_loop()

    assert [j.schedule for j in sched.jobs] == ["interval:15000"]


def test_market_watch_cadence_defaults_when_nonpositive() -> None:
    from src.live.runtime.triggers import Trigger

    tracker = _OrderTracker()
    sched = _FakeScheduler()

    class _EmptyStore:
        def load(self):
            return []

        def save(self, jobs):
            pass

    runner = _build_runner(
        tracker,
        scheduler=sched,
        triggers=[Trigger.market("us_equity")],
        job_store=_EmptyStore(),
        market_watch_ms=0,  # invalid → falls back to the 60s default
    )
    runner.run_loop()

    assert [j.schedule for j in sched.jobs] == ["interval:60000"]


def test_run_loop_resumes_persisted_jobs_over_triggers() -> None:
    # A restart with durable jobs must resume THEM (resume-via-recompute), not
    # re-synthesize from triggers.
    from src.live.runtime.scheduler import Job
    from src.live.runtime.triggers import Trigger

    tracker = _OrderTracker()
    sched = _FakeScheduler()
    persisted = [Job(id="resumed-1", next_run_at=1, schedule="interval:5000")]

    class _Store:
        def load(self):
            return persisted

        def save(self, jobs):  # pragma: no cover - must not be called on resume
            raise AssertionError("save must not run when durable jobs exist")

    runner = _build_runner(
        tracker, scheduler=sched, triggers=[Trigger.market("us_equity")], job_store=_Store()
    )
    runner.run_loop()

    assert [j.id for j in sched.jobs] == ["resumed-1"]


def test_stop_loop_idempotent() -> None:
    tracker = _OrderTracker()
    sched = _FakeScheduler()
    runner = _build_runner(tracker, scheduler=sched)
    runner.stop_loop()
    assert sched.stopped is True
    # No scheduler => no-op, no raise.
    _build_runner(tracker).stop_loop()


# --------------------------------------------------------------------------- #
# Real audit-ledger integration (one path, isolated home)
# --------------------------------------------------------------------------- #


def test_real_audit_write_on_halt(monkeypatch, tmp_path) -> None:
    # Isolate the runtime root so the real ledger lands under tmp.
    monkeypatch.setattr("src.config.paths.Path.home", lambda: tmp_path)
    from src.live.audit import audit_ledger_path, write_live_action
    from src.live.halt import halt_flag_set, trip_halt

    tracker = _OrderTracker()
    runner = LiveRunner(
        BROKER,
        agent_caller=tracker.agent_caller,
        reconcile_fn=tracker.reconcile,
        read_positions=_read_stub,
        read_balance=_read_stub,
        read_open_orders=_read_stub,
        clock=lambda: _FIXED_NOW,
        load_mandate_fn=tracker.load_mandate,
        write_audit_fn=write_live_action,
        halt_flag_fn=lambda broker: True,
        trip_halt_fn=trip_halt,
        session_id="live-test",
    )
    result = asyncio.run(runner.run_once())
    assert result["outcome"] == TICK_HALTED
    assert result["audit_id"] is not None
    ledger = audit_ledger_path()
    assert ledger.exists()
    assert "halt_tripped" in ledger.read_text(encoding="utf-8")
