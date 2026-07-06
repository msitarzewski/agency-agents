"""Regression tests for AgentLoop terminal-state result dict (issue #114).

Before the fix, AgentLoop.run() returned a dict missing the `reason` field
on the cancelled and max-iter-failed branches even though state.json on
disk recorded a useful reason. SessionService then surfaced
'Execution failed: unknown' to the chat UI.

These tests exercise both terminal paths with a stubbed LLM so the loop
exits without hitting any real API.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from src.agent.loop import AgentLoop
from src.providers.chat import ProviderStreamError


class _StubLLMResponse:
    """Minimal stand-in for ChatLLM's response object."""

    def __init__(self) -> None:
        self.content = ""
        self.tool_calls: list[Any] = []
        self.reasoning_content: str | None = None
        self.has_tool_calls = False


class _StubLLMNoFinal:
    """LLM stub that always returns an empty answer with no tool calls.

    Triggers the 'pipeline did not complete' branch on the first iteration
    because `final_content` stays empty and no `metrics.csv` is written.
    """

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        return _StubLLMResponse()

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


class _StubLLMWithUsage:
    model_name = "stub-model"

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        response = _StubLLMResponse()
        response.content = "done"
        response.usage_metadata = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
        return response

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


class _StubLLMCancelMidStream:
    """LLM stub that cancels the loop from inside the LLM call.

    Mimics the user pressing the cancel button while waiting on the
    provider; the loop must surface 'cancelled by user' to the UI.
    """

    def __init__(self, agent_ref: "list[AgentLoop]") -> None:
        self._agent_ref = agent_ref

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        # Set _cancelled on the bound agent so the next loop iteration check
        # picks it up.  We still need a valid response so the current
        # iteration completes cleanly.
        self._agent_ref[0]._cancel_event.set()
        return _StubLLMResponse()

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


def _build_agent(llm: Any, max_iter: int = 3, tmp_run_dir: Path | None = None) -> AgentLoop:
    """Build an AgentLoop with a real (but empty) registry and a stub LLM."""
    from src.tools import build_registry
    from src.memory.persistent import PersistentMemory

    pm = PersistentMemory()
    agent = AgentLoop(
        registry=build_registry(persistent_memory=pm, include_shell_tools=False),
        llm=llm,
        event_callback=None,
        max_iterations=max_iter,
        persistent_memory=pm,
    )
    if tmp_run_dir is not None:
        tmp_run_dir.mkdir(parents=True, exist_ok=True)
        agent.memory.run_dir = str(tmp_run_dir)
    return agent


def test_empty_model_response_returns_specific_reason(
    tmp_path: Path,
) -> None:
    """Empty no-tool provider output is distinct from exhausting iterations."""
    agent = _build_agent(_StubLLMNoFinal(), max_iter=3, tmp_run_dir=tmp_path / "run")

    result = agent.run(user_message="anything")

    assert result["status"] == "failed"
    assert result["reason"].startswith("empty_model_response")
    assert "iteration 1" in result["reason"]
    assert result["iterations"] >= 1
    assert result["max_iterations"] == 3


def test_cancelled_terminal_returns_reason(tmp_path: Path) -> None:
    """Cancelled-by-user runs must also surface a meaningful reason."""
    agent_ref: list[AgentLoop] = []
    agent = _build_agent(
        _StubLLMCancelMidStream(agent_ref),
        max_iter=3,
        tmp_run_dir=tmp_path / "run",
    )
    agent_ref.append(agent)

    result = agent.run(user_message="anything")

    assert result["status"] == "cancelled"
    assert result["reason"] == "cancelled by user"
    assert result["max_iterations"] == 3


class _StubLLMCancelWithToolCalls:
    """LLM stub that cancels mid-stream while returning a tool-calling response.

    Mimics the user pressing Stop during the model's turn. The loop must end
    the run as cancelled WITHOUT executing the turn's tool calls (#229).
    """

    def __init__(self, agent_ref: "list[AgentLoop]") -> None:
        self._agent_ref = agent_ref

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        self._agent_ref[0]._cancel_event.set()
        resp = _StubLLMResponse()
        resp.has_tool_calls = True
        resp.tool_calls = [SimpleNamespace(id="c1", name="get_market_data", arguments={})]
        return resp

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


