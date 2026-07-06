"""M4 — SWARM external MCP tools: end-to-end worker integration tests.

Covers requirements R-04, R-07, R-10 and tests T-12, T-13, T-14, T-15 in
``docs/2026-05-25_swarm_mcp_tools_tdd.md``. M4 is the milestone that makes
the contract from M1+M2+M3 *visible to the operator at run time*: a worker
that calls a remote MCP tool emits ``tool_call`` / ``tool_result`` events
carrying ``server`` and ``remote_tool`` fields, sensitive arguments stay
redacted, and a transport failure on one tool call does not crash the
worker — it surfaces an error envelope to the LLM and execution continues.

Per the TDD's "Test Plan" preface, we **do not** mock the MCP wire
protocol. Instead we drive a real :class:`MCPServerAdapter` with the
existing ``_FakeClient``-style factory used in
``tests/test_mcp_client_adapter.py`` and ``tests/test_registry_mcp_integration.py``.
That keeps the ``MCPRemoteTool`` wrapper, schema normalization, and
adapter error path on the hot path. ``ChatLLM`` is the only thing
stubbed — :func:`run_worker` doesn't need a real LLM to exercise the
event-emit / tool-execution / report-write contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastmcp.client.client import CallToolResult
from mcp import types as mcp_types

from src.config.schema import MCPServerConfig
from src.providers.chat import LLMResponse, ToolCallRequest
from src.swarm.models import SwarmAgentSpec, SwarmEvent, SwarmTask
from src.swarm.worker import run_worker
from src.tools.mcp import build_mcp_tool_wrappers


# --------------------------------------------------------------------------- #
# Fakes — fake MCP transport + scripted ChatLLM
# --------------------------------------------------------------------------- #


class _FakeMCPClient:
    """In-process MCP client that satisfies the ``AsyncMCPClient`` protocol.

    Mirrors ``tests/test_mcp_client_adapter.py::_FakeClient`` so we can drop
    it into a real :class:`MCPServerAdapter` via ``client_factory=`` and
    exercise the real wrapper without reaching for stdio.
    """

    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    async def __aenter__(self) -> "_FakeMCPClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool | None:
        return None

    async def list_tools(self) -> list[mcp_types.Tool]:
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
        self._state["call_records"].append(
            {"name": name, "arguments": arguments or {}, "timeout": timeout}
        )
        outcome = self._state["call_outcomes"].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _make_state(
    *,
    list_outcomes: list,
    call_outcomes: list,
) -> dict[str, Any]:
    return {
        "list_outcomes": list_outcomes,
        "call_outcomes": call_outcomes,
        "call_records": [],
    }


def _make_factory(state: dict[str, Any]):
    def _factory() -> _FakeMCPClient:
        return _FakeMCPClient(state)

    return _factory


def _make_server_config(*, enabled_tools=None) -> MCPServerConfig:
    return MCPServerConfig.model_validate(
        {
            "command": "uvx",
            "args": ["fake-server"],
            "enabledTools": enabled_tools or ["*"],
            "toolTimeout": 7,
        }
    )


def _ok_call_result(payload: dict[str, Any]) -> CallToolResult:
    """Build a CallToolResult that mimics a successful remote call.

    The adapter's normalizer copies ``data`` / ``structured_content`` /
    text content into the JSON envelope returned to the agent loop. We
    populate ``data`` so the caller can read it back as ``payload["data"]``.
    """
    return CallToolResult(content=[], structured_content=payload, meta=None, data=payload)


class _StubChatLLM:
    """Scripted replacement for :class:`ChatLLM`.

    Each ``stream_chat`` call returns the next item from ``responses`` so
    a test can drive the worker through a precise tool-call sequence.
    """

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self.tool_defs_seen: list[list[dict] | None] = []

    def __call__(self, *args, **kwargs):  # pragma: no cover — supports ChatLLM(model_name=...)
        return self

    def stream_chat(self, messages, tools=None, on_text_chunk=None, timeout=None):
        self.tool_defs_seen.append(tools)
        if not self._responses:
            return LLMResponse(content="(stub exhausted)", finish_reason="stop")
        return self._responses.pop(0)

    def chat(self, messages, tools=None, timeout=None):  # pragma: no cover — fallback path
        return self.stream_chat(messages, tools=tools)


def _stub_llm_factory(responses: list[LLMResponse]):
    """Build a callable that reads as ``ChatLLM(model_name=...)`` would.

    The worker does ``llm = ChatLLM(model_name=...)`` once per run; we
    swap that constructor with a callable returning a single shared
    stub so the test can introspect the recorded ``tool_defs_seen``.
    """
    stub = _StubChatLLM(responses)

    def _factory(model_name=None):
        return stub

    _factory.stub = stub  # type: ignore[attr-defined]
    return _factory


# --------------------------------------------------------------------------- #
# Builders — agent specs, tasks, single-call response sequences
# --------------------------------------------------------------------------- #


def _agent_spec(
    *,
    agent_id: str,
    tools: list[str],
    max_iterations: int = 4,
) -> SwarmAgentSpec:
    return SwarmAgentSpec(
        id=agent_id,
        role="Test analyst",
        system_prompt="You analyse markets.",
        tools=tools,
        skills=[],
        max_iterations=max_iterations,
        timeout_seconds=60,
    )


def _task(*, task_id: str, agent_id: str, prompt: str = "Run the tool.") -> SwarmTask:
    return SwarmTask(id=task_id, agent_id=agent_id, prompt_template=prompt)


def _tool_call_response(
    *,
    call_id: str,
    tool: str,
    arguments: dict[str, Any],
) -> LLMResponse:
    return LLMResponse(
        content=None,
        tool_calls=[ToolCallRequest(id=call_id, name=tool, arguments=arguments)],
        finish_reason="tool_calls",
    )


def _final_response(content: str = "Done.") -> LLMResponse:
    return LLMResponse(content=content, tool_calls=[], finish_reason="stop")


# --------------------------------------------------------------------------- #
# T-12 — happy path: 1 agent / 1 task / 1 fake server.
#                    The worker invokes a remote MCP tool, then writes
#                    report.md whose body cites the canned remote payload.
# --------------------------------------------------------------------------- #


def test_run_worker_uses_remote_mcp_tool_and_report_cites_canned_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A run_worker call against a fake MCP server returns a report.md whose
    text comes from the remote tool's payload. This is the smallest possible
    proof that the wiring (M1 plumbing → M2 registry → M4 events) actually
    routes data from a remote MCP server through the worker into the agent's
    deliverable. Maps to T-12 and the R-04 audit-trail requirement.
    """
    # write_file's path sandbox limits run_dir to a known set of roots.
    # ``tmp_path`` is a pytest scratch dir outside those defaults; whitelist
    # it for the duration of this test so the real write_file tool can run.
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_RUN_ROOTS", str(tmp_path))

    canned_payload = {"answer": "Bullish per fake KB", "source": "fake_kb"}
    state = _make_state(
        list_outcomes=[[
            mcp_types.Tool(
                name="search",
                description="Knowledge-base search",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            )
        ]],
        call_outcomes=[_ok_call_result(canned_payload)],
    )
    remote_tools = build_mcp_tool_wrappers(
        "kb",
        _make_server_config(),
        client_factory=_make_factory(state),
    )

    # Simulate two LLM turns: first one calls the remote tool, second writes
    # report.md using the (real) write_file tool, third returns final text.
    report_body = (
        f"# Findings\n\nRemote KB says: {canned_payload['answer']}.\n"
    )
    responses = [
        _tool_call_response(
            call_id="tc-1",
            tool="mcp_kb_search",
            arguments={"query": "AAPL outlook"},
        ),
        _tool_call_response(
            call_id="tc-2",
            tool="write_file",
            arguments={"path": "report.md", "content": report_body},
        ),
        _final_response("Wrote report.md with KB-cited findings."),
    ]
    llm_factory = _stub_llm_factory(responses)

    events: list[SwarmEvent] = []

    with (
        patch(
            "src.swarm.worker.build_swarm_registry",
            wraps=lambda tool_names, *, agent_config=None, include_shell_tools=False: _registry_with_remote(
                tool_names,
                remote_tools,
                include_shell_tools=include_shell_tools,
            ),
        ),
        patch("src.swarm.worker.ChatLLM", llm_factory),
    ):
        result = run_worker(
            agent_spec=_agent_spec(
                agent_id="kb_analyst",
                tools=["mcp_kb_search", "write_file"],
                max_iterations=5,
            ),
            task=_task(task_id="t1", agent_id="kb_analyst"),
            upstream_summaries={},
            user_vars={},
            run_dir=tmp_path,
            event_callback=events.append,
        )

    assert result.status == "completed"
    report_path = tmp_path / "artifacts" / "kb_analyst" / "report.md"
    assert report_path.is_file()
    contents = report_path.read_text(encoding="utf-8")
    assert canned_payload["answer"] in contents
    # report.md was the source of truth for the worker's summary.
    assert canned_payload["answer"] in result.summary

    # The remote MCP server actually got the call — i.e. the registry
    # wired up a real adapter, not a stub that swallows the args.
    assert state["call_records"] == [
        {"name": "search", "arguments": {"query": "AAPL outlook"}, "timeout": 7}
    ]


