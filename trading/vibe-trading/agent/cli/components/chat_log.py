"""Minimal chat-log renderer — stub for the demo.

Iterates a list of turn dicts and prints user / assistant lines with the
expected meta header. Defer the rich features (collapsible tool
timeline, markdown rendering, action footer) to post-demo work — they
belong in the Web bubble (Parcel C / D), not in the CLI replay.

Turn shape:
    {
        "role": "user" | "assistant",
        "content": str,
        "timestamp": str | None,   # ISO or formatted clock
        "meta": str | None,        # "Vibe · 4.1s · 1.2k tokens · $0.003"
    }
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

from rich.console import Console
from rich.text import Text


def _resolve_console(console: Optional[Console]) -> Console:
    """Return ``console`` if given, else the shared CLI console."""
    if console is not None:
        return console
    from cli.theme import get_console

    return get_console()


def _render_turn(turn: Mapping[str, object]) -> Text:
    """Compose the meta header line for one turn."""
    role = str(turn.get("role", "user"))
    timestamp = turn.get("timestamp")
    meta = turn.get("meta")
    header = Text()
    if role == "assistant":
        # "Vibe" is the brand wordmark for assistant turns — primary color
        header.append("Vibe", style="bold #d97706")
    else:
        header.append("you", style="bold")
    if timestamp:
        header.append(f"  {timestamp}", style="dim")
    if meta:
        header.append(f"  ·  {meta}", style="dim")
    return header


def render_history(
    turns: Iterable[Mapping[str, object]],
    *,
    console: Optional[Console] = None,
) -> None:
    """Print past turns to ``console``.

    Args:
        turns: Iterable of turn dicts (see module docstring for shape).
        console: Override; defaults to the shared CLI console.

    No return value — this is a side-effecting renderer.
    """
    cons = _resolve_console(console)
    for turn in turns:
        cons.print(_render_turn(turn))
        content = str(turn.get("content", ""))
        if content:
            # Body intentionally renders as plain text — markdown / katex
            # / syntax highlighting live in the Web bubble. The CLI keeps
            # the body monospaced for diff-friendly replay.
            cons.print(content)
        cons.print()  # blank line between turns


__all__ = ["render_history"]
