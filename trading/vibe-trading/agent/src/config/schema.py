"""Structured agent config schema for MCP client integration."""

from __future__ import annotations

import json
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Live-broker MCP server keys. These channels may place real orders, so a
# wildcard ``enabled_tools`` (which would re-admit every WRITE/UNKNOWN tool) is
# rejected at config-load time unless a broker-specific read-only OAuth probe is
# explicitly documented below.
LIVE_BROKER_SERVER_KEYS: frozenset[str] = frozenset({"robinhood", "ibkr"})

# URL host suffix -> canonical live-broker key. Detection by host prevents an
# aliased config key from bypassing the wildcard rejection / classification gate.
LIVE_BROKER_URL_HOST_SUFFIX_TO_KEY: dict[str, str] = {
    "robinhood.com": "robinhood",
    "ibkr.com": "ibkr",
}

# Live-broker URL host suffixes. Detecting a live broker by config key alone is
# bypassable: a Robinhood agentic URL placed under any other key (e.g. ``rh``)
# would otherwise dodge BOTH the wildcard rejection AND the classification gate,
# exposing ``place_order`` ungated. So a server whose ``url`` host matches one
# of these suffixes is treated as a live broker regardless of its config key.
# The name-key path (``LIVE_BROKER_SERVER_KEYS``) stays as a fallback for stdio
# / non-URL live channels and for keys that intentionally name a known broker.
LIVE_BROKER_URL_HOST_SUFFIXES: tuple[str, ...] = tuple(LIVE_BROKER_URL_HOST_SUFFIX_TO_KEY)

# IBKR's official MCP endpoint does not publish stable tool names until after
# OAuth. To support a first-run read-only probe, we allow a wildcard only when
# the IBKR server is constrained to the documented read scope and does not carry
# the write scope. The live registry still fail-closes WRITE/UNKNOWN tools after
# discovery; this exception is only for read-tool discovery under ``mcp.read``.
LIVE_BROKER_READONLY_WILDCARD_REQUIRED_SCOPES: dict[str, frozenset[str]] = {
    "ibkr": frozenset({"mcp.read"}),
}
LIVE_BROKER_READONLY_WILDCARD_ALLOWED_EXTRA_SCOPES: dict[str, frozenset[str]] = {
    "ibkr": frozenset({"openid", "profile", "email", "account-ids"}),
}
LIVE_BROKER_WRITE_SCOPES: dict[str, frozenset[str]] = {
    "ibkr": frozenset({"mcp.write"}),
}
ROBINHOOD_AGENT_CONFIG_PATH = "~/.vibe-trading/agent.json"
LIVE_BROKER_WILDCARD_ALLOWLIST_ERROR = (
    "enabledTools allowlist ('*'); pin an explicit read-only tool list"
)


def _url_host(url: str) -> str:
    """Return the lower-cased hostname of an http(s) URL, or ``""``.

    Args:
        url: A candidate MCP server URL.

    Returns:
        The lower-cased host with any port stripped, or ``""`` when the URL is
        empty or has no parseable host.
    """
    if not url or not url.strip():
        return ""
    try:
        host = urlsplit(url.strip()).hostname
    except ValueError:
        return ""
    return (host or "").lower()


def is_live_broker_url(url: str) -> bool:
    """Return whether a URL points at a known live-broker host.

    A live broker is detected by host so an aliased config key cannot bypass the
    wildcard rejection / gate. Match is on the host or any subdomain of a known
    suffix (``agent.robinhood.com`` and ``robinhood.com`` both match), never a
    substring (``robinhood.com.evil.test`` does NOT match).

    Args:
        url: The MCP server ``url`` from config.

    Returns:
        ``True`` when the URL host equals or is a subdomain of a live-broker
        host suffix.
    """
    return live_broker_key_for_url(url) is not None


def live_broker_key_for_url(url: str) -> str | None:
    """Resolve a live broker key from an MCP server URL host.

    Args:
        url: The MCP server ``url`` from config.

    Returns:
        The canonical broker key when the URL host equals or is a subdomain of
        a known live-broker suffix; otherwise ``None``.
    """
    host = _url_host(url)
    if not host:
        return None
    for suffix, broker in LIVE_BROKER_URL_HOST_SUFFIX_TO_KEY.items():
        if host == suffix or host.endswith(f".{suffix}"):
            return broker
    return None


def live_broker_key_for_entry(
    server_key: str, server: "MCPServerConfig | MCPServerConfigOverride"
) -> str | None:
    """Resolve the canonical broker key for a config entry.

    Args:
        server_key: The MCP server key from config.
        server: The server config (or override) carrying the ``url``.

    Returns:
        The canonical broker key when either the key or URL identifies a live
        broker; otherwise ``None``.
    """
    key = server_key.strip().lower()
    if key in LIVE_BROKER_SERVER_KEYS:
        return key
    return live_broker_key_for_url(getattr(server, "url", "") or "")


