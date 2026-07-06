"""Interactive CLI front door for Vibe-Trading.

Responsibilities:

1. Detect whether ``~/.vibe-trading/.env`` exists; if missing, run the
   onboarding wizard (:mod:`cli.onboard`) before doing anything else.
2. Render the startup banner (:mod:`cli.intro`) on interactive entry.
3. For interactive entry (no subcommand, or ``chat``) drive the REPL
   built on :mod:`cli.input`, :mod:`cli.completer`,
   :mod:`cli.commands.slash_router`, :mod:`cli.components.working_indicator`,
   :mod:`cli.components.tool_event`, and :mod:`cli.components.hint_bar`.
4. For every other subcommand delegate to ``cli._legacy.main`` so the
   long tail of ``serve``, ``run``, ``mcp``, ``sessions``, ``swarm`` etc.
   keeps working without regression.

The console script entry in ``pyproject.toml`` (``vibe-trading = "cli:main"``)
hits :func:`main`.
"""

from __future__ import annotations

import importlib
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from cli.intro import print_banner
from cli.onboard import run_onboarding
from cli.theme import Theme, get_console


def _register_live_slash_commands() -> None:
    """Surface connector live-trading slash commands in the shared registry.

    Discoverability fix (SPEC.md Consent §4 + §9 audit): ``/connector``,
    ``/halt`` and ``/resume`` are privileged kill-switch / runner surface actions intercepted
    in the REPL input path (never dispatched to the model), so they were absent
    from the slash registry — meaning ``/help``, the typeahead completer, and the
    fuzzy matcher never listed them. We append them here, at this module's import
    time, which runs on every interactive startup *before* the lazily-imported
    ``cli.commands.help`` / ``cli.completer`` first read the registry. Both of
    those read ``slash_router.SLASH_COMMANDS`` (help) / call ``match_commands``
    (completer) which resolve the connector module attribute, so the single
    reassignment here surfaces the commands in all three places.

    The registry is a tuple of frozen dataclasses, so we build a NEW tuple rather
    than mutate in place. Registration is idempotent — re-import (e.g. in tests)
    never duplicates rows.
    """
    from cli.commands import slash_router

    existing = {cmd.name for cmd in slash_router.SLASH_COMMANDS}
    additions = (
        slash_router.Command(
            "connector", "Trading connector profiles (status / start / halt)", "cli.main"
        ),
        slash_router.Command(
            "halt", "Kill switch — halt ALL live trading now", "cli.main"
        ),
        slash_router.Command(
            "resume", "Clear the kill switch (re-enable live trading)", "cli.main"
        ),
    )
    new = tuple(cmd for cmd in additions if cmd.name not in existing)
    if not new:
        return
    # Insert the connector group just before ``quit`` (the conventional last row) so
    # the kill switch sits with the other safety-relevant commands.
    commands = list(slash_router.SLASH_COMMANDS)
    quit_idx = next(
        (i for i, c in enumerate(commands) if c.name == "quit"), len(commands)
    )
    commands[quit_idx:quit_idx] = list(new)
    slash_router.SLASH_COMMANDS = tuple(commands)
    # ``/stop`` is the kill-switch alias of ``/halt`` (SPEC Consent §4) so the
    # fuzzy matcher / find_exact resolve it.
    if "stop" not in slash_router._ALIASES:
        slash_router._ALIASES = {**slash_router._ALIASES, "stop": "halt"}


_register_live_slash_commands()

_ENV_PATH = Path.home() / ".vibe-trading" / ".env"
# Best-effort fallbacks used only when the probe genuinely fails (missing
# dependency, broken install). The numbers track the actual bundled counts
# so a probe failure still shows a plausible banner rather than "0 loaded".
_FALLBACK_SKILLS = 77
_FALLBACK_TOOLS = 31
_HISTORY_RETAINED_TURNS = 6  # how many prior turns to feed the agent loop

# Cached banner-stats and session-store so ``/clear`` and repeat slash handlers
# don't redo the heavy build_registry() / SessionStore construction.
_BANNER_STATS_CACHE: Dict[str, Any] = {}
_SESSION_STORE_CACHE: Any = None


# ---------------------------------------------------------------------------
# Stat probes (best-effort, never blocking)
# ---------------------------------------------------------------------------


