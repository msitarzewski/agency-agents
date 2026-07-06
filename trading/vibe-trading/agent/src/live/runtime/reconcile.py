"""Crash recovery + position reconciliation (SPEC.md §7.5 component 5).

This is the hardest piece of the persistent runtime and has **no nanobot
analog**. On startup and before every trading tick the runner must answer one
question before it is allowed to trade again: *does broker truth match the
durable last-known state we persisted before the crash?* Trading is not
idempotent, so a naive "resume + re-send" closes one hole (lost work) by opening
a far worse one (double-trade real money).

The dangerous case is a **mid-order crash**: we asked the broker to place an
order, the process died, and we never learned whether it filled. The order may
be open, may have filled, or may never have reached the broker. The no-retry
rule (SPEC §8.5 — ``_call_tool`` deliberately never retries mutating calls and
``LiveOrderGuardTool.repeatable = False``) means we MUST NOT auto-resend such an
order. Reconciliation's job is therefore to *classify and SURFACE* the
ambiguity, never to auto-correct or auto-resend it.

Design contract (frozen — R2's runner imports these blind):

* :func:`reconcile` takes the broker key plus three **injected READ callables**
  (``read_positions`` / ``read_balance`` / ``read_open_orders``). These are the
  broker's read-only MCP tools at runtime and stubs in tests. Reconciliation
  NEVER receives, holds, or calls a broker *write* tool — that is structurally
  how we guarantee it cannot resend an order.
* It diffs broker truth against the durable last-known state at
  ``<runtime_root>/<broker>/runtime_state.json`` (via
  :func:`src.live.paths.broker_dir`).
* Every delta is classified into one of :class:`DeltaKind`:
  ``matched`` / ``unknown_fill`` / ``orphan_order`` / ``mid_order_ambiguous``.
* The returned :class:`ReconcileReport` carries the classified deltas plus an
  overall ``is_safe`` / ``requires_halt`` flag the runner consults. Any
  ``mid_order_ambiguous`` (or ``unknown_fill``) delta flips ``requires_halt``:
  the runner halts and surfaces — it never silently retries.
* After a *clean* reconcile (broker truth fully reconciled, nothing ambiguous)
  the new last-known state is persisted atomically (temp + ``os.replace``).

Idempotency / client-order-id: where a client-order-id is derivable from the
recorded state we carry it on the delta and in
:attr:`ReconcileReport.recorded_client_order_ids` so the runner / broker layer
can dedupe instead of resend. The exact broker field that maps to a
client-order-id is broker-specific; see ``_client_order_id`` for the mapping
TODO that needs the real broker catalog.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.live.mandate.store import load_mandate
from src.live.paths import broker_dir

logger = logging.getLogger(__name__)

#: Filename of the durable last-known runtime state under the broker dir.
_STATE_FILENAME = "runtime_state.json"

#: Schema version of the persisted runtime state document.
RUNTIME_STATE_SCHEMA_VERSION = 1

#: A broker READ callable: takes no args, returns the broker truth payload.
#: ``read_positions`` / ``read_open_orders`` return a sequence of dicts;
#: ``read_balance`` returns a single dict. They are the broker's read-only MCP
#: tools at runtime and fabricated stubs in tests. None of them mutate state.
ReadList = Callable[[], Sequence[Mapping[str, Any]]]
ReadDict = Callable[[], Mapping[str, Any]]


class DeltaKind:
    """Classification labels for a single reconciliation delta.

    Not an :class:`enum.Enum` so callers can compare against bare strings in
    audit records without an import; the set is closed and documented here.

    Attributes:
        MATCHED: Broker truth and our recorded state agree — no action needed.
        UNKNOWN_FILL: The broker shows a fill (a position or a filled order) we
            have no record of. Dangerous: real money moved without our audit
            trail. Forces a halt.
        ORPHAN_ORDER: We recorded a resting/open order the broker does NOT show.
            It was cancelled, rejected, or filled-and-cleared out of band. Not
            auto-resent; surfaced for the runner to investigate.
        MID_ORDER_AMBIGUOUS: We recorded an order as *submitted-but-unconfirmed*
            (placed before the crash, never audited as accepted/filled) and the
            broker neither shows it open nor confirms a matching fill. It may
            have filled before our audit write. The no-retry rule forbids
            resending it; this is surfaced and forces a halt.
    """

    MATCHED = "matched"
    UNKNOWN_FILL = "unknown_fill"
    ORPHAN_ORDER = "orphan_order"
    MID_ORDER_AMBIGUOUS = "mid_order_ambiguous"


#: Delta kinds that mean real money may have moved without a clean audit trail,
#: so the runner MUST halt and surface rather than trade on the next tick.
_HALTING_KINDS = frozenset({DeltaKind.UNKNOWN_FILL, DeltaKind.MID_ORDER_AMBIGUOUS})


@dataclass(frozen=True)
class ReconcileDelta:
    """One classified difference between broker truth and recorded state.

    Attributes:
        kind: One of :class:`DeltaKind`'s labels.
        subject: ``"order"`` or ``"position"`` — which kind of broker fact this
            delta concerns.
        identity: Stable identity of the subject (a broker order id or a symbol)
            used to correlate the two sides of the diff. Never credentials.
        client_order_id: The client-order-id derived from recorded state when
            available, so the runner can dedupe instead of resend. ``None`` when
            not derivable (e.g. an unknown broker-side fill).
        detail: Human-readable explanation of why this delta was raised.
        recorded: The recorded-state view of the subject (redaction-safe; ids
            and quantities only), or ``None`` when we had no record.
        broker: The broker-truth view of the subject, or ``None`` when the
            broker did not report it.
    """

    kind: str
    subject: str
    identity: str
    client_order_id: str | None
    detail: str
    recorded: Mapping[str, Any] | None
    broker: Mapping[str, Any] | None


@dataclass(frozen=True)
class ReconcileReport:
    """Outcome of one reconciliation pass (SPEC §7.5 component 5).

    The runner (R2) consults :attr:`is_safe` / :attr:`requires_halt` BEFORE
    constructing a trading turn. Reconciliation never auto-resends or
    auto-corrects: a ``requires_halt`` report means the runner halts and
    surfaces the deltas, in keeping with the no-retry rule (SPEC §8.5).

    Attributes:
        broker: Broker key this report was produced for.
        ts: ISO-8601 UTC timestamp (ms precision) of the reconcile pass.
        deltas: Every classified difference; empty == fully reconciled.
        recorded_client_order_ids: Client-order-ids we had on file for resting
            orders, surfaced so the broker layer can dedupe rather than resend.
        state_persisted: ``True`` when a clean reconcile persisted fresh
            last-known state; ``False`` when persistence was withheld because
            the pass was not safe (we never overwrite the durable record of an
            unresolved ambiguity).
        had_prior_state: ``False`` on a cold/first start (no prior state file),
            ``True`` when a prior durable state was loaded and diffed.
    """

    broker: str
    ts: str
    deltas: tuple[ReconcileDelta, ...]
    recorded_client_order_ids: tuple[str, ...]
    state_persisted: bool
    had_prior_state: bool

    @property
    def is_safe(self) -> bool:
        """Return ``True`` when no delta requires a halt.

        Safe means the runner may proceed to construct a trading turn. A safe
        report may still carry benign ``matched`` / ``orphan_order`` deltas; it
        only excludes the money-moved-without-audit kinds.
        """
        return not self.requires_halt

    @property
    def requires_halt(self) -> bool:
        """Return ``True`` when any delta means the runner must halt + surface.

        Trips on ``unknown_fill`` or ``mid_order_ambiguous`` — the cases where
        real money may have moved without a clean audit trail. The no-retry rule
        forbids resolving these by resending; they must be surfaced to a human.
        """
        return any(delta.kind in _HALTING_KINDS for delta in self.deltas)


def _utc_now_iso_ms() -> str:
    """Return the current UTC time as an ISO-8601 string with ms precision."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _client_order_id(recorded_order: Mapping[str, Any]) -> str | None:
    """Derive a client-order-id from a recorded order for dedupe.

    A client-order-id is the idempotency key the broker echoes back so a caller
    can recognize its own prior submission instead of resending. We store it on
    the order when we place it; here we read it back.

    TODO(broker-catalog): the canonical field name is broker-specific. Robinhood
    Agentic MCP's order schema is not yet frozen (SPEC §9 "still open"), so we
    look up the well-known aliases below. When the real catalog lands, pin the
    exact field for each broker in a per-broker map rather than this alias scan.

    Args:
        recorded_order: One recorded order dict from the durable state.

    Returns:
        The client-order-id string, or ``None`` when none is recorded.
    """
    for key in ("client_order_id", "client_oid", "clientOrderId", "clord_id"):
        value = recorded_order.get(key)
        if value:
            return str(value)
    return None


