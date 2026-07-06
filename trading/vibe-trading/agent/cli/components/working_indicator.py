"""Thinking spinner — picks a random verb on entry, hides on exit.

Wraps :class:`rich.live.Live` with ``transient=True`` so the spinner
erases itself once the context exits — leaving the answer print
uncluttered (the bug nanobot called out in their StreamRenderer
docstring: transient=True avoids the "ghost spinner" duplication).

If :mod:`agent.cli.utils.thinking_verbs` has not landed yet (Parcel α
ships it) we fall back to ``"Pondering…"`` so the demo build still
works.
"""

from __future__ import annotations

import random
from types import TracebackType
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text


_FALLBACK_VERBS: tuple[str, ...] = (
    "Pondering…",
    "Analyzing…",
    "Reasoning…",
    "Thinking…",
    "Investigating…",
)


def _pick_verb() -> str:
    """Pick a thinking verb via the shared helper, with a local fallback."""
    try:
        from cli.utils.thinking_verbs import pick_thinking_verb

        verb = pick_thinking_verb()
        if isinstance(verb, str) and verb:
            return verb
    except Exception:  # noqa: BLE001 — never block the spinner on helper issues
        pass
    return random.choice(_FALLBACK_VERBS)


def _resolve_console() -> Console:
    """Return the shared CLI console."""
    from cli.theme import get_console

    return get_console()


class ThinkingSpinner:
    """Context manager that shows a Rich spinner + thinking verb.

    Usage:
        with ThinkingSpinner() as spinner:
            spinner.update_verb("Backtesting…")   # optional mid-run swap
            ... do agent work ...

    The spinner is ``transient=True`` so it disappears when the block
    exits. Use :meth:`pause` to temporarily hide the spinner while
    printing auxiliary lines (e.g. a tool event row) — borrowed from
    nanobot's StreamRenderer pattern.
    """

    def __init__(
        self,
        verb: Optional[str] = None,
        *,
        console: Optional[Console] = None,
        spinner_name: str = "dots",
    ) -> None:
        self._verb = verb or _pick_verb()
        self._console = console or _resolve_console()
        self._spinner_name = spinner_name
        self._live: Optional[Live] = None

    # --------------------------------------------------------- lifecycle ----
    def __enter__(self) -> "ThinkingSpinner":
        self._live = Live(
            self._renderable(),
            console=self._console,
            transient=True,
            refresh_per_second=12,
        )
        self._live.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        live, self._live = self._live, None
        if live is not None:
            live.__exit__(exc_type, exc, tb)

    # ------------------------------------------------------------- helpers --
    def _renderable(self) -> Spinner:
        # ``Spinner.text`` accepts Rich Text for styling — keep the verb in
        # the dim style so the live region is unobtrusive.
        return Spinner(self._spinner_name, text=Text(self._verb, style="dim"))

    def update_verb(self, verb: str) -> None:
        """Swap the verb mid-run (e.g. ``"Backtesting…"`` once tools fire)."""
        self._verb = verb
        if self._live is not None:
            self._live.update(self._renderable())

    def pause(self) -> "_SpinnerPause":
        """Yield a context manager that hides the spinner inside its block.

        Useful when callers need to ``console.print`` a tool-event row
        without the spinner frame racing with the print to stdout.
        """
        return _SpinnerPause(self)


class _SpinnerPause:
    """Inner context manager returned by :meth:`ThinkingSpinner.pause`."""

    def __init__(self, parent: ThinkingSpinner) -> None:
        self._parent = parent
        self._saved_live: Optional[Live] = None

    def __enter__(self) -> None:
        # Stash the live so __exit__ on the outer spinner does nothing
        # while we are paused; restart it on exit.
        if self._parent._live is not None:
            self._parent._live.__exit__(None, None, None)
            self._saved_live = self._parent._live
            self._parent._live = None

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._saved_live is not None:
            self._parent._live = self._saved_live
            self._parent._live.__enter__()
            self._saved_live = None


__all__ = ["ThinkingSpinner"]
