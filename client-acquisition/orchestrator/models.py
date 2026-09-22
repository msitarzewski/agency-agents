"""Core state contracts for the Client Acquisition OS.

The module is dependency-free so the orchestration foundation can be embedded
in a CLI, API service, worker, or future dashboard without changing contracts.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class LeadStatus(str, Enum):
    NEW = "NEW"
    RESEARCHING = "RESEARCHING"
    QUALIFIED = "QUALIFIED"
    READY_FOR_OUTREACH = "READY_FOR_OUTREACH"
    OUTREACH_PENDING_APPROVAL = "OUTREACH_PENDING_APPROVAL"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    INTERESTED = "INTERESTED"
    MEETING_BOOKED = "MEETING_BOOKED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    WON = "WON"
    LOST = "LOST"


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Lead:
    company_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    status: LeadStatus = LeadStatus.NEW
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class Research:
    lead_id: str
    summary: str
    evidence: List[str] = field(default_factory=list)
    pain_points: List[Dict[str, Any]] = field(default_factory=list)
    confidence: Optional[float] = None
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class OutreachDraft:
    lead_id: str
    channel: str
    subject: Optional[str]
    body: str
    rationale: str = ""
    approved: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class AgentRun:
    agent: str
    lead_id: str
    input: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    status: RunStatus = RunStatus.PENDING
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
