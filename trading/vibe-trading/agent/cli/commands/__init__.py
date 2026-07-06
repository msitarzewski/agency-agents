"""Slash command implementations.

Each command module exports a ``run(ctx, *args) -> int`` callable. Modules
that own multiple commands (``chat``, ``show``, ``session``) also expose
named ``cmd_<name>`` callables so the slash router can dispatch by
command keyword.

The :data:`SLASH_COMMANDS` registry lives in :mod:`.slash_router`.
"""

from .slash_router import SLASH_COMMANDS, Command, find_exact, match_commands

__all__ = [
    "Command",
    "SLASH_COMMANDS",
    "find_exact",
    "match_commands",
]
