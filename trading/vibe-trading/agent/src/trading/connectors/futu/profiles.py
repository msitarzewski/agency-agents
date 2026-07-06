"""Built-in Futu (moomoo) connector profiles.

Read-only paper and live profiles sit alongside order-placing paper and live
profiles. All four reach the same local OpenD gateway; the profile chooses the
trade environment (``SIMULATE`` vs ``REAL``) and the account is resolved by its
``trd_env`` at runtime. The order-placing live profile gates on the mandate
("orders.place.requires_mandate") and requires an OpenD trade-password unlock.
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

FUTU_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="futu-paper-sdk",
        connector="futu",
        label="Futu Paper · futu-api",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper", "filter_trdmarket": "HK"},
        notes=(
            "Reads a Futu paper (SIMULATE) account via futu-api through a local OpenD "
            "gateway (default 127.0.0.1:11111). OpenD must be running and logged in. "
            "The account is resolved by trd_env=SIMULATE; a live account cannot be "
            "driven under this profile."
        ),
    ),
    TradingProfile(
        id="futu-live-sdk-readonly",
        connector="futu",
        label="Futu Live · futu-api Read-Only",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly", "filter_trdmarket": "HK"},
        notes=(
            "Reads a Futu live (REAL) account only, via futu-api through a local OpenD "
            "gateway (default 127.0.0.1:11111). OpenD must be running and logged in. "
            "Order placement is not exposed in this profile."
        ),
    ),
    TradingProfile(
        id="futu-paper-trade",
        connector="futu",
        label="Futu Paper · futu-api Trading",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper", "filter_trdmarket": "HK"},
        notes=(
            "Places orders on a Futu paper (SIMULATE) account via futu-api through a "
            "local OpenD gateway (default 127.0.0.1:11111). OpenD must be running and "
            "logged in. The account is resolved by trd_env=SIMULATE; a live account "
            "cannot be driven under this profile. Paper accounts are never unlocked, so "
            "no trade password is required."
        ),
    ),
    TradingProfile(
        id="futu-live-trade",
        connector="futu",
        label="Futu Live · futu-api Trading",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place.requires_mandate",),
        readonly=False,
        config={"profile": "live", "filter_trdmarket": "HK"},
        notes=(
            "Places orders on a Futu live (REAL) account via futu-api through a local "
            "OpenD gateway (default 127.0.0.1:11111). OpenD must be running and logged "
            "in. Live order placement gates on the user mandate and requires unlocking "
            "the trade context with FUTU_TRADE_PWD_MD5 (the MD5 of the Futu trade "
            "password); without it, orders fail closed."
        ),
    ),
)
