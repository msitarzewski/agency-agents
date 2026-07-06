"""Integration tests: full-stack streamable HTTP MCP client path with FastMCP.

These tests spawn an actual FastMCP streamable HTTP server process
(agent/tests/fixtures/fake_mcp_streamable_http_server.py) and exercise the
entire path:

    load_agent_config()
        -> build_registry(agent_config=...)
            -> MCPServerAdapter
                -> StreamableHttpTransport (real HTTP subprocess)
                    -> remote tool callable from registry
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.mcp_http_test_helpers import (
    make_single_server_agent_json,
    reserved_local_port,
    running_http_mcp_server_on_random_port,
)

_FIXTURE_SERVER = Path(__file__).resolve().parent / "fixtures" / "fake_mcp_streamable_http_server.py"

HTTP_PATH = "/mcp"

pytestmark = pytest.mark.integration


def _http_url(port: int) -> str:
    return f"http://127.0.0.1:{port}{HTTP_PATH}"


def _make_agent_json(tmp_path: Path, server_name: str, *, port: int, **server_kwargs: Any) -> Path:
    return make_single_server_agent_json(
        tmp_path,
        server_name,
        transport_type="streamableHttp",
        url=_http_url(port),
        **server_kwargs,
    )


def test_remote_streamable_http_tool_appears_in_registry(tmp_path: Path) -> None:
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with running_http_mcp_server_on_random_port(
        _FIXTURE_SERVER,
        service_name="FastMCP streamable HTTP service",
        ready_url_builder=_http_url,
        extra_args_builder=lambda port: ["--port", str(port), "--path", HTTP_PATH],
        ready_statuses={200, 400, 405, 406},
    ) as (_, port):
        cfg_path = _make_agent_json(tmp_path, "fake_http", port=port)
        agent_config = load_agent_config(config_path=cfg_path)
        registry = build_registry(agent_config=agent_config)

        assert "mcp_fake_http_echo" in registry.tool_names


def test_remote_streamable_http_tool_is_callable_and_returns_expected_result(tmp_path: Path) -> None:
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with running_http_mcp_server_on_random_port(
        _FIXTURE_SERVER,
        service_name="FastMCP streamable HTTP service",
        ready_url_builder=_http_url,
        extra_args_builder=lambda port: ["--port", str(port), "--path", HTTP_PATH],
        ready_statuses={200, 400, 405, 406},
    ) as (_, port):
        cfg_path = _make_agent_json(tmp_path, "fake_http", port=port)
        agent_config = load_agent_config(config_path=cfg_path)
        registry = build_registry(agent_config=agent_config)

        echo_tool = registry.get("mcp_fake_http_echo")
        assert echo_tool is not None, "mcp_fake_http_echo not found in registry"

        result = echo_tool.execute(message="hello")
        assert "echo: hello" in result


def test_enabled_tools_filter_limits_remote_streamable_http_tools(tmp_path: Path) -> None:
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with running_http_mcp_server_on_random_port(
        _FIXTURE_SERVER,
        service_name="FastMCP streamable HTTP service",
        ready_url_builder=_http_url,
        extra_args_builder=lambda port: ["--port", str(port), "--path", HTTP_PATH],
        ready_statuses={200, 400, 405, 406},
    ) as (_, port):
        cfg_path = _make_agent_json(tmp_path, "fake_http", port=port, enabledTools=["echo"])
        agent_config = load_agent_config(config_path=cfg_path)
        registry = build_registry(agent_config=agent_config)

        mcp_names = [name for name in registry.tool_names if name.startswith("mcp_fake_http_")]
        assert "mcp_fake_http_echo" in mcp_names
        assert "mcp_fake_http_add" not in mcp_names, (
            "mcp_fake_http_add should be excluded by enabledTools filter"
        )


def test_unreachable_streamable_http_server_does_not_block_local_tools(tmp_path: Path) -> None:
    """An unreachable streamable HTTP server must be skipped with a warning."""
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with reserved_local_port() as unused_port:
        bad_url = f"http://127.0.0.1:{unused_port}{HTTP_PATH}"
        cfg_path = make_single_server_agent_json(
            tmp_path,
            "bad-http",
            transport_type="streamableHttp",
            url=bad_url,
        )
        agent_config = load_agent_config(config_path=cfg_path)

        warnings: list[str] = []
        registry = build_registry(agent_config=agent_config, warn_callback=warnings.append)

        local_names = registry.tool_names
        assert any("load_skill" in name or "web_search" in name or "backtest" in name for name in local_names), (
            "Expected at least one well-known local tool to survive an unreachable HTTP MCP server"
        )

        mcp_names = [name for name in local_names if name.startswith("mcp_")]
        assert mcp_names == []
        assert any("bad-http" in warning for warning in warnings), (
            f"Expected a warning mentioning 'bad-http', got: {warnings}"
        )