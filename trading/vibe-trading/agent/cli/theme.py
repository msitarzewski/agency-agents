"""Centralised Rich Style table for the Vibe-Trading CLI.

All visible colour decisions for the CLI live here so the look stays consistent
with the web app (see ``frontend/src/index.css`` design tokens). The brand
accent is the orange wordmark colour selected in the 2026-05-19 UI/UX design
proposal (§1.3):

* light terminals: ``#d97706`` (WCAG-AA white-on-orange contrast 4.8:1)
* dark terminals:  ``#fa9842`` (matches web ``--primary`` in dark mode)

Semantic styles follow the design proposal's "Orange discipline rule" — only
the brand wordmark, the primary CTA, and the agent identity should ever use
``Theme.primary``. Tool status, success, danger and warning use their own
semantic tokens so the orange stays meaningful.

The module exposes a single shared :class:`rich.console.Console` instance via
:func:`get_console` so every component (banner, onboarding wizard, stream
renderer, status bar) renders to the same TTY. ``NO_COLOR`` is honoured by
forcing Rich into no-color mode at construction time.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Final

from rich.console import Console
from rich.style import Style

# ---------------------------------------------------------------------------
# Brand palette (single source of truth — mirrored in frontend/src/index.css)
# ---------------------------------------------------------------------------

BRAND_ORANGE_LIGHT: Final[str] = "#d97706"
"""Wordmark / primary CTA colour on light terminals (web ``--primary`` light)."""

BRAND_ORANGE_DARK: Final[str] = "#fa9842"
"""Wordmark / primary CTA colour on dark terminals (web ``--primary`` dark)."""


def _is_dark_terminal(console: Console) -> bool:
    """Heuristically decide whether the terminal is rendering on a dark theme.

    Rich does not expose a foolproof "dark mode?" probe, so we use a best-effort
    chain:

    1. Explicit override via ``VIBE_TRADING_THEME`` env var (``dark``/``light``).
    2. ``COLORFGBG`` (set by xterm/rxvt/Konsole): the part after ``;`` is the
       background colour index. ``0`` (black) → dark, anything else → light.
    3. macOS Terminal.app sets ``TERM_PROGRAM=Apple_Terminal`` without a colour
       hint — assume dark (it is the macOS Big Sur+ default).
    4. Fallback: dark (matches the modern default across iTerm, Alacritty,
       Windows Terminal, VS Code integrated terminal).

    Args:
        console: Rich console (used to short-circuit when colour is disabled).

    Returns:
        ``True`` if dark mode should be assumed.
    """

    override = os.environ.get("VIBE_TRADING_THEME", "").strip().lower()
    if override in {"dark", "light"}:
        return override == "dark"

    if console.color_system is None:
        # No colour at all — pick dark so dim styles read correctly when forced
        # to ANSI later, but in practice nothing will be coloured.
        return True

    colorfgbg = os.environ.get("COLORFGBG", "")
    if ";" in colorfgbg:
        bg = colorfgbg.split(";")[-1].strip()
        if bg.isdigit():
            return int(bg) in {0, 1, 2, 3, 4, 5, 6, 7, 8}  # low ANSI ⇒ dark

    if os.environ.get("TERM_PROGRAM", "").lower() == "apple_terminal":
        return True

    return True


@dataclass(frozen=True)
class _ThemeStyles:
    """Immutable bundle of Rich :class:`Style` instances used CLI-wide."""

    primary: Style
    """Brand orange. Reserved for wordmark, primary CTA, agent identity."""

    primary_dim: Style
    """Slightly muted brand orange for hover/inactive variants."""

    success: Style
    """Tool completed, backtest passed, env saved (green)."""

    danger: Style
    """Failures, validation errors, destructive prompts (red)."""

    warning: Style
    """Tool running, partial state, non-blocking caution (amber)."""

    info: Style
    """Hints, secondary headings, neutral attention (cyan)."""

    muted: Style
    """Captions, dim metadata, separators (dim grey)."""

    bold: Style
    """Section headers, table column titles."""

    label: Style
    """Inline labels (e.g. ``Model:``) — slightly bolder than ``muted``."""

    accent_bg: Style
    """Reverse-video accent — used for the slash-typeahead highlight."""


_NO_COLOR: Final[bool] = "NO_COLOR" in os.environ


def _build_styles(dark: bool, no_color: bool) -> _ThemeStyles:
    """Construct the style bundle for the current terminal mode."""

    if no_color:
        plain = Style()
        return _ThemeStyles(
            primary=Style(bold=True),
            primary_dim=Style(),
            success=Style(),
            danger=Style(bold=True),
            warning=Style(),
            info=Style(),
            muted=Style(dim=True),
            bold=Style(bold=True),
            label=Style(bold=True),
            accent_bg=Style(reverse=True),
        )

    brand = BRAND_ORANGE_DARK if dark else BRAND_ORANGE_LIGHT
    brand_dim = "#a35a04" if not dark else "#c87a2f"

    return _ThemeStyles(
        primary=Style(color=brand, bold=True),
        primary_dim=Style(color=brand_dim),
        success=Style(color="#16a34a", bold=True),
        danger=Style(color="#dc2626", bold=True),
        warning=Style(color="#d97706"),  # amber for in-flight tools
        info=Style(color="#0891b2"),
        muted=Style(color="#737373", dim=True) if not dark else Style(color="#9ca3af", dim=True),
        bold=Style(bold=True),
        label=Style(color="#525252", bold=True) if not dark else Style(color="#d4d4d8", bold=True),
        accent_bg=Style(color=brand, reverse=True, bold=True),
    )


# ---------------------------------------------------------------------------
# Singleton console + style accessors
# ---------------------------------------------------------------------------


def _make_console() -> Console:
    """Create the shared Rich console.

    ``force_terminal`` is *not* set: Rich's own ``isatty`` detection is
    correct and forcing it leaks ANSI escapes into ``docker exec -i`` /
    piped output (nanobot lesson, issue #3265).

    ``no_color`` honours ``NO_COLOR`` (https://no-color.org).
    """

    return Console(
        no_color=_NO_COLOR,
        soft_wrap=False,
        highlight=False,
        emoji=False,  # project rule: no emoji anywhere
        markup=True,
        stderr=False,
        legacy_windows=False if sys.platform == "win32" else None,
    )


_console: Console = _make_console()
_dark: bool = _is_dark_terminal(_console)
_styles: _ThemeStyles = _build_styles(_dark, _NO_COLOR or _console.color_system is None)


def get_console() -> Console:
    """Return the shared console instance.

    Returns:
        The single :class:`Console` everyone in ``agent/cli`` writes to.
    """

    return _console


def is_dark() -> bool:
    """Return ``True`` if dark-mode styles are active."""

    return _dark


class Theme:
    """Namespace of Rich :class:`Style` instances used across the CLI.

    Use as attribute access (``Theme.primary``) so that swapping the
    underlying palette only requires editing this module. Each attribute is a
    :class:`rich.style.Style` and can be passed to ``console.print`` directly
    or composed via ``Text("…", style=Theme.primary)``.

    Example:
        >>> from cli.theme import Theme, get_console
        >>> get_console().print("Vibe-Trading", style=Theme.primary)
    """

    primary: Final[Style] = _styles.primary
    primary_dim: Final[Style] = _styles.primary_dim
    success: Final[Style] = _styles.success
    danger: Final[Style] = _styles.danger
    warning: Final[Style] = _styles.warning
    info: Final[Style] = _styles.info
    muted: Final[Style] = _styles.muted
    bold: Final[Style] = _styles.bold
    label: Final[Style] = _styles.label
    accent_bg: Final[Style] = _styles.accent_bg

    # Convenience aliases used by intro / stream
    brand_hex: Final[str] = BRAND_ORANGE_DARK if _dark else BRAND_ORANGE_LIGHT


__all__ = [
    "Theme",
    "get_console",
    "is_dark",
    "BRAND_ORANGE_LIGHT",
    "BRAND_ORANGE_DARK",
]
