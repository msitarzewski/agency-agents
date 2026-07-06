"""Regression tests for provider reasoning_content preservation.

Invariant: ``ai_message.additional_kwargs["reasoning_content"]`` is the
single source of truth. ``ChatOpenAIWithReasoning`` populates it from both
the non-streaming response path and the streaming delta path.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

import pytest

from src.agent.context import ContextBuilder
from src.agent.loop import _attach_tool_call_thought_signatures
from src.providers.chat import ChatLLM, ToolCallRequest, _dedupe_finish_reason
from src.providers.llm import ChatOpenAIWithReasoning


class TestParseResponseSingleSource:
    """_parse_response reads reasoning_content from exactly one place."""

    def test_reads_from_additional_kwargs(self) -> None:
        ai_message = SimpleNamespace(
            content="",
            tool_calls=[],
            additional_kwargs={"reasoning_content": "step-by-step reasoning"},
            response_metadata={"finish_reason": "stop"},
        )

        response = ChatLLM._parse_response(ai_message)

        assert response.reasoning_content == "step-by-step reasoning"

    def test_absent_reasoning_content_yields_none(self) -> None:
        """Non-thinking providers leave reasoning_content unset."""
        ai_message = SimpleNamespace(
            content="hello",
            tool_calls=[],
            additional_kwargs={},
            response_metadata={"finish_reason": "stop"},
        )

        response = ChatLLM._parse_response(ai_message)

        assert response.reasoning_content is None
        assert response.content == "hello"

    def test_tool_calls_are_preserved_alongside_reasoning(self) -> None:
        ai_message = SimpleNamespace(
            content="",
            tool_calls=[{"id": "tc_1", "name": "bash", "args": {"command": "pwd"}}],
            additional_kwargs={"reasoning_content": "think then call"},
            response_metadata={"finish_reason": "tool_calls"},
        )

        response = ChatLLM._parse_response(ai_message)

        assert response.reasoning_content == "think then call"
        assert response.finish_reason == "tool_calls"
        assert response.tool_calls[0].id == "tc_1"
        assert response.tool_calls[0].arguments == {"command": "pwd"}

    def test_tool_call_thought_signatures_are_preserved_by_id_and_index(self) -> None:
        ai_message = SimpleNamespace(
            content="",
            tool_calls=[
                {"id": "tc_1", "name": "bash", "args": {"command": "pwd"}},
                {"id": "tc_2", "name": "read_file", "args": {"path": "README.md"}},
            ],
            additional_kwargs={
                "tool_call_thought_signatures": [
                    {"id": "tc_1", "index": 0, "thought_signature": "sig-a"},
                    {"index": 1, "thought_signature": "sig-b"},
                ],
            },
            response_metadata={"finish_reason": "tool_calls"},
        )

        response = ChatLLM._parse_response(ai_message)

        assert response.tool_calls[0].thought_signature == "sig-a"
        assert response.tool_calls[1].thought_signature == "sig-b"

    def test_missing_tool_call_thought_signature_stays_none(self) -> None:
        ai_message = SimpleNamespace(
            content="",
            tool_calls=[
                {"id": "tc_1", "name": "bash", "args": {"command": "pwd"}},
                {"id": "tc_2", "name": "read_file", "args": {"path": "README.md"}},
            ],
            additional_kwargs={
                "tool_call_thought_signatures": [
                    {"id": "tc_1", "index": 0, "thought_signature": "sig-a"},
                ],
            },
            response_metadata={"finish_reason": "tool_calls"},
        )

        response = ChatLLM._parse_response(ai_message)

        assert response.tool_calls[0].thought_signature == "sig-a"
        assert response.tool_calls[1].thought_signature is None


class TestDedupeFinishReason:
    """OpenRouter-style relays emit finish_reason on every stream chunk;
    AIMessageChunk.__add__ concatenates them into 'stopstop', etc. ReAct
    loop uses finish_reason for exit decisions, so equality must survive."""

    def test_clean_values_unchanged(self) -> None:
        assert _dedupe_finish_reason("stop") == "stop"
        assert _dedupe_finish_reason("tool_calls") == "tool_calls"

    def test_duplicated_dedupes(self) -> None:
        assert _dedupe_finish_reason("stopstop") == "stop"
        assert _dedupe_finish_reason("stopstopstop") == "stop"
        assert _dedupe_finish_reason("tool_callstool_calls") == "tool_calls"

    def test_suffix_match_picks_longest_valid_marker(self) -> None:
        # endswith — "stoptool_calls" ends with "tool_calls"
        assert _dedupe_finish_reason("stoptool_calls") == "tool_calls"

    def test_empty_returns_empty(self) -> None:
        # No marker matches; raw is returned. Callers supply a default upstream.
        assert _dedupe_finish_reason("") == ""

    def test_unknown_marker_passed_through(self) -> None:
        assert _dedupe_finish_reason("custom_reason") == "custom_reason"


class TestContextBuilderToolCallReplay:
    """reasoning_content flows back into the next request's assistant message."""

    def test_format_assistant_tool_calls_preserves_reasoning_content(self) -> None:
        message = ContextBuilder.format_assistant_tool_calls(
            [ToolCallRequest(id="tc_1", name="bash", arguments={"command": "pwd"})],
            content="",
            reasoning_content="step-by-step reasoning",
        )

        assert message["role"] == "assistant"
        assert message["reasoning_content"] == "step-by-step reasoning"
        assert message["tool_calls"][0]["id"] == "tc_1"

    def test_format_assistant_tool_calls_omits_reasoning_when_absent(self) -> None:
        message = ContextBuilder.format_assistant_tool_calls(
            [ToolCallRequest(id="tc_1", name="bash", arguments={"command": "pwd"})],
            content="",
        )

        assert "reasoning_content" not in message