def _probe_model_name() -> str:
    """Return the configured LLM model id, or a placeholder."""
    name = os.environ.get("LANGCHAIN_MODEL_NAME") or os.environ.get("OPENAI_MODEL")
    if name:
        return name
    try:
        text = _ENV_PATH.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("LANGCHAIN_MODEL_NAME="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return "unset (use /model to pick one)"


def _probe_tool_count() -> int:
    """Count registered tools without blocking startup on import errors."""
    try:
        from src.tools import build_registry

        return len(build_registry())
    except Exception:  # noqa: BLE001 — never block startup on stats
        return _FALLBACK_TOOLS


def _probe_skill_count() -> int:
    """Count bundled + user skills without blocking startup on import errors.

    Reads ``SkillsLoader.skills`` directly — that is the authoritative list
    populated by :meth:`SkillsLoader._load` from bundled ``agent/skills/``
    plus ``~/.vibe-trading/skills/user/``.
    """
    try:
        from src.agent.skills import SkillsLoader

        loader = SkillsLoader()
        return len(loader.skills)
    except Exception:  # noqa: BLE001
        return _FALLBACK_SKILLS


def _probe_session_count() -> int:
    """Count recorded sessions from the SQLite store."""
    db_path = Path.home() / ".vibe-trading" / "sessions.db"
    if not db_path.exists():
        return 0
    try:
        import sqlite3

        with sqlite3.connect(str(db_path)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()
            return int(row[0]) if row else 0
    except Exception:  # noqa: BLE001
        return 0


def _collect_banner_stats(*, refresh: bool = False) -> Dict[str, Any]:
    """Return the four banner stat values, computing them at most once.

    The interactive launch path runs every probe synchronously (the
    user is already waiting for the prompt). Subsequent callers
    (``/clear`` re-render, ``/debug`` summary) reuse the cached values
    so they don't re-import the tool registry on every keystroke.

    Args:
        refresh: When True, recompute and overwrite the cache.

    Returns:
        ``{"model": str, "skills": int, "tools": int, "sessions": int}``.
    """
    if _BANNER_STATS_CACHE and not refresh:
        return dict(_BANNER_STATS_CACHE)
    stats: Dict[str, Any] = {
        "model": _probe_model_name(),
        "skills": _probe_skill_count(),
        "tools": _probe_tool_count(),
        "sessions": _probe_session_count(),
    }
    _BANNER_STATS_CACHE.clear()
    _BANNER_STATS_CACHE.update(stats)
    return dict(stats)


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------


def _is_interactive_invocation(argv: Sequence[str]) -> bool:
    """Decide whether this invocation should drive the interactive loop.

    Interactive entry requires:

    * Both stdin and stdout are TTYs (no piped / redirected I/O).
    * Either no arguments at all, or exactly the ``chat`` subcommand.

    Anything else — a flag (``-p``, ``--json``, ``--help``), a recognised
    subcommand (``serve``, ``run``, ``alpha``, ``hypothesis`` ...), or an
    unknown positional — is delegated to ``_legacy.main`` so argparse
    can either dispatch it or produce its standard "unrecognized
    arguments" error. Routing typos here would silently drop the user
    into chat, which is worse than the argparse error.

    Args:
        argv: The argument list passed to :func:`main`, *excluding*
            ``sys.argv[0]``.

    Returns:
        ``True`` if the caller should drive the interactive loop.
    """
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return False
    if not argv:
        return True
    if argv[0].startswith("-"):
        return False
    return _is_supported_chat_invocation(argv)


def _is_supported_chat_invocation(argv: Sequence[str]) -> bool:
    """Return True for chat invocations handled by the interactive front door."""
    if not argv or argv[0] != "chat":
        return False
    if len(argv) == 1:
        return True
    if len(argv) == 2 and argv[1].startswith("--max-iter="):
        try:
            int(argv[1].split("=", 1)[1])
            return True
        except ValueError:
            return False
    if len(argv) == 3 and argv[1] == "--max-iter":
        try:
            int(argv[2])
            return True
        except ValueError:
            return False
    return False


def _maybe_run_onboarding() -> bool:
    """Run the first-launch wizard when ``.env`` is missing.

    Returns:
        ``True`` if startup should proceed, ``False`` if the user cancelled
        the wizard cleanly.
    """
    if _ENV_PATH.exists():
        return True
    console = get_console()
    written = run_onboarding(console=console)
    if written is None:
        return False
    # Reload env so downstream code picks up the fresh credentials.
    try:
        from dotenv import load_dotenv

        load_dotenv(written, override=True)
    except Exception:  # noqa: BLE001 — legacy will load again later
        pass
    return True


def _show_banner() -> None:
    """Print the welcome banner using best-effort stat probes."""
    stats = _collect_banner_stats()
    console = get_console()
    print_banner(console, **stats)
    # Discoverability one-liner (SPEC.md §9 audit): point users at the
    # connector channel + its CLI surface. Live profiles are opt-in and read-only by
    # default, so this is a pointer, not an enablement.
    console.print(
        "  [dim]Live trading (opt-in, read-only by default): "
        "[/dim][bold]/connector[/bold][dim] in chat · "
        "[/dim][bold]vibe-trading connector --help[/bold][dim] · "
        "[/dim][bold]/halt[/bold][dim] = kill switch.[/dim]"
    )
    console.print()


# ---------------------------------------------------------------------------
# Interactive context
# ---------------------------------------------------------------------------


@dataclass
class InteractiveContext:
    """State bag handed to slash-command handlers and the run loop.

    Attributes:
        session_id: Active session id (populated lazily on first turn).
        history: Compact transcript (role/content pairs) fed back to the
            agent for follow-up context.
        max_iter: ReAct iteration ceiling.
        debug: Whether the ``/debug`` panel is currently shown.
        last_recap_history_len: Number of history messages covered by the
            most recently printed deterministic recap.
        pending_prompt: Optional prompt queued by a slash handler
            (``/journal``, ``/shadow``) that the loop should execute as
            the next user turn. Consumed by :func:`_interactive_loop`
            and cleared.
        pending_proposal: The most recent live-trading ``mandate.proposal``
            payload emitted by the agent during this session, awaiting the
            user's pick or adjust reply. A numeric pick is intercepted in the
            REPL input path and committed directly via the commit endpoint —
            the model never sees the pick (SPEC.md Consent §2). ``None`` when
            no proposal is outstanding.
    """

    session_id: Optional[str] = None
    history: List[Dict[str, str]] = field(default_factory=list)
    max_iter: int = 50
    debug: bool = False
    last_recap_history_len: int = 0
    pending_prompt: Optional[str] = None
    pending_proposal: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Session-store integration
# ---------------------------------------------------------------------------


def _session_store() -> Any:
    """Return a process-wide :class:`SessionStore` rooted at ``agent/sessions``.

    Cached on the module so repeat ``_append_message`` / ``_new_session``
    calls don't re-import ``src.session.store`` every turn.
    """
    global _SESSION_STORE_CACHE
    if _SESSION_STORE_CACHE is None:
        from cli._legacy import SESSIONS_DIR  # filesystem path constant
        from src.session.store import SessionStore

        _SESSION_STORE_CACHE = SessionStore(base_dir=SESSIONS_DIR)
    return _SESSION_STORE_CACHE


def _build_session_history(store: Any, session_id: str) -> list[dict]:
    """Load and filter recent message history for a session.

    Returns up to ``_HISTORY_RETAINED_TURNS`` user/assistant messages
    with non-empty content.
    """
    try:
        messages = store.get_messages(session_id, limit=_HISTORY_RETAINED_TURNS * 2)
    except Exception:  # noqa: BLE001 — persistence error → empty history
        return []
    history = [
        {"role": m.role, "content": m.content}
        for m in messages
        if m.role in {"user", "assistant"} and m.content.strip()
    ]
    return history[-_HISTORY_RETAINED_TURNS:]


def _new_session(prompt_preview: str) -> Optional[str]:
    """Create a fresh session record. Returns the id, or None on failure.

    Dual-writes to the filesystem :class:`SessionStore` (canonical JSONL
    log under ``agent/sessions/``) *and* to the SQLite FTS5 search index
    (``~/.vibe-trading/sessions.db``) so cross-session search via
    :class:`SessionSearchIndex` finds turns recorded from the interactive
    loop. Matches the pattern in :class:`SessionService`.
    """
    title = prompt_preview[:60] or "untitled"
    try:
        from src.session.models import Session, SessionStatus

        store = _session_store()
        session = Session(
            title=title,
            status=SessionStatus.ACTIVE,
        )
        store.create_session(session)
    except Exception:  # noqa: BLE001 — never block the turn on persistence
        return None

    # Index in SQLite for FTS5 cross-session search. Best-effort — never
    # block the turn if the search index is unavailable.
    try:
        from src.session.search import get_shared_index

        get_shared_index().index_session(session.session_id, title)
    except Exception:  # noqa: BLE001
        pass
    return session.session_id


def _append_message(session_id: str, role: str, content: str) -> None:
    """Append a single message to the session JSONL log + FTS5 index.

    Dual-writes:

    * Canonical: append the :class:`Message` to ``messages.jsonl`` via
      the filesystem :class:`SessionStore`. ``_maybe_resume_last_session``
      and the legacy ``sessions`` CLI both read from here.
    * Search index: insert the same row into the SQLite FTS5 index so
      ``SessionSearchTool`` finds it. Required for the CLAUDE.md promise
      that cross-session full-text search works.

    Args:
        session_id: Active session id. Skipped if empty.
        role: ``"user"`` / ``"assistant"`` / ``"tool"``.
        content: Message text. Empty/whitespace strings are skipped.
    """
    if not session_id or not content:
        return
    try:
        from src.session.models import Message

        store = _session_store()
        store.append_message(
            Message(session_id=session_id, role=role, content=content)
        )
    except Exception:  # noqa: BLE001 — persistence is best-effort
        pass

    # FTS5 cross-session search. Independent try/except so a JSONL write
    # that succeeded is not retried just because the search index failed.
    try:
        from src.session.search import get_shared_index

        get_shared_index().index_message(session_id, role, content)
    except Exception:  # noqa: BLE001
        pass


def _maybe_resume_last_session(console: Any) -> Optional[Dict[str, Any]]:
    """Prompt to resume the most recent session, if any exist.

    Returns:
        A dict ``{"session_id": str, "history": list[dict], "title": str}``
        when the user opts to resume, otherwise ``None`` (new session).
    """
    try:
        store = _session_store()
        sessions = store.list_sessions(limit=1)
    except Exception:  # noqa: BLE001
        return None
    if not sessions:
        return None

    last = sessions[0]
    title = last.title or "(untitled)"
    console.print()
    console.print(
        f"[dim]Resume last session ({title})? (r)esume / (n)ew (default: new)[/dim]"
    )
    try:
        choice = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None
    if choice not in {"r", "resume", "y", "yes"}:
        return None

    return {
        "session_id": last.session_id,
        "history": _build_session_history(store, last.session_id),
        "title": title,
    }


# ---------------------------------------------------------------------------
# Async preflight
# ---------------------------------------------------------------------------


def _start_preflight_async() -> threading.Thread:
    """Run ``src.preflight.run_preflight`` in a daemon thread.

    The welcome banner has already painted by the time this runs, so the
    user sees something useful immediately while credential / network
    probes happen in the background. We swallow exceptions because the
    legacy path runs preflight again before any agent invocation — this
    pre-warm is opportunistic. Audit item 11.
    """
    def _worker() -> None:
        try:
            from src.preflight import run_preflight

            run_preflight(get_console())
        except Exception:  # noqa: BLE001
            pass

    thread = threading.Thread(target=_worker, daemon=True, name="vibe-preflight")
    thread.start()
    return thread


# ---------------------------------------------------------------------------
# Slash dispatch
# ---------------------------------------------------------------------------


# Module paths that fan out to multiple commands via ``run(ctx, name, *args)``.
_MULTI_COMMAND_MODULES = frozenset({
    "cli.commands.chat",
    "cli.commands.show",
    "cli.commands.session",
})


def _suggest_commands(unknown: str) -> List[str]:
    """Return up to three "did you mean" suggestions for ``unknown``.

    Uses :func:`difflib.get_close_matches` (edit-distance based) as the
    primary signal so single-character typos like ``/historu`` → ``/history``
    or ``/jurnal`` → ``/journal`` are caught — the subsequence scorer in
    ``slash_router.match_commands`` ranks transpositions poorly and is
    used here only as a fallback to fill any remaining slot.

    Args:
        unknown: The bare command token (no leading ``/``).

    Returns:
        Deduplicated command names, edit-distance suggestions first,
        capped at three entries.
    """
    import difflib

    from cli.commands.slash_router import SLASH_COMMANDS, match_commands

    all_names = [cmd.name for cmd in SLASH_COMMANDS]
    primary = difflib.get_close_matches(unknown, all_names, n=3, cutoff=0.6)

    # Fill remaining slots from the subsequence scorer so very short
    # typos (``/hi`` → ``/history``) still surface if difflib found
    # nothing close enough.
    suggestions: list[str] = list(primary)
    if len(suggestions) < 3:
        for cmd in match_commands("/" + unknown):
            if cmd.name not in suggestions:
                suggestions.append(cmd.name)
                if len(suggestions) >= 3:
                    break
    return suggestions[:3]


def _dispatch_slash(line: str, ctx: InteractiveContext) -> int:
    """Route a slash command line to its handler.

    Returns:
        Exit code from the handler. ``2`` is the conventional "user
        requested quit" sentinel (see ``cmd_quit``). Any other value is
        treated as continue-the-loop.
    """
    from cli.commands.slash_router import find_exact

    console = get_console()
    stripped = line.lstrip().lstrip("/")
    parts = stripped.split()
    if not parts:
        console.print("[dim]Type /help to see available commands.[/dim]")
        return 0
    name, *args = parts
    cmd = find_exact(name)
    if cmd is None:
        # Use edit-distance suggestions (difflib) so single-char typos
        # surface the right command — the subsequence scorer in
        # ``slash_router.match_commands`` does not handle transpositions.
        suggestions = _suggest_commands(name)
        console.print(f"[bold red]Unknown command:[/] /{name}")
        if suggestions:
            preview = ", ".join(f"/{s}" for s in suggestions)
            console.print(f"[dim]Did you mean: {preview}?[/dim]")
        console.print("[dim]Type /help to see available commands.[/dim]")
        return 0

    try:
        module = importlib.import_module(cmd.handler_module)
    except ImportError as exc:
        console.print(
            f"[bold red]Failed to load /{cmd.name} handler ({exc})[/bold red]"
        )
        return 0

    try:
        if cmd.handler_module in _MULTI_COMMAND_MODULES:
            return int(module.run(ctx, cmd.name, *args))
        return int(module.run(ctx, *args))
    except SystemExit as exc:
        # Treat the canonical "user quit" codes (0 / 2 / None) as
        # a loop break; anything else is a genuine handler failure
        # and should keep the REPL alive so the user can recover.
        code = exc.code
        if code in (None, 0, 2):
            return 2
        console.print(f"[bold red]/{cmd.name} exited with code {code}[/]")
        return 0
    except Exception as exc:  # noqa: BLE001 — never let a handler kill the loop
        console.print(f"[bold red]/{cmd.name} raised {type(exc).__name__}: {exc}[/]")
        return 0


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------


def _summarise_tool_result(tool: str, status: str, preview: str) -> str:
    """Short suffix to render after a finished tool event."""
    if status != "ok":
        return preview[:48].replace("\n", " ")
    # Delegate to the legacy preview helper which already knows about
    # backtest sharpe / shadow id / etc.
    try:
        from cli._legacy import _format_tool_result_preview, _strip_rich_tags

        return _strip_rich_tags(_format_tool_result_preview(tool, status, preview))[:48]
    except Exception:  # noqa: BLE001
        return ""


def _print_debug_summary(
    console: Any,
    result: Dict[str, Any],
    elapsed: float,
    ctx: InteractiveContext,
) -> None:
    """Render the one-line ``[debug]`` summary after a turn.

    Reads the iteration count from ``result`` (populated by
    :class:`src.agent.loop.AgentLoop`), counts tool events from
    ``react_trace`` when present, and approximates the post-turn
    context size from ``ctx.history``. Best-effort — any missing field
    falls back to ``?`` so the summary still prints.
    """
    iterations = result.get("iterations", "?")
    trace = result.get("react_trace") or []
    if isinstance(trace, list):
        tools = sum(
            1
            for entry in trace
            if isinstance(entry, dict) and entry.get("type") == "tool_result"
        )
    else:
        tools = "?"
    history_chars = sum(len(m.get("content", "")) for m in ctx.history)
    # Rough char-to-token ratio (matches the loop's estimator).
    approx_tokens = history_chars // 4
    console.print(
        f"[dim][debug] iter={iterations} tools={tools} "
        f"elapsed={elapsed:.1f}s ctx≈{approx_tokens}tok ({history_chars}ch)[/dim]"
    )


def _run_one_turn(user_input: str, ctx: InteractiveContext) -> None:
    """Execute a single agent turn with the Rich dashboard.

    Routes through :func:`cli._legacy._run_agent` so all tool callbacks,
    persistent memory, and the ReAct engine remain untouched — we only
    swap in the Rich dashboard and persist the turn to ``SessionStore``.
    """
    from cli._legacy import _RunDashboard, _run_agent
    from rich.live import Live

    console = get_console()

    if ctx.session_id is None:
        ctx.session_id = _new_session(user_input)
    _append_message(ctx.session_id or "", "user", user_input)

    start = time.perf_counter()
    dashboard = _RunDashboard(user_input, ctx.max_iter)
    # Capture the latest live-trading mandate proposal emitted this turn so the
    # REPL can intercept the user's pick before the model (SPEC.md Consent §2).
    captured_proposal: Dict[str, Any] = {}

    def _capture_proposal(payload: Dict[str, Any]) -> None:
        captured_proposal.clear()
        captured_proposal.update(payload)

    # ``transient=False`` — keep the final timeline visible after the run
    # completes. Audit item 4.
    try:
        with Live(
            dashboard.render(),
            console=console,
            refresh_per_second=6,
            transient=False,
        ) as live:
            dashboard.live = live
            result = _run_agent(
                user_input,
                history=ctx.history[-_HISTORY_RETAINED_TURNS:],
                max_iter=ctx.max_iter,
                dashboard=dashboard,
                session_id=ctx.session_id or "",
                proposal_sink=_capture_proposal,
            )
            dashboard.finish(result, time.perf_counter() - start)
    except (KeyboardInterrupt, BrokenPipeError):
        dashboard.close()
        # BrokenPipe: caller did ``vibe-trading chat | head`` and the
        # downstream pipe closed mid-render. Print may itself fail on
        # the closed fd, so swallow that defensively too.
        try:
            console.print("\n[yellow]Interrupted[/yellow]")
        except (BrokenPipeError, OSError):
            pass
        return

    elapsed = time.perf_counter() - start
    _print_interactive_result(console, result, elapsed)

    # Render any mandate proposal AFTER the Live dashboard has closed so the
    # numbered choice block isn't clobbered by the live region, and arm the
    # REPL to intercept the next reply (SPEC.md Consent §2).
    if captured_proposal:
        ctx.pending_proposal = dict(captured_proposal)
        _render_mandate_proposal(console, ctx.pending_proposal)

    ctx.history.append({"role": "user", "content": user_input})
    answer = (result.get("content") or "").strip()
    if answer:
        ctx.history.append({"role": "assistant", "content": answer})
        _append_message(ctx.session_id or "", "assistant", answer)

    if ctx.debug:
        _print_debug_summary(console, result, elapsed, ctx)


def _print_interactive_result(console: Any, result: Dict[str, Any], elapsed: float) -> None:
    """Print the assistant answer after the rail without boxed run panels."""

    from cli.ui.transcript import render_answer, render_elapsed_status

    content = (result.get("content") or "").strip()
    if content:
        console.print(render_answer(content))
        console.print()
    console.print(render_elapsed_status(elapsed))
    run_id = result.get("run_id")
    if run_id:
        console.print(f"[dim]/show {run_id} · {elapsed:.1f}s[/dim]")


def _print_recap_if_needed(console: Any, ctx: InteractiveContext) -> None:
    """Print a dim recap once per completed turn."""

    if len(ctx.history) <= ctx.last_recap_history_len:
        return
    from cli.ui.transcript import render_recap

    recap = render_recap(ctx.history)
    if recap is not None:
        console.print()
        console.print(recap)
    ctx.last_recap_history_len = len(ctx.history)


def _print_input_hint(console: Any, hint: str) -> None:
    """Render the bottom hint bar in muted style."""
    from cli.components.hint_bar import render_hint_bar

    console.print(render_hint_bar(left=hint, right="Ctrl+D · /quit to exit"))


# ---------------------------------------------------------------------------
# Live trading channel — REPL intercepts (SPEC.md Consent §2, §4)
#
# Two privileged surface actions are intercepted in the REPL input path BEFORE
# the agent loop is ever entered, so neither depends on the model cooperating:
#
#   1. Kill switch — a bare "停"/"stop"/"kill" turn, or the /halt /stop slash
#      commands, trip the HALT sentinel directly. The model never sees them.
#   2. Mandate pick — when a `mandate.proposal` is outstanding, a bare numeric
#      reply ("1"/"2"/"3") is a COMMIT: it calls the commit endpoint directly
#      and the model never sees the pick. An "按 2，但…"-style adjust reply is
#      re-routed to the agent (PROPOSE re-render), not committed.
# ---------------------------------------------------------------------------

#: Bare turns that trip the kill switch when typed alone (case-insensitive).
_HALT_WORDS = frozenset({"停", "停止", "stop", "kill", "halt", "停手"})

_DEFAULT_LIVE_BROKER = "robinhood"


def _is_halt_turn(text: str) -> bool:
    """Return True if ``text`` is a bare kill-switch turn.

    Matches a turn whose entire content (trimmed, trailing punctuation removed,
    lower-cased) is one of :data:`_HALT_WORDS`. A longer sentence that merely
    *mentions* "stop" is NOT a halt turn — it routes to the agent normally.

    Args:
        text: The raw user input line (already stripped of surrounding space).

    Returns:
        ``True`` if the turn should trip the kill switch.
    """
    token = text.strip().strip(".!。！ ").lower()
    return token in _HALT_WORDS


def _trip_halt_from_repl(console: Any, *, reason: str) -> None:
    """Trip the global kill switch from the REPL and print a notice.

    This is the surface action behind a bare "停"/"stop" turn and the
    ``/halt`` / ``/stop`` slash commands. It writes the HALT sentinel via
    :func:`src.live.halt.trip_halt` — independent of the agent loop, so it works
    even mid-stream.

    Args:
        console: Rich console for the confirmation notice.
        reason: Human-readable reason recorded in the sentinel.
    """
    try:
        from src.live.halt import trip_halt

        path = trip_halt(by="cli", reason=reason)
    except Exception as exc:  # noqa: BLE001 — never let a halt failure kill the loop
        console.print(f"[bold red]Failed to trip kill switch:[/bold red] {exc}")
        return
    console.print(
        "[bold red]Live trading halted[/bold red] — all live order tools are now "
        "disabled until you run [bold]/resume[/bold] or [bold]vibe-trading connector resume[/bold]."
    )
    console.print(f"[dim]HALT sentinel: {path}[/dim]")


def _clear_halt_from_repl(console: Any) -> None:
    """Clear the global kill switch from the REPL (``/resume``).

    Clearing the halt is a privileged surface action — an explicit re-enable,
    never an agent tool (SPEC.md Consent §4). It is intercepted in the input
    path so the model never performs it. Mirrors ``vibe-trading connector resume``
    with no broker (the global scope).

    Args:
        console: Rich console for the confirmation notice.
    """
    try:
        from src.live.halt import clear_halt

        cleared = clear_halt()
    except Exception as exc:  # noqa: BLE001 — never let a resume failure kill the loop
        console.print(f"[bold red]Failed to clear kill switch:[/bold red] {exc}")
        return
    if cleared:
        console.print(
            "[green]Live trading re-enabled[/green] — the global kill switch is cleared."
        )
    else:
        console.print("[dim]No active global halt to clear.[/dim]")


def _run_connector_command_from_repl(console: Any, args: list[str]) -> None:
    """Run a ``/connector ...`` subcommand from the REPL via the dispatcher.

    ``/connector`` is a thin in-REPL bridge to the ``vibe-trading connector``
    subcommand group (SPEC.md §9 Decision 1): ``/connector status``,
    ``/connector start``, ``/connector stop``, ``/connector halt``, etc. It parses the
    arguments through the same argparse surface as the non-interactive CLI and
    dispatches to the same privileged handlers — none of which is an agent tool.
    A bare ``/connector`` defaults to ``status`` so the most common read is one
    keystroke away.

    Args:
        console: Rich console for error messages.
        args: Tokens following ``/connector`` (e.g. ``["status", "robinhood-live-mcp"]``).
    """
    from cli._legacy import _build_parser, _dispatch_connector

    argv = ["connector", *(args or ["status"])]
    parser = _build_parser()
    try:
        parsed = parser.parse_args(argv)
    except SystemExit:
        # argparse already printed usage to stderr; keep the REPL alive.
        console.print("[dim]Usage: /connector [list|status|start|stop|halt|resume|revoke][/dim]")
        return
    try:
        _dispatch_connector(parsed)
    except Exception as exc:  # noqa: BLE001 — never let a connector command kill the loop
        console.print(f"[bold red]/connector failed:[/bold red] {exc}")


def _is_numeric_pick(text: str) -> Optional[int]:
    """Return the chosen ordinal if ``text`` is a bare numeric pick, else None.

    Only a turn that is *exactly* a positive integer (e.g. ``"2"``) counts as a
    pick. Anything with extra words ("按 2 但每日笔数提到 10") is an adjust reply,
    not a pick, and must route back through PROPOSE.

    Args:
        text: The raw user input line.

    Returns:
        The 1-based ordinal, or ``None`` when ``text`` is not a bare pick.
    """
    token = text.strip().strip(".。 ")
    if token.isdigit():
        value = int(token)
        if value >= 1:
            return value
    return None


def _render_mandate_proposal(console: Any, proposal: Dict[str, Any]) -> None:
    """Print the numbered mandate-proposal choice block (SPEC.md Consent §2).

    Renders the agent's candidate mandate profiles as a numbered list with their
    concrete limits, plus the funding note and the kill-switch note. The user
    replies with a bare number to commit, or an adjust sentence to re-propose.

    Args:
        console: Rich console.
        proposal: The ``mandate.proposal`` event payload.
    """
    intent = proposal.get("intent_normalized") or "live trading"
    account = proposal.get("account") or {}
    acct_type = account.get("type")
    acct_suffix = f" ({acct_type} account)" if acct_type else ""
    profiles = proposal.get("profiles") or []

    console.print()
    if proposal.get("reauth_for"):
        console.print(
            f'[bold]AI proposes widening your mandate for "{intent}"{acct_suffix}:[/bold]'
        )
    else:
        console.print(
            f'[bold]AI proposes {len(profiles)} mandate(s) for "{intent}"{acct_suffix}:[/bold]'
        )
    console.print()

    for profile in profiles:
        ordinal = profile.get("ordinal", "?")
        label = profile.get("label", "")
        universe = profile.get("universe")
        if isinstance(universe, (list, tuple)):
            universe = "/".join(str(s) for s in universe)
        bits = []
        if universe:
            bits.append(f"univ: {universe}")
        if profile.get("max_order_usd") is not None:
            bits.append(f"≤${profile['max_order_usd']}/order")
        if profile.get("daily_trade_cap") is not None:
            bits.append(f"{profile['daily_trade_cap']} trades/day")
        leverage = profile.get("leverage")
        if leverage in (None, "none", "None", 1, 1.0):
            bits.append("no leverage")
        elif leverage is not None:
            bits.append(f"leverage {leverage}")
        line = "  · ".join(bits)
        console.print(f"  [bold cyan][{ordinal}][/bold cyan] {label}  {line}")
        notes = profile.get("notes")
        if notes:
            console.print(f"      [dim]{notes}[/dim]")

    console.print()
    funding_note = proposal.get("funding_note") or (
        "Funding is set by YOU in the broker; the agent cannot move money."
    )
    halt_note = proposal.get("halt_note") or '随时一句 "停" = kill switch, halts everything.'
    console.print(f"  [dim]{funding_note}[/dim]")
    console.print(f"  [dim]{halt_note}[/dim]")
    console.print(
        '  [bold]Pick a number to commit, or say "按 2 但每日笔数提到 10" to adjust.[/bold]'
    )
    console.print()


def _commit_mandate(proposal: Dict[str, Any], selected_ordinal: int) -> Dict[str, Any]:
    """Commit a mandate selection via the surface commit endpoint.

    This is the single privileged write that activates a mandate. The pick is a
    SURFACE action — it goes straight to ``POST /mandate/commit`` (owned by the
    commit-endpoint parcel) and is NEVER fed to the model. ``consent_ack`` is set
    here because the user's keypress *is* the affirmative consent.

    The endpoint base URL is read from ``VIBE_TRADING_API_URL`` (falling back to
    ``http://127.0.0.1:8000``); a per-request override is not accepted from the
    proposal payload so the model cannot redirect the commit.

    Args:
        proposal: The outstanding ``mandate.proposal`` payload (binds the commit
            to the exact rendered options via ``proposal_id``).
        selected_ordinal: The 1-based profile the user picked.

    Returns:
        The decoded commit response (``mandate_id`` / ``consent_record_id`` on
        success), or an ``{"status": "error", ...}`` envelope on failure.
    """
    import httpx

    base = os.environ.get("VIBE_TRADING_API_URL", "http://127.0.0.1:8000").rstrip("/")
    body = {
        "proposal_id": proposal.get("proposal_id"),
        "selected_ordinal": selected_ordinal,
        "adjustments": None,
        "session_id": proposal.get("session_id"),
        "consent_ack": True,
    }
    try:
        response = httpx.post(f"{base}/mandate/commit", json=body, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001 — surface a clean error to the user
        return {"status": "error", "error": str(exc)}


def _handle_proposal_reply(text: str, ctx: InteractiveContext) -> bool:
    """Intercept a reply while a mandate proposal is outstanding.

    Must be called only when ``ctx.pending_proposal`` is set. A bare numeric pick
    is a COMMIT (calls the endpoint directly, the model never sees it); any other
    reply is an ADJUST and is routed back to the agent for a fresh proposal.

    Args:
        text: The raw user input line.
        ctx: The interactive context (proposal is cleared on a successful pick).

    Returns:
        ``True`` if the reply was a numeric pick and was handled here (the caller
        must NOT route it to the agent). ``False`` for an adjust reply, which the
        caller routes to the agent normally (keeping the proposal pending until a
        fresh one replaces it).
    """
    console = get_console()
    ordinal = _is_numeric_pick(text)
    if ordinal is None:
        # Adjust path — re-render via PROPOSE. Leave the proposal pending; the
        # agent will emit a fresh one that overwrites it.
        return False

    proposal = ctx.pending_proposal or {}
    profiles = proposal.get("profiles") or []
    valid_ordinals = {p.get("ordinal") for p in profiles}
    if valid_ordinals and ordinal not in valid_ordinals:
        console.print(
            f"[yellow]No option [{ordinal}] in this proposal.[/yellow] "
            f"Pick one of: {', '.join(str(o) for o in sorted(o for o in valid_ordinals if o is not None))}, "
            "or type an adjust sentence."
        )
        return True

    console.print(f"[dim]Committing mandate option [{ordinal}]…[/dim]")
    result = _commit_mandate(proposal, ordinal)
    if result.get("status") == "error":
        console.print(f"[red]Commit failed:[/red] {result.get('error')}")
        console.print("[dim]The proposal is still open — pick again once the issue is resolved.[/dim]")
        return True

    # Success — clear the proposal so subsequent turns route normally.
    ctx.pending_proposal = None
    mandate_id = result.get("mandate_id") or "?"
    console.print(f"[green]Mandate {mandate_id} active.[/green]")
    return True


def _interactive_loop(max_iter: int, resume_session_id: Optional[str] = None) -> int:
    """Drive the new interactive REPL.

    Args:
        max_iter: Maximum ReAct iterations per turn.
        resume_session_id: If set, load this specific session instead of
            prompting to resume the most recent one.

    Returns:
        Process exit code (always ``0`` on a clean exit).
    """
    console = get_console()

    # Keep the first prompt frame uncontested. The preflight renderer writes to
    # stdout, so running it here races prompt_toolkit on cold start and can make
    # the prompt appear only after the user presses Enter.

    ctx = InteractiveContext(max_iter=max_iter)

    if resume_session_id:
        # Resume a specific session by ID (``vibe-trading resume <session-id>``).
        try:
            store = _session_store()
            session = store.get_session(resume_session_id)
        except Exception:  # noqa: BLE001
            session = None
        if session is None:
            console.print(f"[red]Session {resume_session_id} not found[/red]")
            return 1
        ctx.session_id = resume_session_id
        ctx.history = _build_session_history(store, resume_session_id)
        console.print(
            f"[dim]Resumed session: {session.title or session.session_id} "
            f"({len(ctx.history)} prior turns)[/dim]"
        )
    else:
        # Offer to resume the most recent session. Audit item 8.
        resume = _maybe_resume_last_session(console)
        if resume is not None:
            ctx.session_id = resume["session_id"]
            ctx.history = list(resume["history"])
            console.print(
                f"[dim]Resumed session: {resume['title']} ({len(ctx.history)} prior turns)[/dim]"
            )

    # Build the prompt session once so history + completer persist.
    try:
        from cli.input import ctrl_c_within_window, get_user_input, make_session
    except Exception as exc:  # noqa: BLE001 — fall back gracefully if prompt_toolkit broken
        console.print(f"[red]Failed to initialise input layer: {exc}[/red]")
        console.print("[dim]Falling back to legacy interactive loop.[/dim]")
        from cli._legacy import cmd_interactive

        try:
            cmd_interactive(max_iter)
        except Exception:  # noqa: BLE001
            return 1
        return 0

    session = make_session()

    while True:
        _print_recap_if_needed(console, ctx)
        try:
            user_input = get_user_input(session=session)
        except KeyboardInterrupt:
            # Should not reach here — the keybinding raises EOFError instead.
            continue
        except EOFError:
            # Two interpretations: Ctrl+D (always exit), or Ctrl+C on an
            # empty line (show hint, exit on second press).
            #
            # ``ctrl_c_within_window`` reads a press-time decision cached
            # by the keybinding: True iff the gap between the *previous*
            # Ctrl+C press and *this* one is < 2 s. First press → False
            # (no prior press) → we print the hint and continue. Second
            # press inside the window → True → we break.
            if ctrl_c_within_window(session, window_sec=2.0):
                break
            console.print(
                "[dim]Press Ctrl+C again within 2s, Ctrl+D, or type /quit to exit[/dim]"
            )
            continue

        text = user_input.strip()
        if not text:
            continue

        # Kill switch — intercept a bare "停"/"stop"/"kill" turn BEFORE the
        # agent loop so it trips even if a turn is mid-stream and never depends
        # on the model cooperating (SPEC.md Consent §4).
        if _is_halt_turn(text):
            _trip_halt_from_repl(console, reason=f"repl turn: {text}")
            ctx.pending_proposal = None
            continue

        # Mandate pick — when a proposal is outstanding, a bare numeric reply
        # is a COMMIT handled here (the model never sees it). An adjust reply
        # falls through to the agent for a fresh proposal (SPEC.md Consent §2).
        if ctx.pending_proposal is not None and not text.startswith("/"):
            if _handle_proposal_reply(text, ctx):
                continue

        # Slash command path.
        if text.startswith("/"):
            # /halt /stop /resume /connector are privileged live-trading surface
            # actions handled in the input path, never dispatched to the model
            # (SPEC.md Consent §4 / §9 Decision 1).
            slash_tokens = text.lstrip("/").split()
            slash_name = slash_tokens[0].lower() if slash_tokens else ""
            if slash_name in {"halt", "stop"}:
                _trip_halt_from_repl(console, reason=f"/{slash_name}")
                ctx.pending_proposal = None
                continue
            if slash_name == "resume":
                _clear_halt_from_repl(console)
                continue
            if slash_name == "connector":
                _run_connector_command_from_repl(console, slash_tokens[1:])
                continue
            rc = _dispatch_slash(text, ctx)
            if rc == 2:
                break
            # A handler may queue an agent prompt (``/journal <path>``,
            # ``/shadow ...``). Drain it here so the slash command turns
            # into a real turn without round-tripping through stdin.
            queued = ctx.pending_prompt
            if queued:
                ctx.pending_prompt = None
                _run_one_turn(queued, ctx)
            continue

        # Natural-language path — drive the agent.
        _run_one_turn(text, ctx)

    console.print("[dim]Goodbye[/dim]")
    if ctx.session_id:
        console.print(
            f"[dim]To resume this session:[/dim] [bold]vibe-trading resume {ctx.session_id}[/bold]"
        )
    return 0


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint returning a process exit code.

    Behaviour:

    * Interactive entry (no subcommand, or ``chat`` + TTY): show banner,
      run onboarding wizard if needed, then drop into the interactive
      loop driven by ``cli/input.py``, ``cli/completer.py``,
      and ``cli/commands/*``.
    * Non-interactive entry (``serve``, ``run -p ...``, ``mcp``,
      ``swarm``, piped stdin, etc.): pass through to ``cli._legacy.main``
      so every existing subcommand keeps working unchanged.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    interactive = _is_interactive_invocation(raw_argv)

    if interactive:
        if not _maybe_run_onboarding():
            return 0
        _show_banner()
        # Strip the optional ``chat`` token + any ``--max-iter`` flag so
        # the new loop can read them directly without re-parsing argv.
        max_iter = _extract_max_iter(raw_argv, default=50)
        return _interactive_loop(max_iter)

    # Handle ``vibe-trading resume <session-id>`` — enter the interactive
    # loop with a specific session loaded, bypassing the legacy dispatcher.
    if len(raw_argv) == 2 and raw_argv[0] == "resume":
        max_iter = _extract_max_iter(raw_argv, default=50)
        return _interactive_loop(max_iter=max_iter, resume_session_id=raw_argv[1])

    # Delegate every other path to the legacy dispatcher.
    try:
        from cli import _legacy
    except ImportError as exc:  # pragma: no cover — packaging error
        get_console().print(
            f"  Internal error: cannot import cli._legacy ({exc}).",
            style=Theme.danger,
        )
        return 2

    return int(_legacy.main(raw_argv))


def _extract_max_iter(argv: Sequence[str], *, default: int) -> int:
    """Pull ``--max-iter <N>`` (or ``--max-iter=N``) out of ``argv``.

    The legacy argparse setup accepts ``--max-iter`` both at the top
    level and as ``chat --max-iter``. We just need the integer; the
    presence/absence of ``chat`` was already determined upstream.
    """
    it = iter(range(len(argv)))
    for i in it:
        token = argv[i]
        if token == "--max-iter" and i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                return default
        if token.startswith("--max-iter="):
            try:
                return int(token.split("=", 1)[1])
            except ValueError:
                return default
    return default


def _entrypoint() -> None:
    """Thin wrapper so the console script and ``python -m cli.main`` agree."""
    sys.exit(main())


# ---------------------------------------------------------------------------
# Optional typer integration (only used by ``python -m cli.main --help``)
# ---------------------------------------------------------------------------


def _build_typer_app():  # type: ignore[no-untyped-def]
    """Build a typer app that mirrors the legacy surface. Best-effort only."""
    try:
        import typer
    except ImportError:
        return None

    app = typer.Typer(
        add_completion=False,
        no_args_is_help=False,
        help="Vibe-Trading — natural-language finance research agent.",
        rich_markup_mode=None,
    )

    @app.callback(invoke_without_command=True)
    def _default(ctx: typer.Context) -> None:  # noqa: ANN001
        if ctx.invoked_subcommand is None:
            sys.exit(main(ctx.args))

    @app.command("chat", help="Start the interactive ReAct chat loop.")
    def _chat(
        max_iter: int = typer.Option(50, "--max-iter", help="Maximum ReAct iterations."),
    ) -> None:
        sys.exit(main(["chat", "--max-iter", str(max_iter)]))

    @app.command("serve", help="Start the FastAPI server.")
    def _serve(
        host: str = typer.Option("0.0.0.0", "--host"),
        port: int = typer.Option(8000, "--port"),
        dev: bool = typer.Option(False, "--dev", help="Also boot the Vite dev server."),
    ) -> None:
        forwarded = ["serve", "--host", host, "--port", str(port)]
        if dev:
            forwarded.append("--dev")
        sys.exit(main(forwarded))

    @app.command("list", help="List recent runs.")
    def _list(limit: int = typer.Option(20, "--limit")) -> None:
        sys.exit(main(["list", "--limit", str(limit)]))

    @app.command("show", help="Show a recorded run by id.")
    def _show(run_id: str = typer.Argument(...)) -> None:
        sys.exit(main(["show", run_id]))

    @app.command("init", help="Re-run the interactive setup wizard.")
    def _init() -> None:
        run_onboarding(console=get_console())

    @app.command("setup", help="Install frontend deps and build the production bundle (cross-platform).")
    def _setup(
        frontend_dir: str = typer.Option(
            "frontend",
            "--frontend-dir",
            help="Path to the frontend directory (relative to repo root or absolute).",
        ),
    ) -> None:
        sys.exit(main(["setup", "--frontend-dir", frontend_dir]))

    @app.command("dev", help="Start backend + Vite dev server in one process.")
    def _dev(
        port: int = typer.Option(8899, "--port", help="Backend port."),
        frontend_port: int = typer.Option(
            5899,
            "--frontend-port",
            help="Vite dev server port (must match vite.config.ts).",
        ),
        frontend_dir: str = typer.Option("frontend", "--frontend-dir"),
    ) -> None:
        sys.exit(
            main(
                [
                    "dev",
                    "--port",
                    str(port),
                    "--frontend-port",
                    str(frontend_port),
                    "--frontend-dir",
                    frontend_dir,
                ]
            )
        )

    return app


# ``python -m cli.main`` support — uses typer help if available, else main().
if __name__ == "__main__":
    typer_app = _build_typer_app()
    if typer_app is not None:
        typer_app()
    else:
        _entrypoint()


__all__ = ["main", "InteractiveContext"]
