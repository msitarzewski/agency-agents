"""``/memory`` — list / show persistent memory snippets.

Delegates to the legacy ``cmd_memory_list`` / ``cmd_memory_show`` /
``cmd_memory_search`` callables. ``/memory`` with no args lists; with
a single arg shows one; with ``search <q>`` runs FTS; with
``forget <name>`` deletes one.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.text import Text

from cli.theme import get_console


def _resolve_console() -> Console:
    """Return the shared CLI console."""
    return get_console()


def cmd_memory(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Dispatch sub-actions:

    * ``/memory``              → list
    * ``/memory <name>``       → show
    * ``/memory search <q>``   → full-text search
    * ``/memory forget <name>``→ delete a snippet
    """
    console = _resolve_console()

    if not args:
        try:
            from cli._legacy import cmd_memory_list

            return cmd_memory_list()
        except Exception as exc:  # noqa: BLE001
            console.print(Text(f"/memory list failed: {exc}", style="bold red"))
            return 1

    sub = args[0]
    rest = args[1:]
    try:
        if sub == "search" and rest:
            from cli._legacy import cmd_memory_search

            return cmd_memory_search(" ".join(rest))
        if sub == "forget" and rest:
            from cli._legacy import cmd_memory_forget

            return cmd_memory_forget(rest[0], yes=False)
        from cli._legacy import cmd_memory_show

        return cmd_memory_show(sub)
    except Exception as exc:  # noqa: BLE001
        console.print(Text(f"/memory failed: {exc}", style="bold red"))
        return 1


def run(ctx: Any = None, *args: str) -> int:
    """Single-entrypoint wrapper for the slash router."""
    return cmd_memory(ctx, *args)


__all__ = ["run", "cmd_memory"]
