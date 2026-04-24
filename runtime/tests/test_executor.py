"""End-to-end executor test with a stubbed Anthropic client.

Drives the tool-use loop through:
  turn 1: assistant calls list_dir
  turn 2: assistant calls read_file
  turn 3: assistant emits final text and ends the turn

Verifies tool calls hit our sandbox, results round-trip back to the model in the
correct shape, and (with a session) memory persists user/assistant turns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agency.executor import Executor
from agency.memory import MemoryStore, Session
from agency.skills import SkillRegistry, discover_repo_root


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _ToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class _FakeUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class _Resp:
    content: list
    stop_reason: str
    usage: Any = None


@dataclass
class _Cfg:
    model: str = "fake-opus"
    planner_model: str = "fake-haiku"
    max_tokens: int = 16000


class _ScriptedLLM:
    """Yields a pre-baked sequence of responses, one per messages_create call.

    Captures the kwargs of every call so the test can assert on them.
    """

    def __init__(self, responses: list[_Resp]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.config = _Cfg()

    @staticmethod
    def cached_system(text: str):
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    def messages_create(self, **kwargs):
        # Snapshot — the executor mutates the messages list across turns.
        import copy
        self.calls.append({k: copy.deepcopy(v) for k, v in kwargs.items()})
        if not self._responses:
            raise AssertionError("scripted LLM ran out of responses")
        return self._responses.pop(0)


def _registry_with_one_skill():
    reg = SkillRegistry.load(discover_repo_root())
    # Trim to one skill so we don't spend time iterating the full library here.
    skill = reg.all()[0]
    return SkillRegistry([skill]), skill


def test_executor_runs_tool_use_loop_and_returns_final_text(tmp_path: Path):
    (tmp_path / "data.txt").write_text("hello world")

    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="tool_use",
            content=[
                _TextBlock("Let me look around."),
                _ToolUseBlock(id="t1", name="list_dir", input={"path": "."}),
            ],
        ),
        _Resp(
            stop_reason="tool_use",
            content=[
                _ToolUseBlock(id="t2", name="read_file", input={"path": "data.txt"}),
            ],
        ),
        _Resp(
            stop_reason="end_turn",
            content=[_TextBlock("The file says: hello world")],
        ),
    ])

    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "what's in data.txt?")

    assert "hello world" in result.text
    assert result.turns == 3

    # Three API calls; on the 2nd call, the prior assistant + tool_result pair must be present.
    assert len(llm.calls) == 3
    msgs2 = llm.calls[1]["messages"]
    assert msgs2[0] == {"role": "user", "content": "what's in data.txt?"}
    assert msgs2[1]["role"] == "assistant"
    assert msgs2[2]["role"] == "user"
    tool_result_block = msgs2[2]["content"][0]
    assert tool_result_block["type"] == "tool_result"
    assert tool_result_block["tool_use_id"] == "t1"
    assert "data.txt" in tool_result_block["content"]

    # System prompt was sent as a cached block.
    sys_block = llm.calls[0]["system"]
    assert isinstance(sys_block, list)
    assert sys_block[0]["cache_control"] == {"type": "ephemeral"}

    # Event stream surfaces text, tool_use, tool_result, stop, usage.
    kinds = [e.kind for e in result.events]
    assert kinds.count("tool_use") == 2
    assert kinds.count("tool_result") == 2
    assert "stop" in kinds
    assert kinds[-1] == "usage"


def test_executor_persists_session_memory(tmp_path: Path):
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(stop_reason="end_turn", content=[_TextBlock("first answer")]),
        _Resp(stop_reason="end_turn", content=[_TextBlock("second answer")]),
    ])

    memory = MemoryStore(tmp_path / "sessions")
    session = Session(session_id="test-session", skill_slug=skill.slug)

    executor = Executor(reg, llm, memory=memory, workdir=tmp_path)
    executor.run(skill, "first question", session=session)

    # Round-trip from disk and continue the conversation.
    loaded = memory.load("test-session")
    assert loaded is not None
    assert [t.text for t in loaded.turns] == ["first question", "first answer"]

    executor.run(skill, "second question", session=loaded)
    loaded2 = memory.load("test-session")
    assert loaded2 is not None
    assert [t.text for t in loaded2.turns] == [
        "first question", "first answer",
        "second question", "second answer",
    ]

    # On the second run, the user message in call[0] must include the prior turns.
    second_run_msgs = llm.calls[1]["messages"]
    assert len(second_run_msgs) == 3  # u1, a1, u2
    assert second_run_msgs[0]["content"] == "first question"
    assert second_run_msgs[1]["content"] == "first answer"
    assert second_run_msgs[2]["content"] == "second question"


@dataclass
class _Delta:
    text: str
    type: str = "text_delta"


@dataclass
class _StreamEvent:
    delta: Any
    type: str = "content_block_delta"


class _FakeStream:
    """Context manager mimicking the SDK stream object."""

    def __init__(self, deltas: list[str], final: _Resp):
        self._deltas = deltas
        self._final = final

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        for d in self._deltas:
            yield _StreamEvent(delta=_Delta(text=d))

    def get_final_message(self):
        return self._final


class _StreamingStubLLM(_ScriptedLLM):
    def __init__(self, scripted_streams: list[tuple[list[str], _Resp]]):
        super().__init__([s[1] for s in scripted_streams])
        self._streams = list(scripted_streams)

    def messages_stream(self, **kwargs):
        import copy
        self.calls.append({k: copy.deepcopy(v) for k, v in kwargs.items()})
        if not self._streams:
            raise AssertionError("scripted streaming LLM ran out of responses")
        deltas, final = self._streams.pop(0)
        return _FakeStream(deltas, final)


def test_executor_streams_text_deltas_and_tool_events(tmp_path: Path):
    reg, skill = _registry_with_one_skill()
    (tmp_path / "data.txt").write_text("ok")

    llm = _StreamingStubLLM([
        (
            ["Look", "ing ", "around."],
            _Resp(
                stop_reason="tool_use",
                content=[
                    _TextBlock("Looking around."),
                    _ToolUseBlock(id="t1", name="list_dir", input={"path": "."}),
                ],
            ),
        ),
        (
            ["Done."],
            _Resp(stop_reason="end_turn", content=[_TextBlock("Done.")]),
        ),
    ])

    executor = Executor(reg, llm, workdir=tmp_path)
    events = list(executor.stream(skill, "what's here?"))

    deltas = [e.payload for e in events if e.kind == "text_delta"]
    assert "".join(deltas) == "Looking around.Done."
    kinds = [e.kind for e in events]
    assert "tool_use" in kinds
    assert "tool_result" in kinds
    assert "stop" in kinds
    assert kinds[-1] == "usage"


@dataclass
class _ServerToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "server_tool_use"


@dataclass
class _WebSearchResultBlock:
    content: str = "top result..."
    type: str = "web_search_tool_result"


def test_executor_surfaces_server_side_blocks_without_executing(tmp_path: Path):
    """server_tool_use and *_tool_result blocks should flow through, not trigger client dispatch."""
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="end_turn",
            content=[
                _ServerToolUseBlock(id="s1", name="web_search", input={"query": "x"}),
                _WebSearchResultBlock(),
                _TextBlock("Based on search, here's the answer."),
            ],
        ),
    ])
    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "research x")
    kinds = [e.kind for e in result.events]
    assert "server_tool_use" in kinds
    assert "web_search_tool_result" in kinds
    # No client-side tool_result events because no client tool_use was emitted.
    assert "tool_result" not in kinds


def test_executor_resumes_on_pause_turn(tmp_path: Path):
    """pause_turn means the server-side loop hit its limit; we should re-send and continue."""
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(stop_reason="pause_turn", content=[_TextBlock("hmm, need more...")]),
        _Resp(stop_reason="end_turn", content=[_TextBlock("final answer")]),
    ])
    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "long-running query")
    assert "final answer" in result.text
    assert result.turns == 2


def test_delegate_tool_invokes_another_skill(tmp_path: Path):
    """Skill A delegates to skill B; B returns text; A reports it back."""
    reg_full = SkillRegistry.load(discover_repo_root())
    a = reg_full.all()[0]
    b = reg_full.all()[1]
    reg = SkillRegistry([a, b])

    llm = _ScriptedLLM([
        # A calls delegate_to_skill(b, "do the thing")
        _Resp(
            stop_reason="tool_use",
            content=[_ToolUseBlock(
                id="t1", name="delegate_to_skill",
                input={"slug": b.slug, "request": "do the thing"},
            )],
        ),
        # Sub-executor turn for B — returns final text directly
        _Resp(stop_reason="end_turn", content=[_TextBlock("B done: 42")]),
        # A wraps up
        _Resp(stop_reason="end_turn", content=[_TextBlock("Got from B: 42")]),
    ])

    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(a, "please delegate")

    assert "Got from B: 42" in result.text
    tool_results = [e for e in result.events if e.kind == "tool_result"]
    assert tool_results and not tool_results[0].payload["is_error"]
    assert "B done: 42" in tool_results[0].payload["content"]


def test_delegate_depth_cap_blocks_fourth_hop(tmp_path: Path):
    """A -> B -> C is allowed; the next hop must raise via the delegate tool."""
    from agency.executor import Executor as _Exec, MAX_DELEGATION_DEPTH
    from agency.tools import ToolContext, ToolResult

    assert MAX_DELEGATION_DEPTH == 2
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([])  # never invoked — delegate runs synchronously
    executor = _Exec(reg, llm, workdir=tmp_path, delegation_depth=MAX_DELEGATION_DEPTH)
    try:
        executor._delegate(skill.slug, "do it")
    except RecursionError as e:
        assert "Delegation depth" in str(e)
    else:
        raise AssertionError("expected RecursionError")


def test_streaming_persists_memory_when_exception_aborts_mid_stream(tmp_path: Path):
    """If the generator aborts mid-stream, the session save in the finally block still runs."""
    reg, skill = _registry_with_one_skill()

    class _Boom(_StreamingStubLLM):
        def messages_stream(self, **kwargs):
            self.calls.append({})
            raise RuntimeError("simulated SDK failure")

    memory = MemoryStore(tmp_path / "sessions")
    session = Session(session_id="s-boom", skill_slug=skill.slug)

    llm = _Boom([])
    executor = Executor(reg, llm, memory=memory, workdir=tmp_path)

    try:
        for _ in executor.stream(skill, "trigger an error", session=session):
            pass
    except RuntimeError:
        pass  # expected

    # The finally block should have persisted a user turn (empty assistant is OK).
    loaded = memory.load("s-boom")
    assert loaded is not None
    assert loaded.turns, "no turns persisted after abort"
    assert loaded.turns[0].role == "user"
    assert loaded.turns[0].text == "trigger an error"


def test_delegate_tool_rejects_unknown_skill(tmp_path: Path):
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="tool_use",
            content=[_ToolUseBlock(
                id="t1", name="delegate_to_skill",
                input={"slug": "not-a-real-slug", "request": "x"},
            )],
        ),
        _Resp(stop_reason="end_turn", content=[_TextBlock("can't find it")]),
    ])
    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "delegate somewhere")
    tr = [e for e in result.events if e.kind == "tool_result"][0]
    assert tr.payload["is_error"] is True
    assert "not-a-real-slug" in tr.payload["content"]


def test_executor_sums_usage_across_turns(tmp_path: Path):
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="tool_use",
            content=[_ToolUseBlock(id="t1", name="list_dir", input={})],
            usage=_FakeUsage(input_tokens=100, output_tokens=20,
                             cache_creation_input_tokens=500, cache_read_input_tokens=0),
        ),
        _Resp(
            stop_reason="end_turn",
            content=[_TextBlock("done")],
            usage=_FakeUsage(input_tokens=150, output_tokens=30,
                             cache_creation_input_tokens=0, cache_read_input_tokens=500),
        ),
    ])
    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "anything")
    assert result.usage.input_tokens == 250
    assert result.usage.output_tokens == 50
    assert result.usage.cache_creation_input_tokens == 500
    assert result.usage.cache_read_input_tokens == 500
    # The final event is the usage event and carries the same totals.
    last = result.events[-1]
    assert last.kind == "usage"
    assert last.payload["output_tokens"] == 50


def test_parallel_tools_actually_run_concurrently(tmp_path: Path):
    """Three slow read-only tool calls should finish close to single-tool latency."""
    import time
    from agency.tools import Tool, ToolResult, ToolContext, _read_file
    from agency.executor import Executor, PARALLEL_SAFE_TOOLS

    # Register a sleepy tool and mark it parallel-safe for this test.
    def _slow(args, ctx):
        time.sleep(0.2)
        return ToolResult(f"slept {args.get('tag', '?')}")

    slow_tool = Tool(
        name="slow_read",
        description="Sleep a bit then return.",
        input_schema={"type": "object", "properties": {"tag": {"type": "string"}}},
        func=_slow,
    )

    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="tool_use",
            content=[
                _ToolUseBlock(id="t1", name="slow_read", input={"tag": "a"}),
                _ToolUseBlock(id="t2", name="slow_read", input={"tag": "b"}),
                _ToolUseBlock(id="t3", name="slow_read", input={"tag": "c"}),
            ],
        ),
        _Resp(stop_reason="end_turn", content=[_TextBlock("done")]),
    ])

    # Monkeypatch the parallel-safe set to include our test tool.
    import agency.executor as ex_mod
    original = ex_mod.PARALLEL_SAFE_TOOLS
    ex_mod.PARALLEL_SAFE_TOOLS = frozenset(original | {"slow_read"})
    try:
        executor = Executor(reg, llm, workdir=tmp_path, tools=[slow_tool])
        t0 = time.monotonic()
        result = executor.run(skill, "sleep three times")
        elapsed = time.monotonic() - t0
    finally:
        ex_mod.PARALLEL_SAFE_TOOLS = original

    # Serial would be ~0.6s; parallel should be well under ~0.4s.
    assert elapsed < 0.4, f"expected parallel (<0.4s), got {elapsed:.2f}s"
    tool_results = [e for e in result.events if e.kind == "tool_result"]
    assert [r.payload["content"] for r in tool_results] == ["slept a", "slept b", "slept c"]


def test_parallel_tools_preserve_order(tmp_path: Path):
    """When the model calls read-only tools back-to-back, results return in order."""
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")
    (tmp_path / "c.txt").write_text("C")

    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="tool_use",
            content=[
                _ToolUseBlock(id="t1", name="read_file", input={"path": "a.txt"}),
                _ToolUseBlock(id="t2", name="read_file", input={"path": "b.txt"}),
                _ToolUseBlock(id="t3", name="read_file", input={"path": "c.txt"}),
            ],
        ),
        _Resp(stop_reason="end_turn", content=[_TextBlock("saw A, B, C")]),
    ])

    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "read those three")

    tool_results = [e for e in result.events if e.kind == "tool_result"]
    assert [r.payload["content"] for r in tool_results] == ["A", "B", "C"]


def test_executor_handles_unknown_tool_gracefully(tmp_path: Path):
    reg, skill = _registry_with_one_skill()
    llm = _ScriptedLLM([
        _Resp(
            stop_reason="tool_use",
            content=[_ToolUseBlock(id="t1", name="nonexistent_tool", input={})],
        ),
        _Resp(stop_reason="end_turn", content=[_TextBlock("ok, giving up on that tool")]),
    ])

    executor = Executor(reg, llm, workdir=tmp_path)
    result = executor.run(skill, "use a missing tool")

    assert "giving up" in result.text
    tool_results = [e for e in result.events if e.kind == "tool_result"]
    assert tool_results and tool_results[0].payload["is_error"] is True
    assert "Unknown tool" in tool_results[0].payload["content"]
