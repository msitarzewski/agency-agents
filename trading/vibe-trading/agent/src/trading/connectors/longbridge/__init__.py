"""Longbridge (LongPort OpenAPI) trading connector.

Read-only account/market access in Layer A via the official ``longbridge``
Python SDK (``TradeContext`` / ``QuoteContext`` over REST). A ``broker_sdk``
transport, like Tiger.

Safety note: Longbridge exposes no runtime field that distinguishes a paper
account from a live one — paper and live share the same host and App Key and
differ only by which Access Token is loaded. The paper/live distinction here is
therefore operator-declared in config and cannot be self-verified from any API
response. Order placement on this connector stays gated on resolving a reliable
runtime discriminator first.
"""
