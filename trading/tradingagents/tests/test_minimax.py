"""Tests for MinimaxChatOpenAI quirks.

Verifies the subclass injects ``reasoning_split=True`` into outgoing
requests so M2.x reasoning models put their <think> block into
``reasoning_details`` instead of polluting ``message.content``.
"""

import os

import pytest
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from tradingagents.llm_clients.openai_client import MinimaxChatOpenAI


def _client(model: str = "MiniMax-M2.7"):
    os.environ.setdefault("MINIMAX_API_KEY", "placeholder")
    return MinimaxChatOpenAI(
        model=model,
        api_key="placeholder",
        base_url="https://api.minimax.io/v1",
    )


@pytest.mark.unit
class TestMinimaxReasoningSplit:
    def test_reasoning_split_sent_via_extra_body_not_top_level(self):
        # Must be in extra_body, not top-level: the openai SDK validates
        # top-level params and rejects unknown ones like reasoning_split (#826).
        payload = _client()._get_request_payload([HumanMessage(content="hi")])
        assert payload.get("extra_body", {}).get("reasoning_split") is True
        assert "reasoning_split" not in payload  # never top-level

    def test_non_reasoning_minimax_does_not_inject_reasoning_split(self):
        """Coding Plan / MiniMax-Text-01 / any non-M2-prefixed model must NOT
        receive reasoning_split at all (top-level or extra_body) (#826)."""
        for model in ("minimax-text-01", "MiniMax-Coding-Plan"):
            payload = _client(model)._get_request_payload(
                [HumanMessage(content="hi")]
            )
            assert "reasoning_split" not in payload
            assert "reasoning_split" not in payload.get("extra_body", {})


@pytest.mark.unit
class TestMinimaxStructuredOutputDispatch:
    """M2.x models route through the capability table — tool_choice is
    suppressed but the schema is still bound as a tool."""

    class _Pick(BaseModel):
        action: str

    def _bound_kwargs(self, runnable):
        first = runnable.steps[0] if hasattr(runnable, "steps") else runnable
        return getattr(first, "kwargs", {})

    def test_m2_7_suppresses_tool_choice(self):
        bound = _client("MiniMax-M2.7").with_structured_output(self._Pick)
        kwargs = self._bound_kwargs(bound)
        assert kwargs.get("tool_choice") is None or "tool_choice" not in kwargs

    def test_m2_7_highspeed_suppresses_tool_choice(self):
        bound = _client("MiniMax-M2.7-highspeed").with_structured_output(self._Pick)
        kwargs = self._bound_kwargs(bound)
        assert kwargs.get("tool_choice") is None or "tool_choice" not in kwargs

    def test_schema_still_bound_as_tool(self):
        bound = _client("MiniMax-M2.7").with_structured_output(self._Pick)
        tools = self._bound_kwargs(bound).get("tools", [])
        assert any(
            t.get("function", {}).get("name") == "_Pick" for t in tools
        ), f"schema not bound: {tools}"
