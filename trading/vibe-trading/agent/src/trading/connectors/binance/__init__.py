"""Binance (spot) trading connector.

Read-only account/market access in Layer A via the ``ccxt`` library's unified
``binance`` exchange client (REST). A ``broker_sdk`` transport. Order placement
is not exposed here — writes are introduced in a later layer behind the paper
guard and, for live, the mandate gate.

Paper-vs-live separation is structural: the testnet (paper) and live mainnet use
DIFFERENT API keys and DIFFERENT hosts (``testnet.binance.vision`` vs
``api.binance.com``), so a testnet key physically cannot reach the live host. The
configured ``profile`` selects the host (via ``set_sandbox_mode``) and is the
authoritative discriminator; it is recorded on every payload and never flipped
implicitly. Binance spot has no positions — holdings are non-zero balances, so
``get_positions`` shapes the non-zero balances from ``fetch_balance`` as rows.
"""
