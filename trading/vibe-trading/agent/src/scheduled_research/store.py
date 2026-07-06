"""Crash-safe store for scheduled research jobs.

Uses the same atomic write pattern as ``src.live.runtime.jobstore`` (write a
temp file in the same directory, fsync, replace, fsync the parent dir) so the
store survives a SIGKILL at any point without corruption.

A missing store file is the only clean empty result. A file that exists but
fails to parse is quarantined and ``load`` raises ``CorruptStoreError`` instead
of silently returning an empty list.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.config.paths import get_runtime_root
from src.scheduled_research.models import ScheduledResearchJob, validate_schedule

logger = logging.getLogger(__name__)

_STORE_FILENAME = "scheduled_research_jobs.json"
_SCHEMA_VERSION = 1


def _default_store_path() -> Path:
    """Return the default path for the scheduled-research store.

    Roots job state under the user runtime dir (``~/.vibe-trading`` by
    default), never inside the repo working tree — the same root the live
    runtime, swarm config, and persistent memory resolve via
    :func:`src.config.paths.get_runtime_root`.
    """
    return get_runtime_root() / "scheduled_research" / _STORE_FILENAME


class CorruptStoreError(RuntimeError):
    """Raised when the store exists but cannot be parsed.

    The corrupt file is renamed aside (quarantined) before this is raised.

    Attributes:
        original: Path that failed to parse.
        quarantined: Path the corrupt file was moved to.
        cause: Short description of the parse failure.
    """

    def __init__(self, original: Path, quarantined: Path, cause: str) -> None:
        super().__init__(f"scheduled-research store {original} is corrupt ({cause}); quarantined to {quarantined}")
        self.original = original
        self.quarantined = quarantined
        self.cause = cause


class ScheduledResearchJobStore:
    """Durable, crash-safe persistence for scheduled research jobs.

    The store is a thin envelope around a dict of
    :class:`~src.scheduled_research.models.ScheduledResearchJob` keyed by
    job id. It owns only serialization and atomic I/O; scheduling decisions
    live elsewhere.

    Attributes:
        path: Absolute path of the backing JSON file.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        """Initialize the store.

        Args:
            path: Explicit path. Defaults to
                ``agent/data/scheduled_research_jobs.json``.
        """
        self.path: Path = path if path is not None else _default_store_path()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> Dict[str, ScheduledResearchJob]:
        """Load all persisted jobs.

        Returns:
            A dict mapping job id to job. Empty when the store has never been
            written.

        Raises:
            CorruptStoreError: When the file exists but cannot be parsed.
        """
        if not self.path.exists():
            return {}
        try:
            raw = self.path.read_text(encoding="utf-8")
            envelope = json.loads(raw)
            jobs_raw = self._extract_jobs(envelope)
            result: Dict[str, ScheduledResearchJob] = {}
            for item in jobs_raw:
                job = ScheduledResearchJob.from_dict(item)
                result[job.id] = job
            return result
        except (OSError, ValueError, KeyError, TypeError) as exc:
            quarantined = self._quarantine(str(exc))
            raise CorruptStoreError(self.path, quarantined, str(exc)) from exc

    def save(self, jobs: Dict[str, ScheduledResearchJob]) -> None:
        """Atomically persist the full job set.

        Write sequence: temp file in same dir -> fsync -> os.replace -> fsync
        parent dir. A SIGKILL at any step leaves either the old complete store
        or the new one, never a partial write.

        Args:
            jobs: Mapping of job id to job (the full set, not a delta).

        Raises:
            OSError: When the directory cannot be created or the write fails.
        """
        target = self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._envelope(jobs), ensure_ascii=False, indent=2)

        tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, payload.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)

        os.replace(tmp, target)
        self._fsync_dir(target.parent)

    def upsert(self, job: ScheduledResearchJob) -> None:
        """Insert or replace a job by id.

        Validates the schedule string before persisting.

        Args:
            job: The job to store.

        Raises:
            ValueError: When ``job.schedule`` is malformed.
            CorruptStoreError: When the existing store cannot be parsed.
        """
        validate_schedule(job.schedule)
        jobs = self.load()
        jobs[job.id] = job
        self.save(jobs)

    def get(self, job_id: str) -> Optional[ScheduledResearchJob]:
        """Return a job by id, or ``None`` when it does not exist.

        Args:
            job_id: Job identifier.

        Returns:
            The matching job or ``None``.
        """
        return self.load().get(job_id)

    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ScheduledResearchJob]:
        """Return jobs, optionally filtered by status.

        Args:
            status: When provided, include only jobs whose status matches this
                string (e.g. ``"pending"``).
            limit: Maximum number of jobs to return (newest first by
                ``created_at``).

        Returns:
            A list of at most *limit* jobs sorted descending by ``created_at``.
        """
        jobs = list(self.load().values())
        if status is not None:
            jobs = [j for j in jobs if j.status.value == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def delete(self, job_id: str) -> bool:
        """Remove a job by id.

        Args:
            job_id: Identifier of the job to remove.

        Returns:
            ``True`` when the job was found and removed; ``False`` when it was
            not in the store.
        """
        jobs = self.load()
        if job_id not in jobs:
            return False
        del jobs[job_id]
        self.save(jobs)
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _quarantine(self, cause: str) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        quarantined = self.path.with_name(f"{self.path.name}.corrupt-{ts}")
        try:
            os.replace(self.path, quarantined)
            logger.error(
                "scheduled-research store %s corrupt (%s) — quarantined to %s",
                self.path,
                cause,
                quarantined,
            )
        except OSError:
            logger.error(
                "scheduled-research store %s corrupt (%s) — quarantine rename failed",
                self.path,
                cause,
                exc_info=True,
            )
            return self.path
        return quarantined

    @staticmethod
    def _fsync_dir(directory: Path) -> None:
        try:
            dir_fd = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(dir_fd)
        except OSError:
            logger.debug("parent-dir fsync unsupported on %s", directory, exc_info=True)
        finally:
            os.close(dir_fd)

    @staticmethod
    def _envelope(jobs: Dict[str, ScheduledResearchJob]) -> dict:
        return {
            "schema_version": _SCHEMA_VERSION,
            "jobs": [j.to_dict() for j in jobs.values()],
        }

    @staticmethod
    def _extract_jobs(envelope: object) -> List[dict]:
        if not isinstance(envelope, dict):
            raise ValueError("store root is not a JSON object")
        jobs = envelope.get("jobs")
        if not isinstance(jobs, list):
            raise ValueError("store 'jobs' is missing or not a list")
        if not all(isinstance(item, dict) for item in jobs):
            raise ValueError("store 'jobs' contains a non-object entry")
        return jobs