# --------------------------------------------------------------------------- #
# T-13 — isolation: two agents each whitelist their own server's tool, and
#                   the LLM-visible tool list per agent never leaks the other.
# --------------------------------------------------------------------------- #


def test_two_agents_with_distinct_servers_only_see_their_own_remote_tools(
    tmp_path: Path,
) -> None:
    """Per-agent whitelist isolation persists at the LLM-tools layer.

    When agent A's preset declares ``mcp_alpha_search`` and agent B's
    declares ``mcp_beta_query``, the worker for A must hand the LLM only
    A's tools — never B's. We assert this by introspecting the
    ``tools=`` list captured by the stub LLM on the first iteration.
    Maps to T-13 / S-02.
    """
    alpha_state = _make_state(
        list_outcomes=[[
            mcp_types.Tool(name="search", description="Alpha", inputSchema={"type": "object"}),
        ]],
        call_outcomes=[_ok_call_result({"alpha": True})],
    )
    beta_state = _make_state(
        list_outcomes=[[
            mcp_types.Tool(name="query", description="Beta", inputSchema={"type": "object"}),
        ]],
        call_outcomes=[_ok_call_result({"beta": True})],
    )

    alpha_tools = build_mcp_tool_wrappers(
        "alpha", _make_server_config(), client_factory=_make_factory(alpha_state)
    )
    beta_tools = build_mcp_tool_wrappers(
        "beta", _make_server_config(), client_factory=_make_factory(beta_state)
    )

    def _run_agent(agent_id: str, whitelist: list[str], remote_tools, tool_call: str):
        llm_factory = _stub_llm_factory([
            _tool_call_response(
                call_id="tc-1", tool=tool_call, arguments={"q": "x"},
            ),
            _final_response(),
        ])

        with (
            patch(
                "src.swarm.worker.build_swarm_registry",
                wraps=lambda tool_names, *, agent_config=None, include_shell_tools=False: _registry_with_remote(
                    tool_names, remote_tools, include_shell_tools=include_shell_tools,
                ),
            ),
            patch("src.swarm.worker.ChatLLM", llm_factory),
        ):
            run_worker(
                agent_spec=_agent_spec(agent_id=agent_id, tools=whitelist),
                task=_task(task_id=f"task_{agent_id}", agent_id=agent_id),
                upstream_summaries={},
                user_vars={},
                run_dir=tmp_path,
                event_callback=lambda evt: None,
            )
        return llm_factory.stub  # type: ignore[attr-defined]

    alpha_stub = _run_agent("alpha_agent", ["mcp_alpha_search"], alpha_tools, "mcp_alpha_search")
    beta_stub = _run_agent("beta_agent", ["mcp_beta_query"], beta_tools, "mcp_beta_query")

    alpha_first_call_tools = _tool_names(alpha_stub.tool_defs_seen[0])
    beta_first_call_tools = _tool_names(beta_stub.tool_defs_seen[0])

    assert "mcp_alpha_search" in alpha_first_call_tools
    assert "mcp_beta_query" not in alpha_first_call_tools
    assert "mcp_beta_query" in beta_first_call_tools
    assert "mcp_alpha_search" not in beta_first_call_tools


