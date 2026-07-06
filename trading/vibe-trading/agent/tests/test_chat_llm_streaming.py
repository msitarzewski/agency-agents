"""ChatLLM streaming liveness and error semantics."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import patch

import pytest

from src.providers.chat import ChatLLM, ProviderStreamError


class _FakeChunk:
    def __init__(
        self,
        *,
        content: str = "",
        reasoning: str = "",
        finish_reason: str = "stop",
    ) -> None:
        self.content = content
        self.tool_calls: list[dict[str, Any]] = []
        self.additional_kwargs = {"reasoning_content": reasoning} if reasoning else {}
        self.response_metadata = {"finish_reason": finish_reason}
        self.usage_metadata = None

    def __add__(self, other: "_FakeChunk") -> "_FakeChunk":
        merged = _FakeChunk(
            content=f"{self.content}{other.content}",
            reasoning=(
                f"{self.additional_kwargs.get('reasoning_content', '')}"
                f"{other.additional_kwargs.get('reasoning_content', '')}"
            ),
            finish_reason=other.response_metadata.get("finish_reason", "stop"),
        )
        return merged


class _FakeStreamingLLM:
    def __init__(self, chunks: list[_FakeChunk] | None = None, exc: Exception | None = None) -> None:
        self.chunks = chunks or []
        self.exc = exc
        self.invoke_called = False

    def bind_tools(self, tools: list[dict[str, Any]]) -> "_FakeStreamingLLM":
        return self

    def stream(self, messages: list[dict[str, Any]], config: dict[str, Any] | None = None):
        if self.exc is not None:
            raise self.exc
        yield from self.chunks

    def invoke(self, messages: list[dict[str, Any]], config: dict[str, Any] | None = None):
        self.invoke_called = True
        return _FakeChunk(content="fallback")


def _client(fake_llm: _FakeStreamingLLM) -> ChatLLM:
    client = ChatLLM.__new__(ChatLLM)
    client.model_name = "deepseek-v4-pro"
    client._llm = fake_llm
    return client


def test_reasoning_only_chunks_emit_progress_without_final_answer_text() -> None:
    fake = _FakeStreamingLLM([
        _FakeChunk(reasoning="thinking "),
        _FakeChunk(reasoning="more"),
        _FakeChunk(content="final"),
    ])
    text_chunks: list[str] = []
    reasoning_chunks: list[str] = []

    response = _client(fake).stream_chat(
        [{"role": "user", "content": "hi"}],
        on_text_chunk=text_chunks.append,
        on_reasoning_chunk=reasoning_chunks.append,
    )

    assert text_chunks == ["final"]
    assert reasoning_chunks == ["thinking ", "more"]
    assert response.content == "final"
    assert response.reasoning_content == "thinking more"


def test_parse_dsml_tool_call_content_as_structured_tool_call() -> None:
    """DeepSeek-style DSML content must drive the ReAct tool path (#261)."""
    content = (
        '<｜｜DSML｜｜tool_calls> '
        '<｜｜DSML｜｜invoke name="bash"> '
        '<｜｜DSML｜｜parameter name="command" string="true">'
        "python -c \"print('vibe-dsml-ok')\""
        "</｜｜DSML｜｜parameter> "
        "</｜｜DSML｜｜invoke> "
        "</｜｜DSML｜｜tool_calls>/"
    )

    response = ChatLLM._parse_response(_FakeChunk(content=content))

    assert response.content == ""
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].id == "dsml_call_1"
    assert response.tool_calls[0].name == "bash"
    assert response.tool_calls[0].arguments == {
        "command": "python -c \"print('vibe-dsml-ok')\""
    }
    assert response.finish_reason == "tool_calls"


def test_parse_dsml_tool_call_requires_pure_tool_call_payload() -> None:
    """Do not execute DSML examples embedded inside normal assistant text."""
    content = (
        "Here is the syntax:\n"
        '<｜｜DSML｜｜tool_calls><｜｜DSML｜｜invoke name="bash">'
        '<｜｜DSML｜｜parameter name="command">pwd</｜｜DSML｜｜parameter>'
        "</｜｜DSML｜｜invoke></｜｜DSML｜｜tool_calls>"
    )

    response = ChatLLM._parse_response(_FakeChunk(content=content))

    assert response.content == content
    assert response.tool_calls == []
    assert response.finish_reason == "stop"


