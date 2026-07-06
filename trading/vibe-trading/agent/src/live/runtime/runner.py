"""Persistent live-trading runner loop (SPEC.md §7.5 components 2 + 7).

The runner is the persistent process that turns the interactive consent channel
into an *autonomous* one: it wakes on a schedule / market trigger, decides and
trades inside the committed mandate, sleeps, and survives restarts. This module
implements two of the eight §7.5 components:

* **Component 2 — Runner loop.** Per tick, in a fixed fail-closed order:
  ``halt → proactive expiry → reconciliation → autonomous turn → audit``. The
  mandate is **pinned inline** into the turn prompt this runner constructs so it
  survives ``loop.py`` 5-layer compaction — done in the runner-owned prompt
  string, never by editing the protected ``src/agent/context.py``.
* **Component 7 — Proactive expiry.** ``ConsentMeta.expires_at`` is checked every
  tick (not only at order time): an expired mandate trips a stop and clears
  authority *before* any agent invocation, so a dead mandate never reaches the
  order path.

Trust + safety invariants honored here:

* **Caller-only agent invocation.** The agent is reached solely through the
  existing public entry (an injected async caller bound to
  ``SessionService.send_message`` by default). This module never imports or edits
  ``src/agent/`` or ``src/session/`` internals — it is a *caller*.
* **No-retry on mutating calls (§8 finding 5).** When reconciliation surfaces an
  unsafe / ambiguous broker state (e.g. a mid-order crash where a fill may have
  landed before the audit write), the tick **aborts** — it never auto-resends.
  Reconciliation, not re-send, closes the cross-restart double-trade hole.
* **Resume-via-recompute.** :meth:`LiveRunner.run_loop` reloads the mandate and
  recomputes the schedule on (re)start; there is no mid-task checkpoint.

Every external dependency — scheduler, triggers, reconcile, the agent caller and
the clock — is injectable, so the runner is unit-testable with no live agent or
broker. See the live-trading SPEC §7.5.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping, Protocol

from src.live.audit import LiveActionEvent, write_live_action
from src.live.halt import halt_flag_set, trip_halt
from src.live.mandate.model import Mandate
from src.live.mandate.store import load_mandate
from src.live.runtime.flatten import flatten_and_cancel
from src.live.runtime.jobstore import JobStore
from src.live.runtime.liveness import write_heartbeat
from src.live.runtime.scheduler import Job, Scheduler
from src.live.runtime.triggers import Trigger, due_now

logger = logging.getLogger(__name__)

#: Tick outcome codes (the ``outcome`` key of :meth:`LiveRunner.run_once`).
TICK_HALTED = "halted"
TICK_NO_MANDATE = "no_mandate"
TICK_EXPIRED = "expired"
TICK_RECONCILE_UNSAFE = "reconcile_unsafe"
TICK_RECONCILE_ERROR = "reconcile_error"
TICK_INVOKED = "invoked"
TICK_ERROR = "error"

#: Stop-source attribution recorded on the HALT sentinel when the runner trips it.
_RUNNER_TRIP_SOURCE = "file"

#: Default watch cadence (ms) for a MARKET trigger — the runner wakes on this
#: interval and the tick itself re-checks market state + mandate. 60s keeps the
#: runner responsive without hammering the broker. Operator-configurable per
#: runner via ``LiveRunner(market_watch_ms=...)``; it is an operational polling
#: knob, NOT a user-authorized safety limit, so it lives on the runner (not the
#: mandate, which carries only trading limits).
_DEFAULT_MARKET_WATCH_MS = 60_000

# ---- Injected dependency contracts (duck-typed; coded blind against R1/R3/R4) -


class _Job(Protocol):
    """Minimal :class:`src.live.runtime.scheduler.Job` view the runner relies on."""

    id: str
    next_run_at: int
    schedule: Any


class _Scheduler(Protocol):
    """Minimal :class:`src.live.runtime.scheduler.Scheduler` view (R1 contract)."""

    def start(self) -> Any: ...

    def stop(self) -> Any: ...

    def add_job(self, job: _Job) -> Any: ...

    def remove_job(self, job_id: str) -> Any: ...


#: Async agent caller: ``(session_id, prompt) -> result dict``. Bound by default
#: to the public ``SessionService.send_message`` entry (never the loop internals).
AgentCaller = Callable[[str, str], Awaitable[Mapping[str, Any]]]

#: Reconcile callable matching R4: ``reconcile(broker, read_positions,
#: read_balance, read_open_orders) -> ReconcileReport``.
ReconcileFn = Callable[..., Any]

#: Broker READ callables injected into reconciliation (no write surface).
ReadCallable = Callable[[], Any]

#: Broker WRITE callable (place/cancel) injected for the preemptive halt sweep.
#: Receives a normalized order/cancel dict, returns the broker's raw response.
SubmitCallable = Callable[[dict[str, Any]], Mapping[str, Any]]

#: Preemptive flatten action signature (mirrors
#: :func:`src.live.runtime.flatten.flatten_and_cancel`). Injectable so a test can
#: assert it fires exactly once on a halt trip without a real broker.
FlattenFn = Callable[..., Mapping[str, Any]]

#: Heartbeat writer signature (mirrors
#: :func:`src.live.runtime.liveness.write_heartbeat`). Injectable so a test can
#: observe the per-tick liveness write without touching the filesystem.
HeartbeatFn = Callable[..., int]

#: Clock returning a timezone-aware UTC ``datetime`` (injected for determinism).
ClockFn = Callable[[], datetime]


def _default_clock() -> datetime:
    """Return the current time as a timezone-aware UTC ``datetime``."""
    return datetime.now(timezone.utc)


def _report_is_unsafe(report: Any) -> bool:
    """Return whether a reconcile report flags an unsafe / ambiguous state.

    R4 owns :class:`~src.live.runtime.reconcile.ReconcileReport`; its concrete
    field name is not frozen in this parcel's contract, so this reads the report
    defensively across the plausible shapes and **fail-closes** (treats an
    unrecognized report as unsafe) so an ambiguous broker state can never slip
    into the trading path.

    Args:
        report: The object returned by the injected reconcile callable.

    Returns:
        ``True`` if the report is unsafe / ambiguous (abort the tick).
    """
    if report is None:
        return True
    # Positive-safety attributes: present + truthy means safe.
    for safe_attr in ("safe_to_trade", "is_safe", "safe", "ok", "clean"):
        if hasattr(report, safe_attr):
            return not bool(getattr(report, safe_attr))
    # Negative attributes: present + truthy means unsafe.
    for unsafe_attr in ("unsafe", "ambiguous", "has_discrepancies", "discrepancies"):
        if hasattr(report, unsafe_attr):
            return bool(getattr(report, unsafe_attr))
    # An unrecognized report shape cannot be proven safe.
    return True


def _parse_expiry(raw: str) -> datetime | None:
    """Parse an ISO-8601 UTC ``expires_at`` string into an aware ``datetime``.

    The mandate commit path writes the expiry with a trailing ``Z`` (e.g.
    ``2026-06-28T00:00:00Z``); :func:`datetime.fromisoformat` does not accept
    ``Z`` before Python 3.11, so it is normalized to ``+00:00`` first. A naive
    result is assumed UTC. Returns ``None`` when the value cannot be parsed so
    the caller can fail-closed.

    Args:
        raw: The ``ConsentMeta.expires_at`` value.

    Returns:
        A timezone-aware UTC ``datetime``, or ``None`` if unparseable.
    """
    if not isinstance(raw, str) or not raw.strip():
        return None
    normalized = raw.strip()
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _mandate_is_expired(mandate: Mandate, now: datetime) -> bool:
    """Return whether ``mandate`` is at/past its expiry as of ``now`` (fail-closed).

    An unparseable ``expires_at`` is treated as expired: a live mandate with a
    malformed expiry must not keep trading (mirrors
    ``order_guard._is_expired``).

    Args:
        mandate: The loaded mandate.
        now: The injected current UTC time.

    Returns:
        ``True`` if the mandate is dead.
    """
    expires = _parse_expiry(mandate.consent.expires_at)
    if expires is None:
        return True
    return now >= expires


def _pin_mandate_prompt(broker: str, mandate: Mandate, now: datetime) -> str:
    """Build the autonomous-turn prompt with the full mandate pinned inline.

    The mandate text is embedded directly in the prompt this runner owns so it
    survives ``loop.py`` context compaction — the protected ``context.py`` is
    NOT touched. The prompt states the bounded-autonomy contract explicitly: the
    agent trades freely *inside* these limits and must defer (never breach) on
    any action that would exceed them; the enforcement gate is the hard backstop.

    Args:
        broker: Broker key the runner drives.
        mandate: The active, unexpired mandate.
        now: The injected current UTC time (stamped into the prompt for the LLM).

    Returns:
        The full autonomous-turn user prompt.
    """
    caps = mandate.hard_caps
    universe = mandate.universe
    instruments = ", ".join(i.value for i in caps.allowed_instruments) or "(none)"
    asset_classes = ", ".join(a.value for a in universe.asset_classes) or "(none)"
    excluded = ", ".join(universe.exclude_symbols) or "(none)"
    return (
        "You are running an AUTONOMOUS live-trading tick under a bounded "
        "mandate. Trade freely INSIDE the limits below; you must NEVER place an "
        "order that would breach any limit — defer instead. The enforcement "
        "gate and kill switch are hard backstops outside your control.\n\n"
        f"Broker: {broker}\n"
        f"Tick time (UTC): {now.isoformat(timespec='seconds')}\n"
        f"Mandate expires (UTC): {mandate.consent.expires_at}\n\n"
        "=== HARD CAPS (vibe-enforced; broker funding is the absolute ceiling) ===\n"
        f"- Account funding (USD): {caps.account_funding_usd}\n"
        f"- Max single-order notional (USD): {caps.max_order_notional_usd}\n"
        f"- Max total exposure (USD): {caps.max_total_exposure_usd}\n"
        f"- Max gross leverage: {caps.max_leverage}\n"
        f"- Allowed instruments: {instruments}\n"
        f"- Max trades per UTC day: {caps.max_trades_per_day}\n\n"
        "=== DISCOVERY UNIVERSE (pick symbols within these structural filters) ===\n"
        f"- Asset classes: {asset_classes}\n"
        f"- Min market cap (USD): {universe.min_market_cap_usd}\n"
        f"- Min avg daily volume (USD): {universe.min_avg_daily_volume_usd}\n"
        f"- Excluded symbols (hard denylist): {excluded}\n\n"
        "Assess the current opportunity set, then act within the mandate. If no "
        "action is warranted this tick, hold and explain why."
    )


@dataclass(frozen=True)
class TickResult:
    """Immutable outcome of one :meth:`LiveRunner.run_once` tick.

    Attributes:
        outcome: One of the ``TICK_*`` codes.
        broker: Broker the tick ran for.
        reason: Human-readable detail (empty when not applicable).
        agent_result: The raw result dict from the agent caller when the tick
            reached the invocation step, else ``None``.
        audit_id: The audit record id written for this tick, when one was
            written, else ``None``.
    """

    outcome: str
    broker: str
    reason: str = ""
    agent_result: Mapping[str, Any] | None = None
    audit_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a plain JSON-serializable view of this tick result."""
        return {
            "outcome": self.outcome,
            "broker": self.broker,
            "reason": self.reason,
            "agent_result": dict(self.agent_result) if self.agent_result else None,
            "audit_id": self.audit_id,
        }


