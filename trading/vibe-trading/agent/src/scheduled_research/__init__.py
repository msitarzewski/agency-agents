"""Scheduled research job data model and durable store.

This package provides the data model (``ScheduledResearchJob``) and
crash-safe persistence (``ScheduledResearchJobStore``) for scheduled
research / backtest jobs. It intentionally does NOT wire execution --
recording and exposing jobs is the only responsibility here.
"""

from src.scheduled_research.models import JobStatus, ScheduledResearchJob
from src.scheduled_research.store import ScheduledResearchJobStore

__all__ = [
    "JobStatus",
    "ScheduledResearchJob",
    "ScheduledResearchJobStore",
]
