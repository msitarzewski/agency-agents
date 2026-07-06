"""Tests for the OpenAI Codex OAuth provider adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.providers import llm as llm_mod
from src.providers.openai_codex import (
    DEFAULT_CODEX_URL,
    OpenAICodexLLM,
    _events_from_lines,
    _message_chunks_from_events,
    _strip_model_prefix,
    validate_codex_base_url,
)


DEFAULT_CODEX_MODEL = "openai-codex/gpt-5.3-codex"


def test_provider_default_model_matches_live_codex_account_path() -> None:
    providers_path = Path(__file__).resolve().parents[1] / "src" / "providers" / "llm_providers.json"
    providers = json.loads(providers_path.read_text(encoding="utf-8"))
    codex_provider = next(item for item in providers if item["name"] == "openai-codex")

    assert codex_provider["default_model"] == DEFAULT_CODEX_MODEL


def test_codex_base_url_is_restricted_to_chatgpt_endpoint() -> None:
    assert validate_codex_base_url(DEFAULT_CODEX_URL + "/") == DEFAULT_CODEX_URL

    with pytest.raises(ValueError):
        validate_codex_base_url("https://api.openai.com/v1")


def test_build_llm_returns_codex_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_mod, "_dotenv_loaded", True)
    monkeypatch.setenv("LANGCHAIN_PROVIDER", "openai-codex")
    monkeypatch.setenv("LANGCHAIN_MODEL_NAME", DEFAULT_CODEX_MODEL)
    monkeypatch.setenv("OPENAI_CODEX_BASE_URL", DEFAULT_CODEX_URL)

    adapter = llm_mod.build_llm()

    assert isinstance(adapter, OpenAICodexLLM)
    assert adapter.model == DEFAULT_CODEX_MODEL


def test_codex_body_strips_provider_prefix_and_converts_tools() -> None:
    adapter = OpenAICodexLLM(model=DEFAULT_CODEX_MODEL)

    body = adapter.bind_tools([
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Run a shell command",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}},
            },
        }
    ])._body(
        [
            {"role": "system", "content": "You are careful."},
            {"role": "user", "content": "Say hi."},
        ],
        stream=True,
    )

    assert _strip_model_prefix(DEFAULT_CODEX_MODEL) == "gpt-5.3-codex"
    assert body["model"] == "gpt-5.3-codex"
    assert body["instructions"] == "You are careful."
    assert body["tools"][0]["name"] == "bash"
    assert body["input"][0]["content"][0]["text"] == "Say hi."


def test_missing_codex_token_raises_login_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    oauth_cli_kit = pytest.importorskip(
        "oauth_cli_kit",
        reason="oauth-cli-kit is declared in requirements.txt but optional at runtime",
    )

    def _missing_token() -> None:
        raise RuntimeError("missing")

    monkeypatch.setattr(oauth_cli_kit, "get_token", _missing_token)
    adapter = OpenAICodexLLM(model=DEFAULT_CODEX_MODEL)

    with pytest.raises(RuntimeError, match="vibe-trading provider login openai-codex"):
        adapter._headers()


def test_sse_events_parse_text_and_function_calls() -> None:
    events = list(_events_from_lines([
        'data: {"type":"response.output_text.delta","delta":"Hi"}',
        "",
        'data: {"type":"response.output_item.added","item":{"type":"function_call","call_id":"call_1","id":"fc_1","name":"bash","arguments":""}}',
        "",
        'data: {"type":"response.function_call_arguments.delta","call_id":"call_1","delta":"{\\"command\\":\\"pw"}',
        "",
        'data: {"type":"response.function_call_arguments.delta","call_id":"call_1","delta":"d\\"}"}',
        "",
        'data: {"type":"response.output_item.done","item":{"type":"function_call","call_id":"call_1"}}',
        "",
        "data: [DONE]",
        "",
    ]))

    chunks = list(_message_chunks_from_events(events))

    assert chunks[0].content == "Hi"
    assert chunks[1].tool_calls == [{"id": "call_1|fc_1", "name": "bash", "args": {"command": "pwd"}}]


def test_stream_non_200_response_raises_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResponse:
        status_code = 401

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"unauthorized"

    class _FakeClient:
        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def stream(self, *args: object, **kwargs: object) -> _FakeResponse:
            return _FakeResponse()

    import src.providers.openai_codex as codex_mod

    monkeypatch.setattr(codex_mod.httpx, "Client", _FakeClient)
    adapter = OpenAICodexLLM(model=DEFAULT_CODEX_MODEL)
    adapter._headers = lambda: {}

    with pytest.raises(RuntimeError, match="OpenAI Codex HTTP 401"):
        list(adapter.stream([{"role": "user", "content": "hello"}]))
