"""Unit tests for the MCP client adapter core."""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from fastmcp.client.client import CallToolResult
from fastmcp.exceptions import McpError, ToolError
from mcp import types as mcp_types

from src.config.schema import MCPServerConfig
from src.tools.mcp import (
    MCPServerAdapter,
    build_mcp_tool_wrappers,
    format_mcp_server_name_collision_warning,
    make_mcp_tool_name,
    normalize_mcp_tool_schema,
    resolve_mcp_server_tool_name_segments,
)


class _FakeClient:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool | None:
        return None

    async def list_tools(self) -> list[mcp_types.Tool]:
        self._state["list_calls"] += 1
        outcome = self._state["list_outcomes"].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: float | int | None = None,
        raise_on_error: bool = False,
    ) -> CallToolResult:
        self._state["call_calls"] += 1
        self._state["call_records"].append({
            "name": name,
            "arguments": arguments or {},
            "timeout": timeout,
            "raise_on_error": raise_on_error,
        })
        outcome = self._state["call_outcomes"].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _make_factory(state: dict[str, Any]):
    def _factory() -> _FakeClient:
        return _FakeClient(state)

    return _factory


def _make_config(**overrides: Any) -> MCPServerConfig:
    payload = {
        "command": "uvx",
        "args": ["demo-server"],
        "enabled_tools": ["*"],
        "tool_timeout": 7,
    }
    payload.update(overrides)
    return MCPServerConfig.model_validate(payload)


def test_make_mcp_tool_name_is_stable() -> None:
    assert make_mcp_tool_name("Demo Server", "Price Quote") == "mcp_demo_server_price_quote"


def test_format_mcp_server_name_collision_warning_is_operator_facing() -> None:
    message = format_mcp_server_name_collision_warning("foo-bar", "foo_bar_deadbeef")

    assert message == (
        "Configured MCP server 'foo-bar' collides with another server after local name normalization. "
        "Using local tool prefix 'mcp_foo_bar_deadbeef_<tool>' to keep generated tool names unique. "
        "Rename the server in agent config if you want a different prefix."
    )


def test_resolve_mcp_server_tool_name_segments_disambiguates_collisions_stably() -> None:
    resolved = resolve_mcp_server_tool_name_segments(["foo-bar", "foo_bar", "demo"])
    reversed_resolved = resolve_mcp_server_tool_name_segments(["demo", "foo_bar", "foo-bar"])

    assert resolved["demo"] == "demo"
    assert resolved["foo-bar"].startswith("foo_bar_")
    assert resolved["foo_bar"].startswith("foo_bar_")
    assert resolved["foo-bar"] != resolved["foo_bar"]
    assert resolved["foo-bar"] == reversed_resolved["foo-bar"]
    assert resolved["foo_bar"] == reversed_resolved["foo_bar"]


def test_resolve_mcp_server_tool_name_segments_logs_operator_warning(
    caplog,
) -> None:
    with caplog.at_level(logging.WARNING):
        resolve_mcp_server_tool_name_segments(["foo-bar", "foo_bar"])

    assert any(
        "Using local tool prefix 'mcp_foo_bar_" in record.message
        and "Rename the server in agent config" in record.message
        for record in caplog.records
    )


def test_normalize_mcp_tool_schema_collapses_nullable_object() -> None:
    schema = normalize_mcp_tool_schema(
        {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": ["string", "null"]},
                    },
                    "required": ["symbol"],
                },
                {"type": "null"},
            ]
        }
    )

    assert schema["type"] == "object"
    assert schema["properties"]["symbol"]["type"] == "string"
    assert schema["required"] == ["symbol"]


def test_normalize_mcp_tool_schema_preserves_top_level_one_of_branches() -> None:
    schema = normalize_mcp_tool_schema(
        {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                    "required": ["symbol"],
                },
                {
                    "type": "object",
                    "properties": {"cusip": {"type": "string"}},
                    "required": ["cusip"],
                },
            ]
        }
    )

    assert schema["type"] == "object"
    assert "oneOf" in schema
    assert schema["oneOf"][0]["properties"]["symbol"]["type"] == "string"
    assert schema["oneOf"][1]["properties"]["cusip"]["type"] == "string"


def test_build_mcp_tool_wrappers_filters_enabled_tools() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(name="allowed", description="Allowed", inputSchema={"type": "object"}),
            mcp_types.Tool(name="blocked", description="Blocked", inputSchema={"type": "object"}),
        ]],
        "call_outcomes": [],
    }

    tools = build_mcp_tool_wrappers(
        "demo",
        _make_config(enabled_tools=["allowed"]),
        client_factory=_make_factory(state),
    )

    assert [tool.name for tool in tools] == ["mcp_demo_allowed"]
    assert tools[0].is_readonly is False


