"""Regression test: agent loop must not end messages with assistant prefill.

Claude Opus 4.8+ (and other new Anthropic models) reject API requests
when the conversation ends with an assistant-role message, because the
API treats it as an "assistant prefill" which these models no longer
support.  Two code paths in AgentLoop used to emit such messages:
background notification acknowledgments and auto-compact handoff notes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import src.agent.loop as loop_mod
from src.agent.loop import AgentLoop
from src.agent.trace import TraceWriter


class _StubLLM:
    """ChatLLM stub that returns text then an answer after one tool call."""

    def __init__(self) -> None:
        self.model_name = "claude-opus-4-8-20250219"
        self.call_count = 0
        self.seen_messages: list[list[dict[str, Any]]] = []

    class _Response:
        content: str = "Here is the analysis of AAPL stock."
        tool_calls: list[Any] = []
        reasoning_content: str | None = None
        has_tool_calls = False

    class _ToolResponse(_Response):
        has_tool_calls = True
        content = "Here is the analysis of AAPL stock."

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: Any = None,
        on_text_chunk: Any = None,
        on_reasoning_chunk: Any = None,
        should_cancel: Any = None,
    ) -> Any:
        messages = [m for m in messages]
        self.call_count += 1
        self.seen_messages.append(messages)

        for msg in reversed(messages):
            if msg.get("role") in ("user", "system", "tool"):
                break
            if msg.get("role") == "assistant":
                raise AssertionError(
                    f"Messages should not end with assistant role "
                    f"(call #{self.call_count}): {msg}"
                )

        return self._Response()

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> Any:
        return self._Response()


def _build_agent(llm: Any, max_iter: int = 3, tmp_run_dir: Path | None = None) -> AgentLoop:
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


def test_agent_run_messages_never_end_with_assistant(tmp_path: Path) -> None:
    """A simple run() should never send a trailing assistant message to the LLM."""
    llm = _StubLLM()
    agent = _build_agent(
        llm,
        max_iter=5,
        tmp_run_dir=tmp_path / "run",
    )
    result = agent.run("Analyze AAPL stock for 2024")
    assert result["status"] == "success"
    assert llm.call_count >= 1


def test_background_notifications_are_reintroduced_as_user_messages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Background notifications used to append a trailing assistant ack."""

    class _BackgroundManager:
        def drain_notifications(self) -> list[dict[str, str]]:
            return [
                {
                    "task_id": "abc123",
                    "status": "completed",
                    "result": "finished",
                }
            ]

    llm = _StubLLM()
    monkeypatch.setattr(loop_mod, "get_background_manager", lambda: _BackgroundManager())
    agent = _build_agent(llm, max_iter=1, tmp_run_dir=tmp_path / "run")

    result = agent.run("Check background work")

    assert result["status"] == "success"
    first_call_messages = llm.seen_messages[0]
    assert first_call_messages[-1]["role"] == "user"
    assert "<background-results>" in first_call_messages[-1]["content"]


def test_auto_compact_handoff_summary_is_reintroduced_as_user_message(
    tmp_path: Path,
) -> None:
    """Auto-compact used to append a trailing assistant handoff ack."""
    llm = _StubLLM()
    agent = _build_agent(llm, max_iter=1, tmp_run_dir=tmp_path / "run")
    trace = TraceWriter(tmp_path / "trace")
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "earlier context"},
        {"role": "user", "content": "large recent context " + ("x" * 100_000)},
    ]

    try:
        agent._auto_compact(messages, tmp_path / "run", trace, iteration=1)
    finally:
        trace.close()

    assert messages[-1]["role"] == "user"
    assert "Continue from the summary above" in messages[-1]["content"]
