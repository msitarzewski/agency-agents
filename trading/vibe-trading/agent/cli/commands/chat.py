"""Chat-flow slash commands: ``/model``, ``/clear``, ``/journal``,
``/shadow``, ``/swarm``, ``/debug``, ``/quit``.

``/model`` renders the current configuration via the legacy
``_show_settings`` helper. ``/swarm`` dispatches to the legacy
``_handle_swarm_command`` so the existing presets keep working. ``/clear``
clears the screen and reprints the banner. ``/journal``, ``/shadow``, and
``/debug`` show a "Coming soon" placeholder pointing at the established
fallback workflows.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from cli.theme import get_console


def _resolve_console(console: Optional[Console] = None) -> Console:
    """Return the shared CLI console, or a caller-supplied override."""
    if console is not None:
        return console
    return get_console()


def _coming_soon(command: str, *, hint: str) -> int:
    """Render the placeholder panel for not-yet-wired commands."""
    console = _resolve_console()
    body = Text()
    body.append(f"/{command} is not yet wired up to the interactive CLI.\n\n", style="dim")
    body.append("Until then: ", style="dim")
    body.append(hint, style="bold")
    console.print(Panel(body, title=f"/{command}", border_style="dim", padding=(1, 2)))
    return 0


# --- /model ----------------------------------------------------------------


def cmd_model(ctx: Any = None, *args: str) -> int:  # noqa: ARG001 — ctx unused
    """Print the current provider/model + how to re-run the wizard."""
    console = _resolve_console()
    try:
        from cli._legacy import _show_settings

        _show_settings()
    except Exception as exc:  # noqa: BLE001 — legacy may be absent on partial install
        provider = os.getenv("LANGCHAIN_PROVIDER", "(not set)")
        model = os.getenv("LANGCHAIN_MODEL_NAME", "(not set)")
        console.print(Text(f"Provider: {provider}", style="bold"))
        console.print(Text(f"Model:    {model}", style="bold"))
        console.print(Text(f"(legacy _show_settings unavailable: {exc})", style="dim"))

    console.print()
    console.print(
        Text(
            "Run `vibe-trading init` to switch provider, model, or credentials.",
            style="dim",
        )
    )
    return 0


# --- /clear, /journal, /shadow, /swarm, /debug, /quit ----------------------


def cmd_clear(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Clear the screen and reprint the welcome banner."""
    console = _resolve_console()
    try:
        console.clear()
    except Exception:  # noqa: BLE001 — clear can fail on dumb terminals
        pass
    # Best-effort: reprint the banner so the conversation appears fresh.
    # Reuse the cached stats populated at startup so the redrawn banner
    # shows the real skills / tools / sessions counts, not zeros.
    try:
        from cli.intro import print_banner
        from cli.main import _collect_banner_stats

        print_banner(console, **_collect_banner_stats())
    except Exception:  # noqa: BLE001
        console.print(Text("Conversation cleared.", style="dim"))
    # Caller is expected to also drop in-memory conversation history.
    if ctx is not None and hasattr(ctx, "history"):
        try:
            ctx.history.clear()
        except Exception:  # noqa: BLE001
            pass
    return 0


def _queue_prompt(ctx: Any, prompt: str) -> bool:
    """Stash ``prompt`` on ``ctx.pending_prompt`` for the loop to consume.

    Returns ``True`` if the context exposes a writable ``pending_prompt``
    attribute, ``False`` otherwise (e.g. a tiny test stub) — the caller
    falls back to printing the canonical instruction in that case.
    """
    if ctx is None or not hasattr(ctx, "pending_prompt"):
        return False
    try:
        ctx.pending_prompt = prompt
        return True
    except Exception:  # noqa: BLE001 — never crash the slash dispatch
        return False


