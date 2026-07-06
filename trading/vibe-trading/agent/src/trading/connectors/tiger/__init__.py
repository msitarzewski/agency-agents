"""Tiger Brokers (TigerOpen) trading connector.

Read-only account/market access in Layer A. Order placement (paper and
mandate-gated live) is layered on top in later phases. The connector talks to
Tiger's official ``tigeropen`` Python SDK directly (RSA-signed REST), so it is a
``broker_sdk`` transport rather than a local socket or remote MCP server.
"""
