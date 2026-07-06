"""Shadow Account persistence (~/.vibe-trading/shadow_accounts/).

Layout:
    ~/.vibe-trading/shadow_accounts/<shadow_id>.json   ShadowProfile
    ~/.vibe-trading/shadow_runs/<shadow_id>/           backtest run dir
    ~/.vibe-trading/shadow_reports/<shadow_id>.pdf     rendered report
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.shadow_account.models import ShadowProfile, ShadowRule


def _root() -> Path:
    """Return the Shadow Account root directory (auto-created)."""
    root = Path.home() / ".vibe-trading"
    root.mkdir(parents=True, exist_ok=True)
    return root


def profiles_dir() -> Path:
    d = _root() / "shadow_accounts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def runs_dir(shadow_id: str) -> Path:
    d = _root() / "shadow_runs" / shadow_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def reports_dir() -> Path:
    d = _root() / "shadow_reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def new_shadow_id() -> str:
    """Mint a fresh shadow_id."""
    return f"shadow_{uuid.uuid4().hex[:8]}"


def hash_journal(journal_path: Path | str) -> str:
    """SHA1 over the raw journal bytes for idempotent extraction."""
    p = Path(journal_path)
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    """UTC ISO8601 timestamp (seconds precision)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_profile(profile: ShadowProfile) -> Path:
    """Persist a ShadowProfile to disk as JSON."""
    path = profiles_dir() / f"{profile.shadow_id}.json"
    path.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def load_profile(shadow_id: str) -> ShadowProfile:
    """Load a ShadowProfile back from disk.

    Raises:
        FileNotFoundError: No profile with that id.
    """
    path = profiles_dir() / f"{shadow_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Shadow profile not found: {shadow_id}")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rules = tuple(
        ShadowRule(
            rule_id=r["rule_id"],
            human_text=r["human_text"],
            entry_condition=r["entry_condition"],
            exit_condition=r["exit_condition"],
            holding_days_range=tuple(r["holding_days_range"]),
            support_count=r["support_count"],
            coverage_rate=r["coverage_rate"],
            sample_trades=tuple(r["sample_trades"]),
            weight=r.get("weight", 1.0),
        )
        for r in data["rules"]
    )
    return ShadowProfile(
        shadow_id=data["shadow_id"],
        created_at=data["created_at"],
        journal_hash=data["journal_hash"],
        source_market=data["source_market"],
        profitable_roundtrips=data["profitable_roundtrips"],
        total_roundtrips=data["total_roundtrips"],
        date_range=tuple(data["date_range"]),
        profile_text=data["profile_text"],
        rules=rules,
        preferred_markets=tuple(data["preferred_markets"]),
        typical_holding_days=tuple(data["typical_holding_days"]),
    )


def find_by_journal_hash(journal_hash: str) -> ShadowProfile | None:
    """Return the most recent profile sharing this journal_hash, else None."""
    latest: ShadowProfile | None = None
    for path in profiles_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("journal_hash") != journal_hash:
            continue
        candidate = load_profile(data["shadow_id"])
        if latest is None or candidate.created_at > latest.created_at:
            latest = candidate
    return latest
