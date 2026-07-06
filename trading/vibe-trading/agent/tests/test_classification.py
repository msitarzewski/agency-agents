"""Read/write classification ladder: annotations, curated map wins, default-deny."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from src.live.classification import ToolClass, classify_tool
from src.trading.connectors.ibkr.classification import IBKR_TOOL_CLASS
from src.trading.connectors.robinhood.classification import ROBINHOOD_TOOL_CLASS


def test_tier1_explicit_read_only_hint_true_is_read() -> None:
    """readOnlyHint=True with no curated entry → READ."""
    ann = ToolAnnotations(readOnlyHint=True)
    assert classify_tool("get_quotes", ann) is ToolClass.READ


def test_tier1_explicit_read_only_hint_false_is_write() -> None:
    """readOnlyHint=False → WRITE (additive-only is still a write)."""
    ann = ToolAnnotations(readOnlyHint=False, destructiveHint=False)
    assert classify_tool("submit_thing", ann) is ToolClass.WRITE


def test_absent_read_only_hint_is_not_read() -> None:
    """readOnlyHint=None (hint absent) must NOT be treated as read → UNKNOWN."""
    ann = ToolAnnotations(readOnlyHint=None, title="some tool")
    assert classify_tool("mystery_tool", ann) is ToolClass.UNKNOWN


def test_tier2_curated_map_classifies_known_tools() -> None:
    """Curated map drives classification for known names."""
    assert (
        classify_tool("get_positions", None, ROBINHOOD_TOOL_CLASS) is ToolClass.READ
    )
    assert classify_tool("place_order", None, ROBINHOOD_TOOL_CLASS) is ToolClass.WRITE


def test_deceptive_read_only_hint_cannot_demote_curated_write() -> None:
    """A lying readOnlyHint=True on place_order stays WRITE — the map wins."""
    deceptive = ToolAnnotations(readOnlyHint=True)
    assert (
        classify_tool("place_order", deceptive, ROBINHOOD_TOOL_CLASS)
        is ToolClass.WRITE
    )


def test_annotation_catches_write_map_missed() -> None:
    """A tool absent from the map but annotated write → WRITE (not excused)."""
    ann = ToolAnnotations(readOnlyHint=False)
    assert (
        classify_tool("place_bracket_order", ann, ROBINHOOD_TOOL_CLASS)
        is ToolClass.WRITE
    )


def test_tier3_default_deny_unknown_and_unannotated() -> None:
    """Neither annotated read-only nor in the map → UNKNOWN (fail-closed)."""
    assert classify_tool("brand_new_tool", None, ROBINHOOD_TOOL_CLASS) is ToolClass.UNKNOWN
    assert classify_tool("brand_new_tool", None) is ToolClass.UNKNOWN


def test_map_read_pin_not_overridden_by_absent_annotation() -> None:
    """A curated READ wins even when annotations are present but silent."""
    ann = ToolAnnotations(title="quotes", readOnlyHint=None)
    assert classify_tool("get_quotes", ann, ROBINHOOD_TOOL_CLASS) is ToolClass.READ


def test_ibkr_sparse_map_pins_known_order_names_write() -> None:
    """IBKR read names are annotation-discovered, but order names stay WRITE."""
    assert classify_tool("place_order", None, IBKR_TOOL_CLASS) is ToolClass.WRITE
    assert classify_tool("cancelOrder", ToolAnnotations(readOnlyHint=True), IBKR_TOOL_CLASS) is ToolClass.WRITE
