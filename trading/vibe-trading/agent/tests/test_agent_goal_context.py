"""AgentLoop regressions for active research goal context."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src.agent.loop import AgentLoop
from src.goal import GoalStore


class _AnswerResponse:
    def __init__(self, content: str = "done", total_tokens: int = 0) -> None:
        self.content = content
        self.tool_calls: list[Any] = []
        self.reasoning_content: str | None = None
        self.has_tool_calls = False
        self.usage_metadata = {"total_tokens": total_tokens} if total_tokens else {}


class _CapturingLLM:
    def __init__(self, total_tokens: int = 0) -> None:
        self.total_tokens = total_tokens
        self.messages: list[dict[str, Any]] = []
        self.calls: list[list[dict[str, Any]]] = []

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[Any] | None = None,
        on_text_chunk: Callable[[str], None] | None = None,
        on_reasoning_chunk: Callable[[str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> _AnswerResponse:
        del tools, on_text_chunk, on_reasoning_chunk
        self.messages = messages
        self.calls.append([dict(item) for item in messages])
        return _AnswerResponse(total_tokens=self.total_tokens)

    def chat(self, messages: list[dict[str, Any]], **_: Any) -> _AnswerResponse:
        self.messages = messages
        return _AnswerResponse(total_tokens=self.total_tokens)


def _agent(llm: _CapturingLLM, run_dir: Path) -> AgentLoop:
    from src.memory.persistent import PersistentMemory
    from src.tools import build_registry

    pm = PersistentMemory()
    agent = AgentLoop(
        registry=build_registry(persistent_memory=pm, include_shell_tools=False),
        llm=llm,
        max_iterations=2,
        persistent_memory=pm,
    )
    run_dir.mkdir(parents=True)
    agent.memory.run_dir = str(run_dir)
    return agent


def test_agent_loop_injects_active_goal_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("src.agent.loop.GOAL_MAX_CONTINUATIONS", 0)
    monkeypatch.setenv("VIBE_TRADING_GOAL_DB_PATH", str(tmp_path / "goals.db"))
    store = GoalStore()
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis", "Check price action"],
    )
    llm = _CapturingLLM()

    result = _agent(llm, tmp_path / "run").run(
        user_message="Continue the analysis.",
        session_id="session-1",
    )

    user_message = llm.messages[-1]["content"]
    assert result["status"] == "success"
    assert "<current-research-goal>" in user_message
    assert goal.goal_id in user_message
    assert "expected_goal_id" in user_message
    assert "Evaluate NVDA momentum." in user_message
    assert "Continue the analysis." in user_message


def test_agent_loop_accounts_goal_token_and_turn_usage(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("src.agent.loop.GOAL_MAX_CONTINUATIONS", 0)
    monkeypatch.setenv("VIBE_TRADING_GOAL_DB_PATH", str(tmp_path / "goals.db"))
    store = GoalStore()
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis"],
        token_budget=100,
        turn_budget=5,
    )
    llm = _CapturingLLM(total_tokens=17)

    _agent(llm, tmp_path / "run").run(
        user_message="Continue the analysis.",
        session_id="session-1",
    )

    updated = store.get_goal(goal.goal_id)
    assert updated is not None
    assert updated.tokens_used == 17
    assert updated.turns_used == 1


def test_agent_loop_continues_active_incomplete_goal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("src.agent.loop.GOAL_MAX_CONTINUATIONS", 1)
    monkeypatch.setenv("VIBE_TRADING_GOAL_DB_PATH", str(tmp_path / "goals.db"))
    store = GoalStore()
    store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis", "Check price action"],
    )
    llm = _CapturingLLM()

    result = _agent(llm, tmp_path / "run").run(
        user_message="Start the goal.",
        session_id="session-1",
    )

    assert result["status"] == "success"
    assert len(llm.calls) == 2
    assert "<goal-continuation>" in llm.calls[1][-1]["content"]
    assert "criteria_snapshot:" in llm.calls[1][-1]["content"]
    assert "recent_evidence_snapshot:" in llm.calls[1][-1]["content"]
    assert "Check price action" in llm.calls[1][-1]["content"]


def test_agent_loop_continues_active_covered_goal_to_force_audit(tmp_path: Path, monkeypatch) -> None:
    """Covered criteria still need a terminal status audit before the loop stops."""
    from src.goal import EvidenceInput

    monkeypatch.setattr("src.agent.loop.GOAL_MAX_CONTINUATIONS", 1)
    monkeypatch.setenv("VIBE_TRADING_GOAL_DB_PATH", str(tmp_path / "goals.db"))
    store = GoalStore()
    goal = store.replace_goal(
        session_id="session-1",
        objective="Evaluate NVDA momentum.",
        criteria=["Define thesis"],
    )
    criterion = store.list_criteria(goal.goal_id)[0]
    store.append_evidence(
        session_id="session-1",
        goal_id=goal.goal_id,
        expected_goal_id=goal.goal_id,
        evidence=EvidenceInput(
            criterion_id=criterion.criterion_id,
            text="Thesis evidence exists, but the goal is not terminal yet.",
            run_id="missing-run-is-ok-for-coverage",
        ),
    )
    llm = _CapturingLLM()

    result = _agent(llm, tmp_path / "run").run(
        user_message="Finish the goal.",
        session_id="session-1",
    )

    assert result["status"] == "success"
    assert len(llm.calls) == 2
    continuation = llm.calls[1][-1]["content"]
    assert "<goal-continuation>" in continuation
    assert "All criteria appear covered; audit evidence" in continuation
    assert "status: active" in continuation
