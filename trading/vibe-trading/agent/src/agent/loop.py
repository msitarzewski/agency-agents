"""AgentLoop: ReAct core loop.

Five-layer context management:
  Layer 1 (microcompact)     — prunes old tool results once under memory pressure
  Layer 2 (context_collapse) — folds long text blocks without LLM call (zero cost)
  Layer 3 (auto_compact)     — LLM structured summary with token-budget tail protection
  Layer 4 (compact tool)     — model explicitly calls the compact tool to trigger L3
  Layer 5 (iterative update) — Nth compression updates previous summary instead of starting fresh

Tool execution:
  - Read/write batching: consecutive readonly tools run in parallel via threads
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import queue
import threading
import time as _time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.agent.context import ContextBuilder
from src.agent.memory import WorkspaceMemory
from src.agent.progress import HeartbeatTimer, ProgressEvent, _set_emitter
from src.agent.tools import ToolRegistry
from src.agent.trace import TraceWriter
from src.core.state import RunStateStore
from src.goal.context import (
    format_goal_continuation_prompt,
    get_current_goal_context,
    goal_needs_continuation,
    goal_progress_tuple,
)
from src.providers.chat import ChatLLM, ProviderStreamError
from src.providers.content_filter import (
    CONTENT_FILTER_SKIP_MESSAGE,
    MAX_CONSECUTIVE_CONTENT_FILTER_SKIPS,
    compute_content_filter_warnings,
)
from src.tools.background_tools import get_background_manager
from src.tools.redaction import redact_payload

RUNS_DIR = Path(__file__).resolve().parents[2] / "runs"
SESSIONS_DIR = Path(__file__).resolve().parents[2] / "sessions"
TOKEN_THRESHOLD = int(os.getenv("TOKEN_THRESHOLD", "40000"))
KEEP_RECENT = 3
TOOL_RESULT_LIMIT = 10_000
HEARTBEAT_INTERVAL_S = float(os.getenv("VT_HEARTBEAT_INTERVAL_S", "3.0"))
REASONING_DELTA_MIN_INTERVAL_S = float(os.getenv("VT_REASONING_DELTA_MIN_INTERVAL_S", "1.0"))
STREAM_RETRY_DELAY_S = float(os.getenv("VT_STREAM_RETRY_DELAY_S", "1.0"))
TOOL_TIMEOUT_SECONDS = float(os.getenv("VIBE_TRADING_TOOL_TIMEOUT_SECONDS", "1800"))
GOAL_MAX_CONTINUATIONS = int(os.getenv("VIBE_TRADING_GOAL_MAX_CONTINUATIONS", "3"))
LLM_USAGE_ARTIFACT = "llm_usage.json"

# Layer 1: microcompact only prunes old tool results once the transcript is
# under real memory pressure. Below this it would clear tool history on every
# iteration even on short runs, discarding results the model may still need to
# reference (metrics, file contents, search hits).
MICROCOMPACT_THRESHOLD = int(TOKEN_THRESHOLD * 0.5)

# Layer 2: Context collapse thresholds
COLLAPSE_THRESHOLD = int(TOKEN_THRESHOLD * 0.7)
COLLAPSE_PRESERVE_RECENT = 6
COLLAPSE_TEXT_MIN = 2400
COLLAPSE_HEAD = 900
COLLAPSE_TAIL = 500

# Layer 3: Token-budget tail protection
TAIL_TOKEN_BUDGET = 20_000

logger = logging.getLogger(__name__)


def _coerce_usage_int(value: Any) -> int:
    """Coerce provider token counts to non-negative ints."""
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _normalize_llm_usage(usage: Any) -> dict[str, int] | None:
    """Normalize provider-reported usage metadata without estimating tokens."""
    if usage is None:
        return None
    if not isinstance(usage, dict):
        try:
            usage = dict(usage)
        except (TypeError, ValueError):
            return None

    input_tokens = _coerce_usage_int(usage.get("input_tokens"))
    output_tokens = _coerce_usage_int(usage.get("output_tokens"))
    total_tokens = _coerce_usage_int(usage.get("total_tokens"))
    if total_tokens == 0 and (input_tokens or output_tokens):
        total_tokens = input_tokens + output_tokens
    if not (input_tokens or output_tokens or total_tokens):
        return None
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _new_llm_usage_summary(llm: Any) -> dict[str, Any]:
    """Create the run-scoped provider usage accumulator."""
    provider = os.getenv("LANGCHAIN_PROVIDER", "openai").strip() or "openai"
    model = getattr(llm, "model_name", None) or os.getenv("LANGCHAIN_MODEL_NAME", "").strip()
    return {
        "provider": provider,
        "model": model,
        "totals": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "calls": 0,
        },
        "per_iteration": [],
    }


def _record_llm_usage(
    run_dir: Path,
    summary: dict[str, Any],
    usage: Any,
    iteration: int,
) -> dict[str, int] | None:
    """Accumulate and persist one provider-reported usage event."""
    normalized = _normalize_llm_usage(usage)
    if normalized is None:
        return None

    totals = summary.setdefault("totals", {})
    totals["input_tokens"] = int(totals.get("input_tokens") or 0) + normalized["input_tokens"]
    totals["output_tokens"] = int(totals.get("output_tokens") or 0) + normalized["output_tokens"]
    totals["total_tokens"] = int(totals.get("total_tokens") or 0) + normalized["total_tokens"]
    totals["calls"] = int(totals.get("calls") or 0) + 1
    summary.setdefault("per_iteration", []).append({"iter": iteration, **normalized})
    summary["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        path = run_dir / LLM_USAGE_ARTIFACT
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(path)
    except OSError as exc:
        logger.debug("LLM usage artifact write skipped: %s", exc)

    return normalized


def _redact_trace_result(result: str) -> str:
    """Redact structured sensitive fields before persisting trace/event previews.

    Args:
        result: Raw tool result string.

    Returns:
        Redacted JSON string when ``result`` is JSON, otherwise the original
        text. Plain text is left unchanged because reliable free-text secret
        scrubbing would be more error-prone than helpful here.
    """
    try:
        payload = json.loads(result)
    except (TypeError, json.JSONDecodeError):
        return result
    return json.dumps(redact_payload(payload), ensure_ascii=False)


def _format_timeout(seconds: float) -> str:
    """Return a human-readable timeout label."""
    if seconds < 1:
        return f"{seconds:.2f}s"
    return f"{seconds:.0f}s"


def estimate_tokens(messages: list) -> int:
    """Rough token count estimate (~4 chars/token).

    Args:
        messages: Message list.

    Returns:
        Estimated token count.
    """
    return len(json.dumps(messages, default=str, ensure_ascii=False)) // 4


def _microcompact(messages: list) -> None:
    """Layer 1: silently prune old tool results, keeping the most recent N intact.

    Args:
        messages: Message list (mutated in place).
    """
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    if len(tool_msgs) <= KEEP_RECENT:
        return
    for msg in tool_msgs[:-KEEP_RECENT]:
        content = msg.get("content", "")
        if isinstance(content, str) and len(content) > 100:
            msg["content"] = "[cleared]"


def _context_collapse(messages: list) -> None:
    """Layer 2: fold long text blocks in older messages without LLM call.

    Preserves head + tail of large text, collapses the middle.
    Zero API cost — pure string operation.

    Args:
        messages: Message list (mutated in place).
    """
    if len(messages) <= COLLAPSE_PRESERVE_RECENT + 1:
        return
    for msg in messages[1:-COLLAPSE_PRESERVE_RECENT]:
        content = msg.get("content")
        if not isinstance(content, str) or len(content) <= COLLAPSE_TEXT_MIN:
            continue
        if content == "[cleared]":
            continue
        head = content[:COLLAPSE_HEAD]
        tail = content[-COLLAPSE_TAIL:]
        trimmed = len(content) - COLLAPSE_HEAD - COLLAPSE_TAIL
        msg["content"] = f"{head}\n\n...[{trimmed} chars collapsed]...\n\n{tail}"


def _fix_tool_pairs(messages: list) -> None:
    """Repair orphaned tool_call / tool_result pairs after compression.

    Two fixes:
      1. Remove tool results whose matching tool_call was compressed away.
      2. Insert stub results for tool_calls whose results were compressed away.

    Args:
        messages: Message list (mutated in place).
    """
    # Collect all tool_call IDs from assistant messages
    call_ids: set[str] = set()
    for msg in messages:
        if msg.get("role") == "assistant":
            for tc in msg.get("tool_calls", []):
                tc_id = tc.get("id", "")
                if tc_id:
                    call_ids.add(tc_id)

    # Remove orphaned tool results
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.get("role") == "tool" and msg.get("tool_call_id") not in call_ids:
            messages.pop(i)
        else:
            i += 1

    # Collect existing result IDs
    result_ids: set[str] = set()
    for msg in messages:
        if msg.get("role") == "tool":
            tcid = msg.get("tool_call_id", "")
            if tcid:
                result_ids.add(tcid)

    # Insert stub results for orphaned tool_calls
    inserts: list[tuple[int, dict]] = []
    for idx, msg in enumerate(messages):
        if msg.get("role") != "assistant":
            continue
        for tc in msg.get("tool_calls", []):
            tc_id = tc.get("id", "")
            if tc_id and tc_id not in result_ids:
                stub = {
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": tc.get("function", {}).get("name", "unknown"),
                    "content": "[Result from earlier context — see summary above]",
                }
                inserts.append((idx + 1, stub))
                result_ids.add(tc_id)

    for pos, stub in reversed(inserts):
        messages.insert(pos, stub)


def _attach_tool_call_thought_signatures(message: dict[str, Any], tool_calls: list) -> None:
    """Attach Gemini thought signatures to replayed assistant tool calls."""
    outbound_tool_calls = message.get("tool_calls")
    if not isinstance(outbound_tool_calls, list):
        return

    signatures_by_id = {
        tc.id: tc.thought_signature
        for tc in tool_calls
        if getattr(tc, "thought_signature", None)
    }
    for index, outbound_tool_call in enumerate(outbound_tool_calls):
        if not isinstance(outbound_tool_call, dict):
            continue
        signature = signatures_by_id.get(outbound_tool_call.get("id"))
        if not signature and index < len(tool_calls):
            signature = getattr(tool_calls[index], "thought_signature", None)
        if not signature:
            continue

        extra_content = outbound_tool_call.get("extra_content")
        if not isinstance(extra_content, dict):
            extra_content = {}
            outbound_tool_call["extra_content"] = extra_content
        google = extra_content.get("google")
        if not isinstance(google, dict):
            google = {}
            extra_content["google"] = google
        google["thought_signature"] = signature


# -- Structured summary templates ------------------------------------------

_STRUCTURED_SUMMARY_PROMPT = """\
Summarize this conversation for handoff to a fresh context window.
This summary is the ONLY context available — omitted information is lost.

