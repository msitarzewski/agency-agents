"""Tests for the canonical provider->env-var mapping and the CLI key-prompt helper."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from tradingagents.llm_clients.api_key_env import PROVIDER_API_KEY_ENV, get_api_key_env

# ---- Mapping coverage -----------------------------------------------------


def test_every_select_llm_provider_choice_has_an_entry():
    """select_llm_provider() must not present a provider the mapping doesn't know about."""
    # Mirrors the dropdown order in cli/utils.select_llm_provider so the two
    # stay in lockstep. Region-specific keys (qwen-cn / minimax-cn / glm-cn)
    # are reached via the secondary region prompt, so they must also be present.
    expected = {
        "openai", "google", "anthropic", "xai", "deepseek",
        "qwen", "qwen-cn",
        "glm", "glm-cn",
        "minimax", "minimax-cn",
        "openrouter", "azure", "ollama",
    }
    assert expected.issubset(PROVIDER_API_KEY_ENV.keys())


@pytest.mark.parametrize(
    "provider,env_var",
    [
        ("openai",     "OPENAI_API_KEY"),
        ("anthropic",  "ANTHROPIC_API_KEY"),
        ("google",     "GOOGLE_API_KEY"),
        ("azure",      "AZURE_OPENAI_API_KEY"),
        ("xai",        "XAI_API_KEY"),
        ("deepseek",   "DEEPSEEK_API_KEY"),
        ("qwen",       "DASHSCOPE_API_KEY"),
        ("qwen-cn",    "DASHSCOPE_CN_API_KEY"),
        ("glm",        "ZHIPU_API_KEY"),
        ("glm-cn",     "ZHIPU_CN_API_KEY"),
        ("minimax",    "MINIMAX_API_KEY"),
        ("minimax-cn", "MINIMAX_CN_API_KEY"),
        ("openrouter", "OPENROUTER_API_KEY"),
    ],
)
def test_known_providers_resolve(provider, env_var):
    assert get_api_key_env(provider) == env_var


def test_ollama_has_no_key():
    assert get_api_key_env("ollama") is None


def test_unknown_provider_returns_none():
    assert get_api_key_env("not-a-real-provider") is None


def test_case_insensitive_lookup():
    assert get_api_key_env("OpenAI") == "OPENAI_API_KEY"
    assert get_api_key_env("QWEN-CN") == "DASHSCOPE_CN_API_KEY"


# ---- ensure_api_key behavior ---------------------------------------------


@pytest.fixture
def cli_utils(monkeypatch):
    """Import cli.utils with a fresh environment so module-level state is consistent."""
    import importlib

    import cli.utils as cli_utils_module
    return importlib.reload(cli_utils_module)


def test_ensure_api_key_returns_existing(monkeypatch, cli_utils):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-already-set")
    result = cli_utils.ensure_api_key("openai")
    assert result == "sk-already-set"


def test_ensure_api_key_no_op_for_ollama(monkeypatch, cli_utils):
    # Even with no env var set, ollama should not prompt and should return None.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with patch.object(cli_utils, "questionary") as mock_q:
        result = cli_utils.ensure_api_key("ollama")
    assert result is None
    mock_q.password.assert_not_called()


def test_ensure_api_key_unknown_provider_no_prompt(monkeypatch, cli_utils):
    with patch.object(cli_utils, "questionary") as mock_q:
        result = cli_utils.ensure_api_key("totally-fake-provider")
    assert result is None
    mock_q.password.assert_not_called()


def test_ensure_api_key_prompts_and_writes_to_env(monkeypatch, tmp_path, cli_utils):
    """When key is missing, user-pasted value must be written to .env AND os.environ."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    fake_prompt = type("P", (), {"ask": staticmethod(lambda: "sk-deepseek-test")})()
    with patch.object(cli_utils.questionary, "password", return_value=fake_prompt):
        result = cli_utils.ensure_api_key("deepseek")

    assert result == "sk-deepseek-test"
    assert os.environ["DEEPSEEK_API_KEY"] == "sk-deepseek-test"
    env_file = tmp_path / ".env"
    assert env_file.exists()
    assert "DEEPSEEK_API_KEY" in env_file.read_text()
    assert "sk-deepseek-test" in env_file.read_text()


def test_ensure_api_key_user_cancels_returns_none(monkeypatch, tmp_path, cli_utils):
    """Empty prompt response (user cancelled) must not write to .env."""
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    fake_prompt = type("P", (), {"ask": staticmethod(lambda: None)})()
    with patch.object(cli_utils.questionary, "password", return_value=fake_prompt):
        result = cli_utils.ensure_api_key("xai")

    assert result is None
    assert "XAI_API_KEY" not in os.environ
    # .env may or may not exist depending on find_dotenv's walk, but if it
    # does it must not contain the key.
    env_file = tmp_path / ".env"
    if env_file.exists():
        assert "XAI_API_KEY" not in env_file.read_text()


def test_ensure_api_key_updates_existing_env_file(monkeypatch, tmp_path, cli_utils):
    """An existing .env with other keys must be preserved on writeback."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=sk-existing\nOTHER=value\n")

    fake_prompt = type("P", (), {"ask": staticmethod(lambda: "sk-openrouter-new")})()
    with patch.object(cli_utils.questionary, "password", return_value=fake_prompt):
        cli_utils.ensure_api_key("openrouter")

    content = env_file.read_text()
    assert "OPENAI_API_KEY" in content and "sk-existing" in content
    assert "OTHER=value" in content
    assert "OPENROUTER_API_KEY" in content and "sk-openrouter-new" in content
