from typing import Any

from .base_client import BaseLLMClient
from .validators import validate_model


class GoogleClient(BaseLLMClient):
    """Client for Google Gemini models."""

    def get_llm(self) -> Any:
        self.warn_if_unknown_model()
        from tradingagents.llm_adapters.google_openai_adapter import ChatGoogleOpenAI

        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in ("temperature", "max_tokens", "timeout", "max_retries", "callbacks", "http_client", "http_async_client", "transport"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        google_api_key = self.kwargs.get("api_key") or self.kwargs.get("google_api_key")
        if google_api_key:
            llm_kwargs["google_api_key"] = google_api_key

        return ChatGoogleOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        return validate_model("google", self.model)
