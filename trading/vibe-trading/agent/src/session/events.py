"""SSE event bus with support for last_event_id recovery and buffering.

V5: Fixes the thread-safety issue caused by calling queue.put_nowait() on asyncio.Queue from a background thread.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class SSEEvent:
    """Server-sent event.

    Attributes:
        event_id: Globally unique event ID used for last_event_id recovery.
        event_type: Event type stored in the SSE ``event`` field.
        data: Event payload.
        session_id: Owning session ID.
        timestamp: Event timestamp.
    """

    event_id: Optional[str] = field(default_factory=lambda: uuid.uuid4().hex[:16])
    event_type: str = "message"
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """Format the event as an SSE text frame.

        Returns:
            Text that conforms to the SSE specification.
        """
        payload = json.dumps(self.data, ensure_ascii=False)
        lines = []
        if self.event_id:
            lines.append(f"id: {self.event_id}")
        lines.extend([
            f"event: {self.event_type}",
            f"data: {payload}",
            "",
            "",
        ])
        return "\n".join(lines)


class EventBus:
    """Session-scoped event bus with subscribers and buffered events.

    V5: Inject the asyncio event loop with ``set_loop()``, and use
    ``call_soon_threadsafe`` in ``publish()`` to preserve thread safety.

    Attributes:
        max_buffer_size: Maximum number of buffered events per session.
    """

    def __init__(self, max_buffer_size: int = 500) -> None:
        """Initialize the event bus.

        Args:
            max_buffer_size: Maximum number of buffered events per session.
        """
        self.max_buffer_size = max_buffer_size
        self._buffers: Dict[str, List[SSEEvent]] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the asyncio event loop, usually during api_server startup.

        Args:
            loop: asyncio event loop.
        """
        self._loop = loop

    def publish(self, event: SSEEvent) -> None:
        """Publish an event to a session channel in a thread-safe way.

        Args:
            event: Event to publish.
        """
        session_id = event.session_id
        with self._lock:
            if session_id not in self._buffers:
                self._buffers[session_id] = []
            buffer = self._buffers[session_id]
            buffer.append(event)
            if len(buffer) > self.max_buffer_size:
                self._buffers[session_id] = buffer[-self.max_buffer_size:]

            queues = list(self._subscribers.get(session_id, []))

        # Safely enqueue onto the queue from inside the asyncio loop.
        for queue in queues:
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._safe_put, queue, event)
            else:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass

    @staticmethod
    def _safe_put(queue: asyncio.Queue, event: SSEEvent) -> None:
        """Safely put an event onto a queue.

        Args:
            queue: asyncio queue.
            event: SSE event.
        """
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("EventBus queue full, dropping %s event for session %s", event.event_type, event.session_id)

    def emit(
        self,
        session_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> SSEEvent:
        """Build and publish an event in one step.

        Args:
            session_id: Session ID.
            event_type: Event type.
            data: Event payload.

        Returns:
            The published SSEEvent.
        """
        event = SSEEvent(
            event_type=event_type,
            data=data or {},
            session_id=session_id,
        )
        self.publish(event)
        return event

    def replay(
        self,
        session_id: str,
        last_event_id: Optional[str] = None,
        *,
        replay_all: bool = False,
    ) -> List[SSEEvent]:
        """Replay buffered session events for reconnect recovery.

        Args:
            session_id: Session ID.
            last_event_id: Last event ID received by the client.
            replay_all: Return the buffered stream from the beginning when
                ``last_event_id`` is absent. Used only for active run recovery;
                completed history is loaded through REST.

        Returns:
            List of events that should be replayed.
        """
        with self._lock:
            buffer = self._buffers.get(session_id, [])
            if not last_event_id:
                return list(buffer) if replay_all else []  # First connect: history loaded via REST by default.
            found = False
            result: List[SSEEvent] = []
            for event in buffer:
                if found:
                    result.append(event)
                elif event.event_id == last_event_id:
                    found = True
            if not found and replay_all:
                return list(buffer)
            return result

    async def subscribe(
        self,
        session_id: str,
        last_event_id: Optional[str] = None,
        *,
        replay_all: bool = False,
    ) -> AsyncIterator[SSEEvent]:
        """Subscribe to a session event stream asynchronously.

        Args:
            session_id: Session ID.
            last_event_id: Last event ID received by the client for reconnect recovery.
            replay_all: Replay all buffered events when no last event ID is
                available. This is opt-in for active run hydration.

        Yields:
            SSEEvent objects.
        """
        queue: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=200)

        with self._lock:
            if session_id not in self._subscribers:
                self._subscribers[session_id] = []
            self._subscribers[session_id].append(queue)

        try:
            replay_events = self.replay(session_id, last_event_id, replay_all=replay_all)
            for event in replay_events:
                yield event

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    yield SSEEvent(
                        event_id=None,
                        event_type="heartbeat",
                        data={"ts": time.time()},
                        session_id=session_id,
                    )
        finally:
            with self._lock:
                subs = self._subscribers.get(session_id, [])
                if queue in subs:
                    subs.remove(queue)

    def clear(self, session_id: str) -> None:
        """Clear the buffered events for a session.

        Args:
            session_id: Session ID.
        """
        with self._lock:
            self._buffers.pop(session_id, None)