Use EXACTLY this structure:

## Goal
What the user is trying to accomplish.

## Constraints & Preferences
User-stated requirements: risk tolerance, strategy parameters, asset preferences.

## Progress
### Done
- Completed steps with key results and specific numbers.
### In Progress
- Current work when compression triggered.

## Key Decisions
Choices made and rationale.

## Resolved Questions
Questions already answered — do NOT re-answer these.

## Pending User Asks
Unfinished requests still needing action.

## Relevant Files
File paths, run_dir, signal engines, artifact locations.

## Remaining Work
What still needs to be done (background reference, NOT active instructions).

## Critical Context
Specific numbers, parameters, error messages, configuration values.

## Tools & Patterns
Which tools worked, what failed, effective approaches.

IMPORTANT: This is a handoff — background reference, NOT active instructions.
Preserve ALL specific numbers, file paths, and parameter values.
{focus_section}
Conversation to summarize:
"""

_FOCUS_SECTION = """
FOCUS TOPIC: {topic}
Allocate 60-70% of the summary budget to content related to this topic.
Aggressively compress unrelated content to make room.
"""

_ITERATIVE_UPDATE_PROMPT = """\
Update the existing summary with new conversation turns.

PREVIOUS SUMMARY:
{previous_summary}

NEW TURNS TO INCORPORATE:
{new_turns}

