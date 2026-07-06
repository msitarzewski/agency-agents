"""Built-in Interactive Brokers connector profiles."""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

IBKR_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="ibkr-paper-local",
        connector="ibkr",
        label="IBKR Paper · TWS / Gateway",
        environment="paper",
        transport="local_tws",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper", "host": "127.0.0.1", "port": 7497, "client_id": 77},
        notes="Uses the user's local TWS paper session. No IBKR credentials enter Vibe-Trading.",
    ),
    TradingProfile(
        id="ibkr-live-local-readonly",
        connector="ibkr",
        label="IBKR Live · TWS / Gateway Read-Only",
        environment="live",
        transport="local_tws",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly", "host": "127.0.0.1", "port": 7496, "client_id": 77},
        notes="Reads a local live TWS/Gateway session only. Order placement is not exposed.",
    ),
    TradingProfile(
        id="ibkr-live-official-mcp-readonly",
        connector="ibkr",
        label="IBKR Live · Official MCP Read-Only",
        environment="live",
        transport="remote_mcp",
        capabilities=("mcp.read.discovery",),
        readonly=True,
        config={"server": "ibkr"},
        notes=(
            "Requires IBKR official MCP OAuth approval. Generic account/position tools "
            "stay disabled until IBKR publishes stable read tool names."
        ),
    ),
)