def test_build_mcp_tool_wrappers_honors_local_server_name_override() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(name="quote", description="Quote", inputSchema={"type": "object"}),
        ]],
        "call_outcomes": [],
    }

    tools = build_mcp_tool_wrappers(
        "foo-bar",
        _make_config(),
        local_server_name="foo_bar_deadbeef",
        client_factory=_make_factory(state),
    )

    assert [tool.name for tool in tools] == ["mcp_foo_bar_deadbeef_quote"]


def test_remote_tool_execute_does_not_retry_timeout_and_strips_run_dir() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(
                name="quote",
                description="Quote lookup",
                inputSchema={
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                    "required": ["symbol"],
                },
            )
        ]],
        "call_outcomes": [TimeoutError("timed out")],
    }

    tool = build_mcp_tool_wrappers("demo", _make_config(), client_factory=_make_factory(state))[0]

    payload = json.loads(tool.execute(symbol="AAPL", run_dir="/tmp/run"))

    assert payload["status"] == "error"
    assert payload["server"] == "demo"
    assert payload["remote_tool"] == "quote"
    assert payload["tool"] == "mcp_demo_quote"
    assert payload["error"] == "timed out"
    assert state["call_calls"] == 1
    assert state["call_records"][0]["arguments"] == {"symbol": "AAPL"}
    assert state["call_records"][0]["timeout"] == 7
    assert state["call_records"][0]["raise_on_error"] is False


def test_remote_tool_execute_forwards_arguments_for_composed_schema() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(
                name="lookup",
                description="Lookup by symbol or cusip",
                inputSchema={
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {"symbol": {"type": "string"}},
                            "required": ["symbol"],
                        },
                        {
                            "type": "object",
                            "properties": {"cusip": {"type": "string"}},
                            "required": ["cusip"],
                        },
                    ]
                },
            )
        ]],
        "call_outcomes": [
            CallToolResult(content=[], structured_content={"ok": True}, meta=None, data={"ok": True}),
        ],
    }

    tool = build_mcp_tool_wrappers("demo", _make_config(), client_factory=_make_factory(state))[0]

    payload = json.loads(tool.execute(symbol="AAPL", run_dir="/tmp/run"))

    assert payload["status"] == "ok"
    assert state["call_records"][0]["arguments"] == {"symbol": "AAPL"}


def test_build_mcp_tool_wrappers_disambiguates_colliding_local_names() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(name="price-quote", description="Hyphen", inputSchema={"type": "object"}),
            mcp_types.Tool(name="price quote", description="Space", inputSchema={"type": "object"}),
        ]],
        "call_outcomes": [],
    }

    tools = build_mcp_tool_wrappers("demo", _make_config(), client_factory=_make_factory(state))
    names = [tool.name for tool in tools]

    assert names[0] == "mcp_demo_price_quote"
    assert names[1].startswith("mcp_demo_price_quote_")
    assert len(set(names)) == 2


def test_build_mcp_tool_wrappers_retries_transient_discovery_failure() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [
            [McpError(mcp_types.ErrorData(code=mcp_types.CONNECTION_CLOSED, message="Connection closed"))][0],
            [mcp_types.Tool(name="quote", description="Quote", inputSchema={"type": "object"})],
        ],
        "call_outcomes": [],
    }

    tools = build_mcp_tool_wrappers("demo", _make_config(), client_factory=_make_factory(state))

    assert [tool.name for tool in tools] == ["mcp_demo_quote"]
    assert state["list_calls"] == 2


def test_build_mcp_tool_wrappers_single_attempt_does_not_retry_discovery() -> None:
    """max_list_tools_attempts=1 (authorize bootstrap) must not retry.

    Regression for #259: a retry opens a fresh client context that starts a
    second OAuth callback server, orphaning the user's in-progress sign-in. The
    authorize path passes max_list_tools_attempts=1 so the first transient
    failure propagates immediately and exactly one client context is opened.
    """
    transient = McpError(
        mcp_types.ErrorData(code=mcp_types.CONNECTION_CLOSED, message="Connection closed")
    )
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [
            transient,
            [mcp_types.Tool(name="quote", description="Quote", inputSchema={"type": "object"})],
        ],
        "call_outcomes": [],
    }

    with pytest.raises(McpError):
        build_mcp_tool_wrappers(
            "demo",
            _make_config(),
            client_factory=_make_factory(state),
            max_list_tools_attempts=1,
        )

    assert state["list_calls"] == 1


def test_remote_tool_execute_returns_normalized_error_payload_without_retry() -> None:
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(name="quote", description="Quote", inputSchema={"type": "object"})
        ]],
        "call_outcomes": [ToolError("validation failed")],
    }

    tool = build_mcp_tool_wrappers("demo", _make_config(), client_factory=_make_factory(state))[0]

    payload = json.loads(tool.execute(symbol="AAPL"))

    assert payload == {
        "status": "error",
        "server": "demo",
        "remote_tool": "quote",
        "tool": "mcp_demo_quote",
        "error": "validation failed",
        "error_type": "ToolError",
    }


