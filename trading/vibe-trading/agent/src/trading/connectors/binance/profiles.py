"""Built-in Binance (spot) connector profiles.

Read-only paper (testnet) and live profiles plus order-placing paper and live
profiles. Paper and live use different key pairs and different hosts, so they
are distinct profiles. The order-placing live profile carries an
``orders.place.requires_mandate`` capability — the higher trading layer must
gate it behind the user's mandate before any order reaches the connector.
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

BINANCE_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="binance-paper-sdk",
        connector="binance",
        label="Binance Spot Testnet · ccxt",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper"},
        notes=(
            "Reads a Binance spot testnet account (testnet.binance.vision) via ccxt. "
            "Testnet keys cannot reach the live host."
        ),
    ),
    TradingProfile(
        id="binance-live-sdk-readonly",
        connector="binance",
        label="Binance Spot Live · ccxt Read-Only",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly"},
        notes="Reads a Binance spot live account only (api.binance.com). Order placement is not exposed in this profile.",
    ),
    TradingProfile(
        id="binance-paper-trade",
        connector="binance",
        label="Binance Spot Testnet · ccxt Trading",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper"},
        notes=(
            "Places and cancels orders on a Binance spot testnet account "
            "(testnet.binance.vision) via ccxt. Testnet keys cannot reach the live host, "
            "so no order from this profile can touch real funds."
        ),
    ),
    TradingProfile(
        id="binance-live-trade",
        connector="binance",
        label="Binance Spot Live · ccxt Trading",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place.requires_mandate",),
        readonly=False,
        config={"profile": "live"},
        notes=(
            "Places and cancels orders on a Binance spot live account (api.binance.com) "
            "via ccxt. Live order placement must be gated by the user's mandate; the "
            "orders.place.requires_mandate capability signals that requirement upstream."
        ),
    ),
)
