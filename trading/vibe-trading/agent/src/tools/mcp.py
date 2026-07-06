"""MCP client adapter and remote tool wrappers."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import threading
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Coroutine, Iterable, Protocol, TypeVar

from fastmcp.client import Client
from fastmcp.client.auth import OAuth
from fastmcp.client.client import CallToolResult
from fastmcp.client.transports.http import StreamableHttpTransport
from fastmcp.client.transports.sse import SSETransport
from fastmcp.client.transports.stdio import StdioTransport
from fastmcp.exceptions import McpError, ToolError
from key_value.aio.stores.filetree import FileTreeStore, FileTreeV1KeySanitizationStrategy
from mcp import types as mcp_types

from src.agent.tools import BaseTool
from src.config.schema import (
    ROBINHOOD_AGENT_CONFIG_PATH,
    MCPServerConfig,
    live_broker_key_for_entry,
    robinhood_readonly_enabled_tools,
)

logger = logging.getLogger(__name__)

_NAME_SEGMENT_RE = re.compile(r"[^a-z0-9]+")
_SCHEMA_COMPOSITION_KEYS = ("anyOf", "oneOf", "allOf")
_LOCAL_ONLY_ARGUMENTS = {"run_dir"}
_TRANSIENT_ERROR_TOKENS = (
    "broken pipe",
    "connection closed",
    "connection reset",
    "eof",
    "temporar",
    "timed out",
    "timeout",
    "try again",
    "unavailable",
)

ResultT = TypeVar("ResultT")


class AsyncMCPClient(Protocol):
    """Protocol for async MCP clients used by the adapter."""

    async def __aenter__(self) -> "AsyncMCPClient":
        """Enter the async client context."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
        /,
    ) -> None:
        """Exit the async client context."""
        ...

    async def list_tools(self) -> list[mcp_types.Tool]:
        """List tools exposed by the remote MCP server."""
        ...

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: float | int | None = None,
        raise_on_error: bool = False,
    ) -> CallToolResult:
        """Call a remote MCP tool."""
        ...


ClientFactory = Callable[[], AsyncMCPClient]


@dataclass(frozen=True)
class MCPRemoteToolSpec:
    """Resolved metadata for one remote MCP tool.

    Attributes:
        annotations: Server-asserted MCP tool annotations (``readOnlyHint`` /
            ``destructiveHint`` / etc.), or ``None`` when the server omits them.
            These are advisory hints from a possibly-untrusted server and must
            never be the sole basis for relaxing safety — the live classification
            layer (P1) treats them as one tier behind the curated map.
    """

    server_name: str
    remote_name: str
    local_name: str
    description: str
    parameters: dict[str, Any]
    annotations: mcp_types.ToolAnnotations | None = None


def build_mcp_tool_wrappers(
    server_name: str,
    server_config: MCPServerConfig,
    *,
    local_server_name: str | None = None,
    client_factory: ClientFactory | None = None,
    max_list_tools_attempts: int = 2,
) -> list["MCPRemoteTool"]:
    """Build local tool wrappers for a configured MCP server.

    Args:
        server_name: Logical server name from config.
        server_config: Validated stdio MCP server config.
        local_server_name: Optional local naming override for the server
            portion of generated tool names. This lets registry assembly keep
            tool names stable when multiple raw server names sanitize to the
            same local prefix.
        client_factory: Optional async client factory for tests.
        max_list_tools_attempts: Number of ``list_tools`` attempts during tool
            discovery. Defaults to 2 (one transient retry). Set to 1 for the
            interactive ``connector authorize`` bootstrap, where a retry would
            start a second OAuth callback server and orphan the user's
            in-progress sign-in.

    Returns:
        Local BaseTool wrappers for all enabled remote tools.

    Raises:
        Exception: Propagates discovery failures so callers can decide whether
            to warn, skip, or abort.
    """
    adapter = MCPServerAdapter(
        server_name,
        server_config,
        local_server_name=local_server_name,
        client_factory=client_factory,
        max_list_tools_attempts=max_list_tools_attempts,
    )
    return [MCPRemoteTool(adapter=adapter, spec=spec) for spec in adapter.discover_tools()]


