"""Slash command registry + fuzzy matcher.

Source of truth for the 15 user-facing slash commands defined in
``docs/2026-05-19_session02_uiux_design_proposal.md`` §3.4.

Each :class:`Command` is a frozen dataclass — registry entries are
immutable so callers can cache filtered slices without worrying about
mutation. ``match_commands`` powers the typeahead in
:mod:`agent.cli.completer`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """A single slash command entry.

    Attributes:
        name: The command keyword, without leading ``/``.
        description: One-line muted description shown in the completion menu.
        handler_module: Dotted path to the module exposing ``run(ctx, *args)``.
    """

    name: str
    description: str
    handler_module: str


# Order here = order shown in bare ``/`` typeahead. Group by frequency so the
# most-used commands surface first (help/model/memory/history are top).
SLASH_COMMANDS: tuple[Command, ...] = (
    Command("help",    "Show keyboard shortcuts and command list",   "cli.commands.help"),
    Command("model",   "Switch LLM provider and model",              "cli.commands.chat"),
    Command("memory",  "Show / manage persistent memory",            "cli.commands.memory"),
    Command("history", "Browse and resume prior sessions",           "cli.commands.session"),
    Command("goal",    "Start / inspect a finance research goal",    "cli.commands.goal"),
    Command("search",  "Full-text search across all sessions",       "cli.commands.session"),
    Command("swarm",   "Multi-agent presets (committee / quant / risk)", "cli.commands.chat"),
    Command("skill",   "List / load / unload skills",                "cli.commands.show"),
    Command("show",    "Show prior run by id",                       "cli.commands.show"),
    Command("clear",   "Clear current conversation",                 "cli.commands.chat"),
    Command("pine",    "Export current strategy as Pine Script",     "cli.commands.show"),
    Command("journal", "Analyze trade journal CSV",                  "cli.commands.chat"),
    Command("shadow",  "Train / view shadow account",                "cli.commands.chat"),
    Command("export",  "Export current session (md / json)",         "cli.commands.session"),
    Command("debug",   "Toggle debug panel (token usage / latency)", "cli.commands.chat"),
    Command("quit",    "Exit (also: q, exit, :q)",                   "cli.commands.chat"),
)


# Aliases — same handler, different surface keyword. Keep separate from the
# main registry so typeahead does not duplicate rows.
_ALIASES: dict[str, str] = {
    "q":    "quit",
    "exit": "quit",
    ":q":   "quit",
    "?":    "help",
}


def _parse_token(input_text: str) -> str:
    """Strip the leading ``/`` and isolate the command token.

    >>> _parse_token("/me arg")
    'me'
    >>> _parse_token("/")
    ''
    >>> _parse_token("not a slash")
    ''
    """
    text = input_text.lstrip()
    if not text.startswith("/"):
        return ""
    # ``/foo bar`` → ``foo``. Use ``split(None, 1)`` to handle any whitespace.
    parts = text[1:].split(None, 1)
    return parts[0] if parts else ""


def _fuzzy_score(needle: str, name: str) -> int:
    """Return a heuristic score for ``needle`` matching ``name``.

    Higher = better. ``0`` means no match.

    Scoring order (boundary-friendly, like dexter's slash matcher):
        prefix match → 100 + length bonus
        substring match → 50 + length bonus
        subsequence match (chars in order) → 10 + chars matched
        otherwise → 0
    """
    if not needle:
        return 1  # bare ``/`` shows everything in registry order
    needle_l = needle.lower()
    name_l = name.lower()
    if name_l.startswith(needle_l):
        return 100 + len(needle_l)
    if needle_l in name_l:
        return 50 + len(needle_l)
    # subsequence match: every char of needle appears in order inside name
    j = 0
    for ch in name_l:
        if j < len(needle_l) and ch == needle_l[j]:
            j += 1
    if j == len(needle_l):
        return 10 + j
    return 0


def match_commands(input_text: str) -> list[Command]:
    """Return commands that fuzzy-match ``input_text``.

    Only matches when the trimmed input starts with ``/``. The leading slash
    and any trailing arguments are stripped before scoring; only the command
    token participates in the match.

    Result is ordered best-match first, ties broken by registry order.

    Args:
        input_text: Raw input line, possibly empty.

    Returns:
        A new list — callers may freely mutate without side effects.
    """
    token = _parse_token(input_text)
    if not input_text.lstrip().startswith("/"):
        return []

    # Resolve aliases up front so ``/q`` shows the ``quit`` row.
    if token in _ALIASES:
        token = _ALIASES[token]

    scored: list[tuple[int, int, Command]] = []
    for idx, cmd in enumerate(SLASH_COMMANDS):
        score = _fuzzy_score(token, cmd.name)
        if score > 0:
            # Negative idx so ties prefer earlier registry position when
            # sorted descending by score.
            scored.append((score, -idx, cmd))
    scored.sort(reverse=True)
    return [cmd for _score, _idx, cmd in scored]


def find_exact(name: str) -> Command | None:
    """Resolve an exact command name or alias.

    Returns ``None`` if no match — callers handle the "unknown command"
    response themselves so error UX stays consistent.
    """
    key = name.lstrip("/").strip()
    key = _ALIASES.get(key, key)
    for cmd in SLASH_COMMANDS:
        if cmd.name == key:
            return cmd
    return None
