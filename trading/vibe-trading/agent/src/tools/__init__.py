"""Tool registry: auto-discovery via BaseTool.__subclasses__().

Adding a new tool:
  1. Create a file in src/tools/ with a class extending BaseTool
  2. Done. It's automatically discovered and registered.

Tools with missing dependencies can override check_available() → False
to be silently excluded from the registry.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from collections.abc import Mapping
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from src.agent.tools import BaseTool, ToolRegistry

if TYPE_CHECKING:
    from src.config.schema import AgentConfig
    from src.memory.persistent import PersistentMemory

logger = logging.getLogger(__name__)

_SUBCLASSES_CACHE: list[type[BaseTool]] | None = None
_SHELL_TOOL_NAMES = {"bash", "background_run"}


def _discover_subclasses() -> list[type[BaseTool]]:
    """Import all modules in this package, then collect BaseTool subclasses.

    Results are cached after the first call.

    Returns:
        List of concrete BaseTool subclasses with a non-empty name.
    """
    global _SUBCLASSES_CACHE
    if _SUBCLASSES_CACHE is not None:
        return _SUBCLASSES_CACHE

    pkg_dir = str(Path(__file__).parent)
    for _, module_name, _ in pkgutil.iter_modules([pkg_dir]):
        if module_name.startswith("_"):
            continue
        try:
            importlib.import_module(f"src.tools.{module_name}")
        except Exception as exc:
            logger.warning("Skipped src.tools.%s: %s", module_name, exc)

    classes: list[type[BaseTool]] = []
    queue = deque(BaseTool.__subclasses__())
    while queue:
        cls = queue.popleft()
        if cls.name:
            classes.append(cls)
        queue.extend(cls.__subclasses__())

    _SUBCLASSES_CACHE = classes
    return classes


def build_registry(
    *,
    persistent_memory: "PersistentMemory | None" = None,
    include_shell_tools: bool = False,
    agent_config: "AgentConfig | None" = None,
    session_id: str | None = None,
    event_callback: Callable[[str, dict], None] | None = None,
    warn_callback: Callable[[str], None] | None = None,
    interactive: bool | None = None,
    _mcp_server_tool_name_segments: Mapping[str, str] | None = None,
) -> ToolRegistry:
    """Build the tool registry via auto-discovery, optionally enriched with MCP tools.

    Local tools are discovered and registered first. When ``agent_config``
    provides one or more MCP server definitions, remote tools are appended
    after the local tools. Each MCP server is isolated: a failure to connect
    or discover tools for one server emits a warning and skips that server
    without affecting local tools or other MCP servers.

    Args:
        persistent_memory: Shared PersistentMemory instance. Injected into
            tools that need it (e.g. RememberTool) so all tools share one
            instance instead of each creating their own.
        include_shell_tools: Whether to include tools that execute shell
            commands. Local CLI/stdin entry points can enable this; networked
            server entry points should keep it disabled unless explicitly
            opted in.
        agent_config: Optional structured agent config. When provided and
            non-empty, MCP tools are appended to the registry after local
            tool discovery. Pass ``None`` (default) to preserve existing
            behavior with no MCP integration.
        session_id: Optional current session id injected into local tools that
            persist per-session state.
        event_callback: Optional event callback injected into local tools that
            mutate session-scoped state.
        warn_callback: Optional callable invoked with operator-facing warning
            messages. When provided, server-name collision warnings are passed
            to this callback in addition to the standard logger so CLI and
            SessionService can surface them to operators.
        interactive: Whether the session is an interactive TTY. Governs whether
            a live-broker channel with no cached OAuth token is registered: a
            non-interactive run (``serve`` / swarm) skips an unauthorized live
            channel rather than blocking on a browser that cannot open
            (SPEC Transport §4). ``None`` (default) auto-detects via
            ``sys.stdin.isatty()``.

    Returns:
        ToolRegistry containing all available local tools followed by any
        successfully discovered MCP tools.
    """
    from src.tools.goal_tool import (
        AddGoalEvidenceTool,
        GetResearchGoalTool,
        StartResearchGoalTool,
        UpdateResearchGoalStatusTool,
    )
    from src.tools.autopilot_tool import RunResearchAutopilotTool
    from src.tools.remember_tool import RememberTool
    from src.tools.swarm_tool import SwarmTool

    goal_tool_classes = {
        StartResearchGoalTool,
        GetResearchGoalTool,
        AddGoalEvidenceTool,
        UpdateResearchGoalStatusTool,
    }
    # Tools that need the host session id injected: they create or mutate the
    # session's research goal, and the LLM never knows the session id.
    session_injected_classes = goal_tool_classes | {RunResearchAutopilotTool}
    registry = ToolRegistry()
    for cls in _discover_subclasses():
        try:
            if cls.name in _SHELL_TOOL_NAMES and not include_shell_tools:
                logger.info("Tool %s disabled by shell tool policy", cls.name)
                continue
            if not cls.check_available():
                logger.info("Tool %s unavailable, skipping", cls.name)
                continue
            if cls is RememberTool and persistent_memory is not None:
                registry.register(cls(memory=persistent_memory))
            elif cls in session_injected_classes:
                registry.register(cls(default_session_id=session_id, event_callback=event_callback))
            elif cls is SwarmTool:
                registry.register(cls(include_shell_tools=include_shell_tools, event_callback=event_callback))
            else:
                registry.register(cls())
        except Exception as exc:
            logger.warning("Failed to register tool %s: %s", cls.name, exc)

    if agent_config and agent_config.mcp_servers:
        from src.tools.mcp import build_mcp_tool_wrappers, resolve_mcp_server_tool_name_segments

        if _mcp_server_tool_name_segments is None:
            local_server_names = resolve_mcp_server_tool_name_segments(
                agent_config.mcp_servers.keys(),
                warn_callback=warn_callback,
            )
        else:
            local_server_names = {
                server_name: _mcp_server_tool_name_segments[server_name]
                for server_name in agent_config.mcp_servers
            }

        if interactive is None:
            import sys

            interactive = sys.stdin.isatty()

        for server_name, server_config in agent_config.mcp_servers.items():
            try:
                # Live brokers (e.g. Robinhood) gate their order-placing tools
                # behind the mandate + kill switch; reads stay plain (read-only).
                # Detection is by config key OR URL host, so a live-broker URL
                # under an aliased key cannot bypass the gate.
                from src.live.registry import (
                    is_live_broker,
                    should_register_live_channel,
                    wrap_live_broker_tools,
                )

                server_url = server_config.url
                live = is_live_broker(server_name, server_url)

                # Headless / no-token: skip an unauthorized live channel rather
                # than block on a browser that can't open (SPEC Transport §4).
                if live:
                    cache_dir = (
                        server_config.auth.cache_dir
                        if server_config.auth is not None
                        else None
                    )
                    if not should_register_live_channel(
                        interactive=interactive, url=server_url, cache_dir=cache_dir
                    ):
                        profile_hint = (
                            "ibkr-live-official-mcp-readonly"
                            if server_name.strip().lower() == "ibkr"
                            else f"{server_name}-live-mcp"
                        )
                        skip_msg = (
                            f"{server_name} live connector configured but not authorized — "
                            f"run `vibe-trading connector authorize {profile_hint}` "
                            f"on a desktop session"
                        )
                        logger.warning(skip_msg)
                        if warn_callback is not None:
                            warn_callback(skip_msg)
                        continue
                    info_msg = (
                        f"{server_name} live connector is available through trading_* tools; "
                        "broker-specific MCP wrappers are hidden from the agent registry"
                    )
                    logger.info(info_msg)
                    if warn_callback is not None:
                        warn_callback(info_msg)
                    continue

                wrappers = build_mcp_tool_wrappers(
                    server_name,
                    server_config,
                    local_server_name=local_server_names[server_name],
                )
                if live:
                    wrappers = wrap_live_broker_tools(
                        server_name, wrappers, url=server_url
                    )
                for tool in wrappers:
                    registry.register(tool)
                logger.info(
                    "Registered %d MCP tool(s) from server '%s'",
                    len(wrappers),
                    server_name,
                )
            except Exception as exc:
                skip_msg = f"MCP server '{server_name}' skipped: {exc}"
                logger.warning("Skipped MCP server '%s': %s", server_name, exc)
                if warn_callback is not None:
                    warn_callback(skip_msg)

    return registry


def build_filtered_registry(tool_names: list[str], *, include_shell_tools: bool = False) -> ToolRegistry:
    """Build a ToolRegistry with only specified tools.

    Local-tools-only filtered builder. Swarm workers should call
    :func:`build_swarm_registry` instead so they can opt into remote MCP
    tools when the operator has configured them. This function is preserved
    for callers that explicitly want the local-only path.

    Args:
        tool_names: Tool names to include.
        include_shell_tools: Whether to include filtered shell execution tools.

    Returns:
        ToolRegistry containing only the requested tools.
    """
    full = build_registry(include_shell_tools=include_shell_tools)
    return _filter_registry(full, tool_names, include_shell_tools=include_shell_tools)


def build_swarm_registry(
    tool_names: list[str],
    *,
    agent_config: "AgentConfig | None" = None,
    include_shell_tools: bool = False,
) -> ToolRegistry:
    """Build a per-worker registry that merges local + remote MCP tools.

    Swarm workers receive a strict whitelist (``agent_spec.tools``). This
    builder honors that whitelist while letting operator-configured MCP
    servers contribute additional tools by name (``mcp_<server>_<tool>``).
    Tools the whitelist requests but the operator has NOT surfaced — either
    because ``agent_config`` is ``None``, the named MCP server is absent, or
    the server's ``enabled_tools`` allowlist excluded it — are dropped with
    an operator-facing warning instead of failing the worker.

    Trust model: ``agent_config`` is resolved at server boot from a static
    file or env var; callers of swarm entry points (e.g. an external MCP
    client driving ``mcp_server.py::run_swarm``) cannot inject MCP server
    URLs through this path.

    Args:
        tool_names: Per-agent tool whitelist from the preset.
        agent_config: Optional resolved agent config. When provided, remote
            MCP wrappers are appended to the candidate pool before filtering.
            Pass ``None`` to keep the worker strictly local.
        include_shell_tools: Whether shell-execution tools are eligible.

    Returns:
        ToolRegistry containing the whitelist intersection of local tools
        and any operator-surfaced MCP tools.
    """
    swarm_agent_config, swarm_local_server_names = _prune_agent_config_for_swarm_tools(
        agent_config,
        tool_names,
    )
    full = build_registry(
        agent_config=swarm_agent_config,
        include_shell_tools=include_shell_tools,
        _mcp_server_tool_name_segments=swarm_local_server_names,
    )
    return _filter_registry(full, tool_names, include_shell_tools=include_shell_tools)


def _prune_agent_config_for_swarm_tools(
    agent_config: "AgentConfig | None",
    tool_names: list[str],
) -> tuple["AgentConfig | None", dict[str, str] | None]:
    """Keep only MCP servers whose local tool prefix appears in ``tool_names``."""
    if not agent_config or not agent_config.mcp_servers:
        return agent_config, None

    requested_mcp_tool_names = [name for name in tool_names if name.startswith("mcp_")]
    if not requested_mcp_tool_names:
        return None, None

    from src.config.schema import AgentConfig
    from src.tools.mcp import resolve_mcp_server_tool_name_segments

    local_server_names = resolve_mcp_server_tool_name_segments(agent_config.mcp_servers.keys())
    selected_servers = {
        server_name: server_config
        for server_name, server_config in agent_config.mcp_servers.items()
        if any(
            tool_name.startswith(f"mcp_{local_server_names[server_name]}_")
            for tool_name in requested_mcp_tool_names
        )
    }
    selected_local_server_names = {
        server_name: local_server_names[server_name]
        for server_name in selected_servers
    }
    return AgentConfig(mcp_servers=selected_servers), selected_local_server_names


def _filter_registry(
    full: ToolRegistry,
    tool_names: list[str],
    *,
    include_shell_tools: bool,
) -> ToolRegistry:
    """Project a full registry down to a whitelist with consistent drop logging."""
    filtered = ToolRegistry()
    for name in tool_names:
        tool = full.get(name)
        if tool:
            filtered.register(tool)
        else:
            logger.warning(
                "Requested tool %r is unavailable and was dropped from the "
                "filtered registry (include_shell_tools=%s); a preset that "
                "depends on it cannot execute it.",
                name, include_shell_tools,
            )
    return filtered


__all__ = ["build_registry", "build_filtered_registry", "build_swarm_registry"]
