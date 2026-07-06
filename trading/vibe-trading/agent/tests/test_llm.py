"""Tests for LLM provider mapping and JSON extraction."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.providers.capabilities import get_provider_capabilities, provider_env_names
from src.providers.llm import _sync_provider_env, build_llm


class TestProviderCapabilityAliases:
    """Provider aliases and model-name inference."""

    def test_glm_alias_uses_zhipu_capabilities(self) -> None:
        glm_caps = get_provider_capabilities("glm")
        zhipu_caps = get_provider_capabilities("zhipu")

        assert (
            glm_caps.name,
            glm_caps.api_key_env,
            glm_caps.base_url_env,
        ) == (
            zhipu_caps.name,
            zhipu_caps.api_key_env,
            zhipu_caps.base_url_env,
        )

    @pytest.mark.parametrize("model", ["glm-4.6", "glm-5.1"])
    def test_glm_model_inference_uses_zhipu(self, model: str) -> None:
        caps = get_provider_capabilities(provider=None, model=model)

        assert caps.name == "zhipu"

    def test_glm_provider_env_names_use_zhipu_env(self) -> None:
        assert provider_env_names("glm") == ("ZHIPU_API_KEY", "ZHIPU_BASE_URL")

    @pytest.mark.parametrize("model", ["", "something-unknown"])
    def test_unknown_or_empty_model_without_provider_falls_back_to_openai(
        self,
        model: str,
    ) -> None:
        caps = get_provider_capabilities(provider=None, model=model)

        assert caps.name == "openai"


# ---------------------------------------------------------------------------
# _sync_provider_env
# ---------------------------------------------------------------------------


class TestSyncProviderEnv:
    """Provider-specific env vars → OPENAI_* mapping."""

    def _run_sync(self, env: dict[str, str]) -> dict[str, str]:
        """Run _sync_provider_env with a clean env and return relevant keys."""
        # Reset the dotenv guard so it doesn't skip
        import src.providers.llm as llm_mod
        llm_mod._dotenv_loaded = True  # pretend already loaded

        clean = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI_", "LANGCHAIN_", "DEEPSEEK_", "GROQ_", "OLLAMA_", "DASHSCOPE_", "ZAI_"))}
        clean.update(env)
        with patch.dict(os.environ, clean, clear=True):
            _sync_provider_env()
            return {
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                "OPENAI_API_BASE": os.environ.get("OPENAI_API_BASE", ""),
                "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL", ""),
            }

    def test_openai_default(self) -> None:
        result = self._run_sync({
            "OPENAI_API_KEY": "sk-test",
        })
        assert result["OPENAI_API_KEY"] == "sk-test"

    def test_openai_codex_provider_does_not_map_oauth_token_to_api_key(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "openai-codex",
            "OPENAI_CODEX_BASE_URL": "https://chatgpt.com/backend-api/codex/responses",
        })
        assert result["OPENAI_API_KEY"] == ""
        assert result["OPENAI_API_BASE"] == "https://chatgpt.com/backend-api/codex/responses"

    def test_deepseek_provider(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "ds-key-123",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
        })
        assert result["OPENAI_API_KEY"] == "ds-key-123"
        assert result["OPENAI_API_BASE"] == "https://api.deepseek.com/v1"

    def test_groq_provider(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk-test",
            "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        })
        assert result["OPENAI_API_KEY"] == "gsk-test"
        assert "groq" in result["OPENAI_API_BASE"]

    def test_ollama_no_key_required(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
        })
        # Ollama uses "ollama" as fallback key
        assert result["OPENAI_API_KEY"] in ("ollama", "")
        assert result["OPENAI_API_BASE"] == "http://localhost:11434/v1"

    def test_ollama_base_url_appends_v1(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://23.152.56.42:11434/",
        })
        assert result["OPENAI_API_BASE"] == "http://23.152.56.42:11434/v1"
        assert result["OPENAI_BASE_URL"] == "http://23.152.56.42:11434/v1"

    def test_qwen_alias_to_dashscope(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "qwen",
            "DASHSCOPE_API_KEY": "qwen-key",
            "DASHSCOPE_BASE_URL": "https://dashscope.aliyuncs.com/v1",
        })
        assert result["OPENAI_API_KEY"] == "qwen-key"

    def test_zai_provider(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "zai",
            "ZAI_API_KEY": "zai-key-test",
            "ZAI_BASE_URL": "https://api.z.ai/api/coding/paas/v4",
        })
        assert result["OPENAI_API_KEY"] == "zai-key-test"
        assert result["OPENAI_API_BASE"] == "https://api.z.ai/api/coding/paas/v4"

    def test_unknown_provider_falls_back_to_openai(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "unknown_provider_xyz",
            "OPENAI_API_KEY": "sk-fallback",
        })
        assert result["OPENAI_API_KEY"] == "sk-fallback"

    def test_provider_key_fallback_to_openai_key(self) -> None:
        """If provider-specific key is missing, fall back to OPENAI_API_KEY."""
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "deepseek",
            "OPENAI_API_KEY": "sk-shared",
        })
        assert result["OPENAI_API_KEY"] == "sk-shared"

    def test_minimax_provider(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "minimax-key-123",
            "MINIMAX_BASE_URL": "https://api.minimax.io/v1",
        })
        assert result["OPENAI_API_KEY"] == "minimax-key-123"
        assert result["OPENAI_API_BASE"] == "https://api.minimax.io/v1"

    def test_minimax_base_url_in_openai_base_url(self) -> None:
        result = self._run_sync({
            "LANGCHAIN_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "minimax-key",
            "MINIMAX_BASE_URL": "https://api.minimax.io/v1",
        })
        assert "minimax.io" in result["OPENAI_BASE_URL"]


# ---------------------------------------------------------------------------
# MiniMax temperature clamping
# ---------------------------------------------------------------------------


class TestMinimaxTemperature:
    """MiniMax requires temperature > 0; build_llm should clamp the default."""

    def test_minimax_temperature_clamped_from_zero(self) -> None:
        """When LANGCHAIN_TEMPERATURE=0.0 and provider=minimax, temperature must be clamped to 0.01."""
        import src.providers.llm as llm_mod
        llm_mod._dotenv_loaded = True

        captured: dict[str, float] = {}

        class _FakeChatOpenAI:
            def __init__(self, **kwargs: object) -> None:
                captured["temperature"] = float(kwargs.get("temperature", -1))

        env = {
            "LANGCHAIN_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "minimax-key",
            "MINIMAX_BASE_URL": "https://api.minimax.io/v1",
            "LANGCHAIN_MODEL_NAME": "MiniMax-M3",
            "LANGCHAIN_TEMPERATURE": "0.0",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch.object(llm_mod, "ChatOpenAIWithReasoning", _FakeChatOpenAI):
                build_llm()
        assert captured["temperature"] == 0.01, (
            "MiniMax temperature must be clamped to 0.01 when 0.0 is configured"
        )

    def test_minimax_positive_temperature_preserved(self) -> None:
        """When an explicit positive temperature is set, it should be preserved."""
        import src.providers.llm as llm_mod
        llm_mod._dotenv_loaded = True

        captured: dict[str, float] = {}

        class _FakeChatOpenAI:
            def __init__(self, **kwargs: object) -> None:
                captured["temperature"] = float(kwargs.get("temperature", -1))

        env = {
            "LANGCHAIN_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "minimax-key",
            "MINIMAX_BASE_URL": "https://api.minimax.io/v1",
            "LANGCHAIN_MODEL_NAME": "MiniMax-M3",
            "LANGCHAIN_TEMPERATURE": "0.7",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch.object(llm_mod, "ChatOpenAIWithReasoning", _FakeChatOpenAI):
                build_llm()
        assert captured["temperature"] == 0.7


class TestReasoningEffortPassthrough:
    """LANGCHAIN_REASONING_EFFORT is forwarded as extra_body.reasoning.effort
    to the underlying OpenAI-compatible client. Used for OpenRouter-style
    relays that require opt-in to enable thinking."""

    def _capture(self, env: dict[str, str]) -> dict:
        import src.providers.llm as llm_mod
        llm_mod._dotenv_loaded = True

        captured: dict = {}

        class _FakeChatOpenAI:
            def __init__(self, **kwargs: object) -> None:
                captured.update(kwargs)

        with patch.dict(os.environ, env, clear=True):
            with patch.object(llm_mod, "ChatOpenAIWithReasoning", _FakeChatOpenAI):
                build_llm()
        return captured

    def test_effort_unset_leaves_extra_body_none(self) -> None:
        captured = self._capture({
            "LANGCHAIN_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "LANGCHAIN_MODEL_NAME": "gpt-4",
        })
        assert captured["extra_body"] is None

    def test_effort_medium_forwarded_as_extra_body(self) -> None:
        captured = self._capture({
            "LANGCHAIN_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": "or-test",
            "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
            "LANGCHAIN_MODEL_NAME": "moonshotai/kimi-k2-thinking",
            "LANGCHAIN_REASONING_EFFORT": "medium",
        })
        assert captured["extra_body"] == {"reasoning": {"effort": "medium"}}

    def test_effort_case_insensitive(self) -> None:
        captured = self._capture({
            "LANGCHAIN_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": "or-test",
            "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
            "LANGCHAIN_MODEL_NAME": "moonshotai/kimi-k2-thinking",
            "LANGCHAIN_REASONING_EFFORT": "HIGH",
        })
        assert captured["extra_body"]["reasoning"]["effort"] == "high"

