"""Built-in Shoonya (Finvasia) connector profiles.

Shoonya (https://shoonya.com) by Finvasia offers ZERO brokerage on all
segments — the cheapest Indian broker for algorithmic trading.

Supports NSE/BSE equities, F&O (NIFTY/BANKNIFTY options), currency, and
commodity. The API uses a TOTP-based login flow (vendor code + TOTP secret
required alongside user/password).

Paper-only by design: Shoonya exposes no sandbox and no runtime paper/live
discriminator — the TOTP login reaches the same real account whether the
profile is declared ``paper`` or ``live``. Following the Longbridge precedent,
this connector ships read-only paper/live profiles plus a locally simulated
paper-trade profile, and exposes NO live order placement. The connector's
order path is structurally capped at paper (see ``sdk.place_order``).
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

SHOONYA_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="shoonya-paper-sdk",
        connector="shoonya",
        label="Shoonya Paper · NorenApi (India, ₹0 brokerage)",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper"},
        notes=(
            "Reads real-time Indian market data (NSE/BSE) via Shoonya's free API. "
            "Paper vs live is operator-declared (the API exposes no runtime "
            "discriminator). Zero brokerage on all segments. Supports equities, "
            "F&O (NIFTY/BANKNIFTY options), currency, commodity."
        ),
    ),
    TradingProfile(
        id="shoonya-paper-trade",
        connector="shoonya",
        label="Shoonya Paper · NorenApi Trade (India, ₹0 brokerage)",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper"},
        notes=(
            "Places PAPER orders simulated locally using real Shoonya market "
            "data — no real money at risk. Paper-only by design: Shoonya "
            "exposes no runtime paper/live discriminator, so live order "
            "placement is not supported. Zero brokerage. Supports NIFTY/"
            "BANKNIFTY options."
        ),
    ),
    TradingProfile(
        id="shoonya-live-sdk-readonly",
        connector="shoonya",
        label="Shoonya Live · NorenApi Read-Only (India, ₹0 brokerage)",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly"},
        notes=(
            "Reads a live Shoonya account (fund limits, positions, orders, "
            "quotes, history). No order placement. Zero brokerage."
        ),
    ),
)
