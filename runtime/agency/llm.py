"""Anthropic Claude client wrapper used by the agency runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

DEFAULT_MODEL = "claude-opus-4-7"
PLANNER_MODEL = "claude-haiku-4-5"  # cheap model for routing decisions
DEFAULT_MAX_TOKENS = 16000
DEFAULT_PLANNER_MAX_TOKENS = 1024


class LLMError(RuntimeError):
    """Raised when the LLM client is misconfigured or a call fails."""


def _truthy_env(name: str) -> bool:
    import os
    return (os.environ.get(name, "") or "").strip().lower() in ("1", "true", "yes", "on")


@dataclass
class LLMConfig:
    model: str = DEFAULT_MODEL
    planner_model: str = PLANNER_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    api_key: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    # Optional task budget for Opus 4.7 agentic loops.
    # When set, we pass output_config.task_budget and add the beta header.
    task_budget_tokens: int | None = None  # >= 20_000 per Anthropic spec
    betas: list[str] = field(default_factory=list)
    # MCP server passthrough (beta). Each entry is a dict per Anthropic's schema.
    mcp_servers: list[dict] = field(default_factory=list)
    # Opt-in server-side tools that run on Anthropic infra. When enabled, their
    # tool declarations are appended to every request.
    enable_web_search: bool = False
    enable_code_execution: bool = False

    @classmethod
    def from_env(cls) -> "LLMConfig":
        import json, os
        cfg = cls()
        if (m := os.environ.get("AGENCY_MODEL")):
            cfg.model = m
        if (m := os.environ.get("AGENCY_PLANNER_MODEL")):
            cfg.planner_model = m
        if (mt := os.environ.get("AGENCY_MAX_TOKENS")):
            try:
                cfg.max_tokens = int(mt)
            except ValueError:
                pass
        if (tb := os.environ.get("AGENCY_TASK_BUDGET")):
            try:
                cfg.task_budget_tokens = int(tb)
            except ValueError:
                pass
        if (mcp := os.environ.get("AGENCY_MCP_SERVERS")):
            try:
                servers = json.loads(mcp)
                if isinstance(servers, list):
                    cfg.mcp_servers = servers
            except json.JSONDecodeError:
                pass
        cfg.enable_web_search = _truthy_env("AGENCY_ENABLE_WEB_SEARCH")
        cfg.enable_code_execution = _truthy_env("AGENCY_ENABLE_CODE_EXECUTION")
        return cfg


class AnthropicLLM:
    """Thin wrapper around the Anthropic Python SDK.

    Imports `anthropic` lazily so `agency list` and unit tests can run without it.
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client: Any = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as e:
            raise LLMError(
                "The 'anthropic' package is required. Install runtime deps: "
                "pip install -e runtime"
            ) from e
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY is not set. Export it in your shell or pass "
                "api_key= to LLMConfig."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def messages_create(
        self,
        *,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        thinking: dict[str, Any] | None = None,
    ) -> Any:
        """Direct call to messages.create with sensible defaults."""
        client = self._ensure_client()
        kwargs, use_beta = self._build_kwargs(
            system=system, messages=messages, tools=tools,
            model=model, max_tokens=max_tokens, thinking=thinking,
        )
        target = client.beta.messages if use_beta else client.messages
        return target.create(**kwargs)

    def messages_stream(
        self,
        *,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        thinking: dict[str, Any] | None = None,
    ) -> Any:
        """Open a streaming response. Returns the SDK's stream context manager.

        Use as: `with llm.messages_stream(...) as stream: ...`
        Stream exposes `.text_stream`, iterable events, and `.get_final_message()`.
        """
        client = self._ensure_client()
        kwargs, use_beta = self._build_kwargs(
            system=system, messages=messages, tools=tools,
            model=model, max_tokens=max_tokens, thinking=thinking,
        )
        target = client.beta.messages if use_beta else client.messages
        return target.stream(**kwargs)

    def _build_kwargs(self, **opts: Any) -> tuple[dict[str, Any], bool]:
        """Assemble the create/stream kwargs. Returns (kwargs, use_beta)."""
        kwargs: dict[str, Any] = {
            "model": opts["model"] or self.config.model,
            "max_tokens": opts["max_tokens"] or self.config.max_tokens,
            "system": opts["system"],
            "messages": opts["messages"],
        }
        tools = list(opts["tools"] or [])
        if self.config.enable_web_search:
            tools.append({"type": "web_search_20260209", "name": "web_search"})
        if self.config.enable_code_execution:
            tools.append({"type": "code_execution_20260120", "name": "code_execution"})
        if tools:
            kwargs["tools"] = tools
        if opts["thinking"]:
            kwargs["thinking"] = opts["thinking"]
        if self.config.extra_headers:
            kwargs["extra_headers"] = self.config.extra_headers

        use_beta = False
        betas = list(self.config.betas)

        if self.config.task_budget_tokens and self.config.task_budget_tokens >= 20_000:
            kwargs.setdefault("output_config", {})
            kwargs["output_config"]["task_budget"] = {
                "type": "tokens", "total": self.config.task_budget_tokens,
            }
            use_beta = True
            if "task-budgets-2026-03-13" not in betas:
                betas.append("task-budgets-2026-03-13")

        if self.config.mcp_servers:
            kwargs["mcp_servers"] = self.config.mcp_servers
            use_beta = True
            if "mcp-client-2025-11-20" not in betas:
                betas.append("mcp-client-2025-11-20")

        if betas:
            kwargs["betas"] = betas

        return kwargs, use_beta

    @staticmethod
    def cached_system(text: str) -> list[dict[str, Any]]:
        """Build a system prompt list with a cache_control breakpoint at the end.

        The persona body is reused on every turn, so caching it pays for itself
        after the second request.
        """
        return [
            {
                "type": "text",
                "text": text,
                "cache_control": {"type": "ephemeral"},
            }
        ]
