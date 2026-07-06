"""Persistent live-trading runtime (SPEC.md §7.5).

The runtime makes the "agentic" framing honest: a persistent process that
wakes on a schedule, decides + trades inside the committed mandate, sleeps,
and survives restarts. This package holds the *shell* (scheduler, durable
crash-safe job store, runner liveness); the trading-truth layer (reconcile,
preemptive halt, triggers) is built on top in sibling modules.

Submodules are intentionally NOT re-exported here: parcels land sibling
modules (runner, triggers, reconcile, flatten) concurrently, so importing
``src.live.runtime`` must never pull a half-written sibling. Import the exact
module you need (e.g. ``from src.live.runtime.scheduler import Scheduler``).
"""
