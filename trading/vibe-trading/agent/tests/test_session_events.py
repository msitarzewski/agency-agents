"""Session SSE event buffer recovery tests."""

from __future__ import annotations

from src.session.events import EventBus, SSEEvent


def test_first_connect_does_not_replay_completed_history_by_default() -> None:
    bus = EventBus()
    bus.emit("s1", "tool_call", {"tool": "load_skill"})

    assert bus.replay("s1") == []


def test_active_run_first_connect_can_replay_entire_buffer() -> None:
    bus = EventBus()
    first = bus.emit("s1", "tool_call", {"tool": "load_skill"})
    second = bus.emit("s1", "tool_result", {"tool": "load_skill", "status": "ok"})

    assert bus.replay("s1", replay_all=True) == [first, second]


def test_last_event_id_replay_still_returns_only_later_events() -> None:
    bus = EventBus()
    first = bus.emit("s1", "tool_call", {"tool": "load_skill"})
    second = bus.emit("s1", "tool_result", {"tool": "load_skill", "status": "ok"})
    third = bus.emit("s1", "text_delta", {"delta": "done"})

    assert bus.replay("s1", last_event_id=first.event_id, replay_all=True) == [second, third]


def test_replay_all_with_unknown_last_event_id_returns_buffer() -> None:
    """A non-buffered heartbeat id must not cause active terminal events to be skipped."""
    bus = EventBus()
    first = bus.emit("s1", "tool_call", {"tool": "load_skill"})
    terminal = bus.emit("s1", "attempt.completed", {"summary": "done"})

    assert bus.replay("s1", last_event_id="synthetic-heartbeat-id", replay_all=True) == [
        first,
        terminal,
    ]


def test_synthetic_heartbeat_frame_has_no_replay_id() -> None:
    heartbeat = SSEEvent(event_id=None, event_type="heartbeat", data={"ts": 1}, session_id="s1")

    frame = heartbeat.to_sse()

    assert "event: heartbeat" in frame
    assert "id:" not in frame
