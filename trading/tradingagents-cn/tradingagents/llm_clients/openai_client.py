import os
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from .base_client import BaseLLMClient, normalize_content
from .validators import validate_model


class NormalizedChatOpenAI(ChatOpenAI):
    """ChatOpenAI wrapper that normalizes typed content blocks to text."""

    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(input, config, **kwargs))


_PASSTHROUGH_KWARGS = (
    "temperature",
    "max_tokens",
    "timeout",
    "max_retries",
    "callbacks",
    "http_client",
    "http_async_client",
)

_PROVIDER_CONFIG = {
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY"),
    "glm": ("https://open.bigmodel.cn/api/paas/v4/", "ZHIPU_API_KEY"),
    "qianfan": ("https://qianfan.baidubce.com/v2", "QIANFAN_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "aihubmix": ("https://aihubmix.com/v1", "AIHUBMIX_API_KEY"),
    "ollama": ("http://localhost:11434/v1", None),
    "custom_openai": (None, "CUSTOM_OPENAI_API_KEY"),
}


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI and OpenAI-compatible providers."""

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> Any:
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.provider in _PROVIDER_CONFIG:
            default_base_url, api_key_env = _PROVIDER_CONFIG[self.provider]
            llm_kwargs["base_url"] = self.base_url or default_base_url
            if api_key_env:
                api_key = self.kwargs.get("api_key") or os.environ.get(api_key_env)
                if api_key:
                    llm_kwargs["api_key"] = api_key
            else:
                llm_kwargs["api_key"] = "ollama"
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url
            api_key = self.kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key

        for key in _PASSTHROUGH_KWARGS:
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return NormalizedChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        return validate_model(self.provider, self.model)