class LiveRunner:
    """Persistent autonomous runner for one live broker channel (§7.5 #2, #7).

    The runner owns the per-tick ordering and the scheduling loop. Every external
    dependency is injected, so the class is fully unit-testable without a live
    agent or broker.

    Attributes:
        broker: Broker key this runner drives (e.g. ``"robinhood"``).
    """

    def __init__(
        self,
        broker: str,
        *,
        agent_caller: AgentCaller,
        reconcile_fn: ReconcileFn,
        read_positions: ReadCallable,
        read_balance: ReadCallable,
        read_open_orders: ReadCallable,
        scheduler: _Scheduler | None = None,
        clock: ClockFn = _default_clock,
        load_mandate_fn: Callable[[str], Mandate | None] = load_mandate,
        write_audit_fn: Callable[[LiveActionEvent], Mapping[str, Any]] = write_live_action,
        halt_flag_fn: Callable[[str | None], bool] = halt_flag_set,
        trip_halt_fn: Callable[..., Any] = trip_halt,
        report_unsafe_fn: Callable[[Any], bool] = _report_is_unsafe,
        submit_fn: SubmitCallable | None = None,
        flatten_fn: FlattenFn = flatten_and_cancel,
        heartbeat_fn: HeartbeatFn = write_heartbeat,
        job_store: JobStore | None = None,
        triggers: list[Trigger] | None = None,
        market_watch_ms: int = _DEFAULT_MARKET_WATCH_MS,
        session_id: str = "",
    ) -> None:
        """Initialize the runner.

        Args:
            broker: Broker key this runner drives.
            agent_caller: Async ``(session_id, prompt) -> result`` caller bound to
                the public ``SessionService`` entry. The runner never touches the
                agent loop internals.
            reconcile_fn: R4 ``reconcile(broker, read_positions, read_balance,
                read_open_orders) -> ReconcileReport``.
            read_positions: Broker READ callable for current positions.
            read_balance: Broker READ callable for the account balance.
            read_open_orders: Broker READ callable for resting open orders.
            scheduler: R1 scheduler used by :meth:`run_loop`. May be ``None`` when
                only :meth:`run_once` is exercised.
            clock: Injectable UTC clock for deterministic expiry tests.
            load_mandate_fn: Injectable mandate loader (defaults to the protected
                read-only store loader).
            write_audit_fn: Injectable audit writer.
            halt_flag_fn: Injectable halt check.
            trip_halt_fn: Injectable halt tripper (used on proactive expiry).
            report_unsafe_fn: Predicate deciding whether a reconcile report is
                unsafe/ambiguous (defaults to the defensive duck-typed check).
            submit_fn: Broker WRITE callable (place/cancel) used ONLY by the
                preemptive halt sweep. ``None`` (default) means no write surface
                is wired, so a halt trip cancels/flattens nothing it cannot reach
                — the cooperative gate still blocks future orders. The real
                factory binds the broker's ``place_order`` / ``cancel_order``
                tools here.
            flatten_fn: Preemptive sweep action (defaults to
                :func:`src.live.runtime.flatten.flatten_and_cancel`). Injectable
                so a test can assert it fires exactly once on a trip.
            heartbeat_fn: Liveness writer (defaults to
                :func:`src.live.runtime.liveness.write_heartbeat`). Called every
                tick and every loop iteration, keyed by :attr:`runner_id`.
            job_store: Durable job store (R1) loaded on :meth:`run_loop` start for
                resume-via-recompute. ``None`` (default) constructs the default
                store lazily inside :meth:`run_loop`.
            triggers: Watch triggers (R3) the runner schedules ticks from when no
                explicit ``jobs`` are passed to :meth:`run_loop`. ``None`` means
                no trigger-derived jobs (a caller may pass jobs directly).
            market_watch_ms: Polling cadence (ms) a MARKET trigger wakes the
                runner on; the tick re-checks market state + mandate each wake.
                An operational knob (default 60s), NOT a safety limit — non-positive
                values fall back to the default.
            session_id: Session id passed to the agent caller + audit records.
        """
        self.broker = broker
        self._agent_caller = agent_caller
        self._reconcile_fn = reconcile_fn
        self._read_positions = read_positions
        self._read_balance = read_balance
        self._read_open_orders = read_open_orders
        self._scheduler = scheduler
        self._clock = clock
        self._load_mandate = load_mandate_fn
        self._write_audit = write_audit_fn
        self._halt_flag = halt_flag_fn
        self._trip_halt = trip_halt_fn
        self._report_unsafe = report_unsafe_fn
        self._submit_fn = submit_fn
        self._flatten_fn = flatten_fn
        self._heartbeat = heartbeat_fn
        self._job_store = job_store
        self._triggers = list(triggers or [])
        self._market_watch_ms = market_watch_ms if market_watch_ms > 0 else _DEFAULT_MARKET_WATCH_MS
        self._session_id = session_id or f"live-{broker}"
        #: Set once the preemptive sweep has fired so a tripped channel never
        #: flattens twice across consecutive ticks (no-retry, SPEC §8.5).
        self._flatten_fired = False

    @property
    def runner_id(self) -> str:
        """Return the liveness / heartbeat key for this runner.

        Aligned with the API server's ``_runner_liveness_state`` and the CLI
        ``live status`` path, both of which read liveness keyed by the bare
        broker key. Keeping the heartbeat key identical is what makes a running
        runner show as *alive* rather than perpetually dead.

        Returns:
            The broker key (the runner id the status path expects).
        """
        return self.broker

    async def run_once(self) -> dict[str, Any]:
        """Run ONE fail-closed tick in fixed order; return the outcome dict.

        Ordering (each step short-circuits the tick on failure):

        1. **Halt** — if the kill switch is tripped, abort, audit, return.
        2. **Mandate + proactive expiry** — load the mandate; if absent or past
           ``expires_at``, trip a stop + clear authority + audit, and return
           BEFORE any agent invocation. A dead mandate never reaches step 5.
        3. **Reconcile** — pull broker truth via the injected READ callables; an
           unsafe/ambiguous report aborts the tick (no auto-resend, §8 finding 5).
        4. **Pin + invoke** — build the autonomous-turn prompt with the full
           mandate inline and invoke the agent through the public caller.
        5. **Audit** — record the tick outcome.

        Returns:
            A JSON-serializable tick result (see :meth:`TickResult.to_dict`).
        """
        now = self._clock()
        self._write_heartbeat(now)

        if self._halt_flag(self.broker):
            return self._halted_result()

        mandate = self._load_mandate(self.broker)
        if mandate is None:
            return self._no_mandate_result()
        if _mandate_is_expired(mandate, now):
            return self._expired_result()

        reconcile_outcome = self._run_reconcile()
        if reconcile_outcome is not None:
            return reconcile_outcome

        return await self._invoke_and_audit(mandate, now)

    def _run_reconcile(self) -> dict[str, Any] | None:
        """Reconcile broker truth before trading; abort on unsafe/error.

        Returns:
            A tick result dict when the tick must abort (unsafe state or a
            reconcile failure — fail-closed), or ``None`` when it is safe to
            proceed to the agent invocation.
        """
        try:
            report = self._reconcile_fn(
                self.broker,
                self._read_positions,
                self._read_balance,
                self._read_open_orders,
            )
        except Exception as exc:  # Reconcile failure is fail-closed: do not trade.
            logger.warning("live reconcile failed for %s: %s", self.broker, exc)
            audit_id = self._audit(
                kind="breach",
                outcome="blocked",
                intent="reconcile failed — tick aborted (fail-closed)",
                error=str(exc),
            )
            return TickResult(
                outcome=TICK_RECONCILE_ERROR,
                broker=self.broker,
                reason="reconcile raised; tick aborted",
                audit_id=audit_id,
            ).to_dict()

        if self._report_unsafe(report):
            logger.warning("live reconcile unsafe for %s — aborting tick", self.broker)
            audit_id = self._audit(
                kind="breach",
                outcome="blocked",
                intent="reconcile flagged unsafe/ambiguous — no auto-resend",
            )
            return TickResult(
                outcome=TICK_RECONCILE_UNSAFE,
                broker=self.broker,
                reason="reconcile flagged unsafe/ambiguous broker state",
                audit_id=audit_id,
            ).to_dict()
        return None

    async def _invoke_and_audit(self, mandate: Mandate, now: datetime) -> dict[str, Any]:
        """Invoke the agent with the pinned mandate, then audit the outcome.

        Args:
            mandate: The active, unexpired mandate to pin inline.
            now: The injected tick time.

        Returns:
            The tick result dict.
        """
        prompt = _pin_mandate_prompt(self.broker, mandate, now)
        try:
            result = await self._agent_caller(self._session_id, prompt)
        except Exception as exc:
            logger.exception("live agent invocation failed for %s", self.broker)
            audit_id = self._audit(
                kind="breach",
                outcome="error",
                intent="autonomous tick — agent invocation error",
                error=str(exc),
            )
            return TickResult(
                outcome=TICK_ERROR,
                broker=self.broker,
                reason=str(exc),
                audit_id=audit_id,
            ).to_dict()

        audit_id = self._audit(
            kind="order_placed",
            outcome="accepted",
            intent="autonomous tick completed",
        )
        return TickResult(
            outcome=TICK_INVOKED,
            broker=self.broker,
            agent_result=result,
            audit_id=audit_id,
        ).to_dict()

    def _write_heartbeat(self, now: datetime) -> None:
        """Record a liveness heartbeat for this tick (best-effort).

        A failed heartbeat write must never abort a tick (the trading decision is
        far more important than the liveness signal), so the error is logged and
        swallowed — a missed heartbeat only makes the runner *look* stale, which
        the reaper handles safely.

        Args:
            now: The tick's UTC time, converted to epoch ms for the heartbeat.
        """
        try:
            self._heartbeat(self.runner_id, now_ms=int(now.timestamp() * 1000))
        except Exception:  # noqa: BLE001 — liveness must not break trading
            logger.warning("failed to write heartbeat for %s", self.runner_id, exc_info=True)

    def _halted_result(self) -> dict[str, Any]:
        """Fire the preemptive sweep ONCE, audit, and return for a halted tick.

        This closes Hole #1 (SPEC §7.5 #6): a tripped halt is no longer merely
        cooperative (refuse the next order). The runner cancels every resting
        order and — per the mandate's flatten flag — flattens open positions, via
        the injected broker submit callable. The sweep runs at most once per
        runner lifetime (``_flatten_fired`` latch): a halted channel that keeps
        ticking must not re-submit closes (no-retry, SPEC §8.5). With no broker
        write surface wired (``submit_fn is None``) the sweep is skipped and the
        cooperative gate alone blocks future orders.
        """
        self._run_preemptive_sweep()
        audit_id = self._audit(
            kind="halt_tripped",
            outcome="blocked",
            intent="tick aborted — kill switch tripped",
        )
        return TickResult(
            outcome=TICK_HALTED,
            broker=self.broker,
            reason="kill switch tripped",
            audit_id=audit_id,
        ).to_dict()

    def _run_preemptive_sweep(self) -> None:
        """Cancel resting orders + (per mandate) flatten positions, exactly once.

        Invoked the moment the runner observes a tripped HALT. Idempotent across
        ticks via the ``_flatten_fired`` latch so the no-retry rule (SPEC §8.5)
        holds even if the halted runner keeps waking. A sweep failure is audited
        but not retried — flatten/cancel side effects are not idempotent.
        """
        if self._flatten_fired or self._submit_fn is None:
            return
        self._flatten_fired = True
        try:
            self._flatten_fn(
                self.broker,
                self._submit_fn,
                self._read_positions,
                self._read_open_orders,
            )
        except Exception as exc:  # noqa: BLE001 — surfaced via audit, never retried
            logger.exception("preemptive flatten failed for %s", self.broker)
            self._audit(
                kind="breach",
                outcome="error",
                intent="preemptive halt sweep failed — not retried (no-retry §8.5)",
                error=str(exc),
            )

    def _no_mandate_result(self) -> dict[str, Any]:
        """Audit + return the result when no valid mandate is on file."""
        audit_id = self._audit(
            kind="order_rejected",
            outcome="blocked",
            intent="tick aborted — no valid mandate on file",
        )
        return TickResult(
            outcome=TICK_NO_MANDATE,
            broker=self.broker,
            reason="no valid mandate",
            audit_id=audit_id,
        ).to_dict()

    def _expired_result(self) -> dict[str, Any]:
        """Trip a stop, clear authority, audit, and return on proactive expiry.

        This is the §7.5 component-7 proactive path: expiry is acted on in the
        tick, not deferred to the next order attempt, so a dead mandate never
        reaches the agent invocation. The kill switch is tripped (per-broker) so
        all in-flight live authority for this channel is cut immediately.
        """
        try:
            self._trip_halt(
                _RUNNER_TRIP_SOURCE,
                "mandate expired — proactive runner stop",
                broker=self.broker,
            )
        except Exception:  # A trip failure must not swallow the expiry outcome.
            logger.exception("failed to trip halt on expiry for %s", self.broker)
        audit_id = self._audit(
            kind="halt_tripped",
            outcome="blocked",
            intent="mandate expired — proactive stop, authority revoked",
        )
        return TickResult(
            outcome=TICK_EXPIRED,
            broker=self.broker,
            reason="mandate expired — proactive stop",
            audit_id=audit_id,
        ).to_dict()

    def _audit(
        self,
        *,
        kind: str,
        outcome: str,
        intent: str,
        error: str | None = None,
    ) -> str | None:
        """Write one live-action audit record for a tick outcome.

        Audit failures are swallowed (logged) so a ledger problem can never make
        a *blocking* tick outcome look like it proceeded.

        Args:
            kind: The :class:`~src.live.audit.LiveActionKind`.
            outcome: The :class:`~src.live.audit.LiveActionOutcome`.
            intent: Normalized human-readable intent string.
            error: Optional error description.

        Returns:
            The written record's ``audit_id``, or ``None`` if the write failed.
        """
        event = LiveActionEvent(
            kind=kind,  # type: ignore[arg-type]
            session_id=self._session_id,
            outcome=outcome,  # type: ignore[arg-type]
            server=self.broker,
            intent_normalized=intent,
            error=error,
        )
        try:
            record = self._write_audit(event)
        except Exception:
            logger.exception("failed to write live-action audit for %s", self.broker)
            return None
        return record.get("audit_id") if isinstance(record, Mapping) else event.audit_id

    def run_loop(self, jobs: list[_Job] | None = None) -> None:
        """Start the scheduler and register tick jobs (resume-via-recompute).

        On every (re)start this recomputes from durable inputs — it reloads the
        mandate and registers the watch-cadence jobs — rather than restoring a
        mid-task checkpoint (§7.5: "Resume-via-recompute on restart … not mid-task
        checkpoint"). When the mandate is absent or already expired, the loop is
        NOT started: there is nothing to schedule and a dead mandate must not
        wake the runner.

        The scheduler (R1) and triggers (R3) own the wall-clock firing; this
        method only wires the jobs and starts the scheduler. The scheduler is
        expected to invoke :meth:`run_once` per fired job.

        Args:
            jobs: Watch-cadence jobs to register (R1 :class:`Job` instances). When
                ``None``, the runner recomputes its jobs from durable inputs:
                first any jobs persisted in the durable job store (resume), else
                jobs synthesized from the injected triggers (R3). Only when there
                are neither does the scheduler start empty.

        Raises:
            RuntimeError: If no scheduler was injected.
        """
        if self._scheduler is None:
            raise RuntimeError("run_loop requires an injected scheduler")

        now = self._clock()
        mandate = self._load_mandate(self.broker)
        if mandate is None:
            logger.warning("live runner not starting for %s: no mandate", self.broker)
            return
        if _mandate_is_expired(mandate, now):
            logger.warning("live runner not starting for %s: mandate expired", self.broker)
            self._expired_result()
            return

        resolved_jobs = self._resolve_jobs(jobs, now)
        for job in resolved_jobs:
            self._scheduler.add_job(job)
        self._scheduler.start()
        logger.info(
            "live runner started for %s with %d job(s)", self.broker, len(resolved_jobs)
        )

    def _resolve_jobs(self, jobs: list[_Job] | None, now: datetime) -> list[Job]:
        """Recompute the watch-cadence jobs on (re)start (resume-via-recompute).

        Precedence: an explicit ``jobs`` arg wins (test / caller injection); else
        durable jobs reloaded from the job store (a restart resumes the same
        cadence); else jobs synthesized from the injected triggers (R3) and
        persisted so the next restart resumes them. Never a mid-task checkpoint —
        just the schedule, recomputed from durable inputs.

        Args:
            jobs: Explicit jobs to use, or ``None`` to recompute.
            now: Current UTC time (anchors the first fire of synthesized jobs).

        Returns:
            The list of :class:`Job` to register with the scheduler.
        """
        if jobs is not None:
            return list(jobs)

        store = self._job_store or JobStore()
        try:
            persisted = store.load()
        except Exception:  # noqa: BLE001 — a corrupt store must not wedge start
            logger.exception("job store load failed for %s; recomputing", self.broker)
            persisted = []
        if persisted:
            return persisted

        synthesized = self._jobs_from_triggers(now)
        if synthesized:
            try:
                store.save(synthesized)
            except Exception:  # noqa: BLE001 — persistence is best-effort at start
                logger.exception("job store save failed for %s", self.broker)
        return synthesized

    def _jobs_from_triggers(self, now: datetime) -> list[Job]:
        """Convert the injected triggers (R3) into schedulable watch jobs (R1).

        INTERVAL triggers map to an ``interval:<ms>`` job on their own cadence;
        MARKET triggers map to a default watch-cadence interval job (the tick
        itself re-checks market state + mandate); EVENT triggers are skipped here
        because they fire from an out-of-band event source, not the wall clock.

        Args:
            now: Current UTC time, used to anchor the first fire.

        Returns:
            One :class:`Job` per schedulable trigger.
        """
        now_ms = int(now.timestamp() * 1000)
        built: list[Job] = []
        for index, trigger in enumerate(self._triggers):
            kind = getattr(trigger, "kind", None)
            kind_value = getattr(kind, "value", kind)
            if kind_value == "interval":
                interval_ms = int(trigger.interval_ms)
            elif kind_value == "market":
                interval_ms = self._market_watch_ms
            else:  # event triggers fire out-of-band, not via the wall clock
                logger.info(
                    "skipping non-wall-clock trigger %s for %s", kind_value, self.broker
                )
                continue
            built.append(
                Job(
                    id=f"{self.broker}-{kind_value}-{index}",
                    next_run_at=now_ms + interval_ms,
                    schedule=f"interval:{interval_ms}",
                    payload={"broker": self.broker, "trigger": kind_value},
                )
            )
        return built

    def stop_loop(self) -> None:
        """Stop the scheduler if one was injected (idempotent)."""
        if self._scheduler is not None:
            self._scheduler.stop()
