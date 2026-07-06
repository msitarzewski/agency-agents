"""Random "thinking" verb for the streaming spinner.

The status bar shows a verb while the agent is generating to communicate that
work is happening even before the first token arrives. Borrowed from the
dexter CLI: the verb is rerolled per agent turn so the user perceives variety
across runs rather than a single hard-coded label.
"""

from __future__ import annotations

import random
from typing import Final, Tuple

THINKING_VERBS: Final[Tuple[str, ...]] = (
    "Pondering",
    "Analyzing",
    "Reasoning",
    "Investigating",
    "Synthesizing",
    "Cross-checking",
)


def pick_thinking_verb(*, seed: int | None = None) -> str:
    """Pick a random verb suffixed with an ellipsis.

    Args:
        seed: Optional deterministic seed (used by tests). When ``None`` the
            module-level :func:`random.choice` is used.

    Returns:
        ``"Pondering…"``, ``"Analyzing…"``, etc.
    """

    if seed is not None:
        rng = random.Random(seed)
        return f"{rng.choice(THINKING_VERBS)}…"
    return f"{random.choice(THINKING_VERBS)}…"


__all__ = ["pick_thinking_verb", "THINKING_VERBS"]
