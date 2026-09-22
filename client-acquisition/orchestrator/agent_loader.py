"""Load existing Agency Agents personas from this repository."""

from pathlib import Path
from typing import Dict
import json


class AgentCatalog:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        config_path = repo_root / "client-acquisition" / "config" / "agents.json"
        self.mapping: Dict[str, str] = json.loads(config_path.read_text(encoding="utf-8"))["agents"]

    def path_for(self, capability: str) -> Path:
        try:
            relative = self.mapping[capability]
        except KeyError as exc:
            raise ValueError(f"Unknown capability: {capability}") from exc
        path = self.repo_root / relative
        if not path.exists():
            raise FileNotFoundError(f"Agent file not found: {relative}")
        return path

    def load(self, capability: str) -> str:
        return self.path_for(capability).read_text(encoding="utf-8")
