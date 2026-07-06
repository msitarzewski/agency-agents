"""Gemini thinking_level forwarding (Gemini 3.x).

The catalog is Gemini 3.x only, which takes the string ``thinking_level``
directly. Pro accepts low/high; Flash also accepts minimal/medium — an
unsupported "minimal" on Pro is mapped to "low".
"""

from unittest import mock

import pytest

from tradingagents.llm_clients.google_client import GoogleClient


def _captured_kwargs(model, **kwargs):
    captured = {}
    with mock.patch.object(
        __import__("tradingagents.llm_clients.google_client", fromlist=["x"]),
        "NormalizedChatGoogleGenerativeAI",
        lambda **kw: captured.setdefault("kw", kw),
    ):
        GoogleClient(model, api_key="x", **kwargs).get_llm()
    return captured["kw"]


@pytest.mark.parametrize("level", ["minimal", "low", "medium", "high"])
def test_flash_passes_thinking_level_through(level):
    kw = _captured_kwargs("gemini-3.5-flash", thinking_level=level)
    assert kw["thinking_level"] == level
    assert "thinking_budget" not in kw  # the 2.5-era param is gone


def test_pro_remaps_minimal_to_low():
    kw = _captured_kwargs("gemini-3.1-pro-preview", thinking_level="minimal")
    assert kw["thinking_level"] == "low"  # Pro doesn't accept "minimal"


def test_pro_keeps_high():
    kw = _captured_kwargs("gemini-3.1-pro-preview", thinking_level="high")
    assert kw["thinking_level"] == "high"


def test_no_thinking_level_is_omitted():
    kw = _captured_kwargs("gemini-3.5-flash")
    assert "thinking_level" not in kw
    assert "thinking_budget" not in kw
