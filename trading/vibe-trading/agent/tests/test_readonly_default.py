"""Live channel OFF-by-default + read-only-default invariants (SPEC §7.4).

This gate encodes the four SPEC invariants end to end:

1. The seeded ``robinhood`` config's ``enabled_tools`` contains EXACTLY the
   curated READ tool names (and never ``"*"``). This is the structural defense
   that catches finding #1 (seed/map name mismatch): a name here that the
   curated map does not classify READ would classify UNKNOWN -> gated -> refused
   and the real read would be filtered out.
2. The config-load validator rejects ``enabled_tools=["*"]`` for a live broker.
3. With the seed (READ-only) allowlist, the order-placing tools are ABSENT from
   the assembled wrappers — the allowlist filters them at discovery before
   classification ever runs (OFF-by-default).
4. After the user allowlists the WRITE tool names AND a mandate is committed, the
   order tools APPEAR and are gate-wrapped (:class:`LiveOrderGuardTool`).

Reuses the mock-MCP ``client_factory`` seam (``src.tools.mcp``) so no Robinhood
access is required.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastmcp.client.client import CallToolResult
from mcp import types as mcp_types

import src.live.paths as paths
from src.config.schema import (
    LIVE_BROKER_SERVER_KEYS,
    AgentConfig,
    MCPServerConfig,
    ROBINHOOD_MCP_SERVER_SEED,
)
from src.live.mandate.model import MANDATE_SCHEMA_VERSION
from src.live.order_guard import LiveOrderGuardTool
from src.live.registry import is_live_broker, wrap_live_broker_tools
from src.trading.connectors.robinhood.classification import ROBINHOOD_TOOL_CLASS
from src.live.classification import ToolClass
from src.tools.mcp import MCPRemoteTool, build_mcp_tool_wrappers

pytestmark = pytest.mark.unit

# The full Robinhood catalog a mock server would expose (4 READ + 2 WRITE).
_CATALOG = ("get_account", "get_positions", "get_quotes", "list_orders", "place_order", "cancel_order")


class _FakeClient:
    """Mock MCP client exposing the full Robinhood catalog."""

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def list_tools(self) -> list[mcp_types.Tool]:
        return [
            mcp_types.Tool(name=name, description=f"remote {name}", inputSchema={"type": "object"})
            for name in _CATALOG
        ]

    async def call_tool(self, name: str, arguments=None, *, timeout=None, raise_on_error=False) -> CallToolResult:  # noqa: D401
        raise AssertionError("registry assembly must not call tools")


def _factory() -> _FakeClient:
    return _FakeClient()


def _assemble(enabled_tools: list[str]) -> list[MCPRemoteTool]:
    """Discover + live-wrap the robinhood channel for a given allowlist."""
    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "auth": {"type": "oauth", "scopes": ["trading.read"]},
            "enabled_tools": enabled_tools,
        }
    )
    wrappers = build_mcp_tool_wrappers("robinhood", cfg, client_factory=_factory)
    assert is_live_broker("robinhood", cfg.url)
    return wrap_live_broker_tools("robinhood", wrappers, url=cfg.url)


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def _commit_mandate(live_runtime: Path) -> None:
    broker = live_runtime / "live" / "robinhood"
    broker.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    payload = {
        "schema_version": MANDATE_SCHEMA_VERSION,
        "hard_caps": {
            "account_funding_usd": 5000.0,
            "max_order_notional_usd": 750.0,
            "max_total_exposure_usd": 5000.0,
            "max_leverage": 1.0,
            "allowed_instruments": ["equity", "etf"],
            "max_trades_per_day": 5,
        },
        "universe": {
            "asset_classes": ["us_equity", "us_etf"],
            "min_market_cap_usd": None,
            "min_avg_daily_volume_usd": None,
            "exclude_symbols": [],
        },
        "consent": {
            "created_at": created.isoformat(),
            "consent_token_sha256": "deadbeef",
            "broker": "robinhood",
            "account_ref": "acct_ref",
            "expires_at": (created + timedelta(days=30)).isoformat(),
        },
    }
    (broker / "mandate.json").write_text(json.dumps(payload), encoding="utf-8")


# --- Invariant 1: seed allowlist == curated READ names (catches finding #1) ---


def test_seed_enabled_tools_are_exactly_curated_read_names() -> None:
    curated_reads = {
        name for name, cls in ROBINHOOD_TOOL_CLASS.items() if cls is ToolClass.READ
    }
    seed = set(ROBINHOOD_MCP_SERVER_SEED["enabled_tools"])
    assert seed == curated_reads, (
        "seeded enabled_tools must equal the curated READ names exactly; a "
        "mismatch silently hides real reads / refuses them as UNKNOWN"
    )
    # And every seeded name classifies READ in the curated map (no UNKNOWN).
    for name in seed:
        assert ROBINHOOD_TOOL_CLASS.get(name) is ToolClass.READ


def test_seed_never_uses_wildcard() -> None:
    assert "*" not in ROBINHOOD_MCP_SERVER_SEED["enabled_tools"]
    assert ROBINHOOD_MCP_SERVER_SEED["enabled_tools"]  # non-empty


# --- Invariant 2: validator rejects "*" for a live broker ---


def test_validator_rejects_wildcard_for_live_broker() -> None:
    with pytest.raises(ValueError, match="wildcard"):
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
    assert "robinhood" in LIVE_BROKER_SERVER_KEYS


def test_validator_rejects_wildcard_for_aliased_live_broker_url() -> None:
    # H8: a Robinhood URL under a non-canonical key must still be rejected.
    with pytest.raises(ValueError, match="wildcard"):
        AgentConfig.model_validate(
            {
                "mcpServers": {
                    "rh": {
                        "type": "streamableHttp",
                        "url": "https://agent.robinhood.com/mcp/trading",
                        "auth": {"type": "oauth"},
                        "enabledTools": ["*"],
                    }
                }
            }
        )


# --- Invariant 3: no mandate / READ-only seed -> order tools absent ---


def test_order_tools_absent_with_seed_allowlist() -> None:
    """The seeded READ-only allowlist keeps WRITE tools out of the registry."""
    tools = _assemble(list(ROBINHOOD_MCP_SERVER_SEED["enabled_tools"]))
    names = {t._spec.remote_name for t in tools}
    assert names == set(ROBINHOOD_MCP_SERVER_SEED["enabled_tools"])
    assert "place_order" not in names
    assert "cancel_order" not in names
    # Every surviving tool is a plain read-only MCPRemoteTool (no gate).
    assert all(type(t) is MCPRemoteTool and t.is_readonly for t in tools)
    assert not any(isinstance(t, LiveOrderGuardTool) for t in tools)


# --- Invariant 4: write allowlisted + mandate committed -> gated tools appear ---


def test_order_tools_appear_gate_wrapped_when_allowlisted(live_runtime: Path) -> None:
    _commit_mandate(live_runtime)
    enabled = list(ROBINHOOD_MCP_SERVER_SEED["enabled_tools"]) + ["place_order", "cancel_order"]
    tools = _assemble(enabled)
    by_name = {t._spec.remote_name: t for t in tools}

    assert "place_order" in by_name and "cancel_order" in by_name
    assert isinstance(by_name["place_order"], LiveOrderGuardTool)
    assert isinstance(by_name["cancel_order"], LiveOrderGuardTool)
    assert by_name["place_order"].broker == "robinhood"
    # Reads stay plain read-only.
    assert type(by_name["get_account"]) is MCPRemoteTool
    assert by_name["get_account"].is_readonly is True


# --- H8: a Robinhood URL under an aliased key is still a live broker ----------


def test_aliased_key_with_robinhood_url_is_gated() -> None:
    """A Robinhood agentic URL parked under key 'rh' is gated + broker-resolved."""
    from src.config.schema import MCPServerConfig

    assert is_live_broker("rh", "https://agent.robinhood.com/mcp/trading")
    assert not is_live_broker("rh", "https://example.test/mcp")

    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "auth": {"type": "oauth"},
            "enabled_tools": ["get_positions", "place_order"],
        }
    )
    wrappers = build_mcp_tool_wrappers("rh", cfg, client_factory=_factory)
    gated = wrap_live_broker_tools("rh", wrappers, url=cfg.url)
    by_name = {t._spec.remote_name: t for t in gated}

    assert isinstance(by_name["place_order"], LiveOrderGuardTool)
    # Broker namespace resolves to the real broker, not the alias.
    assert by_name["place_order"].broker == "robinhood"
    assert type(by_name["get_positions"]) is MCPRemoteTool


def test_lookalike_host_is_not_a_live_broker() -> None:
    """A substring/lookalike host must NOT match (no false positive)."""
    assert not is_live_broker("rh", "https://robinhood.com.evil.test/mcp")


# --- M1: registration-time halt omits order tools (defense-in-depth) ----------


def test_halt_omits_order_tools_at_registration(live_runtime: Path) -> None:
    from src.live.halt import trip_halt

    _commit_mandate(live_runtime)
    trip_halt(by="test", reason="reg-time halt", broker="robinhood")

    enabled = list(ROBINHOOD_MCP_SERVER_SEED["enabled_tools"]) + ["place_order", "cancel_order"]
    tools = _assemble(enabled)
    names = {t._spec.remote_name for t in tools}

    # Order tools are not even present in the assembled list.
    assert "place_order" not in names
    assert "cancel_order" not in names
    assert not any(isinstance(t, LiveOrderGuardTool) for t in tools)
    # Read tools survive a halt.
    assert "get_account" in names
    assert all(t.is_readonly for t in tools)


# --- H7: headless / no-token live channel is skipped, TTY registers ----------


def test_should_register_live_channel_headless_no_token(live_runtime: Path) -> None:
    from src.live.registry import should_register_live_channel

    cache = str(live_runtime / "live" / "robinhood" / "oauth")
    url = "https://agent.robinhood.com/mcp/trading"

    # Non-interactive + no cached token -> skip (do not block on a browser).
    assert should_register_live_channel(interactive=False, url=url, cache_dir=cache) is False
    # Interactive TTY -> register so first-run authorize works.
    assert should_register_live_channel(interactive=True, url=url, cache_dir=cache) is True


def test_should_register_live_channel_headless_with_cached_token(live_runtime: Path) -> None:
    import asyncio

    from src.live.registry import has_cached_oauth_token, should_register_live_channel
    from src.tools.mcp import _build_token_store

    cache = str(live_runtime / "live" / "robinhood" / "oauth")
    url = "https://agent.robinhood.com/mcp/trading"

    # Seed a token entry using FastMCP's URL-derived token key. The key contains
    # slashes/colon in the logical store API, but the FileTreeStore backend must
    # persist it as a filesystem-safe cache-local filename.
    async def _seed_token() -> None:
        store = _build_token_store(cache)
        await store.put(
            collection="mcp-oauth-token",
            key=f"{url}/tokens",
            value={"access_token": "cached"},
        )

    asyncio.run(_seed_token())

    assert has_cached_oauth_token(url, cache) is True
    # With a cached token, even a non-interactive run registers the channel.
    assert should_register_live_channel(interactive=False, url=url, cache_dir=cache) is True
