"""Built-in Robinhood connector profiles."""

from __future__ import annotations

from src.trading.types import TradingProfile

ROBINHOOD_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="robinhood-live-mcp",
        connector="robinhood",
        label="Robinhood Live · Agentic MCP",
        environment="live",
        transport="remote_mcp",
        capabilities=(
            "account.read",
            "positions.read",
            "orders.read",
            "quotes.read",
            "orders.place.requires_mandate",
            "runner.manage.requires_mandate",
        ),
        readonly=False,
        config={"server": "robinhood"},
        notes="Reads via Robinhood MCP; execution stays behind OAuth, mandate, guard, audit, and halt.",
    ),
)