def make_mcp_tool_name(server_name: str, tool_name: str) -> str:
    """Create the stable local tool name for a remote MCP tool.

    Args:
        server_name: Logical MCP server name.
        tool_name: Remote tool name reported by the MCP server.

    Returns:
        Stable local tool name in ``mcp_<server>_<tool>`` format.
    """
    return f"mcp_{_sanitize_name_segment(server_name)}_{_sanitize_name_segment(tool_name)}"


def format_mcp_server_name_collision_warning(server_name: str, local_server_name: str) -> str:
    """Build operator-facing warning text for sanitized server-name collisions.

    Args:
        server_name: Raw MCP server name from config.
        local_server_name: Unique local server-name segment assigned after
            collision disambiguation.

    Returns:
        Warning copy suitable for CLI, SessionService, and logs.
    """
    return (
        f"Configured MCP server '{server_name}' collides with another server after local name normalization. "
        f"Using local tool prefix 'mcp_{local_server_name}_<tool>' to keep generated tool names unique. "
        "Rename the server in agent config if you want a different prefix."
    )


def resolve_mcp_server_tool_name_segments(
    server_names: Iterable[str],
    warn_callback: Callable[[str], None] | None = None,
) -> dict[str, str]:
    """Resolve unique local server-name segments for MCP tool names.

    The first release keeps MCP tool names ASCII-safe by sanitizing server
    names. Different raw server names can therefore collapse to the same local
    segment, such as ``foo-bar`` and ``foo_bar`` both becoming ``foo_bar``.
    When that happens, all members of the colliding group receive a stable hash
    suffix at the server-segment level so local tool names remain unique
    without depending on config order.

    Args:
        server_names: Ordered raw MCP server names from config.
        warn_callback: Optional callable invoked with the operator-facing
            warning message when a server-name collision is detected and
            disambiguated. Receives the same text as ``logger.warning`` so
            callers (CLI, SessionService) can surface it to operators.

    Returns:
        Mapping of raw server names to unique local server-name segments.
    """
    ordered_names = list(server_names)
    base_counts: dict[str, int] = {}
    for server_name in ordered_names:
        base_segment = _sanitize_name_segment(server_name)
        base_counts[base_segment] = base_counts.get(base_segment, 0) + 1

    resolved_segments: dict[str, str] = {}
    used_segments: set[str] = set()
    for server_name in ordered_names:
        base_segment = _sanitize_name_segment(server_name)
        if base_counts[base_segment] == 1 and base_segment not in used_segments:
            resolved_segments[server_name] = base_segment
            used_segments.add(base_segment)
            continue

        unique_segment = _dedupe_server_name_segment(base_segment, server_name, used_segments)
        warning_text = format_mcp_server_name_collision_warning(server_name, unique_segment)
        logger.warning(warning_text)
        if warn_callback is not None:
            warn_callback(warning_text)
        resolved_segments[server_name] = unique_segment
        used_segments.add(unique_segment)

    return resolved_segments