def _order_identity(order: Mapping[str, Any]) -> str | None:
    """Return the broker-side identity used to correlate an order across sides.

    Prefers the broker order id; falls back to the client-order-id so a
    submitted-but-unconfirmed order (which has no broker id yet) still has a
    stable identity for diffing.

    Args:
        order: An order dict from either broker truth or recorded state.

    Returns:
        A stable identity string, or ``None`` when the order carries neither id.
    """
    for key in ("order_id", "id", "broker_order_id"):
        value = order.get(key)
        if value:
            return str(value)
    return _client_order_id(order)


def _is_confirmed(recorded_order: Mapping[str, Any]) -> bool:
    """Return whether a recorded order was durably confirmed before any crash.

    A recorded order is "confirmed" once we audited the broker's acceptance and
    learned its broker order id. An unconfirmed order is one we submitted but
    whose fate we never persisted — the mid-order-crash candidate.

    Args:
        recorded_order: One recorded order dict from the durable state.

    Returns:
        ``True`` when the order has a broker order id AND a non-pending status.
    """
    has_broker_id = any(recorded_order.get(k) for k in ("order_id", "id", "broker_order_id"))
    status = str(recorded_order.get("status", "")).lower()
    return has_broker_id and status not in ("", "pending", "submitted", "unconfirmed")


