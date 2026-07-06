"""Durable, crash-safe job store for the live runtime (SPEC.md §7.5 #1).

The scheduler's set of jobs must survive a SIGKILL mid-write: a persistent
trading runner that loses or truncates its job store on a crash would silently
stop watching the mandate's cadence. This store guarantees:

* **Atomic save** — write a temp file in the *same* directory, ``fsync`` it,
  ``os.replace`` over the target (atomic on POSIX/NTFS), then ``fsync`` the
  parent directory so the rename itself is durable. A crash at any instant
  leaves either the old complete store or the new complete store, never a
  truncated one.
* **Corruption quarantine** — a store whose JSON no longer parses is renamed
  ``<name>.corrupt-<ts>`` and the load **refuses to start empty**: it raises
  :class:`CorruptJobStoreError` rather than silently booting with zero jobs
  (which on a trading runner would look like "mandate has no work" and stop
  all activity). A genuinely-missing store (first boot) loads as empty — that
  is the only blank-start path.

State lives under ``live_root()/runtime/`` (see :mod:`src.live.paths`).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from src.live.paths import live_root
from src.live.runtime.scheduler import Job

logger = logging.getLogger(__name__)

_STORE_FILENAME = "jobs.json"
_RUNTIME_SUBDIR = "runtime"
#: Schema version of the persisted store envelope. Bump on breaking changes so
#: a future loader can branch instead of mis-parsing an old layout.
_SCHEMA_VERSION = 1


class CorruptJobStoreError(RuntimeError):
    """Raised when the on-disk store exists but cannot be parsed.

    Carries the path the corrupt file was quarantined to so an operator can
    inspect it. The runner must surface this rather than boot with no jobs.
    """

    def __init__(self, original: Path, quarantined: Path, cause: str) -> None:
        """Initialize the error.

        Args:
            original: Path of the store that failed to parse.
            quarantined: Path the corrupt file was renamed to.
            cause: Short description of why parsing failed.
        """
        super().__init__(
            f"job store {original} is corrupt ({cause}); "
            f"quarantined to {quarantined} — refusing empty start"
        )
        self.original = original
        self.quarantined = quarantined
        self.cause = cause


def runtime_dir() -> Path:
    """Return the runtime state directory (``live_root()/runtime``).

    Returns:
        The directory path. Not created here; :meth:`JobStore.save` creates it
        with ``0700`` perms before the first write.
    """
    return live_root() / _RUNTIME_SUBDIR


class JobStore:
    """Crash-safe, on-disk persistence for the scheduler's job set.

    The store is a thin durable envelope around a list of :class:`Job`. It owns
    only serialization + atomic IO; scheduling decisions live in
    :class:`src.live.runtime.scheduler.Scheduler`.

    Attributes:
        path: Absolute path of the JSON store file.
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the store.

        Args:
            path: Explicit store path. When ``None`` (default), resolves to
                ``runtime_dir()/jobs.json``. Resolved lazily-but-once here so a
                test that monkeypatches ``get_runtime_root`` before construction
                gets the isolated path.
        """
        self.path = path if path is not None else runtime_dir() / _STORE_FILENAME

    def load(self) -> list[Job]:
        """Load the persisted jobs.

        A missing store (never written) is the *only* clean empty result. A
        store that exists but fails to parse is quarantined and the load raises,
        so the runner never silently starts with no work.

        Returns:
            The persisted jobs, or an empty list when the store has never been
            written.

        Raises:
            CorruptJobStoreError: If the store exists but its JSON / schema
                cannot be parsed. The corrupt file is renamed first.
        """
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
            envelope = json.loads(raw)
            jobs_raw = self._extract_jobs(envelope)
            return [self._job_from_dict(item) for item in jobs_raw]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            quarantined = self._quarantine(str(exc))
            raise CorruptJobStoreError(self.path, quarantined, str(exc)) from exc

    def save(self, jobs: list[Job]) -> None:
        """Atomically persist the job set.

        Write sequence (durable even under SIGKILL): temp file in the same dir
        → ``os.fsync`` the temp fd → ``os.replace`` onto the target →
        ``fsync`` the parent directory fd so the rename is itself durable.

        Args:
            jobs: The full job set to persist (the store holds the complete
                set, not a delta).

        Raises:
            OSError: If the directory cannot be created or the write fails.
        """
        target = self.path
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
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

    def _quarantine(self, cause: str) -> Path:
        """Rename the corrupt store aside as ``<name>.corrupt-<ts>``.

        Args:
            cause: Reason string (logged only).

        Returns:
            The path the corrupt store was moved to. If the rename itself fails
            the original path is returned (best-effort quarantine).
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        quarantined = self.path.with_name(f"{self.path.name}.corrupt-{ts}")
        try:
            os.replace(self.path, quarantined)
            logger.error(
                "job store %s corrupt (%s) — quarantined to %s",
                self.path,
                cause,
                quarantined,
            )
            return quarantined
        except OSError:
            logger.error(
                "job store %s corrupt (%s) — quarantine rename failed",
                self.path,
                cause,
                exc_info=True,
            )
            return self.path

    @staticmethod
    def _fsync_dir(directory: Path) -> None:
        """Fsync a directory fd so a contained ``os.replace`` is durable.

        On platforms where opening a directory for fsync is unsupported (some
        Windows builds), this is a best-effort no-op: ``os.replace`` is already
        atomic there, only the rename's durability window differs.

        Args:
            directory: The directory whose entry was just renamed.
        """
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
    def _envelope(jobs: list[Job]) -> dict[str, object]:
        """Wrap jobs in the versioned on-disk envelope.

        Args:
            jobs: Jobs to serialize.

        Returns:
            A JSON-serializable dict carrying schema version + job list.
        """
        return {
            "schema_version": _SCHEMA_VERSION,
            "jobs": [JobStore._job_to_dict(job) for job in jobs],
        }

    @staticmethod
    def _extract_jobs(envelope: object) -> list[dict]:
        """Validate the envelope shape and return its raw job dicts.

        Args:
            envelope: The parsed top-level JSON value.

        Returns:
            The list of raw job dicts.

        Raises:
            ValueError: If the envelope shape is unrecognized.
        """
        if not isinstance(envelope, dict):
            raise ValueError("store root is not a JSON object")
        jobs = envelope.get("jobs")
        if not isinstance(jobs, list):
            raise ValueError("store 'jobs' is missing or not a list")
        if not all(isinstance(item, dict) for item in jobs):
            raise ValueError("store 'jobs' contains a non-object entry")
        return jobs

    @staticmethod
    def _job_to_dict(job: Job) -> dict[str, object]:
        """Serialize a :class:`Job` to a plain dict.

        Args:
            job: The job to serialize.

        Returns:
            A JSON-serializable dict.
        """
        return {
            "id": job.id,
            "next_run_at": job.next_run_at,
            "schedule": job.schedule,
            "payload": job.payload,
        }

    @staticmethod
    def _job_from_dict(item: dict) -> Job:
        """Reconstruct a :class:`Job` from a persisted dict.

        Args:
            item: A raw job dict from the store.

        Returns:
            The reconstructed Job.

        Raises:
            KeyError: If a required field is absent.
            TypeError: If a field has the wrong type.
        """
        job_id = item["id"]
        next_run_at = item["next_run_at"]
        schedule = item["schedule"]
        if not isinstance(job_id, str) or not isinstance(schedule, str):
            raise TypeError("job 'id' and 'schedule' must be strings")
        if not isinstance(next_run_at, int):
            raise TypeError("job 'next_run_at' must be an int (epoch ms)")
        payload = item.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise TypeError("job 'payload' must be an object or null")
        return Job(
            id=job_id,
            next_run_at=next_run_at,
            schedule=schedule,
            payload=payload,
        )
