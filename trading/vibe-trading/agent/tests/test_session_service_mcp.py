"""SessionService regressions for remote MCP startup paths."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from src.session.events import EventBus
from src.session.models import Attempt
from src.session.service import SessionService
from src.session.store import SessionStore


class _DummyIndex:
    def index_session(self, session_id: str, title: str) -> None:
        del session_id, title

    def index_message(self, session_id: str, role: str, content: str) -> None:
        del session_id, role, content


class _DummyAgentLoop:
    def __init__(self, *, registry, llm, event_callback, max_iterations, persistent_memory) -> None:
        del registry, llm, event_callback, max_iterations, persistent_memory

    def run(self, *, user_message: str, history, session_id: str) -> dict[str, str]:
        del user_message, history, session_id
        return {"status": "completed"}


def test_run_with_agent_keeps_event_loop_responsive_during_registry_build(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def _slow_build_registry(**kwargs):
        del kwargs
        time.sleep(0.25)
        return object()

    monkeypatch.setattr("src.session.service.get_shared_index", lambda: _DummyIndex())
    monkeypatch.setattr("src.tools.build_registry", _slow_build_registry)
    monkeypatch.setattr("src.providers.chat.ChatLLM", lambda: object())
    monkeypatch.setattr("src.memory.persistent.PersistentMemory", lambda: object())
    monkeypatch.setattr("src.agent.loop.AgentLoop", _DummyAgentLoop)
    monkeypatch.setattr("src.config.loader.load_runtime_agent_config", lambda overrides=None: object())
    monkeypatch.setattr("src.config.loader.sanitize_session_overrides", lambda overrides: dict(overrides))

    service = SessionService(
        store=SessionStore(tmp_path / "sessions"),
        event_bus=EventBus(),
        runs_dir=tmp_path / "runs",
    )
    attempt = Attempt(session_id="session-1", prompt="hello")

    async def _ticker(events: list[float], start: float) -> None:
        await asyncio.sleep(0.05)
        events.append(time.perf_counter() - start)

    async def _exercise() -> tuple[list[float], dict[str, str]]:
        events: list[float] = []
        start = time.perf_counter()
        asyncio.create_task(_ticker(events, start))
        result = await service._run_with_agent(attempt, messages=[], session_config={})
        await asyncio.sleep(0.01)
        return events, result

    tick_times, result = asyncio.run(_exercise())

    assert result["status"] == "completed"
    assert tick_times, "Expected the event loop ticker to run while registry build was pending"
    assert tick_times[0] < 0.18, f"Registry build blocked the event loop for too long: {tick_times[0]:.3f}s"