def _position_symbol(position: Mapping[str, Any]) -> str | None:
    """Return the symbol of a position dict, or ``None`` if absent/flat."""
    symbol = position.get("symbol") or position.get("ticker")
    return str(symbol) if symbol else None


def _position_qty(position: Mapping[str, Any]) -> float:
    """Return the signed quantity of a position dict (0.0 when absent)."""
    for key in ("qty", "quantity", "position"):
        if key in position and position[key] is not None:
            try:
                return float(position[key])
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def reconcile(
    broker: str,
    read_positions: ReadList,
    read_balance: ReadDict,
    read_open_orders: ReadList,
) -> ReconcileReport:
    """Reconcile broker truth against the durable last-known state.

    Pulls the broker's positions, balance, and open orders through the injected
    READ callables, diffs them against the state persisted before the last
    shutdown/crash at ``<runtime_root>/<broker>/runtime_state.json``, classifies
    every difference, and returns a :class:`ReconcileReport`. The mandate is
    loaded for provenance/logging context but reconciliation is mandate-shape
    agnostic. On a clean (safe) reconcile the new last-known state is persisted
    atomically; on an unsafe one the durable record of the unresolved ambiguity
    is preserved untouched.

    This function NEVER mutates broker state: it is handed only READ callables
    and has no write path. The no-retry rule (SPEC §8.5) is enforced by design —
    an ambiguous order is classified ``mid_order_ambiguous`` and surfaced via
    :attr:`ReconcileReport.requires_halt`, never resent.

    Args:
        broker: Broker key, e.g. ``"robinhood"``.
        read_positions: Injected READ callable returning current broker
            positions as a sequence of dicts.
        read_balance: Injected READ callable returning the broker balance dict.
        read_open_orders: Injected READ callable returning resting/open orders
            as a sequence of dicts.

    Returns:
        The classified :class:`ReconcileReport`. The runner consults
        :attr:`ReconcileReport.is_safe` / :attr:`~ReconcileReport.requires_halt`
        before deciding whether it may trade this tick.
    """
    # Loaded for provenance context only; reconcile does not depend on its shape.
    mandate = load_mandate(broker)
    if mandate is None:
        logger.info("reconcile(%s): no committed mandate on file (provenance only)", broker)

    prior = _load_state(broker)
    had_prior_state = prior is not None
    recorded_orders = list(prior.get("open_orders", [])) if prior else []
    recorded_positions = list(prior.get("positions", [])) if prior else []

    broker_orders = list(read_open_orders())
    broker_positions = list(read_positions())
    balance = dict(read_balance())  # pulled for the persisted snapshot + caller context

    # On a cold/first start there is no durable baseline to diff against, so
    # broker truth simply BECOMES the baseline and there are zero deltas — a
    # position we never recorded is not an "unknown fill" when we never recorded
    # anything. Diffing only runs once a prior durable state exists.
    deltas: list[ReconcileDelta] = []
    if had_prior_state:
        deltas.extend(_diff_orders(recorded_orders, broker_orders))
        deltas.extend(_diff_positions(recorded_positions, broker_positions))

    recorded_client_order_ids = tuple(
        coid for coid in (_client_order_id(o) for o in recorded_orders) if coid
    )

    report = ReconcileReport(
        broker=broker,
        ts=_utc_now_iso_ms(),
        deltas=tuple(deltas),
        recorded_client_order_ids=recorded_client_order_ids,
        state_persisted=False,
        had_prior_state=had_prior_state,
    )

    # Persist fresh last-known state ONLY on a clean reconcile. We never
    # overwrite the durable record of an unresolved ambiguity — the runner needs
    # the original recorded order to surface it to a human.
    if report.is_safe:
        _persist_state(broker, broker_orders, broker_positions, balance, report.ts)
        report = ReconcileReport(
            broker=report.broker,
            ts=report.ts,
            deltas=report.deltas,
            recorded_client_order_ids=report.recorded_client_order_ids,
            state_persisted=True,
            had_prior_state=report.had_prior_state,
        )
    else:
        logger.warning(
            "reconcile(%s): UNSAFE — %d halting delta(s); state NOT advanced",
            broker,
            sum(1 for d in report.deltas if d.kind in _HALTING_KINDS),
        )

    return report


