"""Regression coverage for current provider default model IDs."""

from __future__ import annotations

import json
from pathlib import Path

import cli
from cli.onboard import PROVIDERS as ONBOARD_PROVIDERS


EXPECTED_PROVIDER_DEFAULTS = {
    "openrouter": "deepseek/deepseek-v4-pro",
    "openai": "gpt-5.5",
    "deepseek": "deepseek-v4-pro",
    "gemini": "gemini-3.5-flash",
    "groq": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "dashscope": "qwen-plus-latest",
    "qwen": "qwen-plus-latest",
    "zhipu": "glm-5.1",
    "glm": "glm-5.1",
    "moonshot": "kimi-k2.6",
    "minimax": "MiniMax-M3",
    "mimo": "MiMo-72B-A27B",
    "zai": "glm-5.1",
}


def test_llm_provider_registry_uses_current_default_models() -> None:
    providers_path = Path(__file__).resolve().parents[1] / "src" / "providers" / "llm_providers.json"
    providers = json.loads(providers_path.read_text(encoding="utf-8"))
    defaults = {item["name"]: item["default_model"] for item in providers}

    for provider, model in EXPECTED_PROVIDER_DEFAULTS.items():
        assert defaults[provider] == model

    assert defaults["openai"] != "gpt-5.5-instant"


def test_interactive_onboard_openai_defaults_to_available_model() -> None:
    provider = next(provider for provider in ONBOARD_PROVIDERS if provider.key == "openai")

    assert provider.default_model == "gpt-5.5"
    assert provider.suggested_models[0] == "gpt-5.5"
    assert "gpt-5.5-pro" in provider.suggested_models
    assert "gpt-5.5-instant" in provider.suggested_models
    assert provider.default_model != "gpt-5.5-instant"


def test_legacy_cli_provider_choices_match_registry_defaults() -> None:
    legacy_defaults = {
        str(item["provider"]): item["model"]
        for item in cli._PROVIDER_CHOICES
        if item["provider"] in EXPECTED_PROVIDER_DEFAULTS
    }

    for provider, model in legacy_defaults.items():
        assert model == EXPECTED_PROVIDER_DEFAULTS[provider]

    assert legacy_defaults["openai"] == "gpt-5.5"


def test_interactive_onboard_suggests_current_primary_models() -> None:
    onboard_defaults = {provider.key: provider.default_model for provider in ONBOARD_PROVIDERS}

    assert onboard_defaults["openrouter"] == "deepseek/deepseek-v4-pro"
    assert onboard_defaults["openai"] == "gpt-5.5"
    assert onboard_defaults["deepseek"] == "deepseek-v4-pro"