def is_live_broker_entry(server_key: str, server: "MCPServerConfig | MCPServerConfigOverride") -> bool:
    """Return whether a configured MCP server is a live broker.

    Detection is by config key (``LIVE_BROKER_SERVER_KEYS``) OR by URL host
    (``is_live_broker_url``), so a live-broker URL parked under an arbitrary key
    is still gated and still subject to the wildcard-allowlist rejection.

    Args:
        server_key: The MCP server key from config.
        server: The server config (or override) carrying the ``url``.

    Returns:
        ``True`` when either the key or the URL host identifies a live broker.
    """
    return live_broker_key_for_entry(server_key, server) is not None


def _allows_readonly_wildcard_probe(
    server_key: str, server: "MCPServerConfig | MCPServerConfigOverride"
) -> bool:
    """Return whether a live broker may use ``enabled_tools=["*"]``.

    The only supported exception today is IBKR's official MCP read probe:
    tool names are not known before OAuth, but the token request can be pinned
    to ``mcp.read``. Any write scope or missing read scope fails closed.

    Args:
        server_key: The MCP server key from config.
        server: The server config carrying OAuth scopes.

    Returns:
        ``True`` only for a broker-specific read-only OAuth probe.
    """
    broker = live_broker_key_for_entry(server_key, server)
    if broker is None:
        return False

    required = LIVE_BROKER_READONLY_WILDCARD_REQUIRED_SCOPES.get(broker)
    if not required:
        return False

    auth = getattr(server, "auth", None)
    if auth is None:
        return False

    scopes = {scope.strip() for scope in getattr(auth, "scopes", []) if scope.strip()}
    write_scopes = LIVE_BROKER_WRITE_SCOPES.get(broker, frozenset())
    allowed_extras = LIVE_BROKER_READONLY_WILDCARD_ALLOWED_EXTRA_SCOPES.get(
        broker, frozenset()
    )
    allowed = set(required | allowed_extras)
    return required.issubset(scopes) and scopes.isdisjoint(write_scopes) and scopes <= allowed

# Canonical seed for the operator-side ``~/.vibe-trading/agent.json`` mcpServers
# entry that wires the Robinhood Agentic Trading channel. It ships OFF-by-default
# read-only: an explicit READ allowlist (never ``["*"]``), OAuth auth, and the
# streamableHttp transport. Operators copy this block into their protected config
# file; WRITE/order tools are only ever added by the user editing that file by
# hand (never via agent tool args), and only take effect once a mandate exists.
# Documented here (not invented elsewhere) because the operator config file is a
# runtime artifact, not checked into the repo. See SPEC §7.2 / Transport §1–§6.
ROBINHOOD_MCP_SERVER_SEED: dict[str, object] = {
    "type": "streamableHttp",
    "url": "https://agent.robinhood.com/mcp/trading",
    # Robinhood OAuth can require human face verification. Keep normal remote
    # tool calls on the default 30s budget while giving the initial
    # OAuth/initialize round-trip the same 300s window as FastMCP's callback
    # server.
    "init_timeout": 300.0,
    "auth": {
        "type": "oauth",
        "scopes": ["trading.read"],
        "client_name": "Vibe-Trading",
        "cache_dir": "~/.vibe-trading/live/robinhood/oauth",
    },
    # Seed the OFF-by-default READ allowlist to EXACTLY the canonical curated
    # READ tool names (``src.trading.connectors.robinhood.classification.ROBINHOOD_TOOL_CLASS``).
    # These MUST match the curated map's READ entries: a name here that the map
    # does not classify READ would resolve UNKNOWN -> gated -> refused, silently
    # hiding the real read tool. Canonical READ catalog: get_account,
    # get_positions, get_quotes, list_orders. WRITE (place_order, cancel_order)
    # is never seeded — the user adds those by hand once a mandate exists.
    "enabled_tools": [
        "get_account",
        "get_positions",
        "get_quotes",
        "list_orders",
    ],
}

# Canonical seed for IBKR's official remote MCP server. The endpoint is visible
# from Claude's connector page / install command and advertises OAuth scopes
# ``mcp.read`` and ``mcp.write``. This seed intentionally requests ONLY
# ``mcp.read`` and uses ``enabled_tools=["*"]`` as a read-only discovery probe,
# because IBKR tool names are not public until OAuth completes. If the operator
# later requests ``mcp.write``, the wildcard exception no longer applies and the
# config must pin an explicit tool allowlist plus pass the live order gate.
IBKR_MCP_SERVER_SEED: dict[str, object] = {
    "type": "streamableHttp",
    "url": "https://api.ibkr.com/v1/api/mcp",
    "auth": {
        "type": "oauth",
        "scopes": ["mcp.read"],
        "client_name": "Vibe-Trading",
        "cache_dir": "~/.vibe-trading/live/ibkr/oauth",
    },
    "enabled_tools": ["*"],
}


