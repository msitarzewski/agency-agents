"""LangGraph checkpoint support for resumable analysis runs.

Per-ticker SQLite databases so concurrent tickers don't contend.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from tradingagents.dataflows.utils import safe_ticker_component


def _db_path(data_dir: str | Path, ticker: str) -> Path:
    """Return the SQLite checkpoint DB path for a ticker."""
    # Reject ticker values that would escape the checkpoints directory.
    safe = safe_ticker_component(ticker).upper()
    p = Path(data_dir) / "checkpoints"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{safe}.db"


def thread_id(ticker: str, date: str) -> str:
    """Deterministic thread ID for a ticker+date pair."""
    return hashlib.sha256(f"{ticker.upper()}:{date}".encode()).hexdigest()[:16]


@contextmanager
def get_checkpointer(data_dir: str | Path, ticker: str) -> Generator[SqliteSaver, None, None]:
    """Context manager yielding a SqliteSaver backed by a per-ticker DB."""
    db = _db_path(data_dir, ticker)
    conn = sqlite3.connect(str(db), check_same_thread=False)
    try:
        saver = SqliteSaver(conn)
        saver.setup()
        yield saver
    finally:
        conn.close()


def has_checkpoint(data_dir: str | Path, ticker: str, date: str) -> bool:
    """Check whether a resumable checkpoint exists for ticker+date."""
    return checkpoint_step(data_dir, ticker, date) is not None


def checkpoint_step(data_dir: str | Path, ticker: str, date: str) -> int | None:
    """Return the step number of the latest checkpoint, or None if none exists."""
    db = _db_path(data_dir, ticker)
    if not db.exists():
        return None
    tid = thread_id(ticker, date)
    with get_checkpointer(data_dir, ticker) as saver:
        config = {"configurable": {"thread_id": tid}}
        cp = saver.get_tuple(config)
        if cp is None:
            return None
        return cp.metadata.get("step")


def clear_all_checkpoints(data_dir: str | Path) -> int:
    """Remove all checkpoint DBs. Returns number of files deleted."""
    cp_dir = Path(data_dir) / "checkpoints"
    if not cp_dir.exists():
        return 0
    dbs = list(cp_dir.glob("*.db"))
    for db in dbs:
        db.unlink()
    return len(dbs)


def clear_checkpoint(data_dir: str | Path, ticker: str, date: str) -> None:
    """Remove checkpoint for a specific ticker+date by deleting the thread's rows."""
    db = _db_path(data_dir, ticker)
    if not db.exists():
        return
    tid = thread_id(ticker, date)
    conn = sqlite3.connect(str(db))
    try:
        for table in ("writes", "checkpoints"):
            conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (tid,))
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
