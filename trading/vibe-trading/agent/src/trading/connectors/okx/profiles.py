"""Built-in OKX connector profiles.

Layer A ships read-only paper (demo) and live profiles. OKX demo keys live in a
separate key namespace from live keys and select the environment via the SDK
``flag`` (``"1"`` demo, ``"0"`` live), so they are distinct profiles. The
order-placing profiles (``okx-paper-trade`` / ``okx-live-trade``) add the
``orders.place`` capability; the live one is gated behind a mandate.
"""

from __future__ import annotations

from src.trading.types import READ_CAPABILITIES, TradingProfile

OKX_PROFILES: tuple[TradingProfile, ...] = (
    TradingProfile(
        id="okx-paper-sdk",
        connector="okx",
        label="OKX Demo · python-okx",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "paper"},
        notes=(
            "Reads an OKX demo (paper) account via python-okx with the simulated-"
            "trading flag set. Demo keys are a separate namespace and cannot reach "
            "the live environment."
        ),
    ),
    TradingProfile(
        id="okx-live-sdk-readonly",
        connector="okx",
        label="OKX Live · python-okx Read-Only",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES,
        readonly=True,
        config={"profile": "live-readonly"},
        notes="Reads an OKX live account only. Order placement is not exposed in this profile.",
    ),
    TradingProfile(
        id="okx-paper-trade",
        connector="okx",
        label="OKX Demo · python-okx Trading",
        environment="paper",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place",),
        readonly=False,
        config={"profile": "paper"},
        notes=(
            "Places orders on an OKX demo (paper) account via python-okx with the "
            "simulated-trading flag set. Demo keys are a separate namespace and "
            "cannot reach the live environment."
        ),
    ),
    TradingProfile(
        id="okx-live-trade",
        connector="okx",
        label="OKX Live · python-okx Trading",
        environment="live",
        transport="broker_sdk",
        capabilities=READ_CAPABILITIES + ("orders.place.requires_mandate",),
        readonly=False,
        config={"profile": "live"},
        notes=(
            "Places orders on an OKX live account via python-okx. Live order "
            "placement is gated behind a user-defined mandate and kill switch."
        ),
    ),
)
