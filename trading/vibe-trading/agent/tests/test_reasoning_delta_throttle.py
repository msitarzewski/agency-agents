"""Regression test: reasoning_delta SSE events are throttled.

Long DeepSeek/Kimi reasoning streams produce hundreds of chunks. Before the
throttle, each chunk emitted one reasoning_delta event, flooding the 500-event
session replay ring buffer and evicting the tool_call/text_delta events that
reconnect replay depends on. The loop now emits at most one reasoning_delta
per REASONING_DELTA_MIN_INTERVAL_S, but always emits the first chunk of an
iteration immediately so the UI flips to "Reasoning…" without delay.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

CHUNK_COUNT = 300
CHUNK_TEXT = "reasoning…"


class _StubLLMResponse:
    """Minimal stand-in for ChatLLM's response object."""

    def __init__(self, content: str = "") -> None:
        self.content = content
        self.tool_calls: list[Any] = []
        self.reasoning_content: str | None = None
        self.has_tool_calls = False


class _ReasoningBurstLLM:
    """LLM stub that fires many reasoning chunks in a tight loop."""

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _StubLLMResponse:
        assert on_reasoning_chunk is not None
        for _ in range(CHUNK_COUNT):
            on_reasoning_chunk(CHUNK_TEXT)
        return _StubLLMResponse(content="Final answer.")

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _StubLLMResponse:
        return _StubLLMResponse()


def _build_agent(llm: Any, events: list, tmp_run_dir: Path):
    """Build an AgentLoop with a real (but shell-free) registry and a stub LLM.

    Args:
        llm: Stub LLM object exposing stream_chat/chat.
        events: List that collects (event_type, data) tuples.
        tmp_run_dir: Run directory for the agent's workspace memory.

    Returns:
        Configured AgentLoop instance.
    """
    from src.agent.loop import AgentLoop
    from src.memory.persistent import PersistentMemory
    from src.tools import build_registry

    pm = PersistentMemory()
    agent = AgentLoop(
        registry=build_registry(persistent_memory=pm, include_shell_tools=False),
        llm=llm,
        event_callback=lambda event_type, data: events.append((event_type, data)),
        max_iterations=3,
        persistent_memory=pm,
    )
    tmp_run_dir.mkdir(parents=True, exist_ok=True)
    agent.memory.run_dir = str(tmp_run_dir)
    return agent


def test_reasoning_delta_throttled_but_first_chunk_immediate(tmp_path: Path) -> None:
    """A burst of reasoning chunks must collapse to few events, first one instant."""
    events: list[tuple[str, dict[str, Any]]] = []
    agent = _build_agent(_ReasoningBurstLLM(), events, tmp_path / "run")

    result = agent.run(user_message="think hard")

    assert result["status"] == "success"
    deltas = [data for event_type, data in events if event_type == "reasoning_delta"]

    # First chunk emitted immediately: cumulative chars equals exactly one chunk.
    assert deltas, "expected at least one reasoning_delta event"
    assert deltas[0]["chars"] == len(CHUNK_TEXT)

    # Throttled: a tight 300-chunk burst (well under the 1s window) must emit
    # far fewer events than chunks — not one event per chunk.
    assert len(deltas) < CHUNK_COUNT // 10

    # Cumulative "chars" payload semantics preserved (monotonically increasing).
    chars = [d["chars"] for d in deltas]
    assert chars == sorted(chars)
