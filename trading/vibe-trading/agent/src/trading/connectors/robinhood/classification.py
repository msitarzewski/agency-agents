"""Curated read/write classification map for Robinhood Agentic Trading.

Tier 2 of the classification ladder (:mod:`src.live.classification`): an
explicit, version-controlled map keyed by the broker's remote tool name. Map
entries are authoritative and override Tier-1 ``annotations`` when they
disagree (a deceptive ``readOnlyHint=True`` on ``place_order`` cannot demote a
curated WRITE). A tool absent from this map and not annotated read-only is
UNKNOWN and treated as WRITE (fail-closed).

This map is the FROZEN canonical Robinhood catalog (SPEC §7.5):
``READ = {get_account, get_positions, get_quotes, list_orders}`` and
``WRITE = {place_order, cancel_order}``. Any tool the broker reports that is not
in this map and not annotated read-only resolves to UNKNOWN → treated as WRITE
(fail-closed), so an unrecognized new broker tool can never slip through as a
plain read. Adding a tool here is a localized edit to this one dict plus the
classification test parametrize list.
"""

from __future__ import annotations

from src.live.classification import ToolClass

#: Frozen canonical Robinhood read/write catalog.
ROBINHOOD_TOOL_CLASS: dict[str, ToolClass] = {
    # READ
    "get_account": ToolClass.READ,
    "get_positions": ToolClass.READ,
    "get_quotes": ToolClass.READ,
    "list_orders": ToolClass.READ,
    # WRITE
    "place_order": ToolClass.WRITE,
    "cancel_order": ToolClass.WRITE,
}
