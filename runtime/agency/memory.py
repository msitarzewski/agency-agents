"""Tiny on-disk session memory."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class TurnRecord:
    role: str
    text: str
    ts: float = field(default_factory=time.time)


@dataclass
class Session:
    session_id: str
    skill_slug: str
    turns: list[TurnRecord] = field(default_factory=list)

    def append(self, role: str, text: str) -> None:
        self.turns.append(TurnRecord(role=role, text=text))


class MemoryStore:
    """Newline-delimited JSON, one file per session."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "default"
        return self.root / f"{safe}.jsonl"

    def load(self, session_id: str) -> Session | None:
        path = self._path(session_id)
        if not path.exists():
            return None
        skill_slug = ""
        turns: list[TurnRecord] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if data.get("kind") == "header":
                skill_slug = data.get("skill_slug", "")
            elif data.get("kind") == "turn":
                turns.append(TurnRecord(role=data["role"], text=data["text"], ts=data.get("ts", 0)))
        return Session(session_id=session_id, skill_slug=skill_slug, turns=turns)

    def save(self, session: Session) -> None:
        path = self._path(session.session_id)
        with path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"kind": "header", "skill_slug": session.skill_slug}) + "\n")
            for turn in session.turns:
                f.write(json.dumps({"kind": "turn", **asdict(turn)}) + "\n")
