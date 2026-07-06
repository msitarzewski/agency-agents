"""ChatLLM: raw LLM message interface with function calling support.

ChatLLM is designed specifically for the AgentLoop ReAct cycle.
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.providers.content_filter import is_content_filter_triggered
from src.providers.llm import build_llm


def _dedupe_finish_reason(raw: str) -> str:
    """Relays (OpenRouter) emit finish_reason per chunk; AIMessageChunk.__add__
    concatenates into 'stopstop', 'tool_callstool_calls', etc. Return the
    canonical suffix so ReAct equality checks survive.
    """
    return next(
        (m for m in ("tool_calls", "function_call", "content_filter", "length", "stop")
         if raw.endswith(m)),
        raw,
    )


@dataclass
class ToolCallRequest:
    """Tool call request returned by the LLM.

    Attributes:
        id: Tool call ID (used to match tool_result messages).
        name: Tool name.
        arguments: Tool argument dict.
        thought_signature: Gemini thinking-model signature to echo on the next turn.
    """

    id: str
    name: str
    arguments: Dict[str, Any]
    thought_signature: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM response.

    Attributes:
        content: Text content (final answer or thinking text).
        tool_calls: List of tool call requests.
        reasoning_content: Optional thinking trace surfaced by reasoning models.
        finish_reason: Finish reason string.
        usage_metadata: Real token counts reported by the provider, when
            available. Mirrors LangChain's ``AIMessage.usage_metadata`` —
            ``{"input_tokens": int, "output_tokens": int, "total_tokens": int}``.
            ``None`` if the provider did not return usage information; callers
            should fall back to a heuristic in that case.
        content_filter_triggered: ``True`` when the provider blocked the
            response via content moderation (e.g. DashScope/Qwen content
            moderation filter, ``finish_reason == "content_filter"``).
    """

    content: Optional[str] = None
    tool_calls: List[ToolCallRequest] = field(default_factory=list)
    reasoning_content: Optional[str] = None
    finish_reason: str = "stop"
    usage_metadata: Optional[Dict[str, int]] = None
    content_filter_triggered: bool = False

    @property
    def has_tool_calls(self) -> bool:
        """Return True if the response contains tool calls."""
        return len(self.tool_calls) > 0


class ProviderStreamError(RuntimeError):
    """Raised when provider streaming fails before a complete response."""

    def __init__(self, *, provider: str, model: str, original: Exception) -> None:
        """Initialize a provider-contextual stream error.

        Args:
            provider: Effective provider name.
            model: Effective model name.
            original: Original exception from the stream path.
        """
        self.provider = provider
        self.model = model
        self.original = original
        self.status_code: Optional[int] = getattr(original, "status_code", None)
        safe_message = _redact_provider_error(str(original))
        super().__init__(
            f"provider_stream_error provider={provider} model={model}: "
            f"{type(original).__name__}: {safe_message}"
        )

    @property
    def retryable(self) -> bool:
        """Whether a single retry could plausibly succeed.

        Returns:
            False for deterministic client errors (4xx other than 408/429),
            True for everything else — timeouts, rate limits, 5xx, and
            transport errors that carry no HTTP status.
        """
        if self.status_code is None:
            return True
        if self.status_code in (408, 429):
            return True
        return not 400 <= self.status_code < 500


def _redact_provider_error(message: str) -> str:
    """Redact configured secret/proxy values from provider errors."""
    redacted = message
    sensitive_markers = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "PROXY")
    for key, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if any(marker in key.upper() for marker in sensitive_markers):
            redacted = redacted.replace(value, "[redacted]")
    return redacted


