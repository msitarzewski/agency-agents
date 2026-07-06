import unittest
import warnings
from types import ModuleType
from unittest.mock import patch

from tradingagents.llm_clients.base_client import BaseLLMClient
from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.model_catalog import get_known_models
from tradingagents.llm_clients.validators import validate_model


class DummyLLMClient(BaseLLMClient):
    def __init__(self, provider: str, model: str):
        self.provider = provider
        super().__init__(model)

    def get_llm(self):
        self.warn_if_unknown_model()
        return object()

    def validate_model(self) -> bool:
        return validate_model(self.provider, self.model)


class ModelValidationTests(unittest.TestCase):
    def test_catalog_models_are_validator_approved(self):
        for provider, models in get_known_models().items():
            if provider in ("ollama", "openrouter", "aihubmix", "custom_openai"):
                continue

            for model in models:
                with self.subTest(provider=provider, model=model):
                    self.assertTrue(validate_model(provider, model))

    def test_unknown_model_emits_warning_for_strict_provider(self):
        client = DummyLLMClient("openai", "not-a-real-openai-model")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.get_llm()

        self.assertEqual(len(caught), 1)
        self.assertIn("not-a-real-openai-model", str(caught[0].message))
        self.assertIn("openai", str(caught[0].message))

    def test_openrouter_aihubmix_ollama_and_custom_openai_allow_custom_models(self):
        for provider in ("openrouter", "aihubmix", "ollama", "custom_openai"):
            client = DummyLLMClient(provider, "custom-model-name")

            with self.subTest(provider=provider):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    client.get_llm()

                self.assertEqual(caught, [])

    def test_factory_supports_qianfan_as_openai_compatible(self):
        fake_langchain_openai = ModuleType("langchain_openai")

        class _FakeChatOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_langchain_openai.ChatOpenAI = _FakeChatOpenAI

        with patch.dict("sys.modules", {"langchain_openai": fake_langchain_openai}):
            client = create_llm_client("qianfan", "ernie-4.0-8k")

        self.assertEqual(client.provider, "qianfan")

    def test_factory_supports_google_via_compatible_adapter(self):
        fake_google_adapter = ModuleType("tradingagents.llm_adapters.google_openai_adapter")

        class _FakeChatGoogleOpenAI:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        fake_google_adapter.ChatGoogleOpenAI = _FakeChatGoogleOpenAI

        with patch.dict("sys.modules", {"tradingagents.llm_adapters.google_openai_adapter": fake_google_adapter}):
            client = create_llm_client("google", "gemini-2.5-pro")

        self.assertEqual(client.__class__.__name__, "GoogleClient")


if __name__ == "__main__":
    unittest.main()
