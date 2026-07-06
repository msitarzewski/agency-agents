"""Unit tests for the MCP OAuth schema + ``_build_client`` OAuth wiring.

Covers:

* ``MCPOAuthConfig`` / ``MCPServerConfig.auth`` pydantic round-trip (camelCase
  and snake_case keys) and the seeded Robinhood config.
* Validator rejections: OAuth requires https, auth and static headers are
  mutually exclusive, stdio rejects auth, and a live-broker entry rejects a
  wildcard ``["*"]`` allowlist.
* ``_build_client`` yields a ``StreamableHttpTransport`` whose ``.auth`` is an
  ``OAuth`` instance carrying the expected scopes / client_name / callback_port.
* The static-header HTTP path and the stdio path are byte-for-byte unchanged
  (``.auth is None``; transport types and fields untouched).
"""

from __future__ import annotations

import pytest
from fastmcp.client.auth import OAuth
from fastmcp.client.transports.http import StreamableHttpTransport
from fastmcp.client.transports.sse import SSETransport
from fastmcp.client.transports.stdio import StdioTransport
from pydantic import ValidationError

from src.config.schema import (
    IBKR_MCP_SERVER_SEED,
    LIVE_BROKER_SERVER_KEYS,
    ROBINHOOD_MCP_SERVER_SEED,
    AgentConfig,
    MCPOAuthConfig,
    MCPServerConfig,
    MCPServerConfigOverride,
)
from src.tools.mcp import MCPServerAdapter

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Schema round-trip
# --------------------------------------------------------------------------- #
def test_oauth_config_round_trip_snake_and_camel() -> None:
    snake = MCPOAuthConfig.model_validate(
        {
            "type": "oauth",
            "scopes": ["trading.read"],
            "client_name": "Vibe-Trading",
            "cache_dir": "~/.vibe-trading/live/robinhood/oauth",
            "callback_port": 8765,
            "client_id": "client-id",
            "client_secret": "client-secret",
            "client_metadata_url": "https://example.com/oauth/client.json",
        }
    )
    camel = MCPOAuthConfig.model_validate(
        {
            "type": "oauth",
            "scopes": ["trading.read"],
            "clientName": "Vibe-Trading",
            "cacheDir": "~/.vibe-trading/live/robinhood/oauth",
            "callbackPort": 8765,
            "clientId": "client-id",
            "clientSecret": "client-secret",
            "clientMetadataUrl": "https://example.com/oauth/client.json",
        }
    )
    assert snake == camel
    assert snake.client_name == "Vibe-Trading"
    assert snake.callback_port == 8765
    assert snake.client_id == "client-id"
    assert snake.client_secret == "client-secret"
    assert snake.client_metadata_url == "https://example.com/oauth/client.json"


def test_server_config_carries_auth() -> None:
    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "auth": {"type": "oauth", "scopes": ["trading.read"]},
        }
    )
    assert isinstance(cfg.auth, MCPOAuthConfig)
    assert cfg.auth.scopes == ["trading.read"]
    assert cfg.resolved_transport() == "streamableHttp"


def test_server_config_round_trips_init_timeout_snake_and_camel() -> None:
    snake = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "init_timeout": 300,
        }
    )
    camel = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "initTimeout": 300,
        }
    )
    assert snake == camel
    assert snake.init_timeout == 300


def test_override_carries_auth() -> None:
    override = MCPServerConfigOverride.model_validate(
        {"auth": {"type": "oauth", "scopes": ["trading.read"]}}
    )
    assert isinstance(override.auth, MCPOAuthConfig)


def test_robinhood_seed_is_readonly_and_oauth() -> None:
    cfg = AgentConfig.model_validate({"mcpServers": {"robinhood": ROBINHOOD_MCP_SERVER_SEED}})
    rh = cfg.mcp_servers["robinhood"]
    assert rh.resolved_transport() == "streamableHttp"
    assert rh.auth is not None and rh.auth.type == "oauth"
    assert rh.init_timeout == 300
    assert rh.tool_timeout == 30
    assert "*" not in rh.enabled_tools
    assert rh.enabled_tools  # non-empty explicit allowlist
    assert "robinhood" in LIVE_BROKER_SERVER_KEYS


def test_ibkr_seed_is_official_readonly_oauth_probe() -> None:
    cfg = AgentConfig.model_validate({"mcpServers": {"ibkr": IBKR_MCP_SERVER_SEED}})
    ibkr = cfg.mcp_servers["ibkr"]
    assert ibkr.resolved_transport() == "streamableHttp"
    assert ibkr.url == "https://api.ibkr.com/v1/api/mcp"
    assert ibkr.auth is not None and ibkr.auth.type == "oauth"
    assert ibkr.auth.scopes == ["mcp.read"]
    assert ibkr.auth.cache_dir == "~/.vibe-trading/live/ibkr/oauth"
    assert ibkr.enabled_tools == ["*"]
    assert "ibkr" in LIVE_BROKER_SERVER_KEYS


# --------------------------------------------------------------------------- #
# Validator rejections
# --------------------------------------------------------------------------- #
def test_oauth_requires_https() -> None:
    with pytest.raises(ValidationError, match="https"):
        MCPServerConfig.model_validate(
            {"type": "streamableHttp", "url": "http://insecure/mcp", "auth": {"type": "oauth"}}
        )