_DSML_BAR = r"(?:\|\||｜｜)"
_DSML_TAG = rf"{_DSML_BAR}\s*DSML\s*{_DSML_BAR}"
_DSML_TOOL_CALLS_RE = re.compile(
    rf"<\s*{_DSML_TAG}\s*tool_calls\s*>(?P<body>.*?)"
    rf"</\s*{_DSML_TAG}\s*tool_calls\s*>",
    re.DOTALL,
)
_DSML_INVOKE_RE = re.compile(
    rf"<\s*{_DSML_TAG}\s*invoke\b(?P<attrs>[^>]*)>(?P<body>.*?)"
    rf"</\s*{_DSML_TAG}\s*invoke\s*>",
    re.DOTALL,
)
_DSML_PARAMETER_RE = re.compile(
    rf"<\s*{_DSML_TAG}\s*parameter\b(?P<attrs>[^>]*)>(?P<body>.*?)"
    rf"</\s*{_DSML_TAG}\s*parameter\s*>",
    re.DOTALL,
)
_DSML_ATTR_RE = re.compile(r"""([A-Za-z_][\w:-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
_DSML_PREFIXES = ("<||dsml||tool_calls", "<｜｜dsml｜｜tool_calls")


def _parse_dsml_attrs(raw: str) -> dict[str, str]:
    """Parse attributes from a DSML tag."""
    attrs: dict[str, str] = {}
    for match in _DSML_ATTR_RE.finditer(raw):
        attrs[match.group(1)] = html.unescape(match.group(2) or match.group(3) or "")
    return attrs


def _is_possible_dsml_tool_call_prefix(content: str) -> bool:
    """Return True while buffered stream text could still be a DSML call."""
    compact = re.sub(r"\s+", "", content.lstrip()[:80]).lower()
    if not compact:
        return True
    return any(prefix.startswith(compact) or compact.startswith(prefix) for prefix in _DSML_PREFIXES)


def _parse_dsml_tool_calls(content: Any) -> list[ToolCallRequest]:
    """Parse DeepSeek-style DSML tool calls embedded as assistant content.

    Some OpenAI-compatible relays/models return tool calls as a textual DSML
    block rather than LangChain ``AIMessage.tool_calls``. Treat only pure DSML
    tool-call payloads as executable so examples embedded in normal prose never
    cross into the tool path.
    """
    if not isinstance(content, str):
        return []

    stripped = content.strip()
    blocks = list(_DSML_TOOL_CALLS_RE.finditer(stripped))
    if not blocks:
        return []

    outside = _DSML_TOOL_CALLS_RE.sub("", stripped).strip()
    if outside not in {"", "/"}:
        return []

    tool_calls: list[ToolCallRequest] = []
    for block in blocks:
        for invoke in _DSML_INVOKE_RE.finditer(block.group("body")):
            invoke_attrs = _parse_dsml_attrs(invoke.group("attrs"))
            name = invoke_attrs.get("name", "").strip()
            if not name:
                continue

            arguments: dict[str, Any] = {}
            for param in _DSML_PARAMETER_RE.finditer(invoke.group("body")):
                param_attrs = _parse_dsml_attrs(param.group("attrs"))
                param_name = param_attrs.get("name", "").strip()
                if param_name:
                    arguments[param_name] = html.unescape(param.group("body")).strip()

            tool_calls.append(
                ToolCallRequest(
                    id=f"dsml_call_{len(tool_calls) + 1}",
                    name=name,
                    arguments=arguments,
                )
            )

    return tool_calls


class ChatLLM:
    """LLM chat client with function calling support.

    Uses build_llm() to obtain a ChatOpenAI instance and bind_tools() to attach tool definitions.

    Attributes:
        model_name: Model name.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        """Initialize ChatLLM.

        Args:
            model_name: Model name; defaults to the environment variable value.
        """
        self.model_name = model_name
        self._llm = build_llm(model_name=model_name)

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, timeout: Optional[int] = None) -> LLMResponse:
        """Call the LLM synchronously.

        Args:
            messages: Message list (OpenAI format).
            tools: Tool definition list (OpenAI function calling format).
            timeout: Optional per-call timeout in seconds.

        Returns:
            LLMResponse.
        """
        llm = self._llm.bind_tools(tools) if tools else self._llm
        config = {"timeout": timeout} if timeout else {}
        ai_message = llm.invoke(messages, config=config)
        return self._parse_response(ai_message)

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        on_text_chunk: Optional[Any] = None,
        on_reasoning_chunk: Optional[Any] = None,
        timeout: Optional[int] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> LLMResponse:
        """Stream the LLM and optionally forward text deltas (e.g. thinking).

        Iterates AIMessageChunk; text deltas invoke ``on_text_chunk`` and
        reasoning-only deltas invoke ``on_reasoning_chunk``. Aggregates chunks
        into one response. Stream failures are explicit provider errors.

        Args:
            messages: Messages in OpenAI format.
            tools: Tool definitions for function calling.
            on_text_chunk: Optional callback ``(delta: str) -> None``.
            on_reasoning_chunk: Optional callback ``(delta: str) -> None``.
            timeout: Optional per-call timeout in seconds.
            should_cancel: Optional predicate polled per chunk; when it returns
                True the stream stops early and the partial response is returned.
                Lets a caller abort a live stream promptly (cooperative cancel).

        Returns:
            Parsed ``LLMResponse``.
        """
        try:
            llm = self._llm.bind_tools(tools) if tools else self._llm
            config = {"timeout": timeout} if timeout else {}
            accumulated = None
            pending_text = ""
            possible_dsml_text = True
            for chunk in llm.stream(messages, config=config):
                if should_cancel and should_cancel():
                    break
                if chunk.content and on_text_chunk:
                    if possible_dsml_text:
                        pending_text += chunk.content
                        if _is_possible_dsml_tool_call_prefix(pending_text):
                            pass
                        else:
                            possible_dsml_text = False
                            on_text_chunk(pending_text)
                            pending_text = ""
                    else:
                        on_text_chunk(chunk.content)
                reasoning = getattr(chunk, "additional_kwargs", {}).get("reasoning_content")
                if reasoning and not chunk.content and on_reasoning_chunk:
                    on_reasoning_chunk(reasoning)
                accumulated = chunk if accumulated is None else accumulated + chunk
            if accumulated is None:
                return LLMResponse(content="", tool_calls=[], finish_reason="stop")
            response = self._parse_response(accumulated)
            if pending_text and not (response.has_tool_calls and response.content == ""):
                on_text_chunk(pending_text)
            return response
        except Exception as exc:
            provider = os.getenv("LANGCHAIN_PROVIDER", "openai").strip().lower() or "openai"
            model = self.model_name or os.getenv("LANGCHAIN_MODEL_NAME", "").strip() or "(unset)"
            raise ProviderStreamError(provider=provider, model=model, original=exc) from exc

    @staticmethod
    def _tool_call_thought_signature_maps(ai_message: Any) -> tuple[dict[str, str], dict[int, str]]:
        """Return Gemini thought signatures captured by ``ChatOpenAIWithReasoning``."""
        by_id: dict[str, str] = {}
        by_index: dict[int, str] = {}
        additional_kwargs = getattr(ai_message, "additional_kwargs", {})
        entries = additional_kwargs.get("tool_call_thought_signatures", [])

        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            return by_id, by_index

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            signature = entry.get("thought_signature")
            if not signature:
                continue
            if entry.get("id"):
                by_id[str(entry["id"])] = signature
            index = entry.get("index")
            if isinstance(index, int):
                by_index[index] = signature
        return by_id, by_index

    @staticmethod
    def _parse_response(ai_message: Any) -> LLMResponse:
        """Convert a LangChain AIMessage (or AIMessageChunk) to ``LLMResponse``.

        Single source for reasoning: ``additional_kwargs["reasoning_content"]``,
        populated by ``ChatOpenAIWithReasoning`` on both stream and non-stream paths.

        ``usage_metadata`` is forwarded as-is from the underlying message so
        downstream cost / billing audit code (e.g. swarm worker token totals)
        can use real provider tokens instead of a character-count heuristic.
        For ``AIMessageChunk`` the metadata accumulates via the ``__add__``
        merge LangChain performs while the response is being streamed; the
        final aggregate carries the same shape as the non-stream path.
        """
        usage = getattr(ai_message, "usage_metadata", None)
        # Some providers / older LangChain versions surface a ``UsageMetadata``
        # TypedDict that doesn't json-serialise without a cast. Normalise to a
        # plain ``dict[str, int]`` so the value can be persisted alongside the
        # rest of the run state without surprises.
        if usage is not None and not isinstance(usage, dict):
            try:
                usage = dict(usage)
            except (TypeError, ValueError):
                usage = None
        thought_signatures_by_id, thought_signatures_by_index = (
            ChatLLM._tool_call_thought_signature_maps(ai_message)
        )
        native_tool_calls = [
            ToolCallRequest(
                id=tc["id"],
                name=tc["name"],
                arguments=tc["args"],
                thought_signature=thought_signatures_by_id.get(str(tc["id"]))
                or thought_signatures_by_index.get(index),
            )
            for index, tc in enumerate(ai_message.tool_calls)
        ]
        dsml_tool_calls = [] if native_tool_calls else _parse_dsml_tool_calls(ai_message.content)
        tool_calls = native_tool_calls or dsml_tool_calls

        finish_reason = (
            "tool_calls"
            if dsml_tool_calls
            else _dedupe_finish_reason(
                ai_message.response_metadata.get("finish_reason", "stop")
            )
        )
        content_filter_triggered = is_content_filter_triggered(
            ai_message.response_metadata.get("finish_reason")
        )

        return LLMResponse(
            content="" if dsml_tool_calls else ai_message.content,
            tool_calls=tool_calls,
            reasoning_content=ai_message.additional_kwargs.get("reasoning_content"),
            finish_reason=finish_reason,
            usage_metadata=usage,
            content_filter_triggered=content_filter_triggered,
        )
