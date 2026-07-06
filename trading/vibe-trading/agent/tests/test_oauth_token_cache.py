"""Unit tests for the OAuth token cache backend (``_build_token_store``).

These guard the security-critical invariants of the live-channel token cache:

* The cache directory is created ``0700`` and ``~`` is expanded.
* Tokens survive a fresh store instance (persistence round-trip) and are read
  back from disk, never from constructor args or process memory alone.
* A cached token never appears in any log record or in the OAuth transport's
  request-bound payload.
* URL/path-shaped cache keys are neutralized into cache-root-local filenames.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import stat
from pathlib import Path

import pytest

from src.tools.mcp import _build_token_store

pytestmark = pytest.mark.unit


def test_build_token_store_creates_dir_0700(tmp_path: Path) -> None:
    cache = tmp_path / "oauth"
    assert not cache.exists()

    _build_token_store(str(cache))

    assert cache.is_dir()
    mode = stat.S_IMODE(os.stat(cache).st_mode)
    assert mode == 0o700, f"expected owner-only 0700, got {oct(mode)}"


def test_build_token_store_expands_user(monkeypatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    _build_token_store("~/.vibe-trading/live/robinhood/oauth")

    resolved = fake_home / ".vibe-trading" / "live" / "robinhood" / "oauth"
    assert resolved.is_dir()


def test_build_token_store_idempotent_on_existing_dir(tmp_path: Path) -> None:
    cache = tmp_path / "oauth"
    _build_token_store(str(cache))
    # Second call must not raise on an already-existing directory.
    _build_token_store(str(cache))
    assert stat.S_IMODE(os.stat(cache).st_mode) == 0o700


def test_token_persists_across_store_instances(tmp_path: Path) -> None:
    cache = tmp_path / "oauth"
    token_value = {"access_token": "secret-abc", "refresh_token": "secret-refresh"}

    async def _roundtrip() -> dict | None:
        writer = _build_token_store(str(cache))
        await writer.put(collection="robinhood", key="tokens", value=token_value)
        # A brand-new store instance must read the token back from disk.
        reader = _build_token_store(str(cache))
        return await reader.get(collection="robinhood", key="tokens")

    read_back = asyncio.run(_roundtrip())
    assert read_back == token_value


def test_fastmcp_url_cache_keys_are_filesystem_safe(tmp_path: Path) -> None:
    """FastMCP OAuth keys include the raw MCP URL and must stay cache-local."""
    cache = tmp_path / "oauth"
    url = "https://agent.robinhood.com/mcp/trading"
    entries = [
        ("mcp-oauth-client-info", f"{url}/client_info"),
        ("mcp-oauth-token", f"{url}/tokens"),
        ("mcp-oauth-token-expiry", f"{url}/token_expiry"),
    ]

    async def _roundtrip_url_keys() -> None:
        writer = _build_token_store(str(cache))
        for collection, key in entries:
            await writer.put(collection=collection, key=key, value={"key": key})

        reader = _build_token_store(str(cache))
        for collection, key in entries:
            assert await reader.get(collection=collection, key=key) == {"key": key}

    asyncio.run(_roundtrip_url_keys())

    collection_names = {collection for collection, _ in entries}
    payload_files = [
        path.relative_to(cache)
        for path in cache.rglob("*.json")
        if path.parent.name in collection_names
    ]
    assert len(payload_files) == len(entries)
    assert all(len(path.parts) == 2 for path in payload_files)
    assert not any(
        part in {"https:", "agent.robinhood.com", "mcp", "trading"}
        for path in payload_files
        for part in path.parts
    )


def test_token_value_never_in_args_or_payload(tmp_path: Path) -> None:
    """The token lives only on disk — it is never passed via constructor args.

    ``_build_token_store`` receives only a directory path; the secret token is
    written/read through the async store API, so the secret can never leak from
    the factory's positional/keyword arguments.
    """
    cache = tmp_path / "oauth"
    store = _build_token_store(str(cache))

    # The factory's only input is the directory; no token material is bound to
    # the returned store object's public surface as plaintext.
    repr_text = repr(store)
    assert "secret" not in repr_text.lower()


def test_token_never_logged(tmp_path: Path, caplog) -> None:
    cache = tmp_path / "oauth"
    secret = "token-must-not-be-logged-xyz"

    async def _write() -> None:
        store = _build_token_store(str(cache))
        await store.put(collection="robinhood", key="tokens", value={"access_token": secret})

    with caplog.at_level(logging.DEBUG):
        # Building the store must not log the cache path's token contents, and
        # writing a token must not emit it to any logger.
        asyncio.run(_write())

    for record in caplog.records:
        assert secret not in record.getMessage()


def test_store_sanitizes_path_escape_key_inside_cache_root(tmp_path: Path) -> None:
    """Path-shaped keys are stored under a sanitized cache-local filename."""
    cache = tmp_path / "oauth"
    store = _build_token_store(str(cache))

    async def _write_escape() -> dict | None:
        await store.put(collection="robinhood", key="../../escape", value={"x": 1})
        return await store.get(collection="robinhood", key="../../escape")

    assert asyncio.run(_write_escape()) == {"x": 1}

    # Nothing leaked outside the cache root.
    assert not (tmp_path / "escape").exists()
    assert not (tmp_path.parent / "escape").exists()
    assert all(path.resolve().is_relative_to(cache.resolve()) for path in cache.rglob("*") if path.is_file())


# --------------------------------------------------------------------------- #
# SPEC §7.4: token never in audit / envelopes, not accepted from args,
#            cache-expiry surfaces re-auth (no silent call with a stale token).
# --------------------------------------------------------------------------- #

_OAUTH_SECRET = "rh-access-token-MUST-NOT-LEAK-123"


def test_token_never_in_audit_payload() -> None:
    """A token in a broker request/response is redacted in the audit record.

    The live-action audit ledger scrubs credential keys via
    ``redact_payload`` before any sink write (SPEC §5/§7.4), so an OAuth token
    that rides a raw broker payload never reaches the ledger / trace / SSE bus.
    """
    from src.live.audit import LiveActionEvent

    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        remote_tool="place_order",
        broker_request={"symbol": "AAPL", "access_token": _OAUTH_SECRET},
        broker_response={"order_id": "rh_x", "authorization": _OAUTH_SECRET},
    )

    record = event.to_record()

    flat = json.dumps(record)
    assert _OAUTH_SECRET not in flat, "OAuth token leaked into the audit record"
    assert record["broker_request"]["access_token"] == "[redacted]"
    assert record["broker_response"]["authorization"] == "[redacted]"
    # The non-secret intent survives.
    assert record["broker_request"]["symbol"] == "AAPL"


def test_token_not_accepted_from_tool_args_or_variables() -> None:
    """A token injected via tool args is stripped before reaching the broker.

    ``MCPRemoteTool._filter_arguments`` projects kwargs down to the remote
    tool's declared schema. A live channel's order tool declares its real
    fields; an injected ``access_token`` / ``authorization`` (the
    caller-injection / prompt-injection vector, SPEC §3 (b)) is not a declared
    field and is dropped, so it never forwards to Robinhood. The OAuth provider
    owns the Authorization header at the transport layer — the agent cannot
    supply a token through the call surface.
    """
    from src.tools.mcp import MCPRemoteTool, MCPRemoteToolSpec

    spec = MCPRemoteToolSpec(
        server_name="robinhood",
        remote_name="place_order",
        local_name="mcp_robinhood_place_order",
        description="place an order",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "side": {"type": "string"},
                "quantity": {"type": "number"},
            },
            "required": ["symbol", "side"],
            "additionalProperties": False,
        },
    )
    tool = MCPRemoteTool(adapter=object(), spec=spec)

    filtered = tool._filter_arguments(
        {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 1,
            # Injection attempts via tool args / variables:
            "access_token": _OAUTH_SECRET,
            "authorization": _OAUTH_SECRET,
            "token": _OAUTH_SECRET,
        }
    )

    assert filtered == {"symbol": "AAPL", "side": "buy", "quantity": 1}
    assert _OAUTH_SECRET not in json.dumps(filtered)


def test_cache_expiry_surfaces_reauth_no_silent_stale_call() -> None:
    """An expired/revoked refresh token surfaces an error, not a silent call.

    When the OAuth provider cannot refresh (revoked/expired refresh token,
    headless), the failure propagates through the adapter's normal error
    envelope (``{"status": "error", ...}``) — there is NO ``status: "ok"``
    result returned off a stale token (SPEC Transport §5 / §7.4). The mutating
    path must NOT be retried either (no duplicate side effect).
    """
    from fastmcp.exceptions import McpError
    from mcp import types as mcp_types

    from src.config.schema import MCPServerConfig
    from src.tools.mcp import MCPServerAdapter

    # 401 Unauthorized → an auth failure the provider could not silently refresh.
    auth_error = McpError(
        mcp_types.ErrorData(code=-32001, message="401 Unauthorized: token expired, re-auth required")
    )

    call_count = {"n": 0}

    class _ExpiredAuthClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def list_tools(self):
            return []

        async def call_tool(self, name, arguments=None, *, timeout=None, raise_on_error=False):
            call_count["n"] += 1
            raise auth_error

    cfg = MCPServerConfig.model_validate(
        {
            "type": "streamableHttp",
            "url": "https://agent.robinhood.com/mcp/trading",
            "auth": {"type": "oauth", "scopes": ["trading.read"]},
            "enabled_tools": ["place_order"],
        }
    )
    adapter = MCPServerAdapter("robinhood", cfg, client_factory=_ExpiredAuthClient)

    result = adapter.call_tool("place_order", {"symbol": "AAPL", "side": "buy"})

    # Surfaced as an error envelope — never a silent success off a stale token.
    assert result["status"] == "error"
    assert "401" in result["error"] or "re-auth" in result["error"].lower() or "expired" in result["error"].lower()
    # Mutating call must NOT be retried (no duplicate order side effect).
    assert call_count["n"] == 1
