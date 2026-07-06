"""OpenAI ``reasoning_effort`` is gated to reasoning models.

Non-reasoning OpenAI models (gpt-4.1, gpt-4o, ...) 400 with "Unsupported
parameter: 'reasoning.effort'". The client must drop the kwarg for those rather
than forward it and crash the run. The GPT-5 family and the o-series accept it.
"""

import pytest

from tradingagents.llm_clients.openai_client import (
    OpenAIClient,
    _supports_reasoning_effort,
)


@pytest.mark.parametrize(
    "model,expected",
    [
        ("gpt-5.5", True), ("gpt-5.4", True), ("gpt-5.4-mini", True),
        ("gpt-5.5-pro", True), ("o1", True), ("o3-mini", True),
        ("gpt-4.1", False), ("gpt-4o", False), ("gpt-4o-mini", False),
        ("gpt-3.5-turbo", False),
    ],
)
def test_supports_reasoning_effort(model, expected):
    assert _supports_reasoning_effort(model) is expected


def _effort_on(model, monkeypatch):
    # A fake key lets get_llm() construct the client without a network call.
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    llm = OpenAIClient(model, provider="openai", reasoning_effort="low").get_llm()
    return getattr(llm, "reasoning_effort", None)


def test_reasoning_model_receives_effort(monkeypatch):
    assert _effort_on("gpt-5.4-mini", monkeypatch) == "low"


def test_non_reasoning_model_drops_effort(monkeypatch):
    # gpt-4.1 would 400 with reasoning_effort — it must be dropped.
    assert _effort_on("gpt-4.1", monkeypatch) is None
