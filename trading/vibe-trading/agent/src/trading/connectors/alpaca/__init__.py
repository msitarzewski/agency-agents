"""Alpaca trading connector.

Read-only account/market access in Layer A via the official ``alpaca-py`` SDK
(``TradingClient`` + ``StockHistoricalDataClient`` over REST). A ``broker_sdk``
transport.

Paper-vs-live separation is structural: paper and live use DIFFERENT API keys
and DIFFERENT hosts (``paper-api.alpaca.markets`` vs ``api.alpaca.markets``), so
a paper key physically cannot reach the live host. The account response carries
no paper/live field, so the configured ``paper`` flag (and thus the host) is the
authoritative discriminator; it is recorded on every payload and never flipped
implicitly.
"""
