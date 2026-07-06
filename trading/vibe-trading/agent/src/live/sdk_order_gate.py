"""Pre-trade mandate gate for DIRECT-SDK connectors (SPEC Mandate Enforcement §3).

The MCP :class:`~src.live.order_guard.LiveOrderGuardTool` gates Robinhood by
wrapping a remote MCP tool. Direct-SDK connectors (tiger / alpaca / okx /
binance / futu) place orders through a normal Python call, not an MCP tool, so
they need a function-based gate with the SAME ceremony, all fail-closed before
any order reaches the broker:

1. ``load_mandate`` — no valid mandate / unknown schema version → DENY.
2. expiry — past ``consent.expires_at`` → DENY (routes to re-auth).
3. ``halt_flag_set`` — kill switch tripped → DENY, no broker call.
4. notional normalization — a ``quantity`` order is priced (connector quote →
   data loaders) and enforced on the LARGER of explicit notional and
   ``quantity × price``; fail-closed DENY when unpriceable.
5. read positions + balance via the connector's own READ functions.
6. ``check_mandate`` — ALLOW → ``connector.place_order`` / DENY (structural) /
   PAUSE_FOR_REAUTH (quantitative).

A daily count is consumed only on a confirmed ALLOW whose ``place_order``
returned a non-error envelope. Every decision writes one audit event and the
returned payload carries the redacted record under ``live_action``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.live.audit import LiveActionEvent, write_live_action
from src.live.daily_count import increment_daily_count, read_daily_count
from src.live.enforcement import (
    BREACH_KIND_INSTRUMENT,
    BREACH_KIND_UNIVERSE,
    OrderIntent,
    check_mandate,
    instrument_asset_class,
    last_price_usd,
)
from src.live.halt import halt_flag_set
from src.live.mandate.model import MANDATE_SCHEMA_VERSION, Mandate
from src.live.mandate.store import load_mandate

logger = logging.getLogger(__name__)

LIVE_ACTION_RESULT_KEY = "live_action"
_REMOTE_TOOL = "place_order"

_DECISION_ALLOW = "allow"
_DECISION_DENY = "deny"
_DECISION_PAUSE = "pause_for_reauth"


def execute_live_order(
    *,
    broker: str,
    connector_module: Any,
    config: Any,
    intent: OrderIntent,
    place_kwargs: dict[str, Any],
    session_id: str = "",
) -> dict[str, Any]:
    """Run the live mandate gate around a direct-SDK ``place_order``.

    Args:
        broker: Broker key (mandate/halt/counter/audit are keyed by this).
        connector_module: The connector's ``sdk`` module (provides
            ``place_order``/``get_positions``/``get_account_snapshot``/``get_quote``).
        config: The connector config object for a LIVE profile.
        intent: Normalized :class:`OrderIntent` built from the tool args.
        place_kwargs: Keyword args forwarded verbatim to ``connector_module.place_order``
            on ALLOW (``symbol``/``side``/``quantity``/``notional``/``order_type``/
            ``limit_price``/``time_in_force``).
        session_id: Originating session id, stamped onto audit events.

    Returns:
        On ALLOW: the connector's ``place_order`` result dict (with a
        ``live_action`` record attached). Otherwise a refusal envelope
        ``{"status":"blocked","decision",...}``.
    """
    broker = (broker or "").strip().lower()

    mandate = load_mandate(broker)
    if mandate is None or mandate.schema_version != MANDATE_SCHEMA_VERSION:
        return _deny(broker, session_id, "no valid mandate on file", ["mandate"], mandate, intent=None)

    if _is_expired(mandate):
        return _deny(broker, session_id, "mandate expired — re-authorize", ["mandate", "expiry"], mandate, intent=None, reauth=True)

    if halt_flag_set(broker):
        return _deny(broker, session_id, "live trading halted", ["mandate", "expiry", "halt_flag"], mandate, intent=None)

    normalized = _normalize_notional(intent, connector_module, config)
    if normalized is None:
        return _deny(
            broker, session_id, "quantity order notional could not be priced (fail-closed)",
            ["mandate", "expiry", "halt_flag", "quote"], mandate, intent=intent,
        )
    intent = normalized

    positions = _safe_read(connector_module, "get_positions", config)
    balance = _safe_read(connector_module, "get_account_snapshot", config)
    daily_count = read_daily_count(broker)

    breach = check_mandate(
        mandate, intent, positions, balance,
        broker=broker, remote_tool=_REMOTE_TOOL, daily_count=daily_count,
    )

    if breach is None:
        return _allow(broker, session_id, connector_module, config, intent, place_kwargs, mandate)

    reauth = breach.kind not in (BREACH_KIND_UNIVERSE, BREACH_KIND_INSTRUMENT)
    return _deny_breach(broker, session_id, breach, mandate, intent, reauth)


# --------------------------------------------------------------------------- #
# Decision helpers
# --------------------------------------------------------------------------- #


def _allow(broker, session_id, connector_module, config, intent, place_kwargs, mandate) -> dict[str, Any]:
    """Execute the order; consume a count + audit only on a non-error result."""
    try:
        result = connector_module.place_order(config, **place_kwargs)
    except Exception as exc:  # noqa: BLE001 - a connector raise must not escape the gate
        logger.warning("live place_order raised for %s: %s", broker, exc)
        result = {"status": "error", "error": str(exc)}

    is_error = not isinstance(result, dict) or str(result.get("status", "")).lower() != "ok"
    checked = [
        "mandate", "expiry", "halt_flag", "exclude_symbols", "allowed_instruments",
        "asset_classes", "max_order_notional_usd", "max_total_exposure_usd",
        "max_leverage", "max_trades_per_day", "account_funding_usd", "universe_floors",
    ]
    if is_error:
        record = _audit(
            broker, session_id, kind="order_rejected", outcome="error", mandate=mandate, intent=intent,
            broker_request=dict(place_kwargs), broker_response=result if isinstance(result, dict) else {"raw": result},
            gate_decision={"allowed": True, "decision": _DECISION_ALLOW, "checked_limits": checked},
            error=_error_message(result),
        )
    else:
        increment_daily_count(broker)
        record = _audit(
            broker, session_id, kind="order_placed", outcome="accepted", mandate=mandate, intent=intent,
            broker_request=dict(place_kwargs), broker_response=result,
            gate_decision={"allowed": True, "decision": _DECISION_ALLOW, "checked_limits": checked},
        )
    if isinstance(result, dict) and record is not None:
        result = {**result, LIVE_ACTION_RESULT_KEY: record}
    return result if isinstance(result, dict) else {"status": "error", "error": "non-dict broker result"}


def _deny(broker, session_id, reason, checked, mandate, *, intent, reauth=False) -> dict[str, Any]:
    """Audit + return a refusal for a pre-check / structural DENY."""
    record = _audit(
        broker, session_id, kind="order_rejected", outcome="blocked", mandate=mandate, intent=intent,
        broker_request=None, broker_response=None,
        gate_decision={"allowed": False, "decision": _DECISION_DENY, "checked_limits": checked},
        error=reason,
    )
    return _refusal(broker, decision=_DECISION_DENY, reason=reason, reauth=reauth, record=record)


def _deny_breach(broker, session_id, breach, mandate, intent, reauth) -> dict[str, Any]:
    """Audit + return a refusal for a ``check_mandate`` breach."""
    decision = _DECISION_PAUSE if reauth else _DECISION_DENY
    record = _audit(
        broker, session_id, kind="breach", outcome="blocked", mandate=mandate, intent=intent,
        broker_request=None, broker_response=None,
        gate_decision={
            "allowed": False, "decision": decision, "limit": breach.limit, "kind": breach.kind,
            "limit_value": breach.limit_value, "attempted_value": breach.attempted_value,
        },
        error=breach.detail or f"order breaches {breach.limit}",
    )
    return _refusal(
        broker, decision=decision, reason=breach.detail or f"order breaches {breach.limit}",
        reauth=reauth, breach=breach, record=record,
    )


def _refusal(broker, *, decision, reason, reauth, breach=None, record=None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "blocked",
        "decision": decision,
        "reason": reason,
        "broker": broker,
        "requires_reauthorization": reauth,
    }
    if record is not None:
        payload[LIVE_ACTION_RESULT_KEY] = record
    if breach is not None:
        payload["breach"] = {
            "broker": breach.broker, "limit": breach.limit, "limit_value": breach.limit_value,
            "attempted_value": breach.attempted_value, "overage": breach.overage,
            "kind": breach.kind, "detail": breach.detail,
            "proposed_action": {
                "symbol": breach.proposed_action.symbol, "side": breach.proposed_action.side,
                "notional_usd": breach.proposed_action.notional_usd, "quantity": breach.proposed_action.quantity,
                "instrument_type": breach.proposed_action.instrument_type.value,
            },
        }
    return payload


# --------------------------------------------------------------------------- #
# Notional normalization + reads
# --------------------------------------------------------------------------- #


def _normalize_notional(intent: OrderIntent, connector_module: Any, config: Any) -> OrderIntent | None:
    """Stamp a single authoritative ``notional_usd`` (quantity → priced).

    Currency note: the connector quote is the broker's native currency (HKD for
    HK, CNH for A-share). The mandate caps are USD; treating a local-currency
    figure as USD OVER-states USD exposure for HKD/CNH (≈7-8x), so the caps bind
    CONSERVATIVELY (over-deny, never under-deny). FX normalization is a follow-up
    before HK/CN are promoted past the structural asset-class gate.
    """
    if intent.quantity is None:
        return intent
    price = _quote_price(intent, connector_module, config)
    if price is None:
        return None
    implied = intent.quantity * price
    if implied != implied or implied <= 0:
        return None
    explicit = intent.notional_usd if intent.notional_usd is not None else 0.0
    enforced = max(float(explicit), implied)
    return OrderIntent(
        symbol=intent.symbol, side=intent.side, notional_usd=enforced,
        quantity=intent.quantity, instrument_type=intent.instrument_type, asset_class=intent.asset_class,
    )


def _quote_price(intent: OrderIntent, connector_module: Any, config: Any) -> float | None:
    """Live USD price for the intent symbol: connector quote first, loaders next."""
    broker_price = _connector_quote_price(connector_module, config, intent.symbol)
    if broker_price is not None:
        return broker_price
    asset_class = intent.asset_class or instrument_asset_class(intent.instrument_type)
    if asset_class is None:
        return None
    try:
        return last_price_usd(intent.symbol, asset_class)
    except Exception as exc:  # noqa: BLE001 - loader failure → fail-closed
        logger.warning("loader quote failed for %s: %s", intent.symbol, exc)
        return None


def _connector_quote_price(connector_module: Any, config: Any, symbol: str) -> float | None:
    """Parse a positive price from the connector's ``get_quote`` envelope."""
    getter = getattr(connector_module, "get_quote", None)
    if getter is None:
        return None
    try:
        result = getter(symbol, config=config)
    except Exception as exc:  # noqa: BLE001
        logger.warning("connector quote failed for %s: %s", symbol, exc)
        return None
    if not isinstance(result, dict) or str(result.get("status", "")).lower() == "error":
        return None
    quote = result.get("quote")
    if not isinstance(quote, dict):
        return None
    for key in ("last", "ask", "bid", "close"):
        if key in quote:
            try:
                value = float(quote[key])
            except (TypeError, ValueError):
                continue
            if value == value and value > 0:
                return value
    return None


