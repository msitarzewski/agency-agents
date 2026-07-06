"""Gemini content-filter detection regression tests.

Gemini surfaces content moderation via uppercase FinishReason enum values
(SAFETY, RECITATION, BLOCKLIST, ...) instead of OpenAI's lowercase
"content_filter". Google's OpenAI-compatible endpoint passes these through
unmapped, so ``_parse_response`` must recognise both vocabularies — otherwise
the circuit breaker / warning pipeline from issue #307 silently fails for the
Gemini provider.

Response fixtures sourced from:
- google-gemini/deprecated-generative-ai-python tests (Apache-2.0)
- langchain-ai/langchain-google integration tests (MIT)
- firebase/flutterfire response parsing tests (BSD-3-Clause)
"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from src.providers.chat import ChatLLM
from src.providers.content_filter import (
    GEMINI_SAFETY_FINISH_REASONS,
    is_content_filter_triggered,
)


@pytest.mark.parametrize("reason", sorted(GEMINI_SAFETY_FINISH_REASONS))
def test_helper_detects_each_gemini_safety_reason(reason: str) -> None:
    assert is_content_filter_triggered(reason) is True


def test_helper_detects_openai_content_filter() -> None:
    assert is_content_filter_triggered("content_filter") is True


def test_helper_case_insensitive() -> None:
    assert is_content_filter_triggered("safety") is True
    assert is_content_filter_triggered("Recitation") is True


@pytest.mark.parametrize(
    "reason", ["stop", "length", "tool_calls", "end_turn", "max_tokens", ""]
)
def test_helper_rejects_non_filter_reasons(reason: str) -> None:
    assert is_content_filter_triggered(reason) is False


@pytest.mark.parametrize("value", [None, 123, [], {}])
def test_helper_handles_non_string(value: object) -> None:
    assert is_content_filter_triggered(value) is False


def test_parse_response_detects_gemini_safety() -> None:
    ai_msg = AIMessage(content="", response_metadata={"finish_reason": "SAFETY"})
    resp = ChatLLM._parse_response(ai_msg)
    assert resp.content_filter_triggered is True


def test_parse_response_detects_gemini_recitation() -> None:
    ai_msg = AIMessage(content="", response_metadata={"finish_reason": "RECITATION"})
    resp = ChatLLM._parse_response(ai_msg)
    assert resp.content_filter_triggered is True


def test_parse_response_openai_content_filter_regression() -> None:
    ai_msg = AIMessage(
        content="", response_metadata={"finish_reason": "content_filter"}
    )
    resp = ChatLLM._parse_response(ai_msg)
    assert resp.content_filter_triggered is True


def test_parse_response_normal_stop_not_triggered() -> None:
    ai_msg = AIMessage(content="hello", response_metadata={"finish_reason": "stop"})
    resp = ChatLLM._parse_response(ai_msg)
    assert resp.content_filter_triggered is False


def test_parse_response_missing_finish_reason_not_triggered() -> None:
    ai_msg = AIMessage(content="hello", response_metadata={})
    resp = ChatLLM._parse_response(ai_msg)
    assert resp.content_filter_triggered is False
