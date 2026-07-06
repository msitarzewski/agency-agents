"""Bottom hint bar — left + right aligned.

Renders a single-line hint where the right-aligned segment hugs the
terminal edge regardless of left-segment width. Mirrors dexter's
``hint-bar.ts``.

Used to surface keyboard guidance ("Tab to complete · /help for
commands") and ephemeral state ("input cleared", "cancelled").
"""

from __future__ import annotations

import shutil

from rich.text import Text


def _terminal_width(default: int = 80) -> int:
    """Best-effort terminal width detection (falls back gracefully)."""
    try:
        size = shutil.get_terminal_size((default, 20))
        return max(20, size.columns)
    except (OSError, ValueError):
        return default


def render_hint_bar(left: str, right: str = "", *, width: int | None = None) -> Text:
    """Return a Rich :class:`Text` row with ``left`` and right-aligned ``right``.

    The bar always fits the terminal width:
        * If ``left + right`` fits, pad with spaces between them
        * Otherwise truncate the left segment with an ellipsis so the
          right hint remains visible (right-side hint usually carries
          the *current* Ctrl+C semantics — losing it is worse than
          losing context)

    Args:
        left: Left segment (e.g. ``"↑/↓ navigate · Tab/⏎ select"``).
        right: Right segment (e.g. ``"Esc to cancel"``); may be empty.
        width: Override terminal width. Defaults to autodetect.
    """
    cols = width if width is not None else _terminal_width()
    if right == "":
        # Only a left hint — clip and pad to width, dim style throughout.
        text = Text(left[:cols], style="dim")
        return text

    # Reserve at least one space between left and right segments.
    available_for_left = cols - len(right) - 1
    if available_for_left < 1:
        # Right segment alone is wider than the terminal — show right only.
        return Text(right[: cols].rjust(cols), style="dim")

    if len(left) > available_for_left:
        left = left[: max(1, available_for_left - 1)].rstrip() + "…"

    padding = cols - len(left) - len(right)
    if padding < 1:
        padding = 1
    bar = Text()
    bar.append(left, style="dim")
    bar.append(" " * padding)
    bar.append(right, style="dim")
    return bar


__all__ = ["render_hint_bar"]
