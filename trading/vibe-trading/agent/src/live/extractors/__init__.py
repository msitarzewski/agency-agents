"""Per-broker order-intent extractors (SPEC.md Mandate Enforcement §4).

Vibe-Trading does not control a broker's tool arg schema, so the enforcement
gate cannot hard-code arg names. Each broker ships an ``extract_order_intent``
function that maps the broker's ``place_order``-style kwargs to the normalized
:class:`~src.live.enforcement.OrderIntent`, returning ``None`` (→ DENY) whenever
a required field is absent, ambiguous, or fails validation — it never guesses.

Extractors register themselves in :data:`BROKER_EXTRACTORS`, keyed by broker.
The gate looks up the broker's extractor and applies it to the raw tool kwargs.
"""

from __future__ import annotations

from typing import Callable

from src.live.enforcement import OrderIntent
from src.trading.connectors.robinhood.extractor import (
    extract_order_intent as _robinhood_extract,
)

#: Signature every broker extractor satisfies.
OrderIntentExtractor = Callable[[str, dict], "OrderIntent | None"]

#: Broker key → order-intent extractor. Broker-specific parsers live with their
#: connector package; this module is only the live-safety lookup table.
BROKER_EXTRACTORS: dict[str, OrderIntentExtractor] = {
    "robinhood": _robinhood_extract,
}


def get_extractor(broker: str) -> OrderIntentExtractor | None:
    """Return the registered extractor for ``broker``, or ``None``.

    Args:
        broker: Broker key, e.g. ``"robinhood"``.

    Returns:
        The broker's :data:`OrderIntentExtractor`, or ``None`` when no extractor
        is registered (→ the gate fail-closes / DENIES).
    """
    return BROKER_EXTRACTORS.get(broker.strip().lower())


__all__ = ["BROKER_EXTRACTORS", "OrderIntentExtractor", "get_extractor"]
