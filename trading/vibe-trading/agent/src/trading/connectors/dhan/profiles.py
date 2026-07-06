"""Built-in Dhan connector profiles.

Dhan (https://dhan.co) is an Indian discount broker with free API access.
Supports NSE/BSE equities, F&O (NIFTY/BANKNIFTY options), currency, and
commodity segments.

Paper-only by design: Dhan exposes no sandbox and no runtime paper/live
discriminator — a single Access Token reads the same account whether the
profile is declared ``paper`` or ``live``. Following the Longbridge precedent,
this connector therefore ships read-only paper/live profiles plus a locally
simulated paper-trade profile, and exposes NO live order placement. Paper vs
live is operator-declared (config-trust); the connector's order path is
structurally capped at paper (see ``sdk.place_order``).
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

DHAN_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="dhan-paper-sdk",
        connector="dhan",
        label="Dhan Paper · dhanhq (India)",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper"},
        notes=(
            "Reads real-time Indian market data (NSE/BSE) via Dhan's free API. "
            "Paper vs live is operator-declared (the API exposes no runtime "
            "discriminator). Supports equities, F&O (NIFTY/BANKNIFTY options), "
            "currency, commodity."
        ),
    ),
    TradingProfile(
        id="dhan-paper-trade",
        connector="dhan",
        label="Dhan Paper · dhanhq Trade (India)",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper"},
        notes=(
            "Places PAPER orders simulated locally using real Dhan market data "
            "— no real money at risk. Paper-only by design: Dhan exposes no "
            "runtime paper/live discriminator, so live order placement is not "
            "supported. Supports NSE equities and F&O (NIFTY/BANKNIFTY options)."
        ),
    ),
    TradingProfile(
        id="dhan-live-sdk-readonly",
        connector="dhan",
        label="Dhan Live · dhanhq Read-Only (India)",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly"},
        notes=(
            "Reads a live Dhan account (account, positions, orders, quotes, "
            "history). Order placement is not exposed in this profile."
        ),
    ),
)