def _diff_orders(
    recorded_orders: Sequence[Mapping[str, Any]],
    broker_orders: Sequence[Mapping[str, Any]],
) -> list[ReconcileDelta]:
    """Classify the order side of the diff.

    Args:
        recorded_orders: Orders we persisted as open/submitted before shutdown.
        broker_orders: Orders the broker currently reports as open/resting.

    Returns:
        One :class:`ReconcileDelta` per order that is matched, orphaned, or
        mid-order ambiguous. (Unknown broker-side fills surface on the position
        side via :func:`_diff_positions`; a broker order the recorded side lacks
        but is still *open* is benign and not raised.)
    """
    broker_by_id = {
        ident: order
        for order in broker_orders
        if (ident := _order_identity(order)) is not None
    }

    deltas: list[ReconcileDelta] = []
    for recorded in recorded_orders:
        identity = _order_identity(recorded)
        coid = _client_order_id(recorded)
        if identity is not None and identity in broker_by_id:
            deltas.append(
                ReconcileDelta(
                    kind=DeltaKind.MATCHED,
                    subject="order",
                    identity=identity,
                    client_order_id=coid,
                    detail="recorded order still open on broker",
                    recorded=dict(recorded),
                    broker=dict(broker_by_id[identity]),
                )
            )
            continue

        # Recorded order the broker does NOT show open. The split hinges on
        # whether we durably confirmed it before the crash.
        if _is_confirmed(recorded):
            deltas.append(
                ReconcileDelta(
                    kind=DeltaKind.ORPHAN_ORDER,
                    subject="order",
                    identity=identity or (coid or "<unknown>"),
                    client_order_id=coid,
                    detail=(
                        "confirmed order absent from broker open-orders "
                        "(cancelled / rejected / filled-and-cleared); not resent"
                    ),
                    recorded=dict(recorded),
                    broker=None,
                )
            )
        else:
            deltas.append(
                ReconcileDelta(
                    kind=DeltaKind.MID_ORDER_AMBIGUOUS,
                    subject="order",
                    identity=identity or (coid or "<unknown>"),
                    client_order_id=coid,
                    detail=(
                        "submitted-but-unconfirmed order: may have filled before "
                        "the audit write; no-retry rule forbids resend — surfaced "
                        "for halt"
                    ),
                    recorded=dict(recorded),
                    broker=None,
                )
            )
    return deltas


