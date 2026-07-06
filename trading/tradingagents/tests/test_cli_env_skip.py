"""Tests for env-driven CLI behavior (#897, #873).

The config-layer override (TRADINGAGENTS_* -> DEFAULT_CONFIG) is covered by
test_env_overrides.py. These tests cover the CLI layer: an env-configured
provider/model/language must skip its interactive prompt and use the value.
"""

import os
import unittest
from unittest import mock

import pytest


@pytest.mark.unit
class TestProviderDefaultUrl(unittest.TestCase):
    def test_known_providers_resolve(self):
        from cli.utils import provider_default_url
        self.assertEqual(provider_default_url("openai"), "https://api.openai.com/v1")
        self.assertEqual(provider_default_url("DeepSeek"), "https://api.deepseek.com")
        self.assertIsNone(provider_default_url("google"))  # uses SDK default

    def test_unknown_provider_returns_none(self):
        from cli.utils import provider_default_url
        self.assertIsNone(provider_default_url("not-a-provider"))

    def test_ollama_honors_base_url_env(self):
        from cli.utils import provider_default_url
        with mock.patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://host:1234/v1"}):
            self.assertEqual(provider_default_url("ollama"), "http://host:1234/v1")


@pytest.mark.unit
class TestCliSkipsPromptsFromEnv(unittest.TestCase):
    def test_env_config_skips_llm_prompts(self):
        import cli.main as m

        env = {
            "TRADINGAGENTS_LLM_PROVIDER": "openai",
            "TRADINGAGENTS_DEEP_THINK_LLM": "kimi-k2.5",
            "TRADINGAGENTS_QUICK_THINK_LLM": "deepseek-v4-pro",
            "TRADINGAGENTS_LLM_BACKEND_URL": "https://opencode.ai/zen/go/v1",
            "TRADINGAGENTS_OUTPUT_LANGUAGE": "Japanese",
        }
        fake_cfg = dict(m.DEFAULT_CONFIG)
        fake_cfg.update({
            "llm_provider": "openai",
            "backend_url": "https://opencode.ai/zen/go/v1",
            "quick_think_llm": "deepseek-v4-pro",
            "deep_think_llm": "kimi-k2.5",
            "output_language": "Japanese",
        })

        with mock.patch.dict(os.environ, env, clear=False), \
             mock.patch.object(m, "DEFAULT_CONFIG", fake_cfg), \
             mock.patch.object(m, "fetch_announcements", return_value=None), \
             mock.patch.object(m, "display_announcements"), \
             mock.patch.object(m, "get_ticker", return_value="AAPL"), \
             mock.patch.object(m, "get_analysis_date", return_value="2026-05-29"), \
             mock.patch.object(m, "select_analysts", return_value=[]), \
             mock.patch.object(m, "select_research_depth", return_value=1), \
             mock.patch.object(m, "ensure_api_key") as ensure_key, \
             mock.patch.object(m, "select_llm_provider") as prompt_provider, \
             mock.patch.object(m, "ask_output_language") as prompt_lang, \
             mock.patch.object(m, "select_shallow_thinking_agent") as prompt_quick, \
             mock.patch.object(m, "select_deep_thinking_agent") as prompt_deep:
            sel = m.get_user_selections()

        # None of the LLM selection prompts should have been shown.
        prompt_provider.assert_not_called()
        prompt_lang.assert_not_called()
        prompt_quick.assert_not_called()
        prompt_deep.assert_not_called()
        # API key is still verified for the env-configured provider.
        ensure_key.assert_called_once()

        # The env values flow into the returned selections.
        self.assertEqual(sel["llm_provider"], "openai")
        self.assertEqual(sel["backend_url"], "https://opencode.ai/zen/go/v1")
        self.assertEqual(sel["shallow_thinker"], "deepseek-v4-pro")
        self.assertEqual(sel["deep_thinker"], "kimi-k2.5")
        self.assertEqual(sel["output_language"], "Japanese")


@pytest.mark.unit
class TestResearchDepthSkippedFromEnv(unittest.TestCase):
    def test_both_round_envs_skip_depth_prompt(self):
        import cli.main as m

        env = {
            "TRADINGAGENTS_MAX_DEBATE_ROUNDS": "2",
            "TRADINGAGENTS_MAX_RISK_ROUNDS": "4",
        }
        fake_cfg = dict(m.DEFAULT_CONFIG)
        fake_cfg.update({"max_debate_rounds": 2, "max_risk_discuss_rounds": 4})

        with mock.patch.dict(os.environ, env, clear=False), \
             mock.patch.object(m, "DEFAULT_CONFIG", fake_cfg), \
             mock.patch.object(m, "fetch_announcements", return_value=None), \
             mock.patch.object(m, "display_announcements"), \
             mock.patch.object(m, "get_ticker", return_value="AAPL"), \
             mock.patch.object(m, "get_analysis_date", return_value="2026-05-29"), \
             mock.patch.object(m, "select_analysts", return_value=[]), \
             mock.patch.object(m, "select_research_depth") as prompt_depth, \
             mock.patch.object(m, "ensure_api_key"), \
             mock.patch.object(m, "select_llm_provider", return_value=("openai", None)), \
             mock.patch.object(m, "ask_output_language", return_value="English"), \
             mock.patch.object(m, "select_shallow_thinking_agent", return_value="gpt-5.4-mini"), \
             mock.patch.object(m, "select_deep_thinking_agent", return_value="gpt-5.5"), \
             mock.patch.object(m, "ask_openai_reasoning_effort", return_value=None):
            sel = m.get_user_selections()

        # The research-depth prompt is skipped; the value comes from the env config.
        prompt_depth.assert_not_called()
        self.assertEqual(sel["research_depth"], 2)


@pytest.mark.unit
class TestReasoningEffortSkippedFromEnv(unittest.TestCase):
    def test_effort_env_skips_step8_prompt(self):
        import cli.main as m

        env = {"TRADINGAGENTS_OPENAI_REASONING_EFFORT": "high"}
        fake_cfg = dict(m.DEFAULT_CONFIG)
        fake_cfg.update({"openai_reasoning_effort": "high"})

        with mock.patch.dict(os.environ, env, clear=False), \
             mock.patch.object(m, "DEFAULT_CONFIG", fake_cfg), \
             mock.patch.object(m, "fetch_announcements", return_value=None), \
             mock.patch.object(m, "display_announcements"), \
             mock.patch.object(m, "get_ticker", return_value="AAPL"), \
             mock.patch.object(m, "get_analysis_date", return_value="2026-05-29"), \
             mock.patch.object(m, "select_analysts", return_value=[]), \
             mock.patch.object(m, "select_research_depth", return_value=1), \
             mock.patch.object(m, "ensure_api_key"), \
             mock.patch.object(m, "select_llm_provider", return_value=("openai", None)), \
             mock.patch.object(m, "ask_output_language", return_value="English"), \
             mock.patch.object(m, "select_shallow_thinking_agent", return_value="gpt-5.4-mini"), \
             mock.patch.object(m, "select_deep_thinking_agent", return_value="gpt-5.5"), \
             mock.patch.object(m, "ask_openai_reasoning_effort") as prompt_effort:
            sel = m.get_user_selections()

        # The reasoning-effort prompt is skipped; the value comes from env config.
        prompt_effort.assert_not_called()
        self.assertEqual(sel["openai_reasoning_effort"], "high")


if __name__ == "__main__":
    unittest.main()
