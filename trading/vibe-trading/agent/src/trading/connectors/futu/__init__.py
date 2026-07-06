"""Futu (moomoo) trading connector.

Read-only account/market access in Layer A via the official ``futu-api`` Python
SDK talking to a user-owned LOCAL OpenD gateway (default ``127.0.0.1:11111``).
Like the IBKR connector, this is a local-gateway transport: OpenD runs on the
operator's machine, holds the Futu login, and the SDK speaks to it over a local
socket. Vibe-Trading never sees Futu credentials and exposes no order-placement
method (no ``place_order``, no ``unlock_trade``) in this layer; order placement
(paper, then mandate-gated live) is layered on top later.

Paper-vs-live separation is the documented Futu discriminator: every account row
from ``get_acc_list()`` carries a ``trd_env`` field (``SIMULATE`` for paper,
``REAL`` for live). The connector resolves the account whose ``trd_env`` matches
the selected profile and fails closed if a configured ``acc_id`` does not match,
so a live account can never be driven under a paper profile by mistake.
"""

from src.trading.connectors.futu.sdk import (
    FutuConfig,
    FutuConfigError,
    FutuDependencyError,
    FutuProfileMismatchError,
    build_config,
    check_status,
    config_path,
    futu_available,
    get_account_snapshot,
    get_historical_bars,
    get_open_orders,
    get_positions,
    get_quote,
    load_config,
    save_config,
)

__all__ = [
    "FutuConfig",
    "FutuConfigError",
    "FutuDependencyError",
    "FutuProfileMismatchError",
    "build_config",
    "check_status",
    "config_path",
    "futu_available",
    "get_account_snapshot",
    "get_historical_bars",
    "get_open_orders",
    "get_positions",
    "get_quote",
    "load_config",
    "save_config",
]
