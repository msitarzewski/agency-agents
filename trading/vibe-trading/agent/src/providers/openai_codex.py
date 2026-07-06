"""OpenAI Codex OAuth provider.

This provider follows nanobot's OpenAI Codex OAuth path: a ChatGPT account is
authenticated by oauth-cli-kit, then requests are sent to the ChatGPT Codex
Responses endpoint. It is intentionally separate from the standard OpenAI API
key path because ChatGPT OAuth tokens are not OpenAI API keys.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

DEFAULT_CODEX_URL = "https://chatgpt.com/backend-api/codex/responses"
DEFAULT_ORIGINATOR = "vibe-trading"


@dataclass
class CodexToolCall:
    """Internal tool-call representation compatible with ChatLLM parsing."""

    id: str
    name: str
    arguments: dict[str, Any]

    def as_langchain_tool_call(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "args": self.arguments}


@dataclass
class CodexAIMessage:
    """Small LangChain-like message object used by ChatLLM."""

    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    additional_kwargs: dict[str, Any] = field(default_factory=dict)
    response_metadata: dict[str, Any] = field(default_factory=lambda: {"finish_reason": "stop"})

    def __add__(self, other: "CodexAIMessage") -> "CodexAIMessage":
        finish_reason = other.response_metadata.get(
            "finish_reason",
            self.response_metadata.get("finish_reason", "stop"),
        )
        reasoning = (
            self.additional_kwargs.get("reasoning_content", "")
            + other.additional_kwargs.get("reasoning_content", "")
        )
        return CodexAIMessage(
            content=(self.content or "") + (other.content or ""),
            tool_calls=[*self.tool_calls, *other.tool_calls],
            additional_kwargs={"reasoning_content": reasoning} if reasoning else {},
            response_metadata={"finish_reason": finish_reason},
        )


def login_openai_codex(
    print_fn: Callable[[str], None] | None = None,
    prompt_fn: Callable[[str], str] | None = None,
) -> Any:
    """Run interactive ChatGPT/Codex OAuth login and persist the token."""
    try:
        from oauth_cli_kit import get_token, login_oauth_interactive
    except ImportError as exc:
        raise RuntimeError("oauth-cli-kit is not installed. Run: pip install oauth-cli-kit") from exc

    token = None
    try:
        token = get_token()
    except Exception:
        pass
    if token and getattr(token, "access", None):
        return token
    return login_oauth_interactive(print_fn=print_fn or print, prompt_fn=prompt_fn or input)


def get_openai_codex_login_status() -> Any | None:
    """Return the persisted OAuth token, if available."""
    try:
        from oauth_cli_kit import get_token
    except ImportError:
        return None
    try:
        token = get_token()
    except Exception:
        return None
    if token and getattr(token, "access", None):
        return token
    return None


def _get_codex_token() -> Any:
    try:
        from oauth_cli_kit import get_token
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI Codex OAuth requires oauth-cli-kit. Install dependencies, then run: "
            "vibe-trading provider login openai-codex"
        ) from exc
    try:
        token = get_token()
    except Exception as exc:
        raise RuntimeError("OpenAI Codex is not logged in. Run: vibe-trading provider login openai-codex") from exc
    if not (token and getattr(token, "access", None) and getattr(token, "account_id", None)):
        raise RuntimeError("OpenAI Codex is not logged in. Run: vibe-trading provider login openai-codex")
    return token


def validate_codex_base_url(url: str) -> str:
    """Validate the only supported ChatGPT Codex OAuth endpoint.

    ChatGPT OAuth tokens must not be sent to arbitrary OpenAI-compatible base
    URLs. The standard OpenAI API remains API-key authenticated; this provider
    is limited to the ChatGPT Codex backend endpoint used by Codex OAuth.
    """
    value = (url or DEFAULT_CODEX_URL).strip().rstrip("/")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "chatgpt.com"
        or parsed.path != "/backend-api/codex/responses"
    ):
        raise ValueError(
            "OpenAI Codex OAuth only supports https://chatgpt.com/backend-api/codex/responses"
        )
    return value


def _build_headers(account_id: str, access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "chatgpt-account-id": account_id,
        "OpenAI-Beta": "responses=experimental",
        "originator": DEFAULT_ORIGINATOR,
        "User-Agent": "vibe-trading (python)",
        "accept": "text/event-stream",
        "content-type": "application/json",
    }


def _strip_model_prefix(model: str) -> str:
    if model.startswith("openai-codex/") or model.startswith("openai_codex/"):
        return model.split("/", 1)[1]
    return model


def _prompt_cache_key(messages: list[dict[str, Any]]) -> str:
    raw = json.dumps(messages, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _convert_user_message(content: Any) -> dict[str, Any]:
    if isinstance(content, str):
        return {"role": "user", "content": [{"type": "input_text", "text": content}]}
    if isinstance(content, list):
        converted: list[dict[str, Any]] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                converted.append({"type": "input_text", "text": item.get("text", "")})
            elif item.get("type") == "image_url":
                url = (item.get("image_url") or {}).get("url")
                if url:
                    converted.append({"type": "input_image", "image_url": url, "detail": "auto"})
        if converted:
            return {"role": "user", "content": converted}
    return {"role": "user", "content": [{"type": "input_text", "text": ""}]}


def _split_tool_call_id(tool_call_id: Any) -> tuple[str, str | None]:
    if isinstance(tool_call_id, str) and tool_call_id:
        if "|" in tool_call_id:
            call_id, item_id = tool_call_id.split("|", 1)
            return call_id, item_id or None
        return tool_call_id, None
    return "call_0", None


def _convert_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    system_prompt = ""
    input_items: list[dict[str, Any]] = []
    for idx, msg in enumerate(messages):
        role = msg.get("role")
        content = msg.get("content")
        if role == "system":
            system_prompt = content if isinstance(content, str) else ""
        elif role == "user":
            input_items.append(_convert_user_message(content))
        elif role == "assistant":
            if isinstance(content, str) and content:
                input_items.append({
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": content}],
                    "status": "completed",
                    "id": f"msg_{idx}",
                })
            for tool_call in msg.get("tool_calls", []) or []:
                fn = tool_call.get("function") or {}
                call_id, item_id = _split_tool_call_id(tool_call.get("id"))
                input_items.append({
                    "type": "function_call",
                    "id": item_id or f"fc_{idx}",
                    "call_id": call_id or f"call_{idx}",
                    "name": fn.get("name"),
                    "arguments": fn.get("arguments") or "{}",
                })
        elif role == "tool":
            call_id, _ = _split_tool_call_id(msg.get("tool_call_id"))
            output = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            input_items.append({"type": "function_call_output", "call_id": call_id, "output": output})
    return system_prompt, input_items


def _convert_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for tool in tools or []:
        fn = (tool.get("function") or {}) if tool.get("type") == "function" else tool
        name = fn.get("name")
        if not name:
            continue
        params = fn.get("parameters") or {}
        converted.append({
            "type": "function",
            "name": name,
            "description": fn.get("description") or "",
            "parameters": params if isinstance(params, dict) else {},
        })
    return converted


def _decode_tool_args(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
    return parsed if isinstance(parsed, dict) else {"raw": raw}


def _map_finish_reason(status: str | None) -> str:
    return {
        "completed": "stop",
        "incomplete": "length",
        "failed": "error",
        "cancelled": "error",
        "content_filter": "content_filter",
    }.get(status or "completed", "stop")


def _events_from_lines(lines: Iterable[str]) -> Iterable[dict[str, Any]]:
    buffer: list[str] = []

    def flush() -> dict[str, Any] | None:
        data_lines = [line[5:].strip() for line in buffer if line.startswith("data:")]
        buffer.clear()
        if not data_lines:
            return None
        data = "\n".join(data_lines).strip()
        if not data or data == "[DONE]":
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    for line in lines:
        if line == "":
            if buffer:
                event = flush()
                if event is not None:
                    yield event
            continue
        buffer.append(line)
    if buffer:
        event = flush()
        if event is not None:
            yield event


def _message_chunks_from_events(events: Iterable[dict[str, Any]]) -> Iterable[CodexAIMessage]:
    tool_buffers: dict[str, dict[str, Any]] = {}
    for event in events:
        event_type = event.get("type")
        if event_type == "response.output_item.added":
            item = event.get("item") or {}
            if item.get("type") == "function_call" and item.get("call_id"):
                tool_buffers[item["call_id"]] = {
                    "id": item.get("id") or "fc_0",
                    "name": item.get("name") or "",
                    "arguments": item.get("arguments") or "",
                }
        elif event_type == "response.output_text.delta":
            delta = event.get("delta") or ""
            if delta:
                yield CodexAIMessage(content=delta)
        elif event_type == "response.function_call_arguments.delta":
            call_id = event.get("call_id")
            if call_id in tool_buffers:
                tool_buffers[call_id]["arguments"] += event.get("delta") or ""
        elif event_type == "response.function_call_arguments.done":
            call_id = event.get("call_id")
            if call_id in tool_buffers:
                tool_buffers[call_id]["arguments"] = event.get("arguments") or ""
        elif event_type == "response.output_item.done":
            item = event.get("item") or {}
            if item.get("type") == "function_call" and item.get("call_id"):
                call_id = item["call_id"]
                buf = tool_buffers.get(call_id) or {}
                args_raw = buf.get("arguments") or item.get("arguments") or "{}"
                tool = CodexToolCall(
                    id=f"{call_id}|{buf.get('id') or item.get('id') or 'fc_0'}",
                    name=buf.get("name") or item.get("name") or "",
                    arguments=_decode_tool_args(args_raw),
                )
                yield CodexAIMessage(tool_calls=[tool.as_langchain_tool_call()])
        elif event_type == "response.completed":
            status = (event.get("response") or {}).get("status")
            yield CodexAIMessage(response_metadata={"finish_reason": _map_finish_reason(status)})
        elif event_type in {"error", "response.failed"}:
            detail = event.get("error") or event.get("message") or event
            raise RuntimeError(f"OpenAI Codex response failed: {str(detail)[:500]}")


class OpenAICodexLLM:
    """Minimal LangChain-compatible adapter for Vibe-Trading's ChatLLM."""

    def __init__(
        self,
        *,
        model: str,
        temperature: float = 0.0,
        timeout: int = 120,
        tools: list[dict[str, Any]] | None = None,
        reasoning_effort: str | None = None,
        codex_url: str | None = None,
    ) -> None:
        if httpx is None:
            raise RuntimeError("OpenAI Codex OAuth requires httpx. Install dependencies first.")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.tools = tools or []
        self.reasoning_effort = reasoning_effort
        self.codex_url = validate_codex_base_url(
            codex_url or os.getenv("OPENAI_CODEX_BASE_URL", DEFAULT_CODEX_URL)
        )

    def bind_tools(self, tools: list[dict[str, Any]]) -> "OpenAICodexLLM":
        return OpenAICodexLLM(
            model=self.model,
            temperature=self.temperature,
            timeout=self.timeout,
            tools=tools,
            reasoning_effort=self.reasoning_effort,
            codex_url=self.codex_url,
        )

    def _body(self, messages: list[dict[str, Any]], *, stream: bool) -> dict[str, Any]:
        system_prompt, input_items = _convert_messages(messages)
        body: dict[str, Any] = {
            "model": _strip_model_prefix(self.model),
            "store": False,
            "stream": stream,
            "instructions": system_prompt,
            "input": input_items,
            "text": {"verbosity": "medium"},
            "include": ["reasoning.encrypted_content"],
            "prompt_cache_key": _prompt_cache_key(messages),
            "tool_choice": "auto",
            "parallel_tool_calls": True,
        }
        tools = _convert_tools(self.tools)
        if tools:
            body["tools"] = tools
        if self.reasoning_effort and self.reasoning_effort.lower() != "none":
            body["reasoning"] = {"effort": self.reasoning_effort.lower()}
        return body

    def _headers(self) -> dict[str, str]:
        token = _get_codex_token()
        return _build_headers(str(token.account_id), str(token.access))

    def stream(self, messages: list[dict[str, Any]], config: Optional[dict[str, Any]] = None) -> Iterable[CodexAIMessage]:
        timeout = (config or {}).get("timeout") or self.timeout
        with httpx.Client(timeout=timeout, follow_redirects=True, trust_env=True) as client:
            with client.stream("POST", self.codex_url, headers=self._headers(), json=self._body(messages, stream=True)) as response:
                if response.status_code != 200:
                    raw = response.read().decode("utf-8", "ignore")
                    raise RuntimeError(f"OpenAI Codex HTTP {response.status_code}: {raw[:500]}")
                yield from _message_chunks_from_events(_events_from_lines(response.iter_lines()))

    def invoke(self, messages: list[dict[str, Any]], config: Optional[dict[str, Any]] = None) -> CodexAIMessage:
        accumulated: CodexAIMessage | None = None
        for chunk in self.stream(messages, config=config):
            accumulated = chunk if accumulated is None else accumulated + chunk
        return accumulated or CodexAIMessage()

    async def ainvoke(self, messages: list[dict[str, Any]], config: Optional[dict[str, Any]] = None) -> CodexAIMessage:
        return await asyncio.to_thread(self.invoke, messages, config)
