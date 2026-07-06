"""Session data models for the core Session, Message, and Attempt entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionStatus(str, Enum):
    """Session lifecycle states."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AttemptStatus(str, Enum):
    """Statuses for a single execution attempt."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Session:
    """A multi-turn conversation session.

    Attributes:
        session_id: Unique identifier.
        title: User-visible session title.
        status: Session status.
        created_at: Creation time in ISO format.
        updated_at: Last update time in ISO format.
        last_attempt_id: ID of the most recent Attempt.
        config: Session-level configuration such as model overrides or strategy parameters.
    """

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_attempt_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the session to a dictionary.

        Returns:
            A JSON-serializable dictionary.
        """
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Session:
        """Deserialize a session from a dictionary.

        Args:
            data: Dictionary produced from parsed JSON.

        Returns:
            A Session instance.
        """
        data = dict(data)
        if "status" in data:
            data["status"] = SessionStatus(data["status"])
        return cls(**data)


@dataclass
class Message:
    """A session message such as user input or system output.

    Attributes:
        message_id: Unique identifier.
        session_id: Owning session ID.
        role: Message role: user / assistant / system.
        content: Message text content.
        created_at: Creation time in ISO format.
        linked_attempt_id: Related Attempt ID, if any.
        metadata: Additional metadata.
    """

    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = ""
    role: str = "user"
    content: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    linked_attempt_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the message to a dictionary.

        Returns:
            A JSON-serializable dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """Deserialize a message from a dictionary.

        Args:
            data: Dictionary produced from parsed JSON.

        Returns:
            A Message instance.
        """
        return cls(**data)


@dataclass
class Attempt:
    """A strategy execution attempt corresponding to one pipeline run.

    Attributes:
        attempt_id: Unique identifier.
        session_id: Owning session ID.
        parent_attempt_id: Parent Attempt ID for follow-up modification scenarios.
        status: Execution status.
        prompt: User input that triggered this execution.
        run_dir: Run directory path.
        summary: Execution summary.
        react_trace: ReAct agent trace records.
        created_at: Creation time in ISO format.
        completed_at: Completion time in ISO format, if available.
        error: Error message when the attempt fails.
        metrics: Snapshot of backtest metrics.
    """

    attempt_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = ""
    parent_attempt_id: Optional[str] = None
    status: AttemptStatus = AttemptStatus.PENDING
    prompt: str = ""
    run_dir: Optional[str] = None
    summary: Optional[str] = None
    react_trace: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the attempt to a dictionary.

        Returns:
            A JSON-serializable dictionary.
        """
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Attempt:
        """Deserialize an attempt from a dictionary.

        Args:
            data: Dictionary produced from parsed JSON.

        Returns:
            An Attempt instance.
        """
        data = dict(data)
        if "status" in data:
            data["status"] = AttemptStatus(data["status"])
        return cls(**data)

    def mark_running(self) -> None:
        """Mark the attempt as running."""
        self.status = AttemptStatus.RUNNING
        self.completed_at = None

    def mark_completed(self, summary: Optional[str] = None) -> None:
        """Mark the attempt as completed.

        Args:
            summary: Execution summary.
        """
        self.status = AttemptStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        if summary:
            self.summary = summary

    def mark_failed(self, error: str) -> None:
        """Mark the attempt as failed.

        Args:
            error: Error message.
        """
        self.status = AttemptStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error = error
