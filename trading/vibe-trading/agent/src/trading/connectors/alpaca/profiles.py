"""Built-in Alpaca connector profiles.

Layer A ships read-only paper and live profiles; the trade profiles add order
placement. Paper and live use different key pairs and different hosts, so they
are distinct profiles. The live-trade profile carries an
``orders.place.requires_mandate`` capability — placement on live funds is only
authorized once the caller has a mandate in place; this connector layer just
records the capability.
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

ALPACA_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="alpaca-paper-sdk",
        connector="alpaca",
        label="Alpaca Paper · alpaca-py",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper", "feed": "iex"},
        notes=(
            "Reads an Alpaca paper account (paper-api.alpaca.markets) via alpaca-py. "
            "Paper keys cannot reach the live host."
        ),
    ),
    TradingProfile(
        id="alpaca-live-sdk-readonly",
        connector="alpaca",
        label="Alpaca Live · alpaca-py Read-Only",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly", "feed": "iex"},
        notes="Reads an Alpaca live account only (api.alpaca.markets). Order placement is not exposed in this profile.",
    ),
    TradingProfile(
        id="alpaca-paper-trade",
        connector="alpaca",
        label="Alpaca Paper · alpaca-py Trade",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper", "feed": "iex"},
        notes=(
            "Reads and places orders on an Alpaca paper account "
            "(paper-api.alpaca.markets) via alpaca-py. Paper keys cannot reach "
            "the live host, so no real funds are ever at risk."
        ),
    ),
    TradingProfile(
        id="alpaca-live-trade",
        connector="alpaca",
        label="Alpaca Live · alpaca-py Trade",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place.requires_mandate",),
        readonly=False,
        config={"profile": "live", "feed": "iex"},
        notes=(
            "Reads and places orders on an Alpaca live account "
            "(api.alpaca.markets). Placement on live funds requires an "
            "authorized mandate; the caller enforces it."
        ),
    ),
)
