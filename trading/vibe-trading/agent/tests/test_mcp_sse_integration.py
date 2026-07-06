"""Integration tests: full-stack SSE MCP client path with a real FastMCP server.

These tests spawn an actual FastMCP SSE server process
(agent/tests/fixtures/fake_mcp_sse_server.py) and exercise the entire path:

    load_agent_config()
        -> build_registry(agent_config=...)
            -> MCPServerAdapter
                -> SSETransport (real HTTP subprocess)
                    -> remote tool callable from registry
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.mcp_http_test_helpers import (
    make_single_server_agent_json,
    running_http_mcp_server_on_random_port,
)

_FIXTURE_SERVER = Path(__file__).resolve().parent / "fixtures" / "fake_mcp_sse_server.py"

pytestmark = pytest.mark.integration


def _sse_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/sse"


def _make_agent_json(tmp_path: Path, server_name: str, *, port: int, **server_kwargs: Any) -> Path:
    return make_single_server_agent_json(
        tmp_path,
        server_name,
        transport_type="sse",
        url=_sse_url(port),
        **server_kwargs,
    )


def test_remote_sse_tool_appears_in_registry(tmp_path: Path) -> None:
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with running_http_mcp_server_on_random_port(
        _FIXTURE_SERVER,
        service_name="FastMCP SSE service",
        ready_url_builder=_sse_url,
        extra_args_builder=lambda port: ["--port", str(port)],
        ready_request_kwargs={"stream": True},
    ) as (_, port):
        cfg_path = _make_agent_json(tmp_path, "fake_sse", port=port)
        agent_config = load_agent_config(config_path=cfg_path)
        registry = build_registry(agent_config=agent_config)

        assert "mcp_fake_sse_echo" in registry.tool_names


def test_remote_sse_tool_is_callable_and_returns_expected_result(tmp_path: Path) -> None:
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with running_http_mcp_server_on_random_port(
        _FIXTURE_SERVER,
        service_name="FastMCP SSE service",
        ready_url_builder=_sse_url,
        extra_args_builder=lambda port: ["--port", str(port)],
        ready_request_kwargs={"stream": True},
    ) as (_, port):
        cfg_path = _make_agent_json(tmp_path, "fake_sse", port=port)
        agent_config = load_agent_config(config_path=cfg_path)
        registry = build_registry(agent_config=agent_config)

        echo_tool = registry.get("mcp_fake_sse_echo")
        assert echo_tool is not None, "mcp_fake_sse_echo not found in registry"

        result = echo_tool.execute(message="hello")
        assert "echo: hello" in result


def test_enabled_tools_filter_limits_remote_sse_tools(tmp_path: Path) -> None:
    from src.config.loader import load_agent_config
    from src.tools import build_registry

    with running_http_mcp_server_on_random_port(
        _FIXTURE_SERVER,
        service_name="FastMCP SSE service",
        ready_url_builder=_sse_url,
        extra_args_builder=lambda port: ["--port", str(port)],
        ready_request_kwargs={"stream": True},
    ) as (_, port):
        cfg_path = _make_agent_json(tmp_path, "fake_sse", port=port, enabledTools=["echo"])
        agent_config = load_agent_config(config_path=cfg_path)
        registry = build_registry(agent_config=agent_config)

        mcp_names = [name for name in registry.tool_names if name.startswith("mcp_fake_sse_")]
        assert "mcp_fake_sse_echo" in mcp_names
        assert "mcp_fake_sse_add" not in mcp_names, (
            "mcp_fake_sse_add should be excluded by enabledTools filter"
        )