def _to_camel(name: str) -> str:
    """Convert snake_case names to camelCase aliases.

    Args:
        name: Field name in snake_case form.

    Returns:
        The camelCase alias used for external config compatibility.
    """
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _to_wire_config_value(value: object) -> object:
    """Convert internal snake_case seed keys to external config aliases."""
    if isinstance(value, dict):
        return {_to_camel(str(key)): _to_wire_config_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_to_wire_config_value(child) for child in value]
    return value


def robinhood_readonly_enabled_tools() -> tuple[str, ...]:
    """Return the canonical Robinhood read-only tool allowlist."""
    enabled_tools = ROBINHOOD_MCP_SERVER_SEED["enabled_tools"]
    if not isinstance(enabled_tools, list):
        return ()
    return tuple(str(tool) for tool in enabled_tools)


def robinhood_mcp_server_seed_config() -> dict[str, object]:
    """Return the copy-pasteable Robinhood ``mcpServers`` config seed."""
    return {
        "mcpServers": {
            "robinhood": _to_wire_config_value(ROBINHOOD_MCP_SERVER_SEED),
        }
    }


def format_robinhood_mcp_server_seed_json() -> str:
    """Format the canonical Robinhood read-only ``mcpServers`` seed as JSON."""
    return json.dumps(robinhood_mcp_server_seed_config(), indent=2)


def format_robinhood_mcp_config_guidance(*, reason: str = "missing") -> str:
    """Build operator-facing guidance for enabling Robinhood MCP safely."""
    tools = ", ".join(robinhood_readonly_enabled_tools())
    if reason == "wildcard":
        lead = (
            'Robinhood MCP config uses enabledTools: ["*"], which is not allowed for '
            "live brokers."
        )
    else:
        lead = "Robinhood MCP server is missing from mcpServers."
    return (
        f"{lead} Add the safe read-only Robinhood seed to {ROBINHOOD_AGENT_CONFIG_PATH} "
        f"with explicit enabledTools: {tools}.\n"
        f"{format_robinhood_mcp_server_seed_json()}"
    )


class ConfigBase(BaseModel):
    """Base config model accepting both snake_case and camelCase keys."""

    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")


class MCPOAuthConfig(ConfigBase):
    """OAuth authentication for a remote (HTTP) MCP server.

    The OAuth provider owns the runtime ``Authorization`` header, so a server
    using OAuth must not also set static ``headers`` (mutually exclusive — see
    :meth:`MCPServerConfig.validate_transport_config`). OAuth is only valid on an
    HTTPS HTTP transport: a refresh token must never traverse cleartext.

    Attributes:
        type: Auth discriminator. Only ``"oauth"`` is supported today.
        scopes: OAuth scopes requested at authorization time.
        client_name: Client name presented during dynamic client registration.
        cache_dir: Directory for the persistent OAuth token cache. ``~`` is
            expanded and the directory is created ``0700`` at first write by the
            client. This is the single canonical field name (wire alias
            ``cacheDir``) — every consumer reads ``auth.cache_dir`` (the OAuth
            wiring in :func:`src.tools.mcp.MCPServerAdapter._build_client`, the
            ``live revoke`` CLI cache sweep, and the seed below) so there is no
            silent default-path fallback from a name mismatch. (``docs/live-
            trading/SPEC.md`` §2 names this ``token_cache_path``; the shipped
            field name is ``cache_dir`` to stay consistent with the existing CLI
            consumer, which is the authoritative wire name.)
        callback_port: Fixed loopback port for the browser redirect callback.
            ``None`` (default) lets the OAuth provider pick a free port.
        client_id: Optional pre-registered OAuth client id (skips dynamic
            client registration when provided).
        client_secret: Optional pre-registered OAuth client secret. Used only
            with ``client_id`` for providers that reject public clients.
        client_metadata_url: Optional HTTPS client metadata document URL. Some
            MCP OAuth providers use this URL itself as the client id.
    """

    type: Literal["oauth"] = "oauth"
    scopes: list[str] = Field(default_factory=list)
    client_name: str = "Vibe-Trading"
    cache_dir: str = "~/.vibe-trading/live/robinhood/oauth"
    callback_port: int | None = Field(default=None, ge=1, le=65535)
    client_id: str | None = None
    client_secret: str | None = None
    client_metadata_url: str | None = None