# --------------------------------------------------------------------------- #
# T-14 — events.jsonl carries server/remote_tool fields and redacts secrets.
# --------------------------------------------------------------------------- #


def test_tool_call_events_carry_mcp_metadata_and_redact_sensitive_arguments(
    tmp_path: Path,
) -> None:
    """Auditing :file:`events.jsonl` after a run must show *which remote
    server* a tool call hit (``server``), the original remote tool name
    (``remote_tool``), AND it must not leak ``api_key`` / ``token`` /
    ``password`` argument values into the recorded preview. Maps to
    R-04 + R-10.
    """
    state = _make_state(
        list_outcomes=[[
            mcp_types.Tool(
                name="search",
                description="Knowledge base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "api_key": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["query"],
                },
            )
        ]],
        call_outcomes=[
            _ok_call_result(
                {
                    "hit": "ok",
                    "token": "result-token-should-not-appear",
                    "nested": {"authorization": "Bearer result-secret"},
                }
            )
        ],
    )
    remote_tools = build_mcp_tool_wrappers(
        "kb", _make_server_config(), client_factory=_make_factory(state)
    )

    responses = [
        _tool_call_response(
            call_id="tc-1",
            tool="mcp_kb_search",
            arguments={
                "query": "AAPL",
                "api_key": "should-not-appear-in-events",
                "token": "also-secret",
                "request": {
                    "headers": {"Authorization": "Bearer nested-secret"},
                    "payload": {"password": "nested-password"},
                },
            },
        ),
        _final_response("done"),
    ]
    llm_factory = _stub_llm_factory(responses)

    events: list[SwarmEvent] = []

    with (
        patch(
            "src.swarm.worker.build_swarm_registry",
            wraps=lambda tool_names, *, agent_config=None, include_shell_tools=False: _registry_with_remote(
                tool_names, remote_tools, include_shell_tools=include_shell_tools,
            ),
        ),
        patch("src.swarm.worker.ChatLLM", llm_factory),
    ):
        run_worker(
            agent_spec=_agent_spec(
                agent_id="kb_analyst", tools=["mcp_kb_search"], max_iterations=3,
            ),
            task=_task(task_id="t1", agent_id="kb_analyst"),
            upstream_summaries={},
            user_vars={},
            run_dir=tmp_path,
            event_callback=events.append,
        )

    tool_calls = [e for e in events if e.type == "tool_call" and e.data.get("tool") == "mcp_kb_search"]
    tool_results = [e for e in events if e.type == "tool_result" and e.data.get("tool") == "mcp_kb_search"]
    assert tool_calls, f"expected an mcp_kb_search tool_call event; got {[e.type for e in events]}"
    assert tool_results, "expected an mcp_kb_search tool_result event"

    call_data = tool_calls[0].data
    result_data = tool_results[0].data

    # R-04: server + remote_tool must appear on both events.
    assert call_data["server"] == "kb"
    assert call_data["remote_tool"] == "search"
    assert result_data["server"] == "kb"
    assert result_data["remote_tool"] == "search"

    # R-10: redaction is applied to known sensitive keys.
    assert call_data["arguments"]["api_key"] == "[redacted]"
    assert call_data["arguments"]["token"] == "[redacted]"
    assert call_data["arguments"]["query"] == "AAPL"
    assert "nested-secret" not in call_data["arguments"]["request"]
    assert "nested-password" not in call_data["arguments"]["request"]
    assert "result-token-should-not-appear" not in result_data["result_preview"]
    assert "result-secret" not in result_data["result_preview"]
    # Defense-in-depth: the secret values must never appear anywhere in
    # the event payload (including via str-coerced views).
    serialized = json.dumps([e.data for e in events], ensure_ascii=False)
    assert "should-not-appear-in-events" not in serialized
    assert "also-secret" not in serialized
    assert "nested-secret" not in serialized
    assert "nested-password" not in serialized
    assert "result-token-should-not-appear" not in serialized
    assert "result-secret" not in serialized