Rules:
- PRESERVE all existing information from the previous summary.
- ADD new progress, decisions, and findings.
- Move "In Progress" items to "Done" when completed.
- Move answered questions to "Resolved Questions".
- Keep the same section structure.
- Do NOT drop any critical context from the previous summary.
{focus_section}"""


def _is_tool_success(result: str) -> bool:
    """Return True if the tool result does not look like an error response."""
    try:
        data = json.loads(result)
        if isinstance(data, dict) and data.get("status") == "error":
            return False
    except (json.JSONDecodeError, TypeError):
        pass
    return True


def _normalize_tool_run_dir(args: dict[str, Any], memory_run_dir: str | None) -> dict[str, Any]:
    """Normalize ``run_dir`` in tool args to an absolute path when possible.

    If the model supplies a relative ``run_dir`` (for example ``"."`` or
    ``"risk_parity_run"``), resolve it against the active run directory.
    """
    normalized = dict(args)
    if not memory_run_dir:
        return normalized

    if "run_dir" not in normalized:
        normalized["run_dir"] = memory_run_dir
        return normalized

    run_dir_value = str(normalized["run_dir"]).strip()
    if not run_dir_value:
        normalized["run_dir"] = memory_run_dir
        return normalized

    candidate = Path(run_dir_value)
    if not candidate.is_absolute():
        normalized["run_dir"] = str((Path(memory_run_dir) / candidate).resolve())
    return normalized


class AgentLoop:
    """ReAct Agent core loop.

    Attributes:
        registry: Tool registry.
        llm: ChatLLM client.
        memory: Workspace memory.
        max_iterations: Maximum number of iterations.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        llm: ChatLLM,
        memory: Optional[WorkspaceMemory] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        max_iterations: int = 50,
        persistent_memory: Optional[Any] = None,
    ) -> None:
        """Initialize AgentLoop.

        Args:
            registry: Tool registry.
            llm: ChatLLM client.
            memory: Workspace memory (created fresh if not provided).
            event_callback: Event callback (event_type, data).
            max_iterations: Maximum number of loop iterations.
            persistent_memory: PersistentMemory for cross-session recall.
        """
        self.registry = registry
        self.llm = llm
        self.memory = memory or WorkspaceMemory()
        self._event_callback = event_callback
        self.max_iterations = max_iterations
        self._called_ok: set[str] = set()
        self._cancel_event = threading.Event()
        self._previous_summary: str = ""
        self._persistent_memory = persistent_memory
        self._run_iteration: int = 0

    def cancel(self) -> None:
        """Cancel the current loop.

        Sets a thread-safe flag polled at every iteration boundary, per LLM
        stream chunk, and between tool batches, so a running turn stops at the
        next cooperative checkpoint instead of only at the next iteration.
        """
        self._cancel_event.set()

    def run(self, user_message: str, history: Optional[List[Dict[str, Any]]] = None, session_id: str = "") -> Dict[str, Any]:
        """Run the ReAct loop synchronously.

        Args:
            user_message: User message.
            history: Prior conversation messages.
            session_id: Session ID.

        Returns:
            Execution result dict.
        """
        # Reset per-run state (safe for reuse across multiple run() calls)
        self._cancel_event.clear()
        self._called_ok = set()
        self._previous_summary = ""

        state_store = RunStateStore()
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

        if self.memory.run_dir and Path(self.memory.run_dir).exists():
            run_dir = Path(self.memory.run_dir)
        else:
            run_dir = state_store.create_run_dir(RUNS_DIR)
            self.memory.run_dir = str(run_dir)

        state_store.save_request(run_dir, user_message, {"session_id": session_id})

        context = ContextBuilder(self.registry, self.memory,
                                  persistent_memory=self._persistent_memory)
        goal_context, active_goal_id = get_current_goal_context(session_id) if session_id else ("", None)
        llm_user_message = user_message
        if goal_context:
            llm_user_message = (
                f"{goal_context}\n\n"
                f"<user-message>\n{user_message}\n</user-message>"
            )
        goal_store = None
        goal_turn_accounted = False
        messages = context.build_messages(llm_user_message, history)
        react_trace: List[Dict[str, Any]] = []

        trace_dir = SESSIONS_DIR / session_id if session_id else run_dir
        trace = TraceWriter(trace_dir)
        if self._run_iteration == 0 and trace.path.exists():
            existing = TraceWriter.read(trace_dir)
            self._run_iteration = max(
                (int(e.get("iter", 0)) for e in existing if "iter" in e),
                default=0,
            )
        trace.write_text_entry(
            {"type": "start", "iter": self._run_iteration + 1},
            field="prompt",
            value=user_message,
            offload_kind=f"start-{self._run_iteration + 1}",
        )
        trace.write_text_entry(
            {"type": "message", "iter": self._run_iteration + 1, "role": "user"},
            field="content",
            value=user_message,
            offload_kind=f"user-message-{self._run_iteration + 1}",
        )

        iteration = 0
        final_content = ""
        content_filter_count = 0
        consecutive_content_filter_count = 0
        content_filter_circuit_breaker = False
        empty_model_response_iter: int | None = None
        llm_usage_summary = _new_llm_usage_summary(self.llm)
        goal_continuations = 0
        goal_last_progress: tuple[int, int] | None = None
        wrap_up_at = max(1, int(self.max_iterations * 0.8))

        try:
            while iteration < self.max_iterations:
                if self._cancel_event.is_set():
                    trace.write({"type": "cancelled", "iter": self._run_iteration + 1})
                    logger.info("AgentLoop cancelled by user")
                    break

                iteration += 1
                self._run_iteration += 1
                current_iter = self._run_iteration

                # Inject background task notifications
                bg = get_background_manager()
                notifs = bg.drain_notifications()
                if notifs:
                    notif_text = "\n".join(f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifs)
                    messages.append({"role": "user", "content": f"<background-results>\n{notif_text}\n</background-results>\n\n<system>Continue processing with the background results above.</system>"})

                # Estimate transcript size once; each compaction layer below
                # escalates only when its own token threshold is crossed.
                tokens = estimate_tokens(messages)

                # Layer 1: microcompact — prune old tool results only under
                # memory pressure, so short, low-pressure runs keep their full
                # tool history available for the model to reference instead of
                # having every result past the most recent few cleared.
                if tokens > MICROCOMPACT_THRESHOLD:
                    _microcompact(messages)
                    tokens = estimate_tokens(messages)

                # Layer 2: context collapse (fold long text, zero API cost)
                if tokens > COLLAPSE_THRESHOLD:
                    _context_collapse(messages)
                    tokens = estimate_tokens(messages)

                # Layer 3: auto_compact (token threshold exceeded)
                if tokens > TOKEN_THRESHOLD:
                    logger.info(f"Auto compact triggered: {tokens} tokens > {TOKEN_THRESHOLD}")
                    self._auto_compact(messages, run_dir, trace, iteration=current_iter)

                logger.info(f"ReAct iteration {iteration}/{self.max_iterations}")

                # Inject wrap-up nudge when approaching iteration limit.
                # Skip on the first iteration (tiny budgets) and on the last
                # iteration (the forced text-only path already guarantees an
                # answer there) so the nudge never displaces the active-goal
                # context as the most recent user message.
                if iteration == wrap_up_at and 1 < iteration < self.max_iterations:
                    remaining = self.max_iterations - iteration
                    messages.append({
                        "role": "user",
                        "content": (
                            f"[SYSTEM] You have {remaining} iterations remaining out of "
                            f"{self.max_iterations}. Please wrap up your work. "
                            "Stop calling tools and provide your final answer as plain text. "
                            "If you have partial results, summarize what you have so far."
                        ),
                    })

                # Streaming output + collect thinking text
                thinking_chunks: List[str] = []
                reasoning_chars = 0
                last_reasoning_emit: float | None = None

                def _on_text_chunk(delta: str) -> None:
                    thinking_chunks.append(delta)
                    self._emit("text_delta", {"delta": delta, "iter": current_iter})

                def _on_reasoning_chunk(delta: str) -> None:
                    # Throttled: long reasoning streams produce hundreds of
                    # chunks; emitting each one floods the SSE replay buffer
                    # and evicts tool_call/text_delta events. The first chunk
                    # of each iteration always emits immediately so the UI
                    # flips to "Reasoning…" without delay.
                    nonlocal reasoning_chars, last_reasoning_emit
                    reasoning_chars += len(delta)
                    now = _time.monotonic()
                    if (
                        last_reasoning_emit is not None
                        and now - last_reasoning_emit < REASONING_DELTA_MIN_INTERVAL_S
                    ):
                        return
                    last_reasoning_emit = now
                    self._emit(
                        "reasoning_delta",
                        {"iter": current_iter, "chars": reasoning_chars},
                    )

                # On last iteration, drop tool definitions to force text output
                is_last_iteration = (iteration == self.max_iterations)
                tool_defs = None if is_last_iteration else self.registry.get_definitions()
                if is_last_iteration:
                    trace.write({"type": "forced_text_only", "iter": current_iter})

                try:
                    response = self.llm.stream_chat(
                        messages,
                        tools=tool_defs,
                        on_text_chunk=_on_text_chunk,
                        on_reasoning_chunk=_on_reasoning_chunk,
                        should_cancel=self._cancel_event.is_set,
                    )
                except ProviderStreamError as exc:
                    # One retry for transient mid-stream failures (connection
                    # reset, relay hiccup) — mirrors the swarm worker policy.
                    # Deterministic 4xx errors fail immediately. Deltas from
                    # the failed attempt are dropped so the trace does not
                    # contain duplicated thinking text.
                    if not exc.retryable:
                        raise
                    logger.warning(
                        "Provider stream failed (iter %s), retrying once: %s",
                        current_iter,
                        exc,
                    )
                    self._emit(
                        "stream_reset",
                        {
                            "iter": current_iter,
                            "reason": "provider_stream_retry",
                            "provider": exc.provider,
                            "model": exc.model,
                        },
                    )
                    thinking_chunks.clear()
                    reasoning_chars = 0
                    last_reasoning_emit = None
                    _time.sleep(STREAM_RETRY_DELAY_S)
                    response = self.llm.stream_chat(
                        messages,
                        tools=tool_defs,
                        on_text_chunk=_on_text_chunk,
                        on_reasoning_chunk=_on_reasoning_chunk,
                        should_cancel=self._cancel_event.is_set,
                    )

                # Cancelled mid-stream: discard this turn's partial response and
                # end the run now, without executing any of its tool calls.
                if self._cancel_event.is_set():
                    break

                usage = getattr(response, "usage_metadata", None)
                usage_delta = _record_llm_usage(
                    run_dir,
                    llm_usage_summary,
                    usage,
                    current_iter,
                )
                if usage_delta:
                    self._emit(
                        "llm_usage",
                        {
                            **usage_delta,
                            "iter": current_iter,
                        },
                    )
                if active_goal_id and session_id:
                    token_delta = int(usage_delta.get("total_tokens") or 0) if usage_delta else 0
                    turn_delta = 0 if goal_turn_accounted else 1
                    if token_delta or turn_delta:
                        try:
                            if goal_store is None:
                                from src.goal import GoalStore

                                goal_store = GoalStore()
                            goal_store.account_usage(
                                session_id=session_id,
                                goal_id=active_goal_id,
                                expected_goal_id=active_goal_id,
                                token_delta=token_delta,
                                turn_delta=turn_delta,
                            )
                            goal_turn_accounted = True
                            snapshot = goal_store.get_goal_snapshot(active_goal_id)
                            if snapshot is not None:
                                self._emit(
                                    "goal.updated",
                                    {"goal": snapshot["goal"], "snapshot": snapshot},
                                )
                        except Exception as exc:  # noqa: BLE001
                            logger.debug("Goal usage accounting skipped: %s", exc)

                thinking_text = "".join(thinking_chunks)
                if thinking_text:
                    trace.write_text_entry(
                        {"type": "thinking", "iter": current_iter},
                        field="content",
                        value=thinking_text,
                        offload_kind=f"thinking-{current_iter}",
                    )
                    self._emit("thinking_done", {"iter": current_iter, "content": thinking_text[:500]})

                # Content-filter skip: provider blocked the response — continue
                # to the next iteration instead of finalising on empty/garbage
                # content.  Checked *before* the tool-call branch so a filtered
                # response never executes its (likely empty) tool calls.
                # Use getattr for duck-typed response objects from mock LLMs.
                if getattr(response, "content_filter_triggered", False):
                    content_filter_count += 1
                    consecutive_content_filter_count += 1
                    if consecutive_content_filter_count >= MAX_CONSECUTIVE_CONTENT_FILTER_SKIPS:
                        trace.write({
                            "type": "content_filter_circuit_breaker",
                            "iter": current_iter,
                            "count": content_filter_count,
                        })
                        content_filter_circuit_breaker = True
                        break
                    trace.write({"type": "content_filter_skipped", "iter": current_iter})
                    messages.append({
                        "role": "system",
                        "content": CONTENT_FILTER_SKIP_MESSAGE,
                    })
                    continue

                # Not filtered — reset the consecutive-skip counter.
                consecutive_content_filter_count = 0

                if not response.has_tool_calls:
                    final_content = response.content or ""
                    if not final_content:
                        empty_model_response_iter = iteration
                        trace.write(
                            {
                                "type": "empty_model_response",
                                "iter": current_iter,
                                "provider": os.getenv("LANGCHAIN_PROVIDER", "openai"),
                                "model": getattr(self.llm, "model_name", None) or os.getenv("LANGCHAIN_MODEL_NAME", ""),
                            }
                        )
                        break
                    should_continue_goal = False
                    continuation_snapshot = None
                    if active_goal_id and session_id and GOAL_MAX_CONTINUATIONS > 0:
                        try:
                            if goal_store is None:
                                from src.goal import GoalStore

                                goal_store = GoalStore()
                            continuation_snapshot = goal_store.get_goal_snapshot(active_goal_id)
                            should_continue_goal = bool(
                                continuation_snapshot
                                and goal_needs_continuation(continuation_snapshot)
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.debug("Goal continuation check skipped: %s", exc)

                    if should_continue_goal and continuation_snapshot is not None:
                        current_progress = goal_progress_tuple(continuation_snapshot)
                        no_new_progress = (
                            goal_last_progress is not None
                            and current_progress <= goal_last_progress
                        )
                        if goal_continuations >= GOAL_MAX_CONTINUATIONS or (
                            no_new_progress and goal_continuations > 0
                        ):
                            trace.write(
                                {
                                    "type": "goal_continuation_suppressed",
                                    "iter": current_iter,
                                    "goal_id": active_goal_id,
                                    "progress": current_progress,
                                    "continuations": goal_continuations,
                                }
                            )
                        else:
                            trace.write_text_entry(
                                {
                                    "type": "goal_intermediate_answer",
                                    "iter": current_iter,
                                    "goal_id": active_goal_id,
                                    "progress": current_progress,
                                },
                                field="content",
                                value=final_content,
                                offload_kind=f"goal-intermediate-answer-{current_iter}",
                            )
                            trace.write_text_entry(
                                {"type": "message", "iter": current_iter, "role": "assistant"},
                                field="content",
                                value=final_content,
                                offload_kind=f"assistant-message-{current_iter}",
                            )
                            react_trace.append(
                                {"type": "goal_intermediate_answer", "content": final_content[:500]}
                            )
                            messages.append({"role": "assistant", "content": final_content})
                            messages.append(
                                {
                                    "role": "user",
                                    "content": format_goal_continuation_prompt(
                                        continuation_snapshot,
                                        previous_answer=final_content,
                                    ),
                                }
                            )
                            goal_last_progress = current_progress
                            goal_continuations += 1
                            continue

                    trace.write_text_entry(
                        {"type": "answer", "iter": current_iter},
                        field="content",
                        value=final_content,
                        offload_kind=f"answer-{current_iter}",
                    )
                    trace.write_text_entry(
                        {"type": "message", "iter": current_iter, "role": "assistant"},
                        field="content",
                        value=final_content,
                        offload_kind=f"assistant-message-{current_iter}",
                    )
                    react_trace.append({"type": "answer", "content": final_content[:500]})
                    break

                assistant_message = context.format_assistant_tool_calls(
                    response.tool_calls,
                    content=response.content,
                    reasoning_content=response.reasoning_content or thinking_text or None,
                )
                _attach_tool_call_thought_signatures(assistant_message, response.tool_calls)
                messages.append(assistant_message)

                # Execute tools with read/write batching
                compact_requested, focus_topic = self._process_tool_calls(
                    response.tool_calls, context, messages, trace, react_trace, current_iter,
                )

                # Layer 3: compress after all tools have executed
                if compact_requested:
                    logger.info("Manual compact triggered by model")
                    self._auto_compact(messages, run_dir, trace, focus_topic=focus_topic, iteration=current_iter)

        except Exception as exc:
            logger.exception(f"AgentLoop error: {exc}")
            error_code = (
                "provider_stream_error"
                if isinstance(exc, ProviderStreamError)
                else "agent_loop_error"
            )
            trace.write({"type": "end", "iter": self._run_iteration, "status": "error", "reason": str(exc), "iterations": iteration})
            trace.close()
            state_store.mark_failure(run_dir, str(exc))
            return {
                "status": "failed",
                "error_code": error_code,
                "reason": str(exc),
                "run_dir": str(run_dir),
                "run_id": run_dir.name,
                "content": "",
                "react_trace": react_trace,
                "iterations": iteration,
                "max_iterations": self.max_iterations,
            }

        # Determine final status. The reason is also propagated into the
        # returned dict so SessionService can surface a meaningful UI
        # message instead of "Execution failed: unknown" (issue #114).
        final_reason: str | None = None
        if self._cancel_event.is_set():
            final_reason = "cancelled by user"
            state_store.mark_failure(run_dir, final_reason)
            final_status = "cancelled"
        elif content_filter_circuit_breaker:
            final_reason = (
                f"content_filter_circuit_breaker: "
                f"{MAX_CONSECUTIVE_CONTENT_FILTER_SKIPS} consecutive LLM "
                "responses were blocked by content moderation"
            )
            state_store.mark_failure(run_dir, final_reason)
            final_status = "failed"
        elif (run_dir / "artifacts" / "metrics.csv").exists() or final_content:
            state_store.mark_success(run_dir)
            final_status = "success"
        elif empty_model_response_iter is not None:
            provider = os.getenv("LANGCHAIN_PROVIDER", "openai").strip().lower() or "openai"
            model = getattr(self.llm, "model_name", None) or os.getenv("LANGCHAIN_MODEL_NAME", "").strip() or "(unset)"
            final_reason = (
                "empty_model_response: "
                f"provider={provider} model={model} iteration {empty_model_response_iter} "
                "returned no content and no tool calls"
            )
            state_store.mark_failure(run_dir, final_reason)
            final_status = "failed"
        else:
            final_reason = (
                f"reached max iterations ({self.max_iterations}) without final answer"
            )
            state_store.mark_failure(run_dir, final_reason)
            final_status = "failed"

        end_event: dict[str, Any] = {
            "type": "end",
            "iter": self._run_iteration,
            "status": final_status,
            "iterations": iteration,
        }
        if final_reason is not None:
            end_event["reason"] = final_reason
        trace.write(end_event)
        trace.close()

        result: dict[str, Any] = {
            "status": final_status,
            "run_dir": str(run_dir),
            "run_id": run_dir.name,
            "content": final_content,
            "react_trace": react_trace,
            "iterations": iteration,
            "max_iterations": self.max_iterations,
        }
        if final_reason is not None:
            result["reason"] = final_reason

        cf_warnings = compute_content_filter_warnings(
            content_filter_count, max(1, iteration),
        )
        if cf_warnings:
            result["content_filter_warnings"] = cf_warnings

        return result

    # -- Tool execution with read/write batching --------------------------------

    def _process_tool_calls(
        self,
        tool_calls: list,
        context: ContextBuilder,
        messages: list,
        trace: TraceWriter,
        react_trace: list,
        iteration: int,
    ) -> tuple[bool, str]:
        """Pre-process tool calls: handle compact, filter duplicates, batch execute.

        Args:
            tool_calls: Raw tool calls from LLM response.
            context: ContextBuilder for formatting messages.
            messages: Conversation messages (appended in place).
            trace: TraceWriter.
            react_trace: React trace list.
            iteration: Current iteration number.

        Returns:
            Tuple of (compact_requested, focus_topic).
        """
        compact_requested = False
        focus_topic = ""
        to_execute = []

        # Cancelled before this turn's tools ran — skip execution entirely.
        if self._cancel_event.is_set():
            return compact_requested, focus_topic

        for tc in tool_calls:
            # Layer 4: compact tool — mark then defer execution
            if tc.name == "compact":
                compact_requested = True
                focus_topic = tc.arguments.get("focus_topic", "")
                messages.append(context.format_tool_result(tc.id, "compact", '{"status":"ok","message":"Compressing..."}'))
                trace.write({"type": "compact_requested", "iter": iteration})
                continue

            tool_def = self.registry.get(tc.name)
            is_repeatable = tool_def.repeatable if tool_def else False
            if tc.name in self._called_ok and not is_repeatable:
                logger.warning(f"Blocked duplicate call: {tc.name} (already succeeded)")
                skip_msg = json.dumps({"skipped": True, "reason": f"{tc.name} already completed successfully. Use the previous result."})
                messages.append(context.format_tool_result(tc.id, tc.name, skip_msg))
                trace.write({"type": "tool_skipped", "iter": iteration, "tool": tc.name})
                react_trace.append({"type": "tool_skipped", "tool": tc.name})
                continue

            to_execute.append(tc)

        if not to_execute:
            return compact_requested, focus_topic

        # Batch execute: consecutive readonly → parallel, write → serial
        if len(to_execute) == 1:
            self._execute_single(to_execute[0], context, messages, trace, react_trace, iteration)
        else:
            self._batch_execute(to_execute, context, messages, trace, react_trace, iteration)

        return compact_requested, focus_topic

    def _batch_execute(
        self,
        tool_calls: list,
        context: ContextBuilder,
        messages: list,
        trace: TraceWriter,
        react_trace: list,
        iteration: int,
    ) -> None:
        """Execute tools with read/write batching.

        Consecutive readonly tools run in parallel via ThreadPoolExecutor.
        Write tools run serially between readonly batches.

        Args:
            tool_calls: Tool calls to execute.
            context: ContextBuilder.
            messages: Conversation messages.
            trace: TraceWriter.
            react_trace: React trace list.
            iteration: Current iteration.
        """
        # Split into batches: consecutive readonly → parallel, write → serial
        batches: list[tuple[str, list]] = []
        current_ro: list = []

        for tc in tool_calls:
            tool_def = self.registry.get(tc.name)
            if tool_def and tool_def.is_readonly:
                current_ro.append(tc)
            else:
                if current_ro:
                    batches.append(("parallel", current_ro))
                    current_ro = []
                batches.append(("serial", [tc]))
        if current_ro:
            batches.append(("parallel", current_ro))

        for mode, batch in batches:
            # Stop launching further tool batches once cancelled — the current
            # batch (if any) finishes, but no new work starts.
            if self._cancel_event.is_set():
                break
            if mode == "parallel" and len(batch) > 1:
                self._execute_parallel(batch, context, messages, trace, react_trace, iteration)
            else:
                for tc in batch:
                    self._execute_single(tc, context, messages, trace, react_trace, iteration)

    def _execute_parallel(
        self,
        tool_calls: list,
        context: ContextBuilder,
        messages: list,
        trace: TraceWriter,
        react_trace: list,
        iteration: int,
    ) -> None:
        """Execute readonly tools in parallel using threads.

        Args:
            tool_calls: Readonly tool calls to execute in parallel.
            context: ContextBuilder.
            messages: Conversation messages.
            trace: TraceWriter.
            react_trace: React trace list.
            iteration: Current iteration.
        """
        # Prepare args + emit events
        runnable: list[tuple] = []
        for tc in tool_calls:
            args = _normalize_tool_run_dir(tc.arguments, self.memory.run_dir)
            redacted_args = redact_payload(args)
            event_args = {k: str(v)[:200] for k, v in redacted_args.items()}
            self._emit("tool_call", {"tool": tc.name, "arguments": event_args, "iter": iteration})
            trace.write({"type": "tool_call", "iter": iteration, "tool": tc.name, "call_id": tc.id, "args": redacted_args})
            runnable.append((tc, args))

        # Execute in parallel — each worker gets its own heartbeat + progress emitter.
        def _run(tc_args: tuple) -> tuple:
            tc, args = tc_args
            result, elapsed_ms = self._invoke_tool(tc.name, args)
            return tc, result, elapsed_ms

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(runnable), 8)) as pool:
            futures = [pool.submit(_run, item) for item in runnable]
            results = []
            for i, f in enumerate(futures):
                try:
                    results.append(f.result())
                except Exception as exc:
                    tc = runnable[i][0]
                    results.append((tc, json.dumps({"status": "error", "error": str(exc)}), 0))

        # Process results in order
        for tc, result, elapsed_ms in results:
            self._finalize_tool_result(tc, result, elapsed_ms, context, messages, trace, react_trace, iteration)

    def _execute_single(
        self,
        tc: Any,
        context: ContextBuilder,
        messages: list,
        trace: TraceWriter,
        react_trace: list,
        iteration: int,
    ) -> None:
        """Execute a single tool call.

        Args:
            tc: Tool call object.
            context: ContextBuilder.
            messages: Conversation messages.
            trace: TraceWriter.
            react_trace: React trace list.
            iteration: Current iteration.
        """
        args = _normalize_tool_run_dir(tc.arguments, self.memory.run_dir)

        redacted_args = redact_payload(args)
        event_args = {k: str(v)[:200] for k, v in redacted_args.items()}
        self._emit("tool_call", {"tool": tc.name, "arguments": event_args, "iter": iteration})
        trace.write({"type": "tool_call", "iter": iteration, "tool": tc.name, "call_id": tc.id, "args": redacted_args})
        logger.info(f"Tool call: {tc.name}({list(args.keys())})")

        result, elapsed_ms = self._invoke_tool(tc.name, args)

        self._finalize_tool_result(tc, result, elapsed_ms, context, messages, trace, react_trace, iteration)

    def _invoke_tool(self, tool_name: str, args: Dict[str, Any]) -> tuple[str, int]:
        """Execute a tool with heartbeat + structured progress emission.

        Installs a thread-local progress emitter so the tool may call
        ``emit_progress()`` without taking a callback parameter, and runs a
        background heartbeat timer that ticks every ``HEARTBEAT_INTERVAL_S``
        seconds. Both event streams are forwarded through ``self._emit`` and
        therefore land in the same SSE bus and CLI dashboard as normal
        tool events.

        Args:
            tool_name: Tool name to execute.
            args: Tool arguments dict.

        Returns:
            Tuple of (result_str, elapsed_ms).
        """
        readonly = self._is_tool_readonly(tool_name)
        timed_out = threading.Event()

        def _on_progress(event: ProgressEvent) -> None:
            if timed_out.is_set():
                return
            payload = event.to_dict()
            payload["tool"] = tool_name
            self._emit("tool_progress", payload)

        def _on_heartbeat(payload: Dict[str, Any]) -> None:
            if timed_out.is_set():
                return
            self._emit("tool_heartbeat", payload)

        t0 = _time.perf_counter()
        timeout = TOOL_TIMEOUT_SECONDS if TOOL_TIMEOUT_SECONDS > 0 else None
        timeout_label = _format_timeout(timeout) if timeout is not None else ""

        def _elapsed_ms() -> int:
            """Return milliseconds elapsed since tool start.

            Returns:
                Elapsed wall-clock time in milliseconds.
            """
            return int((_time.perf_counter() - t0) * 1000)

        def _heartbeat_timer() -> HeartbeatTimer:
            """Build the per-invocation heartbeat timer.

            Returns:
                HeartbeatTimer wired to this invocation's heartbeat emitter.
            """
            return HeartbeatTimer(
                tool_name=tool_name,
                interval=HEARTBEAT_INTERVAL_S,
                emit=_on_heartbeat,
            )

        def _emit_timeout_progress(stage: str, message: str, **extra: Any) -> int:
            """Emit a timeout-related tool_progress event.

            Args:
                stage: Progress stage label ("timeout" or "timeout_warning").
                message: Human-readable timeout message.
                **extra: Additional payload fields.

            Returns:
                Elapsed milliseconds at emission time.
            """
            elapsed_ms = _elapsed_ms()
            payload: Dict[str, Any] = {
                "tool": tool_name,
                "stage": stage,
                "message": message,
                "elapsed_s": round(elapsed_ms / 1000, 2),
            }
            payload.update(extra)
            self._emit("tool_progress", payload)
            return elapsed_ms

        if not readonly:
            # Write tools are never killed: a watchdog warns once past the
            # timeout, then the result is awaited to completion.
            finished = threading.Event()

            def _warn_if_stale() -> None:
                if timeout is None or finished.wait(timeout):
                    return
                _emit_timeout_progress(
                    "timeout_warning",
                    (
                        f"Write tool exceeded {timeout_label} timeout; "
                        "waiting for completion because it cannot be safely cancelled"
                    ),
                    readonly=False,
                )

            watchdog = threading.Thread(
                target=_warn_if_stale,
                name=f"tool-watchdog-{tool_name}",
                daemon=True,
            )
            watchdog.start()
            _set_emitter(_on_progress)
            try:
                with _heartbeat_timer():
                    result = self.registry.execute(tool_name, args)
            finally:
                finished.set()
                _set_emitter(None)
            return result or "", _elapsed_ms()

        # Readonly tools run in a worker thread so a hung tool becomes a
        # bounded error: late results are discarded and the emitters are
        # suppressed via the timed_out event.
        result_queue: queue.Queue[tuple[str | None, BaseException | None]] = queue.Queue(maxsize=1)

        def _worker() -> None:
            _set_emitter(_on_progress)
            try:
                result_queue.put((self.registry.execute(tool_name, args), None))
            except BaseException as exc:  # noqa: BLE001 - propagate through caller thread
                result_queue.put((None, exc))
            finally:
                _set_emitter(None)

        worker = threading.Thread(
            target=_worker,
            name=f"tool-{tool_name}",
            daemon=True,
        )
        worker.start()
        with _heartbeat_timer():
            try:
                result, exc = result_queue.get(timeout=timeout)
            except queue.Empty:
                timed_out.set()
                elapsed_ms = _emit_timeout_progress(
                    "timeout", f"Tool exceeded {timeout_label} timeout"
                )
                return (
                    json.dumps(
                        {
                            "status": "error",
                            "error_code": "tool_timeout",
                            "tool": tool_name,
                            "timeout_seconds": timeout,
                            "message": f"Tool exceeded {timeout_label} timeout",
                        },
                        ensure_ascii=False,
                    ),
                    elapsed_ms,
                )
        if exc is not None:
            raise exc
        return result or "", _elapsed_ms()

    def _is_tool_readonly(self, tool_name: str) -> bool:
        """Return whether a tool is known to be side-effect free."""
        get_tool = getattr(self.registry, "get", None)
        if not callable(get_tool):
            return False
        try:
            tool_def = get_tool(tool_name)
        except Exception:  # noqa: BLE001 - unknown classification is not readonly
            return False
        return bool(tool_def and getattr(tool_def, "is_readonly", False))

    def _finalize_tool_result(
        self,
        tc: Any,
        result: str,
        elapsed_ms: int,
        context: ContextBuilder,
        messages: list,
        trace: TraceWriter,
        react_trace: list,
        iteration: int,
    ) -> None:
        """Record a tool result: update memory, append message, write trace, emit event.

        Args:
            tc: Tool call object.
            result: Raw tool result string.
            elapsed_ms: Execution time in milliseconds.
            context: ContextBuilder.
            messages: Conversation messages.
            trace: TraceWriter.
            react_trace: React trace list.
            iteration: Current iteration.
        """
        self._update_memory(tc.name)

        success = _is_tool_success(result)
        if success:
            self._called_ok.add(tc.name)

        status = "ok" if success else "error"
        truncated = result[:TOOL_RESULT_LIMIT]
        messages.append(context.format_tool_result(tc.id, tc.name, truncated))

        trace_result = _redact_trace_result(result)
        trace.write_tool_result(
            call_id=tc.id,
            result=trace_result,
            tool_name=tc.name,
            status=status,
            elapsed_ms=elapsed_ms,
            iteration=iteration,
        )
        preview = trace_result[:200]
        react_trace.append({"type": "tool_call", "tool": tc.name, "result_preview": preview})
        self._emit("tool_result", {"tool": tc.name, "status": status, "elapsed_ms": elapsed_ms, "preview": preview})

    # -- Context compression ---------------------------------------------------

    def _auto_compact(
        self,
        messages: list,
        run_dir: Path,
        trace: TraceWriter,
        focus_topic: str = "",
        iteration: int = 0,
    ) -> None:
        """Layer 3/4/5: structured LLM summary with token-budget tail protection.

        Upgrades over the original:
          - Token-budget tail: keeps ~20K tokens of recent messages (not a fixed count).
          - Structured summary template: preserves goal, progress, decisions, files, etc.
          - Iterative update: Nth compression updates previous summary, zero info decay.
          - Tool pair fix: repairs orphaned tool_call/tool_result after compression.
          - Focus-topic: optionally prioritize specific topic in summary.

        Args:
            messages: Message list (replaced in place).
            run_dir: Run directory.
            trace: TraceWriter.
            focus_topic: Optional topic to prioritize in the summary.
            iteration: Current trace iteration.
        """
        del run_dir
        # Save full transcript before compressing next to the active trace.
        transcript_path = trace.dir_path / f"transcript_{int(_time.time())}.jsonl"
        with open(transcript_path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg, default=str, ensure_ascii=False) + "\n")

        system_msg = messages[0]
        body = messages[1:]

        # Token-budget tail: walk backward to find how many recent messages to preserve
        accumulated = 0
        cut_idx = len(body)
        for i in range(len(body) - 1, -1, -1):
            content = body[i].get("content", "")
            msg_tokens = (len(str(content)) // 4) + 10
            if accumulated + msg_tokens > TAIL_TOKEN_BUDGET:
                cut_idx = i + 1
                break
            accumulated += msg_tokens
            cut_idx = i

        # Don't split in the middle of a tool_call/tool_result pair
        while 0 < cut_idx < len(body) and body[cut_idx].get("role") == "tool":
            cut_idx += 1

        head = body[:cut_idx]
        tail = body[cut_idx:]

        if not head:
            # All body fits in tail budget — force a split to avoid infinite loop
            if len(body) > 2:
                cut_idx = max(1, len(body) // 2)
                head = body[:cut_idx]
                tail = body[cut_idx:]
            else:
                logger.warning("Auto compact: nothing to compress (body too small)")
                return

        # Build focus section
        focus_section = _FOCUS_SECTION.format(topic=focus_topic) if focus_topic else ""

        # Build summary prompt (structured template or iterative update)
        conv_text = json.dumps(head, default=str, ensure_ascii=False)[:80000]

        if self._previous_summary:
            prompt = _ITERATIVE_UPDATE_PROMPT.format(
                previous_summary=self._previous_summary,
                new_turns=conv_text,
                focus_section=focus_section,
            )
        else:
            prompt = _STRUCTURED_SUMMARY_PROMPT.format(focus_section=focus_section) + conv_text

        summary_resp = self.llm.chat([{"role": "user", "content": prompt}])
        summary = summary_resp.content or ""
        self._previous_summary = summary

        tokens_before = estimate_tokens(messages)
        trace.write_text_entry(
            {
                "type": "compact",
                "iter": iteration,
                "tokens_before": tokens_before,
                "focus_topic": focus_topic or "(none)",
            },
            field="summary",
            value=summary,
            offload_kind=f"compact-summary-{iteration}",
        )
        self._emit("compact", {"tokens_before": tokens_before, "summary": summary[:200]})

        # Reconstruct: system + summary + acknowledge + preserved tail
        state_summary = self.memory.to_summary()
        compressed = f"[Conversation compressed — handoff summary. Transcript: {transcript_path}]\n\n{summary}"
        if state_summary and state_summary != "(empty state)":
            compressed += f"\n\nCurrent agent state:\n{state_summary}"

        messages.clear()
        messages.append(system_msg)
        messages.append({"role": "user", "content": f"{compressed}\n\n<system>Continue from the summary above.</system>"})
        messages.extend(tail)

        # Fix orphaned tool pairs in the reconstructed message list
        _fix_tool_pairs(messages)

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Fire an event via the callback."""
        if self._event_callback:
            try:
                self._event_callback(event_type, data)
            except Exception:
                pass

    def _update_memory(self, tool_name: str) -> None:
        """Update workspace memory counters after tool execution."""
        self.memory.increment(tool_name)
