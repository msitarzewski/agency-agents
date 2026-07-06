"""Tests for real-token propagation from LangChain through to swarm totals.

The swarm's ``total_input_tokens`` / ``total_output_tokens`` used to be
character-count guesses (``len(json.dumps(messages)) // 4``) — wrong by
20-50% for English prompts and dramatically wrong for CJK / Thai /
emoji-heavy traffic. LangChain already attaches real provider token
counts on every ``AIMessage.usage_metadata``; the swarm just wasn't
reading them. These tests pin down both ends of the new contract:

* :class:`LLMResponse` carries ``usage_metadata`` straight off the
  parsed message (covered by exercising :meth:`ChatLLM._parse_response`
  on a fake AIMessage).
* :func:`worker._estimate_tokens` prefers those real counts when present
  and only falls back to the legacy heuristic when the provider didn't
  report usage.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.providers.chat import ChatLLM, LLMResponse
from src.swarm.worker import _estimate_tokens


# --------------------------------------------------------------------------- #
# ChatLLM._parse_response — usage_metadata propagation
# --------------------------------------------------------------------------- #


def _fake_ai_message(usage_metadata=None, content="hello", finish="stop"):
    """Build the smallest object that quacks like a LangChain AIMessage."""
    return SimpleNamespace(
        content=content,
        tool_calls=[],
        additional_kwargs={},
        response_metadata={"finish_reason": finish},
        usage_metadata=usage_metadata,
    )


def test_parse_response_propagates_usage_metadata_dict() -> None:
    msg = _fake_ai_message(
        usage_metadata={"input_tokens": 1234, "output_tokens": 56, "total_tokens": 1290}
    )
    parsed = ChatLLM._parse_response(msg)
    assert parsed.usage_metadata == {
        "input_tokens": 1234,
        "output_tokens": 56,
        "total_tokens": 1290,
    }


def test_parse_response_normalises_typed_dict_like_usage_to_plain_dict() -> None:
    """Some LangChain versions return a TypedDict; we want a plain dict on the wire."""

    class _UsageLike:
        def __iter__(self):
            return iter([("input_tokens", 7), ("output_tokens", 11)])

    msg = _fake_ai_message(usage_metadata=_UsageLike())
    parsed = ChatLLM._parse_response(msg)
    assert isinstance(parsed.usage_metadata, dict)
    assert parsed.usage_metadata == {"input_tokens": 7, "output_tokens": 11}


def test_parse_response_keeps_usage_metadata_none_when_provider_omits_it() -> None:
    msg = _fake_ai_message(usage_metadata=None)
    parsed = ChatLLM._parse_response(msg)
    assert parsed.usage_metadata is None


def test_parse_response_handles_unconvertible_usage_gracefully() -> None:
    """A non-iterable, non-dict usage object should degrade to None, not crash."""
    msg = _fake_ai_message(usage_metadata=object())
    parsed = ChatLLM._parse_response(msg)
    assert parsed.usage_metadata is None


# --------------------------------------------------------------------------- #
# worker._estimate_tokens — prefers real counts, falls back otherwise
# --------------------------------------------------------------------------- #


def test_estimate_tokens_uses_real_usage_metadata_when_present() -> None:
    response = LLMResponse(
        content="ignored for this assertion",
        usage_metadata={"input_tokens": 980_137, "output_tokens": 15_868},
    )
    in_tok, out_tok = _estimate_tokens(messages=[{"role": "user", "content": "x" * 1_000_000}], response=response)
    # Real provider counts win even though the heuristic would over-estimate
    # massively from the bogus 1M-char message payload above.
    assert in_tok == 980_137
    assert out_tok == 15_868


def test_estimate_tokens_falls_back_when_usage_metadata_is_none() -> None:
    messages = [{"role": "user", "content": "hello world"}]
    response = LLMResponse(content="howdy", usage_metadata=None)
    in_tok, out_tok = _estimate_tokens(messages, response)
    # Heuristic: roughly len(json.dumps(messages)) // 4 and len(content) // 4.
    # We don't pin exact numbers (they depend on json formatting) but they
    # must be positive and proportional to length.
    assert in_tok > 0
    assert out_tok == len("howdy") // 4


def test_estimate_tokens_falls_back_when_usage_metadata_is_all_zero() -> None:
    """A provider that returns ``{"input_tokens": 0, "output_tokens": 0}`` is
    treated as 'no real data' so we don't pin per-run totals at zero."""
    messages = [{"role": "user", "content": "hello"}]
    response = LLMResponse(
        content="hi back",
        usage_metadata={"input_tokens": 0, "output_tokens": 0},
    )
    in_tok, out_tok = _estimate_tokens(messages, response)
    assert in_tok > 0
    assert out_tok > 0


def test_estimate_tokens_partial_usage_metadata_is_used_directly() -> None:
    """If the provider reports input but not output, take input verbatim and
    let output drop to 0 — better than silently mixing real + heuristic."""
    response = LLMResponse(
        content="some text",
        usage_metadata={"input_tokens": 500, "output_tokens": 0},
    )
    in_tok, out_tok = _estimate_tokens([], response)
    assert in_tok == 500
    assert out_tok == 0


def test_estimate_tokens_handles_non_llmresponse_object_safely() -> None:
    """Defensive: callers from older code paths might pass a raw string."""
    in_tok, out_tok = _estimate_tokens([{"role": "user", "content": "abc"}], "not-an-LLMResponse")
    # Input falls through to the heuristic; output can't be derived without
    # an LLMResponse, so it's 0 — same as the old behaviour.
    assert in_tok > 0
    assert out_tok == 0


@pytest.mark.parametrize("metadata_keys_extra", [
    {},
    {"total_tokens": 12345},
    {"input_token_details": {"cached": 100}, "output_token_details": {"reasoning": 50}},
])
def test_estimate_tokens_ignores_extra_metadata_fields(metadata_keys_extra: dict) -> None:
    """LangChain occasionally returns extra fields (cache hits, reasoning
    sub-counts). They should not interfere with the bare input/output read."""
    metadata = {"input_tokens": 100, "output_tokens": 20, **metadata_keys_extra}
    response = LLMResponse(content="x", usage_metadata=metadata)
    in_tok, out_tok = _estimate_tokens([], response)
    assert in_tok == 100
    assert out_tok == 20
