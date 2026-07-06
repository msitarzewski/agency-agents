"""The OpenAI-compatible provider registry is the single source of truth for the
family; this guards each provider's resolved config (base URL, subclass, auth,
Responses API) so a future edit can't silently break one.
"""
import pytest

from tradingagents.llm_clients.openai_client import (
    OPENAI_COMPATIBLE_PROVIDERS,
    DeepSeekChatOpenAI,
    MinimaxChatOpenAI,
    NormalizedChatOpenAI,
    is_openai_compatible,
)


@pytest.mark.unit
def test_registry_membership():
    assert is_openai_compatible("openai")
    assert is_openai_compatible("openai_compatible")  # the generic endpoint
    # native (different API) clients are intentionally NOT in the registry
    assert not is_openai_compatible("anthropic")
    assert not is_openai_compatible("google")
    assert not is_openai_compatible("azure")


@pytest.mark.unit
@pytest.mark.parametrize("provider,base_url,chat_class,responses", [
    ("openai", None, NormalizedChatOpenAI, True),
    ("xai", "https://api.x.ai/v1", NormalizedChatOpenAI, False),
    ("deepseek", "https://api.deepseek.com", DeepSeekChatOpenAI, False),
    ("qwen", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", NormalizedChatOpenAI, False),
    ("qwen-cn", "https://dashscope.aliyuncs.com/compatible-mode/v1", NormalizedChatOpenAI, False),
    ("glm", "https://api.z.ai/api/paas/v4/", NormalizedChatOpenAI, False),
    ("glm-cn", "https://open.bigmodel.cn/api/paas/v4/", NormalizedChatOpenAI, False),
    ("minimax", "https://api.minimax.io/v1", MinimaxChatOpenAI, False),
    ("minimax-cn", "https://api.minimaxi.com/v1", MinimaxChatOpenAI, False),
    ("openrouter", "https://openrouter.ai/api/v1", NormalizedChatOpenAI, False),
    ("mistral", "https://api.mistral.ai/v1", NormalizedChatOpenAI, False),
    ("kimi", "https://api.moonshot.ai/v1", NormalizedChatOpenAI, False),
    ("groq", "https://api.groq.com/openai/v1", NormalizedChatOpenAI, False),
    ("nvidia", "https://integrate.api.nvidia.com/v1", NormalizedChatOpenAI, False),
    ("ollama", "http://localhost:11434/v1", NormalizedChatOpenAI, False),
])
def test_registry_spec(provider, base_url, chat_class, responses):
    spec = OPENAI_COMPATIBLE_PROVIDERS[provider]
    assert spec.base_url == base_url
    assert spec.chat_class is chat_class
    assert spec.use_responses_api is responses


@pytest.mark.unit
def test_key_optionality():
    # Local/generic endpoints are key-optional; hosted APIs require a key.
    assert OPENAI_COMPATIBLE_PROVIDERS["ollama"].key_optional is True
    assert OPENAI_COMPATIBLE_PROVIDERS["openai_compatible"].key_optional is True
    assert OPENAI_COMPATIBLE_PROVIDERS["openai_compatible"].require_base_url is True
    assert OPENAI_COMPATIBLE_PROVIDERS["xai"].key_optional is False
    # OLLAMA_BASE_URL is the only base-URL env override.
    assert OPENAI_COMPATIBLE_PROVIDERS["ollama"].base_url_env == "OLLAMA_BASE_URL"
