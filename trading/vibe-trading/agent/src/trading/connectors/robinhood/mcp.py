"""Robinhood remote MCP generic-operation mapping."""

from __future__ import annotations

from typing import Any

_REMOTE_TOOL_NAMES = {
    "account": "get_account",
    "positions": "get_positions",
    "orders": "list_orders",
    "quote": "get_quotes",
}

_RUNNER_TOOL_NAMES = {
    "account": "get_account",
    "positions": "get_positions",
    "orders": "list_orders",
    "quote": "get_quotes",
    "submit_order": "place_order",
    "cancel_order": "cancel_order",
}


def remote_tool_name(operation: str) -> str | None:
    """Return the Robinhood remote tool name for a generic operation."""
    return _REMOTE_TOOL_NAMES.get(operation)


def runner_tool_name(operation: str) -> str | None:
    """Return the Robinhood remote tool name used by live runner plumbing."""
    return _RUNNER_TOOL_NAMES.get(operation)


def remote_arguments(operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Normalize generic arguments for a Robinhood remote MCP operation."""
    if operation == "quote":
        symbol = arguments.get("symbol")
        symbols = arguments.get("symbols")
        return {"symbols": symbols or ([symbol] if symbol else [])}
    return {}
