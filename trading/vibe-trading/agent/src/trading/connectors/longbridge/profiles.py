"""Built-in Longbridge connector profiles.

Layer A ships read-only paper and live profiles. Because Longbridge exposes no
runtime paper/live discriminator, the paper profile's environment is
operator-declared (config-trust) and order placement is not exposed here.
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

LONGBRIDGE_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="longbridge-paper-sdk",
        connector="longbridge",
        label="Longbridge Paper · LongPort OpenAPI",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper", "region": "global"},
        notes=(
            "Reads a Longbridge paper account via the official longbridge SDK. "
            "Paper vs live is operator-declared (the API exposes no runtime "
            "discriminator); load the paper Access Token for this profile."
        ),
    ),
    TradingProfile(
        id="longbridge-paper-trade",
        connector="longbridge",
        label="Longbridge Paper · LongPort OpenAPI Trade",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper", "region": "global"},
        notes=(
            "Places PAPER orders against a Longbridge paper account via the "
            "official longbridge SDK. Paper-only by design: Longbridge exposes "
            "no runtime paper/live discriminator, so live order placement is "
            "not supported. Load the paper Access Token for this profile."
        ),
    ),
    TradingProfile(
        id="longbridge-live-sdk-readonly",
        connector="longbridge",
        label="Longbridge Live · LongPort OpenAPI Read-Only",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly", "region": "global"},
        notes="Reads a Longbridge live account only. Order placement is not exposed in this profile.",
    ),
)
