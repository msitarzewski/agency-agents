"""Preemptive kill-switch action: cancel resting orders, then flatten positions.

SPEC.md §7.5 component 6. The filesystem ``HALT`` sentinel (``src.live.halt``)
is the LLM-independent *trigger*; this module is the *action* the runner executes
once a trip is observed. It upgrades the cooperative order-time halt (which only
refuses the next order) to **preemptive**: on trip the runner

1. cancels every resting/open order, then
2. — only if the active mandate permits flattening — submits closing orders for
   every open position.

Cancel-before-flatten ordering is deliberate: a resting order left live while we
flatten could fill against our closing trade and re-open exposure. Cancelling
first quiesces the book, then the position sweep closes what is actually held.

**Per-mandate flatten flag (SPEC §7.5 #6 "optionally, per mandate").** The frozen
:class:`~src.live.mandate.model.Mandate` has no flatten field today (its
``HardCaps`` carry only ceilings). Until the mandate schema grows one, flattening
defaults to **OFF** (cancel-only) — the safe default, since auto-submitting market
exits is itself a trading action the user may not have authorized. Callers can
opt in explicitly via ``allow_flatten=True``; and if a future mandate schema adds
a truthy ``flatten_on_halt`` attribute, it is honored automatically (read
defensively via ``getattr`` so this module needs no edit when the field lands).
TODO(live-runtime): once ``Mandate``/``HardCaps`` gains a first-class
``flatten_on_halt`` flag, drop the ``getattr`` probe and read it directly.

**No-retry (SPEC §8.5).** Trading is not idempotent. A broker call that errors is
recorded and we move on — it is NEVER retried, exactly like ``mcp._call_tool``.
A failed cancel/flatten must surface as an error in the returned report, not be
silently re-sent (which could double-trade).

Every broker call — each cancel, each flatten submit, and each error — is written
to the live-action audit ledger via :func:`src.live.audit.write_live_action`
BEFORE the report is returned, so the preemptive sweep is fully reconstructable.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from src.live.audit import LiveActionEvent, write_live_action
from src.live.mandate.store import load_mandate

logger = logging.getLogger(__name__)

#: Session id stamped on audit records emitted by the preemptive sweep. The
#: sweep is runner-initiated (not a chat turn), so it has no user session.
_RUNTIME_SESSION_ID = "live-runtime"

#: Broker remote-tool names recorded in the audit ledger for sweep actions.
_CANCEL_TOOL = "cancel_order"
_FLATTEN_TOOL = "place_order"

#: Type aliases for the injected broker callables (stubbed in tests).
SubmitFn = Callable[[dict[str, Any]], dict[str, Any]]
ReadPositionsFn = Callable[[], list[dict[str, Any]]]
ReadOpenOrdersFn = Callable[[], list[dict[str, Any]]]


def flatten_and_cancel(
    broker: str,
    submit: SubmitFn,
    read_positions: ReadPositionsFn,
    read_open_orders: ReadOpenOrdersFn,
    *,
    allow_flatten: bool | None = None,
) -> dict[str, Any]:
    """Cancel all resting orders, then (if permitted) flatten open positions.

    Executed by the runner the moment a halt trip is observed. Cancels run first
    to quiesce the order book; the position sweep runs only when the mandate
    permits flattening (see module docstring for the per-mandate flag policy).
    Every broker call and every error is audited before this returns; no errored
    call is ever retried (SPEC §8.5).

    Args:
        broker: Broker key, e.g. ``"robinhood"``. Used to load the active mandate
            and to stamp audit records.
        submit: Injected broker callable that places one order. Receives a
            normalized order dict; returns the broker's raw response dict. Used
            for both cancel (``{"action": "cancel", "order_id": ...}``) and
            flatten (a closing order) submissions.
        read_positions: Injected broker callable returning the list of open
            position dicts (each with at least ``symbol`` and a signed ``qty``).
        read_open_orders: Injected broker callable returning the list of
            resting/open order dicts (each with at least ``order_id``).
        allow_flatten: Explicit override for whether to flatten positions. When
            ``None`` (default) the decision is taken from the active mandate's
            ``flatten_on_halt`` attribute if present, else ``False`` (cancel-only).

    Returns:
        A structured report dict::

            {
                "broker": "robinhood",
                "cancelled_order_ids": ["o1", ...],   # successfully cancelled
                "flatten_orders_submitted": [          # closing orders accepted
                    {"symbol": "NVDA", "qty": 3, "side": "sell", "response": {...}},
                ],
                "flatten_skipped_reason": "mandate forbids flatten" | None,
                "errors": [                            # one per failed broker call
                    {"phase": "cancel", "order_id": "o2", "error": "..."},
                ],
            }
    """
    report: dict[str, Any] = {
        "broker": broker,
        "cancelled_order_ids": [],
        "flatten_orders_submitted": [],
        "flatten_skipped_reason": None,
        "errors": [],
    }

    _cancel_resting_orders(broker, submit, read_open_orders, report)

    do_flatten = _resolve_allow_flatten(broker, allow_flatten)
    if not do_flatten:
        report["flatten_skipped_reason"] = "mandate forbids flatten (cancel-only)"
        logger.warning(
            "live preemptive sweep (broker=%s): cancel-only, flatten not permitted",
            broker,
        )
        return report

    _flatten_open_positions(broker, submit, read_positions, report)
    return report


def _resolve_allow_flatten(broker: str, allow_flatten: bool | None) -> bool:
    """Decide whether positions may be flattened on this trip.

    An explicit ``allow_flatten`` argument always wins. Otherwise the active
    mandate is consulted for a (future) ``flatten_on_halt`` attribute, defaulting
    to ``False`` (cancel-only) — the safe default and the current behavior, since
    the frozen mandate schema has no such field yet (see module docstring).

    Args:
        broker: Broker key used to load the mandate.
        allow_flatten: Caller override, or ``None`` to defer to the mandate.

    Returns:
        ``True`` if positions should be flattened, else ``False``.
    """
    if allow_flatten is not None:
        return allow_flatten
    mandate = load_mandate(broker)
    if mandate is None:
        # No valid mandate on file → fail-closed to cancel-only.
        return False
    return bool(getattr(mandate, "flatten_on_halt", False))


def _cancel_resting_orders(
    broker: str,
    submit: SubmitFn,
    read_open_orders: ReadOpenOrdersFn,
    report: dict[str, Any],
) -> None:
    """Cancel every resting/open order, auditing each call (no retry on error).

    Args:
        broker: Broker key for audit stamping.
        submit: Injected broker callable (receives a cancel request dict).
        read_open_orders: Injected broker callable returning open-order dicts.
        report: Mutated in place — successful ids appended to
            ``cancelled_order_ids``, failures to ``errors``.
    """
    try:
        open_orders = read_open_orders()
    except Exception as exc:  # noqa: BLE001 — broker read must not abort the sweep
        report["errors"].append({"phase": "read_open_orders", "error": str(exc)})
        return

    for order in open_orders:
        order_id = order.get("order_id")
        request = {"action": "cancel", "order_id": order_id}
        try:
            response = submit(request)
        except Exception as exc:  # noqa: BLE001 — record + move on, never retry
            report["errors"].append(
                {"phase": "cancel", "order_id": order_id, "error": str(exc)}
            )
            _audit(
                broker,
                _sweep_tool(broker, "cancel_order", _CANCEL_TOOL),
                f"cancel order {order_id}",
                request,
                None,
                "error",
                str(exc),
            )
            continue
        report["cancelled_order_ids"].append(order_id)
        _audit(
            broker,
            _sweep_tool(broker, "cancel_order", _CANCEL_TOOL),
            f"cancel order {order_id}",
            request,
            response,
            "accepted",
            None,
        )


def _flatten_open_positions(
    broker: str,
    submit: SubmitFn,
    read_positions: ReadPositionsFn,
    report: dict[str, Any],
) -> None:
    """Submit a closing order for each open position, auditing each (no retry).

    A long position (``qty > 0``) is closed by a sell of ``abs(qty)``; a short
    (``qty < 0``) by a buy. A zero-qty position is skipped.

    Args:
        broker: Broker key for audit stamping.
        submit: Injected broker callable (receives a closing order dict).
        read_positions: Injected broker callable returning position dicts.
        report: Mutated in place — accepted closes appended to
            ``flatten_orders_submitted``, failures to ``errors``.
    """
    try:
        positions = read_positions()
    except Exception as exc:  # noqa: BLE001 — broker read must not abort the sweep
        report["errors"].append({"phase": "read_positions", "error": str(exc)})
        return

    for position in positions:
        symbol = position.get("symbol")
        qty = float(position.get("qty", 0) or 0)
        if qty == 0:
            continue
        side = "sell" if qty > 0 else "buy"
        close_qty = abs(qty)
        request = {
            "action": "close",
            "symbol": symbol,
            "side": side,
            "qty": close_qty,
            "type": "market",
        }
        intent = f"flatten {symbol}: {side} {close_qty} @ market"
        try:
            response = submit(request)
        except Exception as exc:  # noqa: BLE001 — record + move on, never retry
            report["errors"].append(
                {"phase": "flatten", "symbol": symbol, "error": str(exc)}
            )
            _audit(
                broker,
                _sweep_tool(broker, "submit_order", _FLATTEN_TOOL),
                intent,
                request,
                None,
                "error",
                str(exc),
            )
            continue
        report["flatten_orders_submitted"].append(
            {"symbol": symbol, "qty": close_qty, "side": side, "response": response}
        )
        _audit(
            broker,
            _sweep_tool(broker, "submit_order", _FLATTEN_TOOL),
            intent,
            request,
            response,
            "accepted",
            None,
        )


def _sweep_tool(broker: str, operation: str, fallback: str) -> str:
    """Return the connector-specific sweep tool name for audit records."""
    try:
        from src.trading.service import runner_tool_name

        return runner_tool_name(broker, operation) or fallback
    except Exception:  # pragma: no cover - audit should not fail the sweep
        return fallback


def _audit(
    broker: str,
    remote_tool: str,
    intent: str,
    request: dict[str, Any],
    response: dict[str, Any] | None,
    outcome: str,
    error: str | None,
) -> None:
    """Append one redacted live-action record for a sweep broker call.

    Args:
        broker: Broker key (stamped as ``server``).
        remote_tool: Broker remote tool invoked (``cancel_order`` | ``place_order``).
        intent: Human-readable normalized intent for the ledger.
        request: Raw broker request (redacted before write by the ledger).
        response: Raw broker response, or ``None`` on error.
        outcome: ``"accepted"`` on success, ``"error"`` on failure.
        error: Error string when ``outcome == "error"``, else ``None``.
    """
    write_live_action(
        LiveActionEvent(
            kind="order_placed" if outcome == "accepted" else "order_rejected",
            session_id=_RUNTIME_SESSION_ID,
            outcome=outcome,  # type: ignore[arg-type]
            server=broker,
            remote_tool=remote_tool,
            intent_normalized=intent,
            broker_request=request,
            broker_response=response,
            error=error,
        )
    )
