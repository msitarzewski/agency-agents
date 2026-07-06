"""Workspace memory: shared state across tool calls within a single run.

Lightweight runtime state — survives within one AgentLoop.run() invocation only.
Cross-session persistence is handled by src.memory.persistent.PersistentMemory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class WorkspaceMemory:
    """Shared workspace state between tools during a single agent run.

    Attributes:
        run_dir: Current run directory path.
        counters: Tool invocation counters.
    """

    run_dir: Optional[str] = None
    counters: Dict[str, int] = field(default_factory=dict)

    def increment(self, key: str) -> int:
        """Increment a counter and return the new value.

        Args:
            key: Counter key (typically tool name).

        Returns:
            Updated counter value.
        """
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def to_summary(self) -> str:
        """Generate a state summary for the LLM.

        Includes run_dir and tool counters.
        This summary survives context compression and helps the LLM
        remember what it was working on.

        Returns:
            State summary text.
        """
        lines: list[str] = []
        if self.run_dir:
            lines.append(f"- run_dir: {self.run_dir}")
        if self.counters:
            counter_parts = [f"{k}={v}" for k, v in self.counters.items()]
            lines.append(f"- counters: {', '.join(counter_parts)}")
        return "\n".join(lines) if lines else "(empty state)"