def normalize_mcp_tool_schema(schema: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize remote MCP input schemas into OpenAI-compatible objects.

    Args:
        schema: Raw MCP input schema.

    Returns:
        A JSON Schema object with top-level object semantics and nullable forms
        reduced to non-null branches where possible.
    """
    normalized = _normalize_schema_node(deepcopy(schema) if isinstance(schema, dict) else {})
    normalized = _collapse_nullable_union(normalized)

    if not isinstance(normalized, dict):
        return {"type": "object", "properties": {}, "required": []}

    if _schema_looks_object_like(normalized):
        normalized["type"] = "object"
    else:
        return {"type": "object", "properties": {}, "required": []}

    properties = normalized.get("properties")
    if properties is not None and not isinstance(properties, dict):
        normalized.pop("properties", None)
    elif not isinstance(properties, dict) and not _schema_uses_composed_top_level_rules(normalized):
        normalized["properties"] = {}

    required = normalized.get("required")
    if required is None and not _schema_uses_composed_top_level_rules(normalized):
        normalized["required"] = []
    elif isinstance(required, list):
        normalized["required"] = [item for item in required if isinstance(item, str)]
    elif required is not None:
        normalized.pop("required", None)

    return normalized


def _format_zero_enabled_tools_warning(server_name: str, server_config: MCPServerConfig) -> str:
    """Build a warning when discovery yields no locally enabled tools."""
    enabled_tools = list(getattr(server_config, "enabled_tools", []) or [])
    if "*" in enabled_tools and live_broker_key_for_entry(server_name, server_config) == "robinhood":
        tools = ", ".join(robinhood_readonly_enabled_tools())
        return (
            f"Server '{server_name}' produced 0 enabled tools with wildcard enabledTools ['*']. "
            "Robinhood live MCP must use the safe read-only allowlist "
            f"({tools}); copy the safe seed into {ROBINHOOD_AGENT_CONFIG_PATH}."
        )
    return f"Server '{server_name}' produced 0 enabled tools — check the enabledTools allowlist in agent config."


def _build_token_store(cache_dir: str) -> FileTreeStore:
    """Build a persistent OAuth token store rooted at ``cache_dir``.

    The directory is created (with parents) and locked down to ``0700`` so only
    the owning user can read the cached refresh tokens. ``FileTreeStore`` is a
    pure-stdlib ``AsyncKeyValue`` backend (no ``diskcache`` dependency) and uses
    atomic same-directory temp-file renames for write safety. FastMCP's OAuth
    storage uses raw MCP URLs as logical keys, so key sanitization is enabled to
    keep those URL-shaped keys as filesystem-safe cache-local filenames. The
    collection names stay unchanged because token-presence checks scan FastMCP's
    literal ``mcp-oauth-token`` collection directory.

    Args:
        cache_dir: Token cache directory. A leading ``~`` is expanded.

    Returns:
        A ``FileTreeStore`` rooted at the resolved cache directory.
    """
    from pathlib import Path

    path = Path(cache_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    # 0700: owner-only. Tokens are secrets; no group/other access.
    os.chmod(path, 0o700)
    return FileTreeStore(
        data_directory=path,
        key_sanitization_strategy=FileTreeV1KeySanitizationStrategy(path),
    )


class MCPServerAdapter:
    """Synchronous wrapper around the async FastMCP client."""

    def __init__(
        self,
        server_name: str,
        server_config: MCPServerConfig,
        *,
        local_server_name: str | None = None,
        client_factory: ClientFactory | None = None,
        max_list_tools_attempts: int = 2,
    ) -> None:
        """Initialize the MCP server adapter.

        Args:
            server_name: Logical server name from config.
            server_config: Validated MCP server config.
            local_server_name: Optional local naming override used only for the
                server portion of generated tool names.
            client_factory: Optional async client factory, mainly for tests.
            max_list_tools_attempts: Number of ``list_tools`` attempts (>= 1).
                Defaults to 2 (one transient retry). The authorize bootstrap
                sets this to 1 so a retry cannot start a second OAuth callback
                server and orphan an in-progress sign-in.
        """
        self.server_name = server_name
        self.local_server_name = local_server_name or server_name
        self.server_config = server_config
        self._client_factory = client_factory or self._build_client
        self._list_tools_attempts = max(1, max_list_tools_attempts)

    def discover_tools(self) -> list[MCPRemoteToolSpec]:
        """Discover enabled tools from the remote MCP server.

        Returns:
            Resolved tool specs for enabled remote tools.

        Raises:
            Exception: Propagates discovery failures after retry exhaustion.
        """
        tools = _run_sync(self._list_tools)
        seen_names: dict[str, str] = {}
        specs: list[MCPRemoteToolSpec] = []

        for tool in tools:
            if not _tool_is_enabled(tool.name, self.server_config.enabled_tools):
                continue

            local_name = _dedupe_local_tool_name(
                make_mcp_tool_name(self.local_server_name, tool.name),
                tool.name,
                seen_names,
            )
            specs.append(
                MCPRemoteToolSpec(
                    server_name=self.server_name,
                    remote_name=tool.name,
                    local_name=local_name,
                    description=(tool.description or f"Remote MCP tool {tool.name} from {self.server_name}."),
                    parameters=normalize_mcp_tool_schema(getattr(tool, "inputSchema", None)),
                    annotations=getattr(tool, "annotations", None),
                )
            )

        if not specs:
            logger.warning(_format_zero_enabled_tools_warning(self.server_name, self.server_config))

        return specs

    def call_tool(
        self,
        remote_name: str,
        arguments: dict[str, Any],
        *,
        local_name: str | None = None,
    ) -> dict[str, Any]:
        """Call one remote MCP tool and normalize its result.

        Args:
            remote_name: Remote tool identifier.
            arguments: Tool arguments to forward.
            local_name: Optional local wrapper name for logging/payloads.

        Returns:
            Normalized result payload ready for JSON serialization.
        """
        try:
            result = _run_sync(lambda: self._call_tool(remote_name, arguments))
            payload = _normalize_call_tool_result(result)
            payload.update({
                "server": self.server_name,
                "remote_tool": remote_name,
                "tool": local_name or remote_name,
            })
            return payload
        except Exception as exc:
            return {
                "status": "error",
                "server": self.server_name,
                "remote_tool": remote_name,
                "tool": local_name or remote_name,
                "error": _format_exception_message(exc),
                "error_type": type(exc).__name__,
            }

    def _build_client(self) -> AsyncMCPClient:
        """Create the default FastMCP client from MCP transport config.

        Returns:
            Configured async FastMCP client.
        """
        transport_type = self.server_config.resolved_transport()

        if transport_type == "stdio":
            env = os.environ.copy()
            env.update(self.server_config.env)
            transport = StdioTransport(
                command=self.server_config.command,
                args=list(self.server_config.args),
                env=env,
                keep_alive=False,
            )
        elif transport_type == "sse":
            transport = SSETransport(
                url=self.server_config.url,
                headers=dict(self.server_config.headers) or None,
            )
        else:
            auth = None
            if self.server_config.auth is not None:
                oauth_config = self.server_config.auth
                # `mcp_url` is intentionally omitted — StreamableHttpTransport
                # calls `auth._bind(self.url)` so the URL fills in from the
                # transport. Token cache is persistent (FileTreeStore), so the
                # channel stays authorized across CLI invocations and refresh is
                # handled inside the MCP lib's OAuthClientProvider.
                auth = OAuth(
                    scopes=list(oauth_config.scopes) or None,
                    client_name=oauth_config.client_name,
                    token_storage=_build_token_store(oauth_config.cache_dir),
                    callback_port=oauth_config.callback_port,
                    client_id=oauth_config.client_id,
                    client_secret=oauth_config.client_secret,
                    client_metadata_url=oauth_config.client_metadata_url,
                )
            transport = StreamableHttpTransport(
                url=self.server_config.url,
                headers=dict(self.server_config.headers) or None,
                auth=auth,
            )

        # Use a minimum of 30 s for init_timeout so cold-start servers (pip
        # install, docker pull, slow imports) do not trip the same short
        # deadline as a per-call tool_timeout. OAuth-heavy servers may set an
        # explicit init_timeout without widening ordinary tool-call timeout.
        init_timeout = (
            self.server_config.init_timeout
            if self.server_config.init_timeout is not None
            else max(self.server_config.tool_timeout, 30.0)
        )
        return Client(
            transport,
            name=self.server_name,
            timeout=self.server_config.tool_timeout,
            init_timeout=init_timeout,
        )

    async def _list_tools(self) -> list[mcp_types.Tool]:
        """List remote tools, retrying once on transient failures by default.

        The number of attempts is governed by ``self._list_tools_attempts``
        (1 disables the retry, used by the authorize bootstrap).

        Returns:
            Remote MCP tool definitions.

        Raises:
            Exception: Propagates non-transient or exhausted failures.
        """
        return await self._run_with_retry(
            "list_tools",
            self._list_tools_once,
            attempts=self._list_tools_attempts,
        )

    async def _list_tools_once(self) -> list[mcp_types.Tool]:
        """List remote tools without retry handling.

        Returns:
            Remote MCP tool definitions.
        """
        async with self._client_factory() as client:
            return await client.list_tools()

    async def _call_tool(self, remote_name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Call a remote tool with timeout and no automatic retry.

        Args:
            remote_name: Remote tool name.
            arguments: Arguments to forward.

        Returns:
            Parsed FastMCP call result.

        Raises:
            Exception: Propagates non-transient or exhausted failures.
        """
        async def _invoke() -> CallToolResult:
            async with self._client_factory() as client:
                return await client.call_tool(
                    remote_name,
                    arguments=arguments,
                    timeout=self.server_config.tool_timeout,
                    raise_on_error=False,
                )

        # Remote MCP tools are arbitrary and may mutate external state. If a
        # timeout / connection drop happens after the server has already
        # committed the action, retrying here would duplicate the side effect.
        return await _invoke()

    async def _run_with_retry(
        self,
        operation_name: str,
        operation: Callable[[], Awaitable[ResultT]],
        *,
        attempts: int = 2,
    ) -> ResultT:
        """Run an async MCP operation with bounded transient retries.

        Args:
            operation_name: Human-readable operation label.
            operation: Async operation to execute.
            attempts: Maximum attempts (>= 1). Defaults to 2 (one transient
                retry). Pass 1 to disable retry — used by the authorize
                bootstrap, where a retry restarts the OAuth flow.

        Returns:
            Operation result.

        Raises:
            Exception: Re-raises the last failure when retry is not allowed or
                all attempts fail.
        """
        attempts = max(1, attempts)
        for attempt in range(1, attempts + 1):
            try:
                return await operation()
            except Exception as exc:
                if attempt >= attempts or not _is_retryable_error(exc):
                    raise
                logger.warning(
                    "Retrying MCP operation %s for server %s after transient failure: %s",
                    operation_name,
                    self.server_name,
                    exc,
                )


class MCPRemoteTool(BaseTool):
    """BaseTool wrapper for a discovered remote MCP tool."""

    name = ""
    description = ""
    parameters: dict[str, Any]
    repeatable = True
    is_readonly = False

    def __init__(self, adapter: MCPServerAdapter, spec: MCPRemoteToolSpec) -> None:
        """Initialize a remote MCP tool wrapper.

        Args:
            adapter: Adapter used to invoke the remote server.
            spec: Resolved local metadata for the remote tool.
        """
        self._adapter = adapter
        self._spec = spec
        self.name = spec.local_name
        self.description = spec.description
        self.parameters = spec.parameters

    def execute(self, **kwargs: Any) -> str:
        """Execute the remote MCP tool and return normalized JSON.

        Args:
            **kwargs: Tool arguments from the agent loop.

        Returns:
            JSON string with normalized success or error payload.
        """
        payload = self._adapter.call_tool(
            self._spec.remote_name,
            self._filter_arguments(kwargs),
            local_name=self.name,
        )
        return json.dumps(payload, ensure_ascii=False, default=_json_default)

    def _filter_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Drop local-only arguments before forwarding to the remote tool.

        Args:
            arguments: Raw arguments from the local agent loop.

        Returns:
            Filtered arguments compatible with the remote tool schema.
        """
        allowed_keys = _collect_top_level_property_names(self.parameters)
        allow_additional = _schema_allows_additional_top_level_keys(self.parameters)

        if allowed_keys:
            return {
                key: value
                for key, value in arguments.items()
                if key in allowed_keys or (allow_additional and key not in _LOCAL_ONLY_ARGUMENTS)
            }

        if allow_additional:
            return {
                key: value
                for key, value in arguments.items()
                if key not in _LOCAL_ONLY_ARGUMENTS
            }

        return {}


def _run_sync(operation: Callable[[], Coroutine[Any, Any, ResultT]]) -> ResultT:
    """Run an async operation from sync code.

    Args:
        operation: Async callable to execute.

    Returns:
        Result returned by the async callable.

    Raises:
        BaseException: Re-raises exceptions from the async operation.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(operation())

    result: dict[str, ResultT] = {}
    failure: dict[str, BaseException] = {}

    def _runner() -> None:
        try:
            result["value"] = asyncio.run(operation())
        except BaseException as exc:
            failure["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in failure:
        raise failure["error"]
    return result["value"]


def _sanitize_name_segment(value: str) -> str:
    """Normalize a server or tool name segment for stable local naming.

    Args:
        value: Raw server or tool name.

    Returns:
        Lowercase ASCII-safe identifier segment.
    """
    normalized = _NAME_SEGMENT_RE.sub("_", value.strip().lower()).strip("_")
    return normalized or "tool"


def _dedupe_server_name_segment(base_segment: str, server_name: str, used_segments: set[str]) -> str:
    """Disambiguate colliding sanitized server-name segments.

    Args:
        base_segment: Preferred sanitized server-name segment.
        server_name: Raw server name from config.
        used_segments: Already-assigned local server-name segments.

    Returns:
        Unique local server-name segment.
    """
    suffix_source = server_name.encode("utf-8")
    unique_segment = f"{base_segment}_{hashlib.sha1(suffix_source).hexdigest()[:8]}"
    salt = 1
    while unique_segment in used_segments:
        unique_segment = (
            f"{base_segment}_{hashlib.sha1(suffix_source + f':{salt}'.encode('utf-8')).hexdigest()[:8]}"
        )
        salt += 1
    return unique_segment


def _dedupe_local_tool_name(candidate: str, remote_name: str, seen_names: dict[str, str]) -> str:
    """Disambiguate colliding local MCP tool names deterministically.

    Args:
        candidate: Preferred local tool name.
        remote_name: Original remote tool name.
        seen_names: Mapping of assigned local names to remote names.

    Returns:
        Unique local tool name for one server.
    """
    existing_remote = seen_names.get(candidate)
    if existing_remote is None:
        seen_names[candidate] = remote_name
        return candidate
    if existing_remote == remote_name:
        return candidate

    suffix_source = remote_name.encode("utf-8")
    unique_name = f"{candidate}_{hashlib.sha1(suffix_source).hexdigest()[:8]}"
    salt = 1
    while unique_name in seen_names and seen_names[unique_name] != remote_name:
        unique_name = f"{candidate}_{hashlib.sha1(suffix_source + f':{salt}'.encode('utf-8')).hexdigest()[:8]}"
        salt += 1

    logger.warning("Disambiguated MCP tool name collision: %s -> %s", remote_name, unique_name)
    seen_names[unique_name] = remote_name
    return unique_name


def _tool_is_enabled(tool_name: str, enabled_tools: list[str]) -> bool:
    """Check whether a remote tool passes the config allowlist.

    Args:
        tool_name: Remote tool name.
        enabled_tools: Configured allowlist.

    Returns:
        ``True`` when the tool should be exposed locally.
    """
    if not enabled_tools:
        return False
    return "*" in enabled_tools or tool_name in enabled_tools


def _normalize_schema_node(value: Any) -> Any:
    """Recursively normalize nullable JSON Schema fragments.

    Args:
        value: Schema fragment.

    Returns:
        Normalized schema fragment.
    """
    if isinstance(value, dict):
        normalized = {key: _normalize_schema_node(item) for key, item in value.items()}
        normalized_type = normalized.get("type")
        if isinstance(normalized_type, list):
            non_null_types = [item for item in normalized_type if item != "null"]
            if not non_null_types:
                normalized.pop("type", None)
            elif len(non_null_types) == 1:
                normalized["type"] = non_null_types[0]
            else:
                normalized["type"] = non_null_types
        elif normalized_type == "null":
            normalized.pop("type", None)

        for key in ("anyOf", "oneOf"):
            norm_branches = normalized.get(key)
            orig_branches = value.get(key)
            if isinstance(norm_branches, list) and isinstance(orig_branches, list):
                # Check nullness against the *original* branch before recursive
                # normalization strips the "type" key from {"type": "null"} → {}.
                # This preserves Copilot's requirement: {} means "accept anything"
                # in JSON Schema and must NOT be treated as null-only.
                normalized[key] = [
                    nb for nb, ob in zip(norm_branches, orig_branches)
                    if not _is_null_schema(ob)
                ]

        return normalized

    if isinstance(value, list):
        return [_normalize_schema_node(item) for item in value]

    return value


def _collapse_nullable_union(schema: dict[str, Any]) -> dict[str, Any]:
    """Collapse top-level nullable unions when a single non-null branch exists.

    Args:
        schema: Normalized schema.

    Returns:
        Collapsed schema when possible; otherwise the original schema.
    """
    for key in ("anyOf", "oneOf"):
        branches = schema.get(key)
        if isinstance(branches, list) and len(branches) == 1 and isinstance(branches[0], dict):
            merged = dict(schema)
            merged.pop(key, None)
            merged.update(branches[0])
            return merged
    return schema


def _schema_looks_object_like(schema: dict[str, Any]) -> bool:
    """Return whether a schema appears to describe a top-level object."""
    if schema.get("type") == "object":
        return True
    if isinstance(schema.get("properties"), dict):
        return True
    if "additionalProperties" in schema or "patternProperties" in schema or "$ref" in schema:
        return True

    for key in _SCHEMA_COMPOSITION_KEYS:
        branches = schema.get(key)
        if isinstance(branches, list) and any(isinstance(branch, dict) and _schema_looks_object_like(branch) for branch in branches):
            return True

    return False


def _schema_uses_composed_top_level_rules(schema: dict[str, Any]) -> bool:
    """Return whether a schema relies on top-level composition or refs."""
    if "$ref" in schema or "patternProperties" in schema:
        return True
    return any(isinstance(schema.get(key), list) and schema[key] for key in _SCHEMA_COMPOSITION_KEYS)


def _collect_top_level_property_names(schema: dict[str, Any] | None) -> set[str]:
    """Collect top-level property names across composed object schemas."""
    if not isinstance(schema, dict):
        return set()

    names: set[str] = set()
    properties = schema.get("properties")
    if isinstance(properties, dict):
        names.update(key for key in properties if isinstance(key, str))

    for key in _SCHEMA_COMPOSITION_KEYS:
        branches = schema.get(key)
        if isinstance(branches, list):
            for branch in branches:
                names.update(_collect_top_level_property_names(branch))

    return names


def _schema_allows_additional_top_level_keys(schema: dict[str, Any] | None) -> bool:
    """Return whether a schema may accept top-level keys beyond known properties."""
    if not isinstance(schema, dict):
        return False
    if "$ref" in schema:
        return True
    if _schema_keyword_allows_values(schema.get("additionalProperties")):
        return True

    pattern_properties = schema.get("patternProperties")
    if isinstance(pattern_properties, dict) and pattern_properties:
        return True

    for key in _SCHEMA_COMPOSITION_KEYS:
        branches = schema.get(key)
        if isinstance(branches, list) and any(_schema_allows_additional_top_level_keys(branch) for branch in branches):
            return True

    return False


def _schema_keyword_allows_values(value: Any) -> bool:
    """Return whether a schema keyword encodes an open-ended allowance."""
    return value is not None and value is not False


def _is_null_schema(schema: Any) -> bool:
    """Return whether a schema branch represents only ``null``.

    Args:
        schema: Candidate schema branch.

    Returns:
        ``True`` when the branch encodes a null-only schema.
    """
    if not isinstance(schema, dict):
        return False
    branch_type = schema.get("type")
    return branch_type == "null" or branch_type == ["null"]


def _normalize_call_tool_result(result: CallToolResult) -> dict[str, Any]:
    """Convert a FastMCP call result into the local JSON payload shape.

    Args:
        result: Parsed FastMCP tool result.

    Returns:
        Normalized payload with ``status`` plus structured/text content.
    """
    if result.is_error:
        return {
            "status": "error",
            "error": _extract_result_error(result),
        }

    payload: dict[str, Any] = {"status": "ok"}
    if result.data is not None:
        payload["data"] = _make_jsonable(result.data)
    if result.structured_content is not None:
        payload["structured_content"] = _make_jsonable(result.structured_content)
    if result.content:
        payload["content"] = [_make_jsonable(block) for block in result.content]
        text = _extract_text_content(result.content)
        if text:
            payload["text"] = text
    return payload


def _extract_result_error(result: CallToolResult) -> str:
    """Extract a readable error message from a failed MCP result.

    Args:
        result: Failed FastMCP result.

    Returns:
        Human-readable error text.
    """
    text = _extract_text_content(result.content)
    if text:
        return text
    if result.structured_content is not None:
        return _to_display_text(result.structured_content)
    if result.data is not None:
        return _to_display_text(result.data)
    return "Remote MCP tool returned an error"


def _extract_text_content(content: list[Any]) -> str:
    """Join text content blocks from a FastMCP response.

    Args:
        content: Content block list.

    Returns:
        Joined text block content.
    """
    texts: list[str] = []
    for block in content:
        raw = _make_jsonable(block)
        if isinstance(raw, dict) and raw.get("type") == "text" and isinstance(raw.get("text"), str):
            texts.append(raw["text"])
    return "\n".join(texts).strip()


def _is_retryable_error(exc: Exception) -> bool:
    """Determine whether a failure should receive a single retry.

    Args:
        exc: Exception raised by an MCP operation.

    Returns:
        ``True`` for transient timeout/connection failures.
    """
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, BrokenPipeError, ConnectionError, EOFError, OSError)):
        return True

    if isinstance(exc, McpError) and getattr(exc, "error", None) is not None:
        error_code = getattr(exc.error, "code", None)
        if error_code == mcp_types.CONNECTION_CLOSED:
            return True
        message = getattr(exc.error, "message", "")
        return _message_looks_transient(message)

    # ToolError signals a remote business / validation error, not a
    # connection-level transient failure.  Do not retry these.
    if isinstance(exc, ToolError):
        return False

    return _message_looks_transient(str(exc))


