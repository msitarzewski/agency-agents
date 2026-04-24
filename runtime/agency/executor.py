"""Run a skill against a user request with a tool-use loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .llm import AnthropicLLM
from .memory import MemoryStore, Session
from .skills import Skill, SkillRegistry
from .tools import Tool, ToolContext, builtin_tools, tools_by_name

MAX_TURNS = 12  # safety cap on tool-use iterations
MAX_DELEGATION_DEPTH = 2  # A → B → C is allowed; A → B → C → D is not


@dataclass
class ExecutionEvent:
    kind: str  # "text" | "tool_use" | "tool_result" | "stop"
    payload: Any = None


@dataclass
class ExecutionResult:
    text: str
    turns: int
    events: list[ExecutionEvent] = field(default_factory=list)


class Executor:
    """One Executor per agent loop. Reuse across turns of a session."""

    def __init__(
        self,
        registry: SkillRegistry,
        llm: AnthropicLLM,
        memory: MemoryStore | None = None,
        tools: list[Tool] | None = None,
        workdir: Path | None = None,
        delegation_depth: int = 0,
    ):
        self.registry = registry
        self.llm = llm
        self.memory = memory
        self.tools = tools if tools is not None else builtin_tools()
        self._tool_index = tools_by_name(self.tools)
        self.ctx = ToolContext.from_env(workdir=workdir)
        self._delegation_depth = delegation_depth
        # Inject sibling-skill summary so the `list_skills` tool can describe them.
        summary_lines = [
            f"- {s.slug}: {s.name} ({s.category}) — {s.description}"
            for s in registry.all()
        ]
        setattr(self.ctx, "_skills_summary", "\n".join(summary_lines))
        setattr(self.ctx, "_delegate_runner", self._delegate)

    def _bind_session_to_ctx(self, session: Session | None) -> None:
        if session is None:
            setattr(self.ctx, "_plan_root", None)
            setattr(self.ctx, "_plan_session_id", None)
            return
        plan_root = Path.home() / ".agency" / "plans"
        setattr(self.ctx, "_plan_root", plan_root)
        setattr(self.ctx, "_plan_session_id", session.session_id)

    def _delegate(self, slug: str, request: str) -> str:
        if self._delegation_depth >= MAX_DELEGATION_DEPTH:
            raise RecursionError(
                f"Delegation depth {self._delegation_depth} exceeds cap {MAX_DELEGATION_DEPTH}."
            )
        sub_skill = self.registry.by_slug(slug)
        if sub_skill is None:
            raise KeyError(slug)
        sub = Executor(
            self.registry, self.llm, memory=None, tools=self.tools,
            workdir=self.ctx.workdir, delegation_depth=self._delegation_depth + 1,
        )
        return sub.run(sub_skill, request).text

    def run(self, skill: Skill, user_message: str, session: Session | None = None) -> ExecutionResult:
        events: list[ExecutionEvent] = []
        text_parts: list[str] = []

        self._bind_session_to_ctx(session)
        messages = self._initial_messages(session, user_message)
        system = AnthropicLLM.cached_system(skill.system_prompt)
        tool_defs = [t.to_anthropic() for t in self.tools]

        turns = 0
        for _ in range(MAX_TURNS):
            turns += 1
            response = self.llm.messages_create(
                system=system,
                messages=messages,
                tools=tool_defs,
            )

            assistant_blocks = [self._block_to_dict(b) for b in response.content]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_uses = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "text":
                    text_parts.append(block.text)
                    events.append(ExecutionEvent("text", block.text))
                elif btype == "tool_use":
                    events.append(ExecutionEvent("tool_use", {"name": block.name, "input": block.input}))

            if response.stop_reason != "tool_use" or not tool_uses:
                events.append(ExecutionEvent("stop", response.stop_reason))
                break

            tool_results = []
            for use in tool_uses:
                result = self._run_tool(use.name, use.input)
                events.append(ExecutionEvent("tool_result", {
                    "name": use.name,
                    "is_error": result.is_error,
                    "content": result.content,
                }))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": result.content,
                    "is_error": result.is_error,
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            events.append(ExecutionEvent("stop", "max_turns_exceeded"))

        final_text = "\n".join(text_parts).strip()

        if self.memory is not None and session is not None:
            session.append("user", user_message)
            session.append("assistant", final_text)
            self.memory.save(session)

        return ExecutionResult(text=final_text, turns=turns, events=events)

    def stream(self, skill: Skill, user_message: str, session: Session | None = None) -> Iterator[ExecutionEvent]:
        """Yield events as they happen.

        Emits `text_delta` events for each token chunk from the model and
        `tool_use` / `tool_result` / `stop` events at turn boundaries. If the
        underlying LLM doesn't support streaming, falls back to `run()` and
        yields the buffered events.
        """
        if not hasattr(self.llm, "messages_stream"):
            result = self.run(skill, user_message, session=session)
            yield from result.events
            return

        self._bind_session_to_ctx(session)
        text_parts: list[str] = []
        messages = self._initial_messages(session, user_message)
        system = AnthropicLLM.cached_system(skill.system_prompt)
        tool_defs = [t.to_anthropic() for t in self.tools]

        for _ in range(MAX_TURNS):
            with self.llm.messages_stream(
                system=system, messages=messages, tools=tool_defs,
            ) as stream:
                for event in stream:
                    etype = getattr(event, "type", None)
                    if etype == "content_block_delta":
                        delta = getattr(event, "delta", None)
                        if getattr(delta, "type", None) == "text_delta":
                            yield ExecutionEvent("text_delta", delta.text)
                final = stream.get_final_message()

            assistant_blocks = [self._block_to_dict(b) for b in final.content]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_uses = [b for b in final.content if getattr(b, "type", None) == "tool_use"]
            for block in final.content:
                if getattr(block, "type", None) == "text":
                    text_parts.append(block.text)
                elif getattr(block, "type", None) == "tool_use":
                    yield ExecutionEvent("tool_use", {"name": block.name, "input": block.input})

            if final.stop_reason != "tool_use" or not tool_uses:
                yield ExecutionEvent("stop", final.stop_reason)
                break

            tool_results = []
            for use in tool_uses:
                result = self._run_tool(use.name, use.input)
                yield ExecutionEvent("tool_result", {
                    "name": use.name,
                    "is_error": result.is_error,
                    "content": result.content,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": result.content,
                    "is_error": result.is_error,
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            yield ExecutionEvent("stop", "max_turns_exceeded")

        if self.memory is not None and session is not None:
            session.append("user", user_message)
            session.append("assistant", "\n".join(text_parts).strip())
            self.memory.save(session)

    # ----- helpers -----

    def _initial_messages(self, session: Session | None, user_message: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if session is not None:
            for turn in session.turns:
                messages.append({"role": turn.role, "content": turn.text})
        messages.append({"role": "user", "content": user_message})
        return messages

    def _run_tool(self, name: str, args: dict[str, Any]):
        tool = self._tool_index.get(name)
        if tool is None:
            from .tools import ToolResult
            return ToolResult(f"Unknown tool: {name}", is_error=True)
        try:
            return tool.func(args, self.ctx)
        except PermissionError as e:
            from .tools import ToolResult
            return ToolResult(str(e), is_error=True)
        except Exception as e:  # noqa: BLE001 - surface tool errors to the model
            from .tools import ToolResult
            return ToolResult(f"Tool error: {type(e).__name__}: {e}", is_error=True)

    @staticmethod
    def _block_to_dict(block) -> dict[str, Any]:
        btype = getattr(block, "type", None)
        if btype == "text":
            return {"type": "text", "text": block.text}
        if btype == "tool_use":
            return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
        if btype == "thinking":
            d = {"type": "thinking", "thinking": getattr(block, "thinking", "")}
            sig = getattr(block, "signature", None)
            if sig:
                d["signature"] = sig
            return d
        # Fallback for any other block type — preserve raw via model_dump if available.
        if hasattr(block, "model_dump"):
            return block.model_dump()
        return {"type": btype or "unknown"}
