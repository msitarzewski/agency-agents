"""Integration tests: full-stack MCP client path with a real stdio subprocess.

These tests spawn an actual fake MCP server process (agent/tests/fixtures/
fake_mcp_server.py) over stdio and exercise the entire path:

    load_agent_config()
        -> build_registry(agent_config=...)
            -> MCPServerAdapter
                -> StdioTransport (real subprocess)
                    -> remote tool callable from registry

Unlike test_mcp_client_adapter.py which stubs the fastmcp client, these tests
start a real subprocess and verify end-to-end tool discovery + execution.

IMPORTANT — v1 limits exercised here:
  - stdio transport only (no SSE / streamable HTTP)
  - serial execution (is_readonly == False on every remote tool)
  - tools-only exposure (resources / prompts excluded)
  - Swarm path NOT tested (excluded from MCP config propagation in v1)

TODO(v1): Add Swarm-path integration tests once Swarm worker registries are
allowed to load MCP config.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_AGENT_DIR = Path(__file__).resolve().parent.parent
_FIXTURE_SERVER = Path(__file__).resolve().parent / "fixtures" / "fake_mcp_server.py"

# Use the same Python interpreter that is running the tests so the fake server
# has access to the same packages (e.g. fastmcp).
_PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_json(tmp_path: Path, server_name: str, **server_kwargs: Any) -> Path:
    """Write a minimal agent.json config pointing at the fake stdio server.

    Args:
        tmp_path: Temporary directory to place the config file in.
        server_name: Key name for the MCP server entry.
        **server_kwargs: Extra fields merged into the server config object.

    Returns:
        Path to the written config file.
    """
    config: dict[str, Any] = {
        "mcpServers": {
            server_name: {
                "command": _PYTHON,
                "args": [str(_FIXTURE_SERVER)],
                **server_kwargs,
            }
        }
    }
    cfg_path = tmp_path / "agent.json"
    cfg_path.write_text(json.dumps(config))
    return cfg_path


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


def test_remote_tools_appear_in_registry_after_local_tools(tmp_path: Path) -> None:
    """Remote tools injected by MCP config appear in the registry.

    Verifies:
    - Registry contains at least the two fake server tools.
    - Tool names follow the stable mcp_<server>_<tool> convention.
    - Remote tools are positioned after all local tools.
    """
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    cfg_path = _make_agent_json(tmp_path, "fake")
    agent_config = load_agent_config(config_path=cfg_path)

    registry = build_registry(agent_config=agent_config)
    all_names = registry.tool_names

    assert "mcp_fake_echo" in all_names
    assert "mcp_fake_add" in all_names

    # Remote tools must come after all local tools (no MCP name before local tools end).
    first_mcp = next(i for i, name in enumerate(all_names) if name.startswith("mcp_"))
    local_after_first_mcp = [
        name for name in all_names[first_mcp:] if not name.startswith("mcp_")
    ]
    assert local_after_first_mcp == [], (
        "Local tools found after the first MCP tool — ordering guarantee violated"
    )


def test_remote_tool_is_callable_and_returns_expected_result(tmp_path: Path) -> None:
    """The remote echo tool can be called and returns the correct result."""
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    cfg_path = _make_agent_json(tmp_path, "fake")
    agent_config = load_agent_config(config_path=cfg_path)
    registry = build_registry(agent_config=agent_config)

    echo_tool = registry.get("mcp_fake_echo")
    assert echo_tool is not None, "mcp_fake_echo not found in registry"
    result = echo_tool.execute(message="hello")

    # The tool returns a JSON string with the text content.
    # Successful call: the raw return is the text content from the remote tool.
    assert "hello" in result


def test_remote_tool_add_returns_correct_sum(tmp_path: Path) -> None:
    """The remote add tool computes the correct sum."""
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    cfg_path = _make_agent_json(tmp_path, "fake")
    agent_config = load_agent_config(config_path=cfg_path)
    registry = build_registry(agent_config=agent_config)

    add_tool = registry.get("mcp_fake_add")
    assert add_tool is not None, "mcp_fake_add not found in registry"
    result = add_tool.execute(a=3, b=4)

    assert "7" in result


def test_remote_tool_is_serial_only(tmp_path: Path) -> None:
    """Every MCP-injected tool must have is_readonly=False (serial-only).

    v1 design: MCP tools never enter the parallel readonly path.
    """
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    cfg_path = _make_agent_json(tmp_path, "fake")
    agent_config = load_agent_config(config_path=cfg_path)
    registry = build_registry(agent_config=agent_config)

    mcp_tools = [registry.get(n) for n in registry.tool_names if n.startswith("mcp_fake_")]
    assert mcp_tools, "No MCP tools found in registry"
    for tool in mcp_tools:
        assert tool.is_readonly is False, (
            f"Tool {tool.name!r} has is_readonly=True; "
            "MCP tools must be serial-only in v1"
        )


def test_enabled_tools_filter_limits_remote_tools(tmp_path: Path) -> None:
    """enabledTools allowlist restricts which remote tools appear in the registry."""
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    cfg_path = _make_agent_json(tmp_path, "fake", enabledTools=["echo"])
    agent_config = load_agent_config(config_path=cfg_path)
    registry = build_registry(agent_config=agent_config)

    mcp_names = [n for n in registry.tool_names if n.startswith("mcp_fake_")]
    assert "mcp_fake_echo" in mcp_names
    assert "mcp_fake_add" not in mcp_names, (
        "mcp_fake_add should be excluded by enabledTools filter"
    )


def test_broken_server_command_does_not_block_local_tools(tmp_path: Path) -> None:
    """A server with an invalid command must be skipped; local tools still load.

    IMPORTANT: This verifies the safe degradation contract — a misconfigured
    external MCP server must never prevent the agent from using its built-in
    local toolset.
    """
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    config: dict[str, Any] = {
        "mcpServers": {
            "bad-server": {
                "command": "/this/binary/does/not/exist",
                "args": [],
            }
        }
    }
    cfg_path = tmp_path / "agent.json"
    cfg_path.write_text(json.dumps(config))
    agent_config = load_agent_config(config_path=cfg_path)

    # Must not raise even though the server command is invalid.
    warnings: list[str] = []
    registry = build_registry(agent_config=agent_config, warn_callback=warnings.append)

    # Local tools (e.g. list_skills) must still be present.
    local_names = registry.tool_names
    assert any("load_skill" in n or "web_search" in n or "backtest" in n for n in local_names), (
        "Expected at least one well-known local tool to survive a broken MCP server"
    )

    # The operator must receive a warning about the skipped server.
    assert any("bad-server" in w for w in warnings), (
        f"Expected a warning mentioning 'bad-server', got: {warnings}"
    )
