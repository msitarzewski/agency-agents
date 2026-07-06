"""Kill switch for the live trading channel (SPEC.md Consent §4).

The kill switch is a single, instant, global halt of all live activity. It is
enforced at the filesystem layer — **independent of the LLM cooperating** — via
an out-of-band sentinel file. The enforcement gate (P3) checks
:func:`halt_flag_set` at the top of every live order tool invocation, before any
broker call, so the halt works even if the agent loop is wedged mid-iteration,
the model is looping, or the SSE bus is down.

Authoritative sentinel (SPEC §2 / Consent §4)::

    <runtime_root>/live/HALT        # global kill switch; halts ALL brokers

An optional per-broker sentinel (``<runtime_root>/live/<broker>/HALT``) lets a
single broker channel be halted without stopping others. The global flag always
wins: when the global sentinel exists, :func:`halt_flag_set` returns ``True`` for
every broker regardless of per-broker state.

Sentinel payload is a small JSON object so audit can attribute the trip::

    {"tripped_at": "2026-05-29T14:03:11.482000+00:00", "by": "cli", "reason": "..."}

A user (or an external watchdog) may ``touch`` the file directly; a sentinel with
unreadable / malformed contents is still treated as tripped (fail-closed: the
file's *existence* is the halt, the JSON is only attribution metadata).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.live.paths import broker_dir, live_root

logger = logging.getLogger(__name__)

_HALT_FILENAME = "HALT"

#: Recognized trip sources written into the sentinel's ``by`` field.
_VALID_BY = ("cli", "frontend", "file")


def halt_path() -> Path:
    """Return the path to the global kill-switch sentinel.

    Returns:
        ``<runtime_root>/live/HALT``. The file is NOT created here; use
        :func:`trip_halt` to write it.
    """
    return live_root() / _HALT_FILENAME


def broker_halt_path(broker: str) -> Path:
    """Return the path to a per-broker kill-switch sentinel.

    Args:
        broker: Broker key, e.g. ``"robinhood"``.

    Returns:
        ``<runtime_root>/live/<broker>/HALT``. Not created here.

    Raises:
        ValueError: If ``broker`` is invalid (delegated to
            :func:`src.live.paths.broker_dir`).
    """
    return broker_dir(broker) / _HALT_FILENAME


def trip_halt(by: str, reason: str, broker: str | None = None) -> Path:
    """Trip the kill switch by writing a sentinel file.

    Writing is atomic (same-directory temp file + ``os.replace``) so a partial
    write can never leave a corrupt sentinel that a concurrent
    :func:`halt_flag_set` would misread. Tripping is idempotent: a fresh sentinel
    overwrites any prior one, recording the latest trip metadata.

    Args:
        by: Trip source — one of ``"cli"``, ``"frontend"``, ``"file"``. An
            unrecognized value is stored verbatim (the file's existence is what
            enforces the halt; ``by`` is attribution only).
        reason: Human-readable reason recorded in the sentinel for the audit
            trail.
        broker: When ``None`` (default), trips the **global** switch that halts
            all brokers. When set, trips only that broker's sentinel.

    Returns:
        The path to the sentinel that was written.
    """
    path = broker_halt_path(broker) if broker is not None else halt_path()
    payload: dict[str, Any] = {
        "tripped_at": datetime.now(timezone.utc).isoformat(),
        "by": by,
        "reason": reason,
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    logger.warning(
        "live kill switch tripped (broker=%s, by=%s): %s",
        broker or "*",
        by,
        reason,
    )
    return path


def clear_halt(broker: str | None = None) -> bool:
    """Clear a tripped kill switch by deleting its sentinel.

    Clearing is a privileged surface action (never an agent tool). Clearing the
    global switch does NOT clear per-broker sentinels and vice versa — each is
    cleared independently.

    Args:
        broker: When ``None`` (default), clears the global sentinel. When set,
            clears only that broker's sentinel.

    Returns:
        ``True`` if a sentinel existed and was removed, ``False`` if there was
        nothing to clear.
    """
    path = broker_halt_path(broker) if broker is not None else halt_path()
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    logger.warning("live kill switch cleared (broker=%s)", broker or "*")
    return True


def halt_flag_set(broker: str | None = None) -> bool:
    """Return whether live trading is halted — a pure filesystem check.

    This is the authoritative kill-switch check the enforcement gate calls before
    every live order. It performs NO LLM/agent-state lookup and reads NO
    in-process flag: it is solely the presence of the sentinel file(s), so it
    holds even when the agent loop is wedged or the model is non-cooperating.

    The global sentinel always halts: if ``<runtime_root>/live/HALT`` exists,
    this returns ``True`` for any ``broker``. When ``broker`` is given and the
    global switch is not set, the broker's own sentinel is also consulted.

    Args:
        broker: Optional broker key. When provided, the per-broker sentinel is
            checked in addition to the global one. An invalid broker key is
            treated as halted (fail-closed) rather than raising.

    Returns:
        ``True`` if live trading is halted (globally, or for ``broker``).
    """
    if halt_path().exists():
        return True
    if broker is None:
        return False
    try:
        return broker_halt_path(broker).exists()
    except ValueError:
        # An unresolvable broker key can never be safely traded — fail closed.
        return True


def read_halt(broker: str | None = None) -> dict[str, Any] | None:
    """Read the sentinel metadata for a tripped kill switch.

    Args:
        broker: When ``None``, reads the global sentinel; otherwise the broker's.

    Returns:
        The parsed sentinel payload (``tripped_at`` / ``by`` / ``reason``), or
        ``None`` when no sentinel exists. A sentinel that exists but is empty or
        holds malformed JSON returns an empty dict ``{}`` — the halt is still in
        effect (existence is authoritative), only its attribution is unreadable.
    """
    path = broker_halt_path(broker) if broker is not None else halt_path()
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


# --- Preemptive halt action hook (SPEC §7.5 component 6) -------------------
#
# The functions above are the LLM-independent *trigger* (the filesystem
# sentinel). The hook below is the *action* plumbing: a runner registers a
# per-broker callable (in practice a closure over
# ``src.live.runtime.flatten.flatten_and_cancel`` with broker callables bound)
# and invokes it via :func:`on_halt_action` the moment it observes a trip —
# cancelling resting orders and (per mandate) flattening positions, instead of
# merely refusing the next order.
#
# This is deliberately a SEPARATE register/invoke pair, NOT auto-fired inside
# :func:`trip_halt`: ``trip_halt`` must stay a pure, side-effect-bounded
# sentinel writer (a user / watchdog may also trip the switch by touching the
# file directly, bypassing ``trip_halt`` entirely — see SPEC §Consent 4.1). The
# runner observing the sentinel is the single place that drives the preemptive
# action, so the broker-call side effect is never coupled to the flag write.

from typing import Callable  # noqa: E402 — additive import kept local to the hook section

#: Per-broker preemptive-halt actions, keyed by broker. A ``None`` key is the
#: global default action used when no broker-specific action is registered.
_HALT_ACTIONS: dict[str | None, Callable[[str], object]] = {}


def register_halt_action(
    action: Callable[[str], object], broker: str | None = None
) -> None:
    """Register the preemptive action a runner runs when a halt is observed.

    The action is invoked by :func:`on_halt_action` with the tripped broker key.
    Registering is idempotent per key: a later registration replaces the prior
    one. Registering does NOT trip or check the halt — it only wires the action;
    the filesystem sentinel remains the sole, LLM-independent trigger.

    Args:
        action: Callable invoked as ``action(broker)`` on a trip. In production
            this wraps :func:`src.live.runtime.flatten.flatten_and_cancel` with
            the broker's READ/submit callables bound.
        broker: Broker this action applies to, or ``None`` (default) to register
            the fallback action used for any broker lacking a specific one.
    """
    _HALT_ACTIONS[broker] = action


def unregister_halt_action(broker: str | None = None) -> bool:
    """Remove a previously registered preemptive-halt action.

    Args:
        broker: The broker key whose action to remove, or ``None`` for the
            global fallback.

    Returns:
        ``True`` if an action was registered and removed, ``False`` otherwise.
    """
    return _HALT_ACTIONS.pop(broker, None) is not None


def on_halt_action(broker: str) -> object | None:
    """Run the registered preemptive-halt action for a tripped ``broker``.

    Called by the runner after it observes the HALT sentinel (via
    :func:`halt_flag_set`) — it does the cancel-resting-orders + optional
    flatten sweep. A broker-specific action takes precedence over the global
    fallback. If neither is registered this is a no-op (the cooperative
    order-time gate still blocks all future orders regardless).

    The action's own exceptions are NOT swallowed here: a failure to flatten is
    load-bearing and must propagate to the runner's error handling / audit. (The
    per-broker-call no-retry handling lives inside the action itself.)

    Args:
        broker: The broker key whose channel was halted.

    Returns:
        Whatever the registered action returns (e.g. the flatten report dict),
        or ``None`` when no action is registered for ``broker``.
    """
    action = _HALT_ACTIONS.get(broker) or _HALT_ACTIONS.get(None)
    if action is None:
        logger.warning(
            "halt observed for broker=%s but no preemptive action registered "
            "(cooperative gate still blocks future orders)",
            broker,
        )
        return None
    logger.warning("running preemptive halt action for broker=%s", broker)
    return action(broker)
