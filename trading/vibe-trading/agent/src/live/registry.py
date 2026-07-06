"""Live-broker tool wrapping for the registry (SPEC §7.2 + integration seam).

``build_mcp_tool_wrappers`` returns a plain :class:`~src.tools.mcp.MCPRemoteTool`
for every discovered tool. For a live broker (e.g. Robinhood) that is not safe:
every order-placing (WRITE or UNKNOWN) tool must be re-wrapped in
:class:`~src.live.order_guard.LiveOrderGuardTool` so the mandate gate + kill
switch run before any broker call, while READ tools stay on the plain path but
are marked read-only for downstream UI/audit. Classification uses the 3-tier
ladder (annotations -> curated map -> default-deny); UNKNOWN is treated as WRITE
(fail-closed), so an unrecognized broker tool is never exposed ungated.
"""

from __future__ import annotations

import logging

from src.config.schema import (
    LIVE_BROKER_SERVER_KEYS,
    is_live_broker_url,
    live_broker_key_for_url,
)
from src.live.classification import ToolClass, classify_tool
from src.live.halt import halt_flag_set
from src.live.order_guard import LiveOrderGuardTool
from src.tools.mcp import MCPRemoteTool
from src.trading.connectors.alpaca.classification import ALPACA_TOOL_CLASS
from src.trading.connectors.binance.classification import BINANCE_TOOL_CLASS
from src.trading.connectors.dhan.classification import DHAN_TOOL_CLASS
from src.trading.connectors.futu.classification import FUTU_TOOL_CLASS
from src.trading.connectors.ibkr.classification import IBKR_TOOL_CLASS
from src.trading.connectors.longbridge.classification import LONGBRIDGE_TOOL_CLASS
from src.trading.connectors.okx.classification import OKX_TOOL_CLASS
from src.trading.connectors.robinhood.classification import ROBINHOOD_TOOL_CLASS
from src.trading.connectors.shoonya.classification import SHOONYA_TOOL_CLASS
from src.trading.connectors.tiger.classification import TIGER_TOOL_CLASS

logger = logging.getLogger(__name__)

#: Per-broker curated classification maps (Tier 2). Keyed by broker name; an
#: aliased server key resolves to its broker via :func:`_broker_for`. Order-
#: mutating ops are pinned WRITE so the live gate fails closed; an op absent
#: from its broker map and not annotated read-only resolves to UNKNOWN → WRITE.
_BROKER_CURATED_MAPS = {
    "robinhood": ROBINHOOD_TOOL_CLASS,
    "ibkr": IBKR_TOOL_CLASS,
    "tiger": TIGER_TOOL_CLASS,
    "longbridge": LONGBRIDGE_TOOL_CLASS,
    "alpaca": ALPACA_TOOL_CLASS,
    "okx": OKX_TOOL_CLASS,
    "binance": BINANCE_TOOL_CLASS,
    "futu": FUTU_TOOL_CLASS,
    "dhan": DHAN_TOOL_CLASS,
    "shoonya": SHOONYA_TOOL_CLASS,
}


def is_live_broker(server_name: str, url: str = "") -> bool:
    """Return whether an MCP server denotes a live-trading broker.

    Detection is by config key OR by URL host, so a live-broker URL parked under
    an arbitrary key (e.g. ``rh``) is still gated and wildcard-rejected. The
    name-key path stays as a fallback for non-URL / intentionally-named entries.

    Args:
        server_name: The MCP server key from agent config.
        url: The server's ``url`` (empty for stdio). When its host matches a
            known live-broker host, the server is a live broker regardless of
            ``server_name``.

    Returns:
        ``True`` when the server is a live broker requiring gated wrapping.
    """
    if server_name.strip().lower() in LIVE_BROKER_SERVER_KEYS:
        return True
    return is_live_broker_url(url)


def _broker_for(server_name: str, url: str = "") -> str:
    """Resolve the canonical broker namespace for a live-broker server.

    A server keyed by a known broker name uses that key; a server detected only
    by URL host maps to the broker that owns that host. This keeps the curated
    map, mandate store, and HALT sentinel all keyed by the real broker even when
    the config key is an alias.

    Args:
        server_name: The MCP server key from agent config.
        url: The server's ``url``.

    Returns:
        The canonical broker key (e.g. ``"robinhood"``).
    """
    key = server_name.strip().lower()
    if key in LIVE_BROKER_SERVER_KEYS:
        return key

    return live_broker_key_for_url(url) or key


#: FastMCP's OAuth token cache collection name (``TokenStorageAdapter``).
_OAUTH_TOKEN_COLLECTION = "mcp-oauth-token"


