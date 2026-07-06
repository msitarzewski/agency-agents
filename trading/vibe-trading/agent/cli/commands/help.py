"""``/help`` — Show the slash command list and keyboard shortcuts.

Renders ``SLASH_COMMANDS`` as a two-column Rich table (name in primary
color, description muted) plus a short keyboard-shortcuts panel.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .slash_router import SLASH_COMMANDS


def _resolve_console() -> Console:
    """Return the shared CLI console."""
    from cli.theme import get_console

    return get_console()


_SHORTCUTS: tuple[tuple[str, str], ...] = (
    ("⏎",            "Send"),
    ("Shift+⏎",      "Newline"),
    ("Tab",          "Accept completion"),
    ("↑/↓",          "Browse history (or navigate completions)"),
    ("Ctrl+C",       "Clear input · then exit hint"),
    ("Ctrl+D",       "Exit (auto-saves session)"),
    ("/",            "Open slash command typeahead"),
)


def run(ctx: Any = None, *args: str) -> int:  # noqa: ARG001 — ctx unused here
    """Print the help screen. Always returns 0."""
    console = _resolve_console()

    commands_table = Table.grid(padding=(0, 2))
    commands_table.add_column(style="bold #d97706", no_wrap=True)
    commands_table.add_column(style="dim")
    for cmd in SLASH_COMMANDS:
        commands_table.add_row(f"/{cmd.name}", cmd.description)

    console.print()
    console.print(Text("Commands", style="bold"))
    console.print(commands_table)
    console.print()

    shortcuts_table = Table.grid(padding=(0, 2))
    shortcuts_table.add_column(style="bold", no_wrap=True)
    shortcuts_table.add_column(style="dim")
    for key, desc in _SHORTCUTS:
        shortcuts_table.add_row(key, desc)

    console.print(Text("Keyboard", style="bold"))
    console.print(shortcuts_table)
    console.print()

    return 0


__all__ = ["run"]