def _message_looks_transient(message: str) -> bool:
    """Check whether an exception message looks transient.

    Args:
        message: Exception message.

    Returns:
        ``True`` when the message matches common transient failure markers.
    """
    lowered = message.lower()
    return any(token in lowered for token in _TRANSIENT_ERROR_TOKENS)


def _format_exception_message(exc: Exception) -> str:
    """Render an exception into a user-facing error string.

    Args:
        exc: Exception to format.

    Returns:
        Human-readable error message.
    """
    if isinstance(exc, McpError) and getattr(exc, "error", None) is not None:
        return getattr(exc.error, "message", str(exc))
    return str(exc) or type(exc).__name__


def _make_jsonable(value: Any) -> Any:
    """Convert FastMCP response payloads into JSON-serializable objects.

    Args:
        value: Arbitrary response value.

    Returns:
        JSON-serializable equivalent.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, list):
        return [_make_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _make_jsonable(item) for key, item in value.items()}
    return value


def _json_default(value: Any) -> Any:
    """Fallback serializer used by ``json.dumps``.

    Args:
        value: Value rejected by the standard encoder.

    Returns:
        JSON-serializable representation.
    """
    return _make_jsonable(value)


def _to_display_text(value: Any) -> str:
    """Render structured values into compact human-readable text.

    Args:
        value: Structured response value.

    Returns:
        Human-readable string.
    """
    jsonable = _make_jsonable(value)
    if isinstance(jsonable, str):
        return jsonable
    return json.dumps(jsonable, ensure_ascii=False, sort_keys=True)


__all__ = [
    "MCPRemoteTool",
    "MCPRemoteToolSpec",
    "MCPServerAdapter",
    "build_mcp_tool_wrappers",
    "format_mcp_server_name_collision_warning",
    "make_mcp_tool_name",
    "normalize_mcp_tool_schema",
    "resolve_mcp_server_tool_name_segments",
]