def has_cached_oauth_token(url: str, cache_dir: str) -> bool:
    """Return whether a cached OAuth token already exists for a live channel.

    FastMCP's OAuth provider persists tokens through the same
    :func:`~src.tools.mcp._build_token_store` (``FileTreeStore``) backend, under
    the ``mcp-oauth-token`` collection. ``FileTreeStore`` lays a collection out
    as ``<cache_dir>/mcp-oauth-token/`` containing one entry file per cached
    token. We detect authorization by the PRESENCE of any token entry file in
    that collection directory rather than by reconstructing FastMCP's exact
    (server-URL-derived) cache key — the key scheme is an internal detail and is
    not stable to reconstruct, so a directory-level presence check is the robust
    signal. The token VALUE is never read, returned, or logged — only presence.

    Args:
        url: The live channel's MCP server URL (unused for the presence scan,
            kept for signature symmetry and future per-URL scoping).
        cache_dir: The configured token cache directory.

    Returns:
        ``True`` when at least one token entry file is present; ``False`` on an
        absent/empty cache or any read error (fail-closed: unreadable = not
        authorized, so a non-interactive run skips rather than blocks).
    """
    from pathlib import Path

    try:
        collection = Path(cache_dir).expanduser() / _OAUTH_TOKEN_COLLECTION
        if not collection.is_dir():
            return False
        # Any persisted token entry (FileTreeStore writes one file per key, plus
        # a sidecar ``*-info.json`` at the cache root — not inside the dir).
        return any(p.is_file() for p in collection.iterdir())
    except OSError as exc:
        logger.debug("OAuth token presence check failed for %s: %s", url, exc)
        return False


def should_register_live_channel(
    *, interactive: bool, url: str, cache_dir: str | None
) -> bool:
    """Decide whether to register a live channel given session interactivity.

    SPEC Transport §4 (headless / no-token-yet): a non-interactive
    ``serve``/swarm run with no cached OAuth token must NOT register the channel,
    because the first authorized call would block on ``webbrowser.open`` against
    a browser that cannot open. An interactive TTY session always registers so
    first-run browser authorize works. When a cached token already exists, the
    channel registers in any context (no browser needed).

    Args:
        interactive: Whether the session is an interactive TTY.
        url: The live channel's MCP server URL.
        cache_dir: The configured OAuth token cache dir (``None`` when the
            channel has no OAuth config — then there is no token to wait on and
            registration proceeds).

    Returns:
        ``True`` when the channel should be registered.
    """
    if interactive:
        return True
    if cache_dir is None:
        return True
    return has_cached_oauth_token(url, cache_dir)


def wrap_live_broker_tools(
    server_name: str,
    wrappers: list[MCPRemoteTool],
    *,
    url: str = "",
) -> list[MCPRemoteTool]:
    """Re-wrap a live broker's discovered tools by read/write class.

    READ tools are returned as-is with ``is_readonly = True``; WRITE and UNKNOWN
    tools are replaced by a :class:`LiveOrderGuardTool` over the same adapter and
    spec, so order placement passes the mandate gate + kill switch.

    Registration-time halt (SPEC §Consent 4, defense-in-depth): when the kill
    switch is tripped for this broker, the WRITE/UNKNOWN (order) tools are
    OMITTED from the assembled list entirely — a halted session's tool list does
    not even contain them. READ tools stay. The call-time gate
    (:class:`LiveOrderGuardTool`) is the un-bypassable check that also covers the
    race where the flag is set after the list was built mid-turn; this is the
    belt-and-suspenders registration-time half.

    Args:
        server_name: The live-broker MCP server key (e.g. ``"robinhood"`` or an
            alias like ``"rh"``).
        wrappers: The plain ``MCPRemoteTool`` wrappers from
            :func:`~src.tools.mcp.build_mcp_tool_wrappers`.
        url: The server's ``url``, used to resolve the canonical broker when the
            config key is an alias (so curated map / mandate / halt all key off
            the real broker).

    Returns:
        The wrappers with order-placing tools gated, and (when halted) with the
        order tools omitted. Order is preserved.
    """
    broker = _broker_for(server_name, url)
    curated = _BROKER_CURATED_MAPS.get(broker)
    halted = halt_flag_set(broker)
    result: list[MCPRemoteTool] = []
    for tool in wrappers:
        spec = tool._spec  # internal seam: the gate is constructed from the same spec/adapter
        tool_class = classify_tool(spec.remote_name, spec.annotations, curated)
        if tool_class is ToolClass.READ:
            tool.is_readonly = True
            result.append(tool)
        elif halted:
            # WRITE/UNKNOWN + halt tripped -> do not even hand it to the model.
            logger.warning(
                "live kill switch tripped for broker '%s' — omitting order tool "
                "'%s' from the registry",
                broker,
                spec.remote_name,
            )
        else:
            # WRITE or UNKNOWN -> mandate-gated (fail-closed for UNKNOWN).
            result.append(LiveOrderGuardTool(tool._adapter, spec, broker=broker))
    return result
