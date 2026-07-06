"""AgentLoop trace integration tests for PR #206 rebase."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest

import src.agent.loop as loop_mod
import src.agent.trace as trace_mod
from src.agent.context import ContextBuilder
from src.agent.loop import AgentLoop
from src.agent.trace import TraceWriter


class _Tool:
    is_readonly = False
    repeatable = True


class _SecretRegistry:
    """Minimal registry returning a JSON result with sensitive fields."""

    _tools: dict[str, Any] = {}

    def get(self, tool_name: str) -> _Tool:
        return _Tool()

    def execute(self, tool_name: str, args: dict[str, Any]) -> str:
        del tool_name, args
        return json.dumps(
            {
                "status": "ok",
                "symbol": "AAPL",
                "authorization": "Bearer secret-token",
                "nested": {"api_key": "secret-key"},
            }
        )


def test_tool_call_trace_redacts_args_and_structured_results(tmp_path: Path) -> None:
    """Persistent trace entries should not store raw credentials/account fields."""
    agent = AgentLoop(
        registry=_SecretRegistry(),  # type: ignore[arg-type]
        llm=SimpleNamespace(),
        max_iterations=1,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    agent.memory.run_dir = str(run_dir)
    trace = TraceWriter(run_dir)
    messages: list[dict[str, Any]] = []
    react_trace: list[dict[str, Any]] = []
    tc = SimpleNamespace(
        id="tc_secret",
        name="secret_tool",
        arguments={
            "symbol": "AAPL",
            "api_key": "raw-secret",
            "nested": {"authorization": "Bearer raw-secret"},
        },
    )

    agent._execute_single(tc, ContextBuilder, messages, trace, react_trace, 1)
    trace.close()

    entries = TraceWriter.read(run_dir, resolve_offloads=True)
    tool_call = next(entry for entry in entries if entry["type"] == "tool_call")
    assert tool_call["args"]["symbol"] == "AAPL"
    assert tool_call["args"]["api_key"] == "[redacted]"
    assert tool_call["args"]["nested"]["authorization"] == "[redacted]"

    tool_result = next(entry for entry in entries if entry["type"] == "tool_result")
    assert "secret-token" not in json.dumps(tool_result)
    assert "secret-key" not in json.dumps(tool_result)
    result_payload = json.loads(tool_result["result"])
    assert result_payload["authorization"] == "[redacted]"
    assert result_payload["nested"]["api_key"] == "[redacted]"
    assert messages[0]["content"].count("secret-token") == 1


class _LongAnswerResponse:
    content = "final answer " * 10
    tool_calls: list[Any] = []
    reasoning_content: str | None = None
    has_tool_calls = False
    usage_metadata: dict[str, int] | None = None


class _LongAnswerLLM:
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _LongAnswerResponse:
        del messages, tools, on_reasoning_chunk
        if on_text_chunk:
            on_text_chunk("final answer ")
        return _LongAnswerResponse()

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _LongAnswerResponse:
        del messages
        return _LongAnswerResponse()


def test_session_trace_uses_session_dir_and_round_trips_long_answer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Session runs aggregate trace.jsonl under sessions/<id> without truncation."""
    monkeypatch.setattr(trace_mod, "TRACE_TEXT_OFFLOAD_THRESHOLD", 16)
    monkeypatch.setattr(loop_mod, "SESSIONS_DIR", tmp_path / "sessions")
    agent = AgentLoop(
        registry=_SecretRegistry(),  # type: ignore[arg-type]
        llm=_LongAnswerLLM(),
        max_iterations=1,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    agent.memory.run_dir = str(run_dir)

    result = agent.run(user_message="hello from session", session_id="sid123")

    assert result["status"] == "success"
    trace_dir = tmp_path / "sessions" / "sid123"
    assert (trace_dir / "trace.jsonl").exists()
    assert not (run_dir / "trace.jsonl").exists()

    unresolved = TraceWriter.read(trace_dir)
    answer = next(entry for entry in unresolved if entry["type"] == "answer")
    assert "content" not in answer
    assert answer["content_size"] == len(result["content"])

    resolved = TraceWriter.read(
        trace_dir,
        resolve_offloads=True,
        resolve_fields={"content", "prompt"},
    )
    answer = next(entry for entry in resolved if entry["type"] == "answer")
    start = next(entry for entry in resolved if entry["type"] == "start")
    assert answer["content"] == result["content"]
    assert start["prompt"] == "hello from session"
