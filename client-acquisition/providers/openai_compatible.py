"""Minimal OpenAI-compatible chat-completions client using only the stdlib."""

import json
import os
from typing import Any, Dict
from urllib.request import Request, urlopen


class LLMProviderError(RuntimeError):
    pass


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 90):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL")
        if not api_key or not model:
            raise LLMProviderError("Set LLM_API_KEY and LLM_MODEL before using --provider llm")
        return cls(base_url, api_key, model)

    def generate_json(self, system: str, user: str) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise LLMProviderError(f"LLM request failed: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMProviderError("LLM returned a non-JSON or unexpected response") from exc
        if not isinstance(result, dict):
            raise LLMProviderError("LLM JSON response must be an object")
        return result
