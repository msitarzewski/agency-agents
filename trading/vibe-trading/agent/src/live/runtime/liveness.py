"""Runner liveness for the live runtime (SPEC.md §7.5 #3).

A persistent trading runner must be *detectably* alive. Each runner writes a
heartbeat file (its last-tick epoch-ms timestamp) under ``live_root()/runtime/``
every tick; a stale heartbeat means the process died without cleanup (zombie /
SIGKILL / host crash). The reaper borrows :mod:`src.swarm.runtime`'s shape: a
read-only staleness check (``last_tick`` older than a threshold) drives a
separate purge, so the same predicate serves both "is this runner alive?" reads
and the destructive reap.

A live runner that looks dead must never be re-spawned blindly — reconciliation
(SPEC #5) runs first — so this module only *reports* and *purges sentinels*; it
never starts or kills processes.

Heartbeat writes are atomic (same-dir temp + ``os.replace``) so a concurrent
:func:`last_tick` read can never see a torn timestamp.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from src.live.runtime.jobstore import runtime_dir

logger = logging.getLogger(__name__)

_HEARTBEAT_SUFFIX = ".heartbeat"
_HEARTBEAT_DIR = "heartbeats"

#: A runner is considered dead if its last tick is older than this. Generous
#: relative to a tick (the runner heartbeats once per scheduler wake, well
#: under a minute) so a momentarily slow tick is never false-reaped.
DEFAULT_STALENESS_MS = 90 * 1000


def _now_ms() -> int:
    """Return the current wall-clock time in epoch milliseconds.

    Returns:
        Milliseconds since the Unix epoch.
    """
    return int(time.time() * 1000)


def heartbeats_dir() -> Path:
    """Return the directory holding per-runner heartbeat files.

    Returns:
        ``live_root()/runtime/heartbeats``. Not created here; written lazily by
        :func:`write_heartbeat`.
    """
    return runtime_dir() / _HEARTBEAT_DIR


def heartbeat_path(runner_id: str) -> Path:
    """Return the heartbeat file path for a runner.

    Args:
        runner_id: Stable runner identifier.

    Returns:
        ``live_root()/runtime/heartbeats/<runner_id>.heartbeat``.

    Raises:
        ValueError: If ``runner_id`` is empty/whitespace or contains a path
            separator or ``..`` segment (a runner id is never a path).
    """
    key = runner_id.strip()
    if not key:
        raise ValueError("runner_id must not be empty")
    if "/" in key or "\\" in key or ".." in key:
        raise ValueError(f"invalid runner_id: {runner_id!r}")
    return heartbeats_dir() / f"{key}{_HEARTBEAT_SUFFIX}"


def write_heartbeat(runner_id: str, *, now_ms: int | None = None) -> int:
    """Atomically record a runner's last-tick timestamp.

    Args:
        runner_id: The runner writing its heartbeat.
        now_ms: Timestamp to record, in epoch ms. Defaults to the current
            wall-clock; injectable for deterministic tests.

    Returns:
        The timestamp that was written, in epoch ms.

    Raises:
        ValueError: If ``runner_id`` is invalid.
        OSError: If the directory cannot be created or the write fails.
    """
    tick = now_ms if now_ms is not None else _now_ms()
    path = heartbeat_path(runner_id)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(str(tick), encoding="utf-8")
    os.replace(tmp, path)
    return tick


def last_tick(runner_id: str) -> int | None:
    """Return a runner's last recorded heartbeat timestamp.

    Args:
        runner_id: The runner to read.

    Returns:
        The last-tick timestamp in epoch ms, or ``None`` when no heartbeat
        exists or the file is unreadable / malformed (treated as "no signal",
        which :func:`is_runner_alive` reads as not-alive — fail-closed).
    """
    try:
        path = heartbeat_path(runner_id)
    except ValueError:
        return None
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return int(raw)
    except (OSError, ValueError):
        return None


def is_runner_alive(
    runner_id: str,
    *,
    now_ms: int | None = None,
    staleness_ms: int = DEFAULT_STALENESS_MS,
) -> bool:
    """Report whether a runner's heartbeat is fresh enough to call it alive.

    Args:
        runner_id: The runner to check.
        now_ms: Reference time in epoch ms. Defaults to current wall-clock.
        staleness_ms: Maximum age of the last tick before the runner is
            considered dead.

    Returns:
        ``True`` if a heartbeat exists and its last tick is within
        ``staleness_ms`` of ``now_ms``; ``False`` otherwise (missing, stale, or
        unreadable heartbeat).
    """
    tick = last_tick(runner_id)
    if tick is None:
        return False
    now = now_ms if now_ms is not None else _now_ms()
    return (now - tick) <= staleness_ms


def reap_stale(
    *,
    now_ms: int | None = None,
    staleness_ms: int = DEFAULT_STALENESS_MS,
) -> list[str]:
    """Purge heartbeat sentinels of runners that have gone stale.

    Mirrors the swarm reaper shape: scan every heartbeat, keep the live ones,
    delete the stale ones, and return the ids reaped so the caller can log /
    trigger reconciliation. Reaping only removes the *sentinel* — it never
    touches a process or any trading state.

    Args:
        now_ms: Reference time in epoch ms. Defaults to current wall-clock.
        staleness_ms: Age threshold; a heartbeat older than this is reaped.

    Returns:
        The runner ids whose stale heartbeats were removed (empty list when
        none were stale or the heartbeat dir does not exist).
    """
    directory = heartbeats_dir()
    if not directory.is_dir():
        return []
    now = now_ms if now_ms is not None else _now_ms()
    reaped: list[str] = []
    for entry in directory.glob(f"*{_HEARTBEAT_SUFFIX}"):
        runner_id = entry.name[: -len(_HEARTBEAT_SUFFIX)]
        if is_runner_alive(runner_id, now_ms=now, staleness_ms=staleness_ms):
            continue
        try:
            entry.unlink()
            reaped.append(runner_id)
            logger.warning("reaped stale live runner heartbeat: %s", runner_id)
        except FileNotFoundError:
            continue
        except OSError:
            logger.warning("failed to reap stale heartbeat %s", entry, exc_info=True)
    return reaped