class TestAgentLoopToolCallReplay:
    """Gemini tool-call thought_signature flows back into the next assistant message."""

    def test_attaches_thought_signatures_to_matching_tool_calls(self) -> None:
        tool_calls = [
            ToolCallRequest(
                id="tc_1",
                name="bash",
                arguments={"command": "pwd"},
                thought_signature="sig-a",
            ),
            ToolCallRequest(
                id="tc_2",
                name="read_file",
                arguments={"path": "README.md"},
                thought_signature="sig-b",
            ),
        ]
        message = ContextBuilder.format_assistant_tool_calls(tool_calls, content="")

        _attach_tool_call_thought_signatures(message, tool_calls)

        assert message["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "sig-a"
        assert message["tool_calls"][1]["extra_content"]["google"]["thought_signature"] == "sig-b"

    def test_unsigned_tool_calls_are_left_untouched(self) -> None:
        tool_calls = [
            ToolCallRequest(
                id="tc_1",
                name="bash",
                arguments={"command": "pwd"},
                thought_signature="sig-a",
            ),
            ToolCallRequest(id="tc_2", name="read_file", arguments={"path": "README.md"}),
        ]
        message = ContextBuilder.format_assistant_tool_calls(tool_calls, content="")

        _attach_tool_call_thought_signatures(message, tool_calls)

        assert message["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "sig-a"
        assert "extra_content" not in message["tool_calls"][1]


class TestChatOpenAIWithReasoningNonStreaming:
    """_create_chat_result path: invoke / ainvoke."""

    def _instance(self, model: str = "kimi-k2-thinking") -> Any:
        if ChatOpenAIWithReasoning is None:
            pytest.skip("langchain-openai is not installed")
        os.environ.setdefault("OPENAI_API_KEY", "sk-test")
        return ChatOpenAIWithReasoning(model=model, api_key="sk-test")

    def test_preserves_reasoning_on_tool_call_response(self) -> None:
        instance = self._instance()
        response = {
            "id": "chatcmpl-test",
            "model": "kimi-k2-thinking",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "reasoning_content": "step-by-step reasoning from provider",
                        "tool_calls": [
                            {
                                "id": "tc_1",
                                "type": "function",
                                "function": {
                                    "name": "bash",
                                    "arguments": '{"command":"pwd"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        result = instance._create_chat_result(response)

        assert result.generations[0].message.additional_kwargs["reasoning_content"] == \
            "step-by-step reasoning from provider"

    def test_preserves_tool_call_thought_signatures_on_response(self) -> None:
        instance = self._instance(model="gemini-3-pro-preview")
        response = {
            "id": "chatcmpl-test",
            "model": "gemini-3-pro-preview",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "tc_1",
                                "type": "function",
                                "extra_content": {"google": {"thought_signature": "sig-a"}},
                                "function": {
                                    "name": "bash",
                                    "arguments": '{"command":"pwd"}',
                                },
                            },
                            {
                                "id": "tc_2",
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{"path":"README.md"}',
                                },
                            },
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        result = instance._create_chat_result(response)
        parsed = ChatLLM._parse_response(result.generations[0].message)

        assert parsed.tool_calls[0].thought_signature == "sig-a"
        assert parsed.tool_calls[1].thought_signature is None

    def test_no_reasoning_content_when_absent(self) -> None:
        """OpenAI / Claude / Groq-style responses leave additional_kwargs clean."""
        instance = self._instance(model="gpt-4")
        response = {
            "id": "chatcmpl-test",
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        }

        result = instance._create_chat_result(response)

        assert "reasoning_content" not in result.generations[0].message.additional_kwargs


class TestChatOpenAIWithReasoningStreaming:
    """_convert_chunk_to_generation_chunk path: stream / astream.

    This is the path swarm workers take via ChatLLM.stream_chat → llm.stream.
    PR #41 only fixed the non-streaming path; this class covers the gap.
    """

    def _instance(self, model: str = "kimi-k2-thinking") -> Any:
        if ChatOpenAIWithReasoning is None:
            pytest.skip("langchain-openai is not installed")
        os.environ.setdefault("OPENAI_API_KEY", "sk-test")
        return ChatOpenAIWithReasoning(model=model, api_key="sk-test")

    def _delta_chunk(self, delta: dict, model: str = "kimi-k2-thinking") -> dict:
        return {
            "id": "chatcmpl-test",
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }

    def test_preserves_reasoning_on_streaming_delta(self) -> None:
        from langchain_core.messages import AIMessageChunk

        instance = self._instance()
        chunk = self._delta_chunk(
            {"role": "assistant", "content": "", "reasoning_content": "thinking step"}
        )

        gen_chunk = instance._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)

        assert gen_chunk is not None
        assert gen_chunk.message.additional_kwargs["reasoning_content"] == "thinking step"

    def test_streaming_chunks_accumulate_reasoning_across_chunks(self) -> None:
        """Multiple deltas: AIMessageChunk.__add__ concatenates via merge_dicts."""
        from langchain_core.messages import AIMessageChunk

        instance = self._instance()
        chunks = [
            self._delta_chunk({"role": "assistant", "content": "", "reasoning_content": "first "}),
            self._delta_chunk({"content": "", "reasoning_content": "second "}),
            self._delta_chunk({"content": "", "reasoning_content": "third"}),
        ]

        accumulated = None
        for raw in chunks:
            gen = instance._convert_chunk_to_generation_chunk(raw, AIMessageChunk, None)
            assert gen is not None
            accumulated = gen.message if accumulated is None else accumulated + gen.message

        assert accumulated is not None
        assert accumulated.additional_kwargs["reasoning_content"] == "first second third"

    def test_streaming_delta_without_reasoning_is_unchanged(self) -> None:
        """OpenAI-style stream deltas (no reasoning_content) produce empty additional_kwargs."""
        from langchain_core.messages import AIMessageChunk

        instance = self._instance(model="gpt-4")
        chunk = self._delta_chunk({"role": "assistant", "content": "hello"}, model="gpt-4")

        gen_chunk = instance._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)

        assert gen_chunk is not None
        assert "reasoning_content" not in gen_chunk.message.additional_kwargs

    def test_preserves_tool_call_thought_signature_on_streaming_delta(self) -> None:
        from langchain_core.messages import AIMessageChunk

        instance = self._instance(model="gemini-3-pro-preview")
        chunk = self._delta_chunk(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "tc_1",
                        "type": "function",
                        "extra_content": {"google": {"thought_signature": "sig-a"}},
                        "function": {
                            "name": "bash",
                            "arguments": '{"command":"pwd"}',
                        },
                    },
                    {
                        "index": 1,
                        "id": "tc_2",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path":"README.md"}',
                        },
                    },
                ],
            },
            model="gemini-3-pro-preview",
        )

        gen_chunk = instance._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)

        assert gen_chunk is not None
        assert gen_chunk.message.additional_kwargs["tool_call_thought_signatures"] == [
            {"id": "tc_1", "index": 0, "thought_signature": "sig-a"},
        ]

    def test_openrouter_field_name_reasoning_maps_to_reasoning_content(self) -> None:
        """OpenRouter relays Kimi/DeepSeek with delta.reasoning (not reasoning_content).

        All variants must normalize to additional_kwargs["reasoning_content"] so
        downstream reads one canonical key.
        """
        from langchain_core.messages import AIMessageChunk

        instance = self._instance(model="moonshotai/kimi-k2-thinking")
        chunk = self._delta_chunk(
            {"role": "assistant", "content": "", "reasoning": "openrouter-style reasoning"},
            model="moonshotai/kimi-k2-thinking",
        )

        gen_chunk = instance._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)

        assert gen_chunk is not None
        # Canonical key — not "reasoning"
        assert gen_chunk.message.additional_kwargs["reasoning_content"] == \
            "openrouter-style reasoning"
        assert "reasoning" not in gen_chunk.message.additional_kwargs

    def test_reasoning_content_takes_priority_over_reasoning(self) -> None:
        """If both variants are present, reasoning_content wins (higher priority)."""
        from langchain_core.messages import AIMessageChunk

        instance = self._instance()
        chunk = self._delta_chunk(
            {
                "role": "assistant",
                "content": "",
                "reasoning_content": "canonical",
                "reasoning": "variant",
            }
        )

        gen_chunk = instance._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)

        assert gen_chunk is not None
        assert gen_chunk.message.additional_kwargs["reasoning_content"] == "canonical"

    def test_usage_only_chunk_returns_without_modification(self) -> None:
        """Final usage-only chunks have no choices[] — must not crash."""
        from langchain_core.messages import AIMessageChunk

        instance = self._instance()
        usage_only = {
            "id": "chatcmpl-test",
            "model": "kimi-k2-thinking",
            "choices": [],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        gen_chunk = instance._convert_chunk_to_generation_chunk(usage_only, AIMessageChunk, None)

        # super() returns a default-content chunk for usage-only; we should
        # pass it through unchanged (no choices to read reasoning from).
        assert gen_chunk is not None
        assert "reasoning_content" not in gen_chunk.message.additional_kwargs


class TestChatOpenAIWithReasoningOutboundPayload:
    """_get_request_payload path: re-inject reasoning_content on continuation
    calls and normalize content=None for strict providers (issue #39 round-trip).
    """

    def _instance(self, model: str = "kimi-k2-0905-preview") -> Any:
        if ChatOpenAIWithReasoning is None:
            pytest.skip("langchain-openai is not installed")
        os.environ.setdefault("OPENAI_API_KEY", "sk-test")
        return ChatOpenAIWithReasoning(model=model, api_key="sk-test")

    def test_reinjects_reasoning_content_from_additional_kwargs(self) -> None:
        """Assistant messages with reasoning_content in additional_kwargs are
        preserved across LangChain's dict → AIMessage → dict serialization."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance()
        history = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                additional_kwargs={
                    "reasoning_content": "I should call a tool",
                    "tool_calls": [
                        {"id": "c1", "type": "function",
                         "function": {"name": "t", "arguments": "{}"}},
                    ],
                },
            ),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert assistant_msg["reasoning_content"] == "I should call a tool"

    def test_normalizes_none_content_on_assistant_messages(self) -> None:
        """LangChain serializes AIMessage(content='', tool_calls=[...]) as
        content=null; Moonshot kimi-k2.6 rejects that, so we normalize to ''."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance()
        history = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                additional_kwargs={
                    "tool_calls": [
                        {"id": "c1", "type": "function",
                         "function": {"name": "t", "arguments": "{}"}},
                    ],
                },
            ),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert assistant_msg["content"] == ""
        assert "extra_content" not in assistant_msg["tool_calls"][0]

    def test_reinjects_tool_call_thought_signature_from_additional_kwargs(self) -> None:
        """Captured Gemini signatures survive LangChain's tool-call serialization."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance(model="gemini-3-pro-preview")
        history = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                additional_kwargs={
                    "tool_call_thought_signatures": [
                        {"id": "c1", "index": 0, "thought_signature": "sig-a"},
                    ],
                    "tool_calls": [
                        {"id": "c1", "type": "function",
                         "function": {"name": "t", "arguments": "{}"}},
                    ],
                },
            ),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert assistant_msg["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "sig-a"

    def test_reinjects_tool_call_thought_signature_from_raw_tool_call(self) -> None:
        """Loop-provided raw tool calls carry Gemini's OpenAI-compat extra_content."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance(model="gemini-3-pro-preview")
        history = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                additional_kwargs={
                    "tool_calls": [
                        {
                            "id": "c1",
                            "type": "function",
                            "extra_content": {"google": {"thought_signature": "sig-a"}},
                            "function": {"name": "t", "arguments": "{}"},
                        },
                    ],
                },
            ),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert assistant_msg["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "sig-a"

    def _payload_via_runtime(self, instance: Any, dict_history: list) -> dict:
        """Mirror ``invoke``: convert the raw OpenAI-format input first (where
        ``_convert_input`` re-attaches signatures), then build the request payload
        from the converted messages — exactly the runtime order."""
        converted = instance._convert_input(dict_history).to_messages()
        return instance._get_request_payload(converted)

    def test_reattaches_thought_signature_from_raw_dict_input(self) -> None:
        """Regression: the AgentLoop replays history as OpenAI-format dicts (not
        AIMessage objects). LangChain's ``_convert_dict_to_message`` discards the
        ``extra_content`` Gemini signature, so the #176 in-memory machinery alone
        leaves the outbound payload unsigned and Gemini 400s on the next turn.
        ``_convert_input`` must lift the signature back onto the converted message.
        """
        from src.agent.context import ContextBuilder
        from src.agent.loop import _attach_tool_call_thought_signatures
        from src.providers.chat import ToolCallRequest

        instance = self._instance(model="gemini-3-pro-preview")
        tool_calls = [
            ToolCallRequest(id="c1", name="load_skill",
                            arguments={"name": "momentum"}, thought_signature="sig-a"),
        ]
        assistant = ContextBuilder.format_assistant_tool_calls(tool_calls)
        _attach_tool_call_thought_signatures(assistant, tool_calls)
        history = [
            {"role": "user", "content": "load momentum"},
            assistant,
            {"role": "tool", "tool_call_id": "c1", "content": "loaded"},
        ]

        payload = self._payload_via_runtime(instance, history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert assistant_msg["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "sig-a"

    def test_parallel_dict_input_keeps_first_signature_only(self) -> None:
        """Gemini signs only the first of N parallel calls. The natural state
        (first signed, rest genuinely absent) must round-trip unchanged through
        the dict path — Gemini accepts the single signature for the whole block,
        so we must neither drop the first nor fabricate the others.
        """
        from src.agent.context import ContextBuilder
        from src.agent.loop import _attach_tool_call_thought_signatures
        from src.providers.chat import ToolCallRequest

        instance = self._instance(model="gemini-3-pro-preview")
        tool_calls = [
            ToolCallRequest(id="c1", name="load_skill", arguments={"name": "a"}, thought_signature="sig-a"),
            ToolCallRequest(id="c2", name="load_skill", arguments={"name": "b"}, thought_signature=None),
            ToolCallRequest(id="c3", name="load_skill", arguments={"name": "c"}, thought_signature=None),
        ]
        assistant = ContextBuilder.format_assistant_tool_calls(tool_calls)
        _attach_tool_call_thought_signatures(assistant, tool_calls)
        history = [
            {"role": "user", "content": "load a, b, c"},
            assistant,
            {"role": "tool", "tool_call_id": "c1", "content": "ok"},
            {"role": "tool", "tool_call_id": "c2", "content": "ok"},
            {"role": "tool", "tool_call_id": "c3", "content": "ok"},
        ]

        payload = self._payload_via_runtime(instance, history)

        tcs = next(m for m in payload["messages"] if m["role"] == "assistant")["tool_calls"]
        assert tcs[0]["extra_content"]["google"]["thought_signature"] == "sig-a"
        assert "extra_content" not in tcs[1]
        assert "extra_content" not in tcs[2]

    def test_injects_empty_reasoning_content_when_absent(self) -> None:
        """kimi-k2.6 requires reasoning_content on every assistant turn."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance()
        history = [
            HumanMessage(content="hi"),
            AIMessage(content="plain assistant reply"),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert assistant_msg["reasoning_content"] == ""

    def test_openai_does_not_inject_empty_reasoning_content(self) -> None:
        """Strict Kimi continuation fields must not leak into OpenAI payloads."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance(model="gpt-4")
        history = [
            HumanMessage(content="hi"),
            AIMessage(content="plain assistant reply"),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert "reasoning_content" not in assistant_msg

    def test_deepseek_does_not_replay_reasoning_content_outbound(self) -> None:
        """DeepSeek reasoning traces are inbound progress, not next-turn payload."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance(model="deepseek-v4-pro")
        history = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                additional_kwargs={"reasoning_content": "internal reasoning"},
            ),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert "reasoning_content" not in assistant_msg

    def test_user_and_system_messages_untouched(self) -> None:
        """Only assistant messages get the reasoning_content injection."""
        from langchain_core.messages import HumanMessage, SystemMessage

        instance = self._instance()
        history = [
            SystemMessage(content="be brief"),
            HumanMessage(content="hi"),
        ]

        payload = instance._get_request_payload(history)

        for m in payload["messages"]:
            assert "reasoning_content" not in m

    def test_non_gemini_does_not_inject_tool_call_thought_signature(self) -> None:
        """Gemini thought signatures must be Gemini-only payload mutations."""
        from langchain_core.messages import AIMessage, HumanMessage

        instance = self._instance(model="gpt-4")
        history = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                additional_kwargs={
                    "tool_call_thought_signatures": [
                        {"id": "c1", "index": 0, "thought_signature": "sig-a"},
                    ],
                    "tool_calls": [
                        {"id": "c1", "type": "function",
                         "function": {"name": "t", "arguments": "{}"}},
                    ],
                },
            ),
        ]

        payload = instance._get_request_payload(history)

        assistant_msg = next(m for m in payload["messages"] if m["role"] == "assistant")
        assert "extra_content" not in assistant_msg["tool_calls"][0]
