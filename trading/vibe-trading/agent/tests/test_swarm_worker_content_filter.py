"""Tests for content-filter skip logic in run_worker.

When the LLM returns ``content_filter_triggered=True``, the worker should
skip that iteration and continue instead of finalizing on empty/garbage
content. The worker injects a system message telling the agent to move on,
emits a ``content_filter_skipped`` event, and increments an internal counter.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.providers.chat import LLMResponse, ToolCallRequest
from src.swarm.models import SwarmAgentSpec, SwarmEvent, SwarmTask, WorkerResult
import src.swarm.worker as worker_mod
from src.swarm.worker import run_worker

FINAL_TEXT = (
    "# BTC-USDT — Short-Term View\n\n"
    "Spot 81,704.6 (2026-05-05). 7d range 77,750-82,842.\n\n"
    "**Recommendation: accumulate on dips to 79k; invalidation below 77.5k.**\n"
    "Position 3% NAV, stop 76,900, target 86,000. Funding 0.035%/8h elevated\n"
    "but not extreme; exchange reserves declining (bullish)."
)


class _EmptyRegistry:
    def get_definitions(self) -> list[dict]:
        return []

    def execute(self, name: str, args: dict) -> str:
        return "ok"

    def get(self, name: str):
        return None


class _ScriptedChatLLM:
    """Scripted ChatLLM that returns queued responses in order."""

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0
        self.received_messages: list[list[dict]] = []

    def __call__(self, *args, **kwargs) -> "_ScriptedChatLLM":
        return self

    def stream_chat(
        self, messages, tools=None, on_text_chunk=None, timeout=None
    ) -> LLMResponse:
        self.calls += 1
        self.received_messages.append(list(messages))
        if self._responses:
            return self._responses.pop(0)
        return LLMResponse(content=FINAL_TEXT)


def _run(
    monkeypatch,
    tmp_path: Path,
    llm: _ScriptedChatLLM,
    event_callback=None,
    max_iterations: int = 5,
) -> WorkerResult:
    monkeypatch.setattr(worker_mod, "_STREAM_RETRY_DELAY_S", 0.0)
    agent = SwarmAgentSpec(
        id="analyst",
        role="Synthesis analyst",
        system_prompt="You synthesize upstream findings.",
        tools=[],
        skills=[],
        max_iterations=max_iterations,
        timeout_seconds=60,
    )
    task = SwarmTask(id="t1", agent_id="analyst", prompt_template="Summarize.")
    with (
        patch.object(
            worker_mod, "build_swarm_registry", lambda *a, **k: _EmptyRegistry()
        ),
        patch.object(worker_mod, "ChatLLM", llm),
    ):
        return run_worker(
            agent_spec=agent,
            task=task,
            upstream_summaries={},
            user_vars={},
            run_dir=tmp_path,
            event_callback=event_callback,
        )


def test_content_filter_skipped_and_worker_continues(monkeypatch, tmp_path):
    """Content-filtered response is skipped; worker completes on next iteration."""
    events: list[SwarmEvent] = []
    llm = _ScriptedChatLLM([
        LLMResponse(content="", content_filter_triggered=True),
        LLMResponse(content=FINAL_TEXT),
    ])

    result = _run(monkeypatch, tmp_path, llm, event_callback=events.append)

    assert result.status == "completed"
    assert result.error is None
    assert llm.calls == 2


def test_content_filter_event_emitted(monkeypatch, tmp_path):
    """A content_filter_skipped event is emitted with iteration and count."""
    events: list[SwarmEvent] = []
    llm = _ScriptedChatLLM([
        LLMResponse(content="", content_filter_triggered=True),
        LLMResponse(content=FINAL_TEXT),
    ])

    _run(monkeypatch, tmp_path, llm, event_callback=events.append)

    cf_events = [e for e in events if e.type == "content_filter_skipped"]
    assert len(cf_events) == 1
    assert cf_events[0].agent_id == "analyst"
    assert cf_events[0].task_id == "t1"
    assert cf_events[0].data["iteration"] == 0
    assert cf_events[0].data["content_filter_count"] == 1


def test_content_filter_system_message_injected(monkeypatch, tmp_path):
    """A system message is injected after content-filter skip."""
    llm = _ScriptedChatLLM([
        LLMResponse(content="", content_filter_triggered=True),
        LLMResponse(content=FINAL_TEXT),
    ])

    _run(monkeypatch, tmp_path, llm)

    assert llm.calls == 2
    second_call_messages = llm.received_messages[1]
    system_msgs = [
        m for m in second_call_messages
        if m.get("role") == "system" and "content moderation" in m.get("content", "")
    ]
    assert len(system_msgs) == 1


def test_multiple_content_filters_increment_counter(monkeypatch, tmp_path):
    """Multiple consecutive content filters each increment the counter."""
    events: list[SwarmEvent] = []
    llm = _ScriptedChatLLM([
        LLMResponse(content="", content_filter_triggered=True),
        LLMResponse(content="", content_filter_triggered=True),
        LLMResponse(content=FINAL_TEXT),
    ])

    result = _run(monkeypatch, tmp_path, llm, event_callback=events.append)

    assert result.status == "completed"
    assert llm.calls == 3
    cf_events = [e for e in events if e.type == "content_filter_skipped"]
    assert len(cf_events) == 2
    assert cf_events[0].data["content_filter_count"] == 1
    assert cf_events[1].data["content_filter_count"] == 2


def test_no_content_filter_uses_existing_finalization(monkeypatch, tmp_path):
    """When content_filter_triggered=False with no tool calls, normal finalization runs."""
    events: list[SwarmEvent] = []
    llm = _ScriptedChatLLM([
        LLMResponse(content=FINAL_TEXT, content_filter_triggered=False),
    ])

    result = _run(monkeypatch, tmp_path, llm, event_callback=events.append)

    assert result.status == "completed"
    assert llm.calls == 1
    cf_events = [e for e in events if e.type == "content_filter_skipped"]
    assert len(cf_events) == 0


def _tool_response(idx: int) -> LLMResponse:
    return LLMResponse(
        content="searching...",
        tool_calls=[ToolCallRequest(id=f"tc{idx}", name="web_search", arguments={"q": "test"})],
    )


def test_content_filter_warning_in_result(monkeypatch, tmp_path):
    """4/10 iterations content-filtered (40%) -> WorkerResult.content_filter_warnings contains warning."""
    responses = [
        LLMResponse(content="", content_filter_triggered=True) if i < 4 else _tool_response(i)
        for i in range(10)
    ]
    llm = _ScriptedChatLLM(responses)

    result = _run(monkeypatch, tmp_path, llm, max_iterations=10)

    assert len(result.content_filter_warnings) == 1
    assert "4/10" in result.content_filter_warnings[0]
    assert "40%" in result.content_filter_warnings[0]


def test_content_filter_no_warning_below_threshold(monkeypatch, tmp_path):
    """0/10 iterations content-filtered -> WorkerResult.content_filter_warnings is empty."""
    responses = [_tool_response(i) for i in range(10)]
    llm = _ScriptedChatLLM(responses)

    result = _run(monkeypatch, tmp_path, llm, max_iterations=10)

    assert result.content_filter_warnings == []


def test_content_filter_circuit_breaker(monkeypatch, tmp_path):
    """10 consecutive content filters trip the circuit breaker → worker fails early."""
    responses = [LLMResponse(content="", content_filter_triggered=True) for _ in range(15)]
    llm = _ScriptedChatLLM(responses)

    result = _run(monkeypatch, tmp_path, llm, max_iterations=20)

    assert result.status == "failed"
    assert "circuit_breaker" in (result.error or "")
    assert result.iterations <= 11