def _diff_positions(
    recorded_positions: Sequence[Mapping[str, Any]],
    broker_positions: Sequence[Mapping[str, Any]],
) -> list[ReconcileDelta]:
    """Classify the position side of the diff.

    A broker position (or quantity) we have no record of is an ``unknown_fill``:
    real money moved without a matching audit record. A recorded position that
    still matches broker truth is ``matched``.

    Args:
        recorded_positions: Positions we persisted before shutdown.
        broker_positions: Positions the broker currently reports.

    Returns:
        One :class:`ReconcileDelta` per symbol where broker truth diverges from
        (or matches) the recorded snapshot.
    """
    recorded_by_symbol = {
        sym: _position_qty(p)
        for p in recorded_positions
        if (sym := _position_symbol(p)) is not None
    }

    deltas: list[ReconcileDelta] = []
    for position in broker_positions:
        symbol = _position_symbol(position)
        if symbol is None:
            continue
        broker_qty = _position_qty(position)
        recorded_qty = recorded_by_symbol.get(symbol)
        if recorded_qty is not None and recorded_qty == broker_qty:
            deltas.append(
                ReconcileDelta(
                    kind=DeltaKind.MATCHED,
                    subject="position",
                    identity=symbol,
                    client_order_id=None,
                    detail="recorded position matches broker truth",
                    recorded={"symbol": symbol, "qty": recorded_qty},
                    broker=dict(position),
                )
            )
        else:
            deltas.append(
                ReconcileDelta(
                    kind=DeltaKind.UNKNOWN_FILL,
                    subject="position",
                    identity=symbol,
                    client_order_id=None,
                    detail=(
                        "broker reports a position/quantity we have no record of "
                        f"(recorded={recorded_qty}, broker={broker_qty}); "
                        "real money moved without a matching audit record"
                    ),
                    recorded=(
                        None
                        if recorded_qty is None
                        else {"symbol": symbol, "qty": recorded_qty}
                    ),
                    broker=dict(position),
                )
            )
    return deltas


def _state_path(broker: str) -> Path:
    """Return the durable runtime-state path for ``broker``."""
    return broker_dir(broker) / _STATE_FILENAME


def _load_state(broker: str) -> dict[str, Any] | None:
    """Load the durable last-known runtime state for ``broker``.

    Loading is fail-open-to-cold-start: a missing file means a first/cold start
    (``None``). A *corrupt* file is NOT silently treated as cold start — that
    would hide a partial write — it is renamed aside and surfaced as a fresh
    start so the diff can never run against a half-truth.

    Args:
        broker: Broker key.

    Returns:
        The decoded state dict, or ``None`` on cold start / unreadable state.
    """
    path = _state_path(broker)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        corrupt = path.with_name(f"{path.name}.corrupt-{int(datetime.now().timestamp())}")
        try:
            os.replace(path, corrupt)
        except OSError:
            pass
        logger.warning(
            "reconcile(%s): runtime_state.json unreadable (%s); renamed to %s, cold start",
            broker,
            exc,
            corrupt.name,
        )
        return None
    if not isinstance(raw, dict):
        logger.warning("reconcile(%s): runtime_state.json is not an object; cold start", broker)
        return None
    return raw


def _persist_state(
    broker: str,
    open_orders: Sequence[Mapping[str, Any]],
    positions: Sequence[Mapping[str, Any]],
    balance: Mapping[str, Any],
    ts: str,
) -> None:
    """Persist the new last-known state atomically (temp + ``os.replace``).

    A same-directory temp file is written then atomically renamed over the
    target, so a SIGKILL mid-write can never leave a truncated state file a later
    reconcile would misread (mirrors the mandate commit + scheduler store
    pattern, SPEC §7.5 component 1).

    Args:
        broker: Broker key.
        open_orders: Broker-truth open orders to record as the new baseline.
        positions: Broker-truth positions to record as the new baseline.
        balance: Broker-truth balance snapshot.
        ts: ISO-8601 UTC timestamp to stamp the state with.
    """
    payload = {
        "schema_version": RUNTIME_STATE_SCHEMA_VERSION,
        "broker": broker,
        "reconciled_at": ts,
        "open_orders": [dict(o) for o in open_orders],
        "positions": [dict(p) for p in positions],
        "balance": dict(balance),
    }
    path = _state_path(broker)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        # Best-effort on platforms without POSIX perms (e.g. Windows).
        pass
    os.replace(tmp, path)