class MCPServerConfig(ConfigBase):
    """Single external MCP server definition."""

    type: Literal["stdio", "sse", "streamableHttp"] | None = None
    command: str = ""
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    url: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    auth: MCPOAuthConfig | None = None
    tool_timeout: float = Field(default=30.0, ge=0.1)
    init_timeout: float | None = Field(default=None, ge=0.1)
    enabled_tools: list[str] = Field(default_factory=lambda: ["*"])

    def resolved_transport(self) -> Literal["stdio", "sse", "streamableHttp"]:
        """Resolve the effective transport from explicit type or implied fields."""
        if self.type is not None:
            return self.type
        if self.command.strip() or self.args or self.env:
            return "stdio"
        if self.url.strip():
            raise ValueError("HTTP MCP servers require an explicit type of 'sse' or 'streamableHttp'")
        return "stdio"

    @model_validator(mode="after")
    def validate_transport_config(self) -> "MCPServerConfig":
        """Validate transport-specific MCP server configuration.

        Returns:
            The validated MCP server config instance.

        Raises:
            ValueError: If required fields are missing for the resolved
                transport or conflicting fields are provided.
        """
        transport = self.resolved_transport()

        if transport == "stdio":
            if not self.command.strip():
                raise ValueError("stdio MCP servers require a command")
            if self.url.strip() or self.headers:
                raise ValueError("stdio MCP servers do not accept url/headers")
            if self.auth is not None:
                raise ValueError("stdio MCP servers do not accept auth (OAuth is HTTP-only)")
            return self

        if not self.url.strip():
            raise ValueError(f"{transport} MCP servers require a url")
        if self.command.strip() or self.args or self.env:
            raise ValueError(f"{transport} MCP servers do not accept command/args/env")

        if self.auth is not None:
            # The OAuth provider owns the runtime Authorization header; a
            # hand-set static header alongside it is always a config error.
            if self.headers:
                raise ValueError(
                    "MCP servers using auth must not also set static headers "
                    "(the OAuth provider owns the Authorization header)"
                )
            # A refresh token must never traverse cleartext.
            if not self.url.strip().lower().startswith("https://"):
                raise ValueError("OAuth MCP servers require an https url")
        return self


class MCPServerConfigOverride(ConfigBase):
    """Partial MCP server override used for runtime config layering."""

    type: Literal["stdio", "sse", "streamableHttp"] | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    auth: MCPOAuthConfig | None = None
    tool_timeout: float | None = Field(default=None, ge=0.1)
    init_timeout: float | None = Field(default=None, ge=0.1)
    enabled_tools: list[str] | None = None


class AgentConfig(ConfigBase):
    """Top-level structured agent config."""

    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_live_broker_servers(self) -> "AgentConfig":
        """Reject wildcard allowlists on live-broker MCP server entries.

        A live-broker channel places real orders, so a wildcard
        ``enabled_tools`` of ``["*"]`` — which would re-admit every WRITE/UNKNOWN
        tool — is a config error. Live channels must pin an explicit read-only
        allowlist. A server is a live broker by config key OR by URL host
        (:func:`is_live_broker_entry`), so a Robinhood URL parked under an
        aliased key (e.g. ``rh``) cannot dodge this rejection. The server key is
        only known at this top-level scope, which is why the check lives here
        rather than on :class:`MCPServerConfig`.

        Returns:
            The validated agent config instance.

        Raises:
            ValueError: If a live-broker server entry uses ``["*"]``.
        """
        for server_key, server in self.mcp_servers.items():
            if is_live_broker_entry(server_key, server) and "*" in server.enabled_tools:
                if _allows_readonly_wildcard_probe(server_key, server):
                    continue
                broker = live_broker_key_for_entry(server_key, server)
                if broker == "robinhood":
                    detail = (
                        f"{LIVE_BROKER_WILDCARD_ALLOWLIST_ERROR}. "
                        f"{format_robinhood_mcp_config_guidance(reason='wildcard')}"
                    )
                else:
                    detail = LIVE_BROKER_WILDCARD_ALLOWLIST_ERROR
                raise ValueError(
                    f"Live-broker MCP server '{server_key}' may not use a wildcard {detail}"
                )
        return self


class AgentConfigOverride(ConfigBase):
    """Partial top-level config override used for runtime layering."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        # Load-bearing: SessionService passes the entire session.config dict
        # (which carries unrelated keys like include_shell_tools) through
        # merge_agent_config_overrides.  Flipping this back to "forbid" makes
        # any such payload raise ValidationError and silently drops the whole
        # override, including any valid mcpServers.  Regression test:
        # tests/test_agent_config.py::
        #   test_runtime_load_preserves_mcp_servers_when_opted_in_with_unknown_keys
        extra="ignore",
    )

    mcp_servers: dict[str, MCPServerConfigOverride] = Field(default_factory=dict)