def test_build_mcp_tool_wrappers_wildcard_enabled_tools_passes_all() -> None:
    """enabledTools: ["*"] must pass every tool through without filtering."""
    state = {
        "list_calls": 0,
        "call_calls": 0,
        "call_records": [],
        "list_outcomes": [[
            mcp_types.Tool(name="alpha", description="A", inputSchema={"type": "object"}),
            mcp_types.Tool(name="beta", description="B", inputSchema={"type": "object"}),
            mcp_types.Tool(name="gamma", description="C", inputSchema={"type": "object"}),
        ]],
        "call_outcomes": [],
    }

    # enabled_tools=["*"] is the default in _make_config()
    tools = build_mcp_tool_wrappers("demo", _make_config(enabled_tools=["*"]), client_factory=_make_factory(state))

    assert [t.name for t in tools] == [
        "mcp_demo_alpha",
        "mcp_demo_beta",
        "mcp_demo_gamma",
    ]


def test_normalize_mcp_tool_schema_strips_null_from_any_of_branches() -> None:
    """anyOf with a null-only branch should have that branch removed."""
    schema = normalize_mcp_tool_schema(
        {
            "type": "object",
            "properties": {
                "value": {
                    "anyOf": [
                        {"type": "integer"},
                        {"type": "null"},
                    ]
                }
            },
        }
    )

    # The null branch in the anyOf must be stripped.
    value_schema = schema["properties"]["value"]
    any_of_branches = value_schema["anyOf"]
    assert all(branch != {"type": "null"} for branch in any_of_branches)
    assert {"type": "integer"} in any_of_branches


def test_normalize_mcp_tool_schema_collapses_nested_type_list_with_null() -> None:
    """type: ["string", "null"] at any nesting level must collapse to type: "string"."""
    schema = normalize_mcp_tool_schema(
        {
            "type": "object",
            "properties": {
                "label": {"type": ["string", "null"]},
            },
        }
    )

    assert schema["properties"]["label"]["type"] == "string"


def test_build_client_uses_stdio_transport(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class _DummyClient:
        pass

    def _fake_stdio_transport(**kwargs: Any) -> object:
        captured["transport"] = "stdio"
        captured["transport_kwargs"] = kwargs
        return object()

    def _fake_client(transport: object, **kwargs: Any) -> _DummyClient:
        captured["client_transport"] = transport
        captured["client_kwargs"] = kwargs
        return _DummyClient()

    monkeypatch.setattr("src.tools.mcp.StdioTransport", _fake_stdio_transport)
    monkeypatch.setattr("src.tools.mcp.Client", _fake_client)

    adapter = MCPServerAdapter("demo", _make_config(command="uvx", args=["demo-server"]))
    adapter._build_client()

    assert captured["transport"] == "stdio"
    assert captured["transport_kwargs"]["command"] == "uvx"
    assert captured["transport_kwargs"]["args"] == ["demo-server"]


def test_build_client_uses_sse_transport(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class _DummyClient:
        pass

    def _fake_sse_transport(**kwargs: Any) -> object:
        captured["transport"] = "sse"
        captured["transport_kwargs"] = kwargs
        return object()

    def _fake_client(transport: object, **kwargs: Any) -> _DummyClient:
        captured["client_transport"] = transport
        captured["client_kwargs"] = kwargs
        return _DummyClient()

    monkeypatch.setattr("src.tools.mcp.SSETransport", _fake_sse_transport)
    monkeypatch.setattr("src.tools.mcp.Client", _fake_client)

    adapter = MCPServerAdapter(
        "demo",
        _make_config(type="sse", command="", args=[], url="http://localhost:8900/sse", headers={"X-Test": "1"}),
    )
    adapter._build_client()

    assert captured["transport"] == "sse"
    assert captured["transport_kwargs"]["url"] == "http://localhost:8900/sse"
    assert captured["transport_kwargs"]["headers"] == {"X-Test": "1"}


def test_build_client_uses_streamable_http_transport(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class _DummyClient:
        pass

    def _fake_http_transport(**kwargs: Any) -> object:
        captured["transport"] = "streamableHttp"
        captured["transport_kwargs"] = kwargs
        return object()

    def _fake_client(transport: object, **kwargs: Any) -> _DummyClient:
        captured["client_transport"] = transport
        captured["client_kwargs"] = kwargs
        return _DummyClient()

    monkeypatch.setattr("src.tools.mcp.StreamableHttpTransport", _fake_http_transport)
    monkeypatch.setattr("src.tools.mcp.Client", _fake_client)

    adapter = MCPServerAdapter(
        "demo",
        _make_config(type="streamableHttp", command="", args=[], url="http://localhost:8900/mcp"),
    )
    adapter._build_client()

    assert captured["transport"] == "streamableHttp"
    assert captured["transport_kwargs"]["url"] == "http://localhost:8900/mcp"


def test_build_client_rejects_url_only_config_without_explicit_type() -> None:
    config = _make_config(type="sse", command="", args=[], url="http://localhost:8900/sse")
    config.type = None

    adapter = MCPServerAdapter("demo", config)

    with pytest.raises(ValueError, match="explicit type"):
        adapter._build_client()