def test_auth_and_static_headers_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError, match="static headers"):
        MCPServerConfig.model_validate(
            {
                "type": "streamableHttp",
                "url": "https://agent.robinhood.com/mcp/trading",
                "headers": {"Authorization": "Bearer hand-set"},
                "auth": {"type": "oauth"},
            }
        )


def test_stdio_rejects_auth() -> None:
    with pytest.raises(ValidationError, match="HTTP-only"):
        MCPServerConfig.model_validate({"command": "uvx", "args": ["demo"], "auth": {"type": "oauth"}})


def test_live_broker_rejects_wildcard_allowlist() -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        AgentConfig.model_validate(
            {
                "mcpServers": {
                    "robinhood": {
                        "type": "streamableHttp",
                        "url": "https://agent.robinhood.com/mcp/trading",
                        "auth": {"type": "oauth"},
                        "enabledTools": ["*"],
                    }
                }
            }
        )


def test_ibkr_rejects_wildcard_when_write_scope_is_requested() -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        AgentConfig.model_validate(
            {
                "mcpServers": {
                    "ibkr": {
                        "type": "streamableHttp",
                        "url": "https://api.ibkr.com/v1/api/mcp",
                        "auth": {"type": "oauth", "scopes": ["mcp.read", "mcp.write"]},
                        "enabledTools": ["*"],
                    }
                }
            }
        )


def test_ibkr_rejects_wildcard_without_read_scope() -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        AgentConfig.model_validate(
            {
                "mcpServers": {
                    "ibkr": {
                        "type": "streamableHttp",
                        "url": "https://api.ibkr.com/v1/api/mcp",
                        "auth": {"type": "oauth", "scopes": ["openid"]},
                        "enabledTools": ["*"],
                    }
                }
            }
        )


def test_non_live_broker_still_allows_wildcard() -> None:
    # A non-broker HTTP server keeps the default ["*"] semantics.
    cfg = AgentConfig.model_validate(
        {"mcpServers": {"internal_kb": {"type": "streamableHttp", "url": "https://kb/mcp"}}}
    )
    assert cfg.mcp_servers["internal_kb"].enabled_tools == ["*"]


# --------------------------------------------------------------------------- #
# _build_client OAuth wiring
# --------------------------------------------------------------------------- #
def _build_client(server_config: MCPServerConfig):
    return MCPServerAdapter("robinhood", server_config)._build_client()


def _build_transport(server_config: MCPServerConfig):
    return _build_client(server_config).transport


def test_build_client_yields_oauth_streamable_transport() -> None:
    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "auth": {
                "type": "oauth",
                "scopes": ["trading.read"],
                "client_name": "Vibe-Trading",
                "callback_port": 8765,
                "client_id": "client-id",
                "client_secret": "client-secret",
                "client_metadata_url": "https://example.com/oauth/client.json",
            },
        }
    )
    transport = _build_transport(cfg)

    assert isinstance(transport, StreamableHttpTransport)
    assert isinstance(transport.auth, OAuth)
    # Scopes / name / port flow through from config to the OAuth provider.
    assert transport.auth._scopes == ["trading.read"]
    assert transport.auth._client_name == "Vibe-Trading"
    assert transport.auth._callback_port == 8765
    assert transport.auth._client_id == "client-id"
    assert transport.auth._client_secret == "client-secret"
    assert transport.auth._client_metadata_url == "https://example.com/oauth/client.json"


def test_build_client_uses_explicit_init_timeout_without_widening_tool_timeout() -> None:
    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "tool_timeout": 7,
            "init_timeout": 300,
            "auth": {"type": "oauth", "scopes": ["trading.read"]},
        }
    )

    client = _build_client(cfg)

    assert client._init_timeout == 300
    assert client._session_kwargs["read_timeout_seconds"].total_seconds() == 7


def test_build_client_keeps_default_init_timeout_floor() -> None:
    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://kb/mcp",
            "tool_timeout": 7,
        }
    )

    client = _build_client(cfg)

    assert client._init_timeout == 30
    assert client._session_kwargs["read_timeout_seconds"].total_seconds() == 7


def test_static_header_http_path_unchanged() -> None:
    cfg = MCPServerConfig.model_validate(
        {"type": "streamableHttp", "url": "https://kb/mcp", "headers": {"X-Api-Key": "k"}}
    )
    transport = _build_transport(cfg)

    assert isinstance(transport, StreamableHttpTransport)
    # No auth was constructed; the static-header path is byte-unchanged.
    assert transport.auth is None
    assert transport.headers == {"X-Api-Key": "k"}


def test_sse_path_unchanged() -> None:
    cfg = MCPServerConfig.model_validate(
        {"type": "sse", "url": "https://kb/sse", "headers": {"X-Api-Key": "k"}}
    )
    transport = _build_transport(cfg)
    assert isinstance(transport, SSETransport)


def test_stdio_path_unchanged() -> None:
    cfg = MCPServerConfig.model_validate({"command": "uvx", "args": ["demo"]})
    transport = _build_transport(cfg)
    assert isinstance(transport, StdioTransport)