def _safe_read(connector_module: Any, fn_name: str, config: Any) -> object:
    """Call a connector read fn, returning ``None`` on any error (fail-closed)."""
    fn = getattr(connector_module, fn_name, None)
    if fn is None:
        return None
    try:
        result = fn(config)
    except Exception as exc:  # noqa: BLE001
        logger.warning("connector read %s failed: %s", fn_name, exc)
        return None
    if isinstance(result, dict) and str(result.get("status", "")).lower() == "error":
        return None
    return result


# --------------------------------------------------------------------------- #
# Audit + misc
# --------------------------------------------------------------------------- #


def _audit(broker, session_id, *, kind, outcome, mandate, intent, broker_request, broker_response, gate_decision, error=None) -> dict | None:
    consent = mandate.consent if mandate is not None else None
    try:
        event = LiveActionEvent(
            kind=kind,  # type: ignore[arg-type]
            session_id=session_id,
            outcome=outcome,  # type: ignore[arg-type]
            server=broker,
            remote_tool=_REMOTE_TOOL,
            intent_normalized=_describe_intent(intent),
            mandate_snapshot_ref=consent.consent_token_sha256 if consent else None,
            consent_record_ref=consent.account_ref if consent else None,
            broker_request=broker_request,
            broker_response=broker_response,
            gate_decision=gate_decision,
            error=error,
        )
        try:
            return write_live_action(event, event_callback=None, trace_writer=None)
        except TypeError:
            return write_live_action(event)
    except Exception as exc:  # auditing must never block a decision
        logger.warning("live-action audit write failed (%s): %s", kind, exc)
        return None


def _is_expired(mandate: Mandate) -> bool:
    raw = mandate.consent.expires_at
    try:
        expires = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return True
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= expires


def _error_message(result: object) -> str:
    if isinstance(result, dict):
        for key in ("error", "message", "detail"):
            value = result.get(key)
            if isinstance(value, str) and value:
                return value
    return "broker order returned an error"


def _describe_intent(intent: OrderIntent | None) -> str | None:
    if intent is None:
        return None
    size = (
        f"${intent.notional_usd:g}" if intent.notional_usd is not None
        else f"{intent.quantity:g} units" if intent.quantity is not None
        else "?"
    )
    return f"{intent.side} {size} {intent.symbol} ({intent.instrument_type.value})"