def test_stream_dsml_tool_call_content_is_not_emitted_as_text() -> None:
    """DSML tool-call payloads should not flash as assistant text in CLI/UI."""
    content = (
        '<｜｜DSML｜｜tool_calls>'
        '<｜｜DSML｜｜invoke name="bash">'
        '<｜｜DSML｜｜parameter name="command">pwd</｜｜DSML｜｜parameter>'
        "</｜｜DSML｜｜invoke>"
        "</｜｜DSML｜｜tool_calls>"
    )
    fake = _FakeStreamingLLM([_FakeChunk(content=content)])
    text_chunks: list[str] = []

    response = _client(fake).stream_chat(
        [{"role": "user", "content": "hi"}],
        on_text_chunk=text_chunks.append,
    )

    assert text_chunks == []
    assert response.content == ""
    assert response.tool_calls[0].name == "bash"


def test_should_cancel_stops_stream_early() -> None:
    """A should_cancel predicate breaks the chunk loop; later chunks are dropped."""
    fake = _FakeStreamingLLM([
        _FakeChunk(content="a"),
        _FakeChunk(content="b"),
        _FakeChunk(content="c"),
    ])
    seen: list[str] = []
    calls = {"n": 0}

    def should_cancel() -> bool:
        # Polled at the top of each chunk: let the first through, cancel after.
        n = calls["n"]
        calls["n"] += 1
        return n >= 1

    response = _client(fake).stream_chat(
        [{"role": "user", "content": "hi"}],
        on_text_chunk=seen.append,
        should_cancel=should_cancel,
    )

    assert seen == ["a"]
    assert response.content == "a"


def test_should_cancel_absent_consumes_full_stream() -> None:
    """Without should_cancel the stream is consumed in full (no behavior change)."""
    fake = _FakeStreamingLLM([_FakeChunk(content="x"), _FakeChunk(content="y")])
    seen: list[str] = []

    response = _client(fake).stream_chat(
        [{"role": "user", "content": "hi"}],
        on_text_chunk=seen.append,
    )

    assert seen == ["x", "y"]
    assert response.content == "xy"


def test_stream_failure_raises_provider_error_without_silent_fallback() -> None:
    fake = _FakeStreamingLLM(exc=RuntimeError("stream exploded"))

    with patch.dict(
        os.environ,
        {"LANGCHAIN_PROVIDER": "deepseek", "LANGCHAIN_MODEL_NAME": "deepseek-v4-pro"},
        clear=True,
    ):
        with pytest.raises(ProviderStreamError) as excinfo:
            _client(fake).stream_chat([{"role": "user", "content": "hi"}])

    assert "provider=deepseek" in str(excinfo.value)
    assert "model=deepseek-v4-pro" in str(excinfo.value)
    assert fake.invoke_called is False


def test_stream_error_redacts_configured_secret_values() -> None:
    fake = _FakeStreamingLLM(exc=RuntimeError("bad key sk-live-secret-123456"))

    with patch.dict(
        os.environ,
        {
            "LANGCHAIN_PROVIDER": "deepseek",
            "LANGCHAIN_MODEL_NAME": "deepseek-v4-pro",
            "DEEPSEEK_API_KEY": "sk-live-secret-123456",
        },
        clear=True,
    ):
        with pytest.raises(ProviderStreamError) as excinfo:
            _client(fake).stream_chat([{"role": "user", "content": "hi"}])

    assert "sk-live-secret-123456" not in str(excinfo.value)
    assert "[redacted]" in str(excinfo.value)


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (None, True),   # transport error, no HTTP status — plausibly transient
        (400, False),   # deterministic client error
        (401, False),
        (404, False),
        (408, True),    # request timeout — transient
        (429, True),    # rate limit — transient
        (500, True),
        (503, True),
    ],
)
def test_provider_stream_error_retryable_classification(
    status_code: int | None, expected: bool
) -> None:
    original = Exception("boom")
    if status_code is not None:
        original.status_code = status_code  # type: ignore[attr-defined]
    err = ProviderStreamError(provider="kimi", model="kimi-k2.6", original=original)
    assert err.status_code == status_code
    assert err.retryable is expected


def test_content_filter_triggered_flag() -> None:
    """content_filter finish_reason sets content_filter_triggered=True."""
    response = ChatLLM._parse_response(
        _FakeChunk(content="", finish_reason="content_filter")
    )

    assert response.content == ""
    assert response.finish_reason == "content_filter"
    assert response.content_filter_triggered is True


def test_content_filter_triggered_flag_false_on_stop() -> None:
    """Normal stop reason leaves content_filter_triggered=False."""
    response = ChatLLM._parse_response(
        _FakeChunk(content="text", finish_reason="stop")
    )

    assert response.content == "text"
    assert response.finish_reason == "stop"
    assert response.content_filter_triggered is False
