"""Structured agent config loading utilities."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from src.config.paths import get_config_path, get_runtime_root
from src.config.schema import AgentConfig, AgentConfigOverride, MCPServerConfig

logger = logging.getLogger(__name__)

_SWARM_AGENT_CONFIG_ENV_VAR = "VIBE_TRADING_SWARM_AGENT_CONFIG"
_SWARM_AGENT_CONFIG_FILENAME = "swarm-agent.json"
_MAIN_AGENT_FALLBACK_FILENAMES = ("agent.json", "agent.yaml", "agent.yml")

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def load_agent_config(config_path: Path | None = None) -> AgentConfig:
    """Load structured agent config from disk with safe fallback.

    Args:
        config_path: Optional explicit config path. When omitted, the default
            config discovery path is used.

    Returns:
        The validated agent config. Invalid or unreadable config files fall
        back to ``AgentConfig()``.
    """
    path = get_config_path(config_path)

    if not path.exists():
        return AgentConfig()

    try:
        raw = _read_config_file(path)
        return AgentConfig.model_validate(raw)
    except (OSError, ValueError, ValidationError) as exc:
        logger.warning(
            "Failed to load agent config from %s: %s",
            path,
            type(exc).__name__,
        )
        logger.debug("Agent config load error details: %s", exc)
        return AgentConfig()


def merge_agent_config_overrides(
    config: AgentConfig,
    overrides: Mapping[str, Any] | None,
) -> AgentConfig:
    """Merge runtime overrides on top of a base config.

    Overrides are validated against a partial schema first so both snake_case
    and camelCase keys are accepted while only explicitly provided fields
    override the base config.

    Args:
        config: Base agent config loaded from disk or defaults.
        overrides: Runtime overrides, typically from session-level config.

    Returns:
        A new validated config containing the merged result.
    """
    if not overrides:
        return config

    try:
        override_model = AgentConfigOverride.model_validate(dict(overrides))
    except ValidationError as exc:
        logger.warning(
            "Ignoring invalid agent config overrides (%s): %s — using base config",
            type(exc).__name__,
            [str(e["loc"]) for e in exc.errors()],
        )
        return config

    merged = _merge_agent_config_dicts(
        config.model_dump(mode="json"),
        override_model.model_dump(mode="json", exclude_unset=True),
    )
    try:
        return AgentConfig.model_validate(merged)
    except ValidationError as exc:
        logger.warning(
            "Ignoring merged agent config overrides after validation failure (%s): %s — using base config",
            type(exc).__name__,
            [str(e["loc"]) for e in exc.errors()],
        )
        return config


# Keys in session overrides that carry subprocess definitions and therefore
# require operator-level trust rather than API-caller trust.
_SESSION_RESTRICTED_KEYS: frozenset[str] = frozenset({"mcpServers", "mcp_servers"})


def sanitize_session_overrides(overrides: Mapping[str, Any]) -> dict[str, Any]:
    """Strip operator-only keys from API-caller-supplied session overrides.

    ``mcpServers`` / ``mcp_servers`` define subprocess ``command``/``args``/``env``
    and therefore grant execution-level capabilities.  They must originate from
    the operator-controlled config file on disk, not from unauthenticated or
    semi-trusted API callers.  Operators who deliberately want to allow session-
    level MCP injection can set ``ALLOW_SESSION_MCP_SERVERS=1``.

    Args:
        overrides: Raw session config dict received from the API caller.

    Returns:
        A new dict with restricted keys removed (or the original mapping
        converted to dict if the env opt-in is active).
    """
    if os.environ.get("ALLOW_SESSION_MCP_SERVERS", "").strip().lower() in {"1", "true", "yes"}:
        return dict(overrides)

    restricted_present = _SESSION_RESTRICTED_KEYS & overrides.keys()
    if restricted_present:
        logger.warning(
            "Stripped %s from session config overrides: MCP server definitions "
            "require operator-level trust (disk config). "
            "Set ALLOW_SESSION_MCP_SERVERS=1 to allow session-level injection.",
            sorted(restricted_present),
        )
    return {k: v for k, v in overrides.items() if k not in _SESSION_RESTRICTED_KEYS}


def load_runtime_agent_config(
    config_path: Path | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> AgentConfig:
    """Load disk config and apply runtime overrides.

    Args:
        config_path: Optional explicit config file path.
        overrides: Runtime override mapping applied on top of file-based config.

    Returns:
        The merged runtime config.
    """
    config = load_agent_config(config_path)
    return merge_agent_config_overrides(config, overrides)


def _resolve_swarm_agent_config_path(
    *,
    runtime_root: Path | None = None,
) -> Path | None:
    """Pick the operator config the swarm runtime should boot against.

    Resolution order (first hit wins):

    1. ``VIBE_TRADING_SWARM_AGENT_CONFIG`` env var — absolute override hatch
       for CI / sandbox deployments where the runtime root is read-only.
       Returned even if the file does not yet exist; the caller logs &
       degrades gracefully so a misconfigured env var doesn't crash boot.
    2. ``<runtime_root>/swarm-agent.json`` — the swarm-specific operator
       allowlist. Lets the swarm path use a *different* set of MCP servers
       from the main agent without duplicating non-MCP fields.
    3. ``<runtime_root>/{agent.json,agent.yaml,agent.yml}`` — fallback to the
       main agent config so single-config operators don't have to duplicate
       their MCP allowlist.
    4. ``None`` when nothing matches — preserves byte-for-byte legacy
       behaviour where the swarm runs strictly on local tools.

    Trust model: callers of swarm entry points (e.g. an external MCP client
    invoking ``run_swarm``) cannot influence this path — config resolution is
    a boot-time / operator-trusted action.

    Args:
        runtime_root: Override the directory the on-disk lookup uses. Defaults
            to ``~/.vibe-trading``. Tests pass a ``tmp_path`` here to keep
            assertions hermetic.

    Returns:
        The chosen config path, or ``None`` when no candidate is available.
    """
    env_value = os.environ.get(_SWARM_AGENT_CONFIG_ENV_VAR, "").strip()
    if env_value:
        return Path(env_value).expanduser()

    root = runtime_root if runtime_root is not None else get_runtime_root()
    swarm_specific = root / _SWARM_AGENT_CONFIG_FILENAME
    if swarm_specific.exists():
        return swarm_specific

    for fallback in _MAIN_AGENT_FALLBACK_FILENAMES:
        candidate = root / fallback
        if candidate.exists():
            return candidate

    return None


def load_swarm_agent_config(
    *,
    runtime_root: Path | None = None,
) -> AgentConfig:
    """Load the swarm-side AgentConfig using the M3 boot resolution order.

    This is the helper boot wiring (``mcp_server.py``, ``api_server.py``, CLI
    swarm runners, in-process ``swarm_tool``) calls before constructing
    ``SwarmRuntime``. It returns an :class:`AgentConfig` (never ``None``) so
    every caller can pass the result through to ``SwarmRuntime(agent_config=...)``
    without conditional unwrapping. An empty config (``mcp_servers={}``) is
    treated identically to ``agent_config=None`` by ``build_swarm_registry``,
    so the swarm stays strictly local-tool-only when nothing is configured.

    Args:
        runtime_root: Override the directory the on-disk lookup uses. Defaults
            to ``~/.vibe-trading``.

    Returns:
        The validated swarm agent config, or an empty :class:`AgentConfig`
        when no candidate is on disk / the chosen file fails to parse.
    """
    path = _resolve_swarm_agent_config_path(runtime_root=runtime_root)
    if path is None:
        return AgentConfig()
    return load_agent_config(path)


def _read_config_file(path: Path) -> dict[str, Any]:
    """Read a supported config file format into a dictionary.

    Args:
        path: Config file path to decode.

    Returns:
        The decoded config object as a dictionary.

    Raises:
        ValueError: If the file format is unsupported, YAML support is
            unavailable, or the decoded payload is not an object.
    """
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML config is not available because PyYAML is missing")
        data = yaml.safe_load(text) or {}
    else:
        raise ValueError(f"Unsupported config file format: {suffix or '<none>'}")

    if not isinstance(data, dict):
        raise ValueError("Agent config must decode to a JSON/YAML object")
    return data


def _merge_agent_config_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge top-level agent config payloads with MCP-aware server replacement."""
    non_mcp_override = {key: value for key, value in override.items() if key != "mcp_servers"}
    merged = _merge_dicts(base, non_mcp_override)

    override_servers = override.get("mcp_servers")
    if not isinstance(override_servers, dict):
        if "mcp_servers" in override:
            merged["mcp_servers"] = override_servers
        return merged

    merged_servers = dict(base.get("mcp_servers", {}))
    for server_name, server_override in override_servers.items():
        current_server = merged_servers.get(server_name)
        if isinstance(current_server, dict) and isinstance(server_override, dict):
            merged_servers[server_name] = _merge_mcp_server_dicts(current_server, server_override)
        else:
            merged_servers[server_name] = server_override

    merged["mcp_servers"] = merged_servers
    return merged