def cmd_journal(ctx: Any = None, *args: str) -> int:
    """Queue an "analyze my trade journal at <path>" agent turn.

    With a path: ``/journal trades.csv`` becomes the prompt
    ``Analyze my trade journal at trades.csv`` which is queued on
    ``ctx.pending_prompt`` and executed by the interactive loop on the
    next tick. Without a path the command prints the canonical
    instruction so the user can paste it themselves.
    """
    console = _resolve_console()
    path = " ".join(args).strip()
    if not path:
        body = Text()
        body.append("Usage: ", style="dim")
        body.append("/journal <path-to-csv>\n", style="bold")
        body.append("Example: ", style="dim")
        body.append('/journal ~/Downloads/journal.csv\n\n', style="bold")
        body.append("Or type the prompt directly: ", style="dim")
        body.append('"analyze my trade journal at <path>"', style="bold")
        console.print(Panel(body, title="/journal", border_style="dim", padding=(1, 2)))
        return 0

    prompt = f"Analyze my trade journal at {path}"
    if _queue_prompt(ctx, prompt):
        console.print(Text(f"→ Running: {prompt}", style="dim"))
        return 0
    # Fallback when the context does not support queuing (legacy callers).
    console.print(Text(f'Type: "{prompt}"', style="bold"))
    return 0


def cmd_shadow(ctx: Any = None, *args: str) -> int:
    """Queue a Shadow Account agent turn.

    ``/shadow`` opens / inspects the shadow account. ``/shadow <path>``
    trains a new shadow from a trade journal at that path. Both forms
    queue the canonical natural-language prompt on ``ctx.pending_prompt``
    so the ReAct loop picks the right tool (``extract_shadow_strategy``,
    ``run_shadow_backtest``, ``render_shadow_report``).
    """
    console = _resolve_console()
    path = " ".join(args).strip()
    if path:
        prompt = f"Train a shadow account from my trade journal at {path}"
    else:
        prompt = "Open the shadow account dashboard and show the latest report"

    if _queue_prompt(ctx, prompt):
        console.print(Text(f"→ Running: {prompt}", style="dim"))
        return 0
    console.print(Text(f'Type: "{prompt}"', style="bold"))
    return 0


def cmd_swarm(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Dispatch to the legacy swarm handler."""
    try:
        from cli._legacy import _handle_swarm_command

        _handle_swarm_command(" ".join(args))
        return 0
    except Exception as exc:  # noqa: BLE001
        console = _resolve_console()
        console.print(Text(f"/swarm failed: {exc}", style="bold red"))
        return 1


def cmd_debug(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Toggle the debug summary that prints after each agent turn.

    When ON the interactive loop appends a single muted line after every
    turn containing ``iter``, ``tools``, ``elapsed``, and an approximate
    context-size estimate — see ``_print_debug_summary`` in
    :mod:`cli.main`. When OFF the summary is suppressed.
    """
    console = _resolve_console()
    if ctx is not None and hasattr(ctx, "debug"):
        try:
            ctx.debug = not bool(getattr(ctx, "debug", False))
            state = "ON" if ctx.debug else "OFF"
            console.print(Text(f"Debug summary: {state}", style="bold"))
            if ctx.debug:
                console.print(
                    Text(
                        "After each turn a one-line summary will print: "
                        "iterations, tool count, elapsed, approx context tokens.",
                        style="dim",
                    )
                )
            return 0
        except Exception as exc:  # noqa: BLE001
            console.print(Text(f"/debug toggle failed: {exc}", style="bold red"))
            return 1
    return _coming_soon(
        "debug",
        hint="set `VIBE_TRADING_DEBUG=1` and restart for verbose logging.",
    )


def cmd_quit(ctx: Any = None, *args: str) -> int:  # noqa: ARG001
    """Signal exit by returning a distinct exit code.

    The interactive loop interprets ``2`` as "user-requested quit" and
    performs session persistence + final farewell before terminating.
    """
    return 2


# --- Module-level dispatch table -----------------------------------------

_DISPATCH = {
    "model": cmd_model,
    "clear": cmd_clear,
    "journal": cmd_journal,
    "shadow": cmd_shadow,
    "swarm": cmd_swarm,
    "debug": cmd_debug,
    "quit": cmd_quit,
}


def run(ctx: Any = None, command: str = "model", *args: str) -> int:
    """Dispatch ``run("model")`` / ``run("clear")`` / ... to the right handler."""
    handler = _DISPATCH.get(command)
    if handler is None:
        console = _resolve_console()
        console.print(Text(f"Unknown chat command: /{command}", style="bold red"))
        return 1
    return handler(ctx, *args)


__all__ = [
    "run",
    "cmd_model",
    "cmd_clear",
    "cmd_journal",
    "cmd_shadow",
    "cmd_swarm",
    "cmd_debug",
    "cmd_quit",
]
