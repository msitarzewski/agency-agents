"""E2E content-filter resilience: detection -> skip -> ratio -> warning -> trace.

Simulates a full agent run where semiconductor/geopolitics news triggers
DashScope/Qwen content moderation on some LLM calls (e.g. event-driven
backtest on 159516.SZ).  Verifies the entire pipeline:

1. Run completes successfully despite content-filter hits.
2. ``content_filter_warnings`` surfaced in result when ratio > 5 %.
3. Trace contains exactly the expected ``content_filter_skipped`` entries.
4. Warning message format includes ratio, "content moderation", and provider
   recommendation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from src.providers.chat import LLMResponse, ToolCallRequest


# ---------------------------------------------------------------------------
# LLM stubs
# ---------------------------------------------------------------------------


class _InterleavedFilterLLM:
    """Scripted LLM stub producing an interleaved content-filter pattern.

    Call pattern (1-indexed):
      call 1  -> content_filter_triggered=True
      call 2  -> tool call (_noop) to keep the loop alive
      call 3  -> content_filter_triggered=True
      call 4  -> tool call (_noop) to keep the loop alive
      call 5  -> final content (breaks the loop)

    This gives 2 content-filter hits out of 5 iterations (40 %).
    """

    def __init__(self, final_content: str = "Final analysis complete.") -> None:
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
        # Calls 1 and 3: content filter triggered
        if self.calls in (1, 3):
            return LLMResponse(content="", content_filter_triggered=True)
        # Calls 2 and 4: tool call to keep the loop going
        if self.calls in (2, 4):
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCallRequest(
                        id=f"call_{self.calls}", name="_noop", arguments={}
                    )
                ],
            )
        # Call 5+: final answer
        if on_text_chunk:
            on_text_chunk(self._final_content)
        return LLMResponse(content=self._final_content)

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> LLMResponse:
        return LLMResponse(content="")


class _CleanRunLLM:
    """Scripted LLM stub producing zero content-filter hits over 5 calls.

    Call pattern:
      calls 1-4 -> tool call (_noop) to keep the loop alive
      call 5    -> final content
    """

    def __init__(self, final_content: str = "Clean analysis complete.") -> None:
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
        if self.calls < 5:
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


# ---------------------------------------------------------------------------
# Harness helpers
# ---------------------------------------------------------------------------


def _run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    llm: Any,
    max_iterations: int = 5,
) -> dict[str, Any]:
    """Build an AgentLoop, wire up a scratch run_dir, and execute."""
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
    return agent.run(user_message="Analyze 159516.SZ with recent news sentiment")


def _read_trace(run_dir: str) -> list[dict[str, Any]]:
    """Read trace.jsonl entries from a run directory."""
    from src.agent.trace import TraceWriter

    return TraceWriter.read(Path(run_dir))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_e2e_content_filter_pipeline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """2/5 iterations hit content_filter (40 %) -> full pipeline verified.

    Asserts:
      1. Run completes successfully.
      2. ``content_filter_warnings`` present in result dict.
      3. Trace contains exactly 2 ``content_filter_skipped`` entries.
      4. Warning message contains "40%", "content moderation", and "provider".
    """
    llm = _InterleavedFilterLLM()

    result = _run(monkeypatch, tmp_path, llm)

    # 1. Run completes successfully
    assert result["status"] == "success"
    assert result["content"] == "Final analysis complete."
    assert llm.calls == 5

    # 2. Warning surfaced because 2/5 = 40% > 5% threshold
    assert "content_filter_warnings" in result
    warnings = result["content_filter_warnings"]
    assert len(warnings) == 1

    # 3. Trace contains exactly 2 content_filter_skipped entries
    trace = _read_trace(result["run_dir"])
    filter_entries = [e for e in trace if e.get("type") == "content_filter_skipped"]
    assert len(filter_entries) == 2
    # Each entry carries an iter key
    assert all("iter" in entry for entry in filter_entries)

    # 4. Warning message format
    warning = warnings[0]
    assert "40%" in warning
    assert "content moderation" in warning
    assert "provider" in warning.lower()


def test_e2e_no_content_filter_clean_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """0/5 iterations hit content_filter -> no warnings, no trace entries.

    Asserts:
      1. Run completes successfully.
      2. No ``content_filter_warnings`` key in result dict.
      3. No ``content_filter_skipped`` entries in trace.
    """
    llm = _CleanRunLLM()

    result = _run(monkeypatch, tmp_path, llm)

    # 1. Run completes successfully
    assert result["status"] == "success"
    assert result["content"] == "Clean analysis complete."
    assert llm.calls == 5

    # 2. No warnings
    assert "content_filter_warnings" not in result

    # 3. No content_filter_skipped trace entries
    trace = _read_trace(result["run_dir"])
    filter_entries = [e for e in trace if e.get("type") == "content_filter_skipped"]
    assert len(filter_entries) == 0