# --------------------------------------------------------------------------- #
# T-15 — failure mode: a remote tool transport failure must not crash the
#                       worker; the LLM sees an error envelope and the worker
#                       continues to a clean completion.
# --------------------------------------------------------------------------- #


def test_remote_tool_transport_failure_does_not_crash_worker(tmp_path: Path) -> None:
    """Per S-07 / R-07, a transport-level failure on a remote MCP call must
    surface as an error envelope to the LLM (so the LLM can decide whether
    to retry or fall back) — it must NOT bubble up as an exception that
    fails the whole worker. The worker continues with the next iteration
    and ends in a normal completion state.
    """
    state = _make_state(
        list_outcomes=[[
            mcp_types.Tool(name="search", description="KB", inputSchema={"type": "object"}),
        ]],
        call_outcomes=[TimeoutError("simulated remote stall")],
    )
    remote_tools = build_mcp_tool_wrappers(
        "kb", _make_server_config(), client_factory=_make_factory(state)
    )

    responses = [
        _tool_call_response(
            call_id="tc-1", tool="mcp_kb_search", arguments={"query": "x"},
        ),
        _final_response("Tool call failed; falling back to qualitative analysis."),
    ]
    llm_factory = _stub_llm_factory(responses)

    events: list[SwarmEvent] = []

    with (
        patch(
            "src.swarm.worker.build_swarm_registry",
            wraps=lambda tool_names, *, agent_config=None, include_shell_tools=False: _registry_with_remote(
                tool_names, remote_tools, include_shell_tools=include_shell_tools,
            ),
        ),
        patch("src.swarm.worker.ChatLLM", llm_factory),
    ):
        result = run_worker(
            agent_spec=_agent_spec(
                agent_id="kb_analyst", tools=["mcp_kb_search"], max_iterations=3,
            ),
            task=_task(task_id="t1", agent_id="kb_analyst"),
            upstream_summaries={},
            user_vars={},
            run_dir=tmp_path,
            event_callback=events.append,
        )

    # The worker did NOT crash; it returned a status that lets the
    # runtime decide whether to mark the task complete or retry.
    assert result.status in {"completed", "incomplete"}
    # The fake adapter actually saw the call (we routed through the real
    # MCPRemoteTool wrapper, not a stubbed-out path that swallows it).
    assert state["call_records"] and state["call_records"][0]["name"] == "search"

    # The LLM observed the error envelope on its second turn so it could
    # decide what to do next. ``stream_chat`` was called twice: once to
    # produce the tool call and once to produce the final text.
    assert len(llm_factory.stub.tool_defs_seen) >= 2  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _registry_with_remote(
    tool_names: list[str],
    remote_tools,
    *,
    include_shell_tools: bool = False,
):
    """Build a swarm registry that exposes the given remote tools verbatim.

    Reuses the real :func:`build_swarm_registry` for the local-tool side
    (so e.g. ``write_file`` continues to work end-to-end) and then
    grafts the supplied :class:`MCPRemoteTool` instances on top — but
    only the ones the agent's whitelist actually names. This mirrors
    what the M2 path does in production, just without spinning up a real
    MCP server discovery cycle inside the test.
    """
    from src.tools import build_swarm_registry as _real

    registry = _real(tool_names, agent_config=None, include_shell_tools=include_shell_tools)
    whitelist = set(tool_names)
    for tool in remote_tools:
        if tool.name in whitelist:
            registry.register(tool)
    return registry


def _tool_names(tool_defs: list[dict] | None) -> set[str]:
    """Extract tool names from an OpenAI-format tool-definitions list."""
    if not tool_defs:
        return set()
    names: set[str] = set()
    for entry in tool_defs:
        fn = entry.get("function") if isinstance(entry, dict) else None
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.add(fn["name"])
    return names
