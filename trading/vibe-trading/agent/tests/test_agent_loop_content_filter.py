"""AgentLoop content-filter skip-and-continue behavior.

When the LLM returns a content-filtered response (content_filter_triggered=True),
the agent loop should skip that iteration and continue instead of breaking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from src.providers.chat import LLMResponse, ToolCallRequest


class _ContentFilterLoopLLM:
    """LLM stub returning scripted content_filter_triggered responses."""

    def __init__(
        self,
        filter_count: int,
        final_content: str = "Final answer.",
    ) -> None:
        self._filter_remaining = filter_count
        self._final_content = final_content
        self.calls = 0
        self.messages_history: list[list[dict[str, Any]]] = []

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> LLMResponse:
        self.calls += 1
        self.messages_history.append(list(messages))
        if self._filter_remaining > 0:
            self._filter_remaining -= 1
            return LLMResponse(
                content="",
                content_filter_triggered=True,
            )
        if on_text_chunk:
            on_text_chunk(self._final_content)
        return LLMResponse(content=self._final_content)

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> LLMResponse:
        return LLMResponse(content="")


class _EmptyResponseLoopLLM:
    """LLM stub returning empty content with no content filter."""

    def __init__(self) -> None:
        self.calls = 0

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> LLMResponse:
        self.calls += 1
        return LLMResponse(content="", content_filter_triggered=False)

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> LLMResponse:
        return LLMResponse(content="")


def _run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    llm: Any,
    max_iterations: int = 5,
) -> dict[str, Any]:
    from src.agent.loop import AgentLoop
    from src.memory.persistent import PersistentMemory
    from src.tools import build_registry

    pm = PersistentMemory()
    agent = AgentLoop(
        registry=build_registry(persistent_memory=pm, include_shell_tools=False),
        llm=llm,
        max_iterations=max_iterations,
        persistent_memory=pm,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    agent.memory.run_dir = str(run_dir)
    return agent.run(user_message="hello")


def _read_trace(run_dir: str) -> list[dict[str, Any]]:
    from src.agent.trace import TraceWriter

    return TraceWriter.read(Path(run_dir))


def test_content_filter_skip_and_continue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Content filter on first call, then normal response -> loop continues and succeeds."""
    llm = _ContentFilterLoopLLM(filter_count=1, final_content="Final answer.")

    result = _run(monkeypatch, tmp_path, llm)

    assert result["status"] == "success"
    assert result["content"] == "Final answer."
    assert llm.calls == 2


def test_content_filter_trace_entry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Trace contains content_filter_skipped entry when filter is triggered."""
    llm = _ContentFilterLoopLLM(filter_count=1, final_content="Done.")

    result = _run(monkeypatch, tmp_path, llm)

    trace = _read_trace(result["run_dir"])
    filter_entries = [e for e in trace if e.get("type") == "content_filter_skipped"]
    assert len(filter_entries) == 1
    assert "iter" in filter_entries[0]


def test_content_filter_injects_system_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """System message is injected into messages after content filter hit."""
    llm = _ContentFilterLoopLLM(filter_count=1, final_content="Done.")

    _run(monkeypatch, tmp_path, llm)

    assert llm.calls == 2
    messages_on_second_call = llm.messages_history[1]
    system_messages = [
        m for m in messages_on_second_call
        if "content moderation" in str(m.get("content", ""))
    ]
    assert len(system_messages) == 1
    assert "[SYSTEM]" in system_messages[0]["content"]


def test_multiple_content_filter_hits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Multiple content filter hits are all traced and counted."""
    llm = _ContentFilterLoopLLM(filter_count=3, final_content="Finally.")

    result = _run(monkeypatch, tmp_path, llm)

    assert result["status"] == "success"
    assert result["content"] == "Finally."
    assert llm.calls == 4

    trace = _read_trace(result["run_dir"])
    filter_entries = [e for e in trace if e.get("type") == "content_filter_skipped"]
    assert len(filter_entries) == 3


def test_empty_content_no_filter_still_breaks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Empty content with content_filter_triggered=False triggers existing break."""
    llm = _EmptyResponseLoopLLM()

    result = _run(monkeypatch, tmp_path, llm)

    assert result["status"] == "failed"
    assert "empty_model_response" in result.get("reason", "")
    assert llm.calls == 1

    trace = _read_trace(result["run_dir"])
    empty_entries = [e for e in trace if e.get("type") == "empty_model_response"]
    assert len(empty_entries) == 1
    filter_entries = [e for e in trace if e.get("type") == "content_filter_skipped"]
    assert len(filter_entries) == 0


class _RatioFilterLoopLLM:
    """LLM stub producing content_filter on first N calls, tool calls to keep
    the loop going, then final content on the last call.

    Call pattern (1-indexed):
      calls 1..filter_count       → content_filter_triggered
      calls filter_count+1..total-1 → fake tool call (keeps loop alive)
      call total                  → final content (breaks loop)
    """

    def __init__(
        self,
        filter_count: int,
        total_iterations: int,
        final_content: str = "Final answer.",
    ) -> None:
        self._filter_count = filter_count
        self._total = total_iterations
        self._final_content = final_content
        self.calls = 0

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> LLMResponse:
        self.calls += 1
        if self.calls <= self._filter_count:
            return LLMResponse(content="", content_filter_triggered=True)
        if self.calls < self._total:
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCallRequest(
                        id=f"call_{self.calls}", name="_noop", arguments={}
                    )
                ],
            )
        if on_text_chunk:
            on_text_chunk(self._final_content)
        return LLMResponse(content=self._final_content)

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> LLMResponse:
        return LLMResponse(content="")


def test_content_filter_warning_in_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """5/10 iterations hit content_filter (50%) → warning surfaced in result."""
    llm = _RatioFilterLoopLLM(filter_count=5, total_iterations=10)

    result = _run(monkeypatch, tmp_path, llm, max_iterations=10)

    assert "content_filter_warnings" in result
    warnings = result["content_filter_warnings"]
    assert len(warnings) == 1
    assert "50%" in warnings[0]
    assert "provider" in warnings[0].lower()


def test_content_filter_no_warning_below_threshold(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """0/10 iterations hit content_filter → no warning key in result."""
    llm = _ContentFilterLoopLLM(filter_count=0, final_content="Clean run.")

    result = _run(monkeypatch, tmp_path, llm, max_iterations=10)

    assert "content_filter_warnings" not in result


def test_content_filter_circuit_breaker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """10 consecutive content filters trip the circuit breaker → run fails early."""
    llm = _ContentFilterLoopLLM(filter_count=15, final_content="Never reached.")

    result = _run(monkeypatch, tmp_path, llm, max_iterations=20)

    assert result["status"] == "failed"
    assert "circuit_breaker" in result.get("reason", "")
    assert result["iterations"] <= 11