def test_cancel_mid_stream_skips_tool_execution(tmp_path: Path) -> None:
    """Cancelling during the stream ends the run before any tool runs (#229)."""
    agent_ref: list[AgentLoop] = []
    agent = _build_agent(
        _StubLLMCancelWithToolCalls(agent_ref),
        max_iter=3,
        tmp_run_dir=tmp_path / "run",
    )
    agent_ref.append(agent)

    processed = {"tools": False}
    original = agent._process_tool_calls

    def _spy(*args: Any, **kwargs: Any):
        processed["tools"] = True
        return original(*args, **kwargs)

    agent._process_tool_calls = _spy  # type: ignore[method-assign]

    result = agent.run(user_message="anything")

    assert result["status"] == "cancelled"
    assert result["reason"] == "cancelled by user"
    assert processed["tools"] is False


def test_session_service_renders_meaningful_error_from_result(tmp_path: Path) -> None:
    """End-to-end guard for the original UI symptom in #114: with the new
    `reason` field populated, `result.get('reason', 'unknown')` returns the
    meaningful string SessionService passes to attempt.mark_failed."""
    agent = _build_agent(_StubLLMNoFinal(), max_iter=2, tmp_run_dir=tmp_path / "run")

    result = agent.run(user_message="anything")
    ui_error = result.get("reason", "unknown")

    assert ui_error != "unknown"
    assert "empty_model_response" in ui_error
    assert "iteration 1" in ui_error


def test_usage_metadata_is_persisted_to_run_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Provider usage should remain auditable after the live SSE event is gone."""
    monkeypatch.setenv("LANGCHAIN_PROVIDER", "pytest-provider")
    agent = _build_agent(_StubLLMWithUsage(), max_iter=2, tmp_run_dir=tmp_path / "run")

    result = agent.run(user_message="anything")

    assert result["status"] == "success"
    usage_path = tmp_path / "run" / "llm_usage.json"
    payload = json.loads(usage_path.read_text(encoding="utf-8"))
    assert payload["provider"] == "pytest-provider"
    assert payload["model"] == "stub-model"
    assert payload["totals"] == {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
        "calls": 1,
    }
    assert payload["per_iteration"] == [
        {"iter": 1, "input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    ]
    assert payload["updated_at"].endswith("Z")


class _StubLLMAlwaysToolCalls:
    """LLM stub that returns tool calls until tools=None forces text."""

    def __init__(self) -> None:
        self._counter = 0

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        resp = _StubLLMResponse()
        if tools is not None:
            self._counter += 1
            resp.has_tool_calls = True
            resp.tool_calls = [
                type("TC", (), {"id": f"tc_{self._counter}", "name": "compact", "arguments": {}})()
            ]
        else:
            resp.content = "Final answer from forced text-only."
            resp.has_tool_calls = False
        return resp

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


class _StubLLMIgnoresForcedTextOnly:
    """LLM stub that keeps returning tool calls even when tools=None."""

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        resp = _StubLLMResponse()
        resp.has_tool_calls = True
        resp.tool_calls = [
            type("TC", (), {"id": "tc_1", "name": "compact", "arguments": {}})()
        ]
        return resp

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


class _StubLLMStreamFailure:
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        raise ProviderStreamError(
            provider="deepseek",
            model="deepseek-v4-pro",
            original=RuntimeError("stream exploded"),
        )

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


def test_provider_stream_error_returns_structured_failure(tmp_path: Path) -> None:
    """Provider stream failures should stay diagnosable at the session boundary."""
    agent = _build_agent(_StubLLMStreamFailure(), max_iter=3, tmp_run_dir=tmp_path / "run")

    result = agent.run(user_message="anything")

    assert result["status"] == "failed"
    assert result["error_code"] == "provider_stream_error"
    assert "provider_stream_error" in result["reason"]
    assert result["iterations"] == 1
    assert result["max_iterations"] == 3


def test_true_max_iterations_still_returns_max_iteration_reason(tmp_path: Path) -> None:
    """A provider that ignores the forced text-only last turn is still max-iter."""
    agent = _build_agent(
        _StubLLMIgnoresForcedTextOnly(), max_iter=1, tmp_run_dir=tmp_path / "run"
    )

    result = agent.run(user_message="do something")

    assert result["status"] == "failed"
    assert result["reason"] == "reached max iterations (1) without final answer"
    assert result["iterations"] == 1


def test_force_text_only_on_last_iteration(tmp_path: Path) -> None:
    """When the LLM keeps calling tools, the last iteration forces text-only
    output by passing tools=None, producing a final answer instead of failure."""
    agent = _build_agent(
        _StubLLMAlwaysToolCalls(), max_iter=5, tmp_run_dir=tmp_path / "run"
    )
    result = agent.run(user_message="do something")

    assert result["status"] == "success"
    assert "Final answer" in result["content"]
    assert result["iterations"] == 5