def _merge_mcp_server_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge one MCP server payload, resetting incompatible transport fields when needed."""
    if _override_switches_transport(base, override):
        return _merge_dicts(_default_mcp_server_payload(base), override)
    return _merge_dicts(base, override)


def _override_switches_transport(base: dict[str, Any], override: dict[str, Any]) -> bool:
    """Return whether a partial override changes the server transport family."""
    override_transport = _resolve_override_transport(override)
    if override_transport is None:
        return False
    base_transport = MCPServerConfig.model_validate(base).resolved_transport()
    return override_transport != base_transport


def _resolve_override_transport(override: dict[str, Any]) -> str | None:
    """Infer transport intent from a partial MCP server override."""
    explicit_type = override.get("type")
    if explicit_type in {"stdio", "sse", "streamableHttp"}:
        return str(explicit_type)
    if any(key in override for key in ("command", "args", "env")):
        return "stdio"
    return None


def _default_mcp_server_payload(base: dict[str, Any]) -> dict[str, Any]:
    """Return a transport-neutral MCP server payload preserving non-transport defaults."""
    enabled_tools = base.get("enabled_tools")
    return {
        "type": None,
        "command": "",
        "args": [],
        "env": {},
        "url": "",
        "headers": {},
        "tool_timeout": base.get("tool_timeout", 30.0),
        "init_timeout": base.get("init_timeout"),
        "enabled_tools": list(enabled_tools) if isinstance(enabled_tools, list) else ["*"],
    }


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two plain dictionaries.

    Args:
        base: Base dictionary.
        override: Override dictionary applied on top of ``base``.

    Returns:
        A merged dictionary where nested mappings are merged recursively and
        scalar values from ``override`` replace those in ``base``.
    """
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(current, value)
        else:
            merged[key] = value
    return merged
