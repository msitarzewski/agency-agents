"""prompt_toolkit input editor + ``SafeFileHistory``.

Wraps a :class:`PromptSession` with:
    * The slash :class:`~cli.completer.SlashCompleter`
    * Multi-line editing — Enter inserts a newline only when the buffer is
      mid-bracket; Alt+Enter / Esc-Enter inserts a newline unconditionally;
      a plain Enter on a balanced buffer submits.
    * Ctrl+C with three-state semantics (clear buffer → exit hint → exit)
    * A surrogate-safe :class:`FileHistory` subclass for Windows users
    * UTF-8 stdout reconfigure on Windows so the brand glyph ``●`` and the
      Rich box-drawing characters print without ``UnicodeEncodeError``

Cancel-during-generation lives outside the input loop — that is owned by
the agent runner in :mod:`cli.main`. Here we only handle the *input
editing* and *idle* states.
"""

from __future__ import annotations

import sys
import shutil
import time
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style


# Sentinel raised by the Ctrl+C path so the caller can distinguish
# "user pressed Ctrl+C on an empty line" from real EOF. We reuse
# :class:`EOFError` so prompt_toolkit's existing plumbing keeps working;
# the caller decides between "show hint" and "exit" via timing.
_EXIT_HINT_GAP_SEC = 2.0


# ---------------------------------------------------------------- history ----


class SafeFileHistory(FileHistory):
    """:class:`FileHistory` that strips invalid surrogate code points.

    Background:
        Windows terminals occasionally inject lone surrogate halves into
        pasted Unicode (emoji, mixed-script CJK). prompt_toolkit's default
        ``store_string`` writes the line straight to disk using the
        system encoding, which raises ``UnicodeEncodeError`` and corrupts
        the history file. This subclass round-trips the string through
        ``utf-16-le`` with ``surrogatepass`` and then back to a sanitised
        string before delegating to the parent implementation.

    The cleanup is safe to run on every line — sanitised input that
    contains only valid code points round-trips unchanged.
    """

    def store_string(self, string: str) -> None:  # type: ignore[override]
        super().store_string(_strip_surrogates(string))


def _strip_surrogates(text: str) -> str:
    """Drop unpaired surrogate code points from ``text``."""
    try:
        round_tripped = text.encode("utf-16-le", "surrogatepass").decode(
            "utf-16-le", "replace"
        )
    except UnicodeError:
        return "".join(ch for ch in text if not 0xD800 <= ord(ch) <= 0xDFFF)
    cleaned = round_tripped.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return cleaned.replace("�", "")


# ---------------------------------------------------------------- session ----


class _VibePromptSession(PromptSession):
    """PromptSession with a prompt-height that hugs the edited text."""

    def _create_layout(self):  # type: ignore[no-untyped-def]
        layout = super()._create_layout()
        # prompt_toolkit's bottom_toolbar is a screen-bottom status bar. Insert
        # our divider directly after the input container so it hugs the prompt.
        layout.container.children.insert(1, _prompt_divider_window())
        return layout

    def _get_default_buffer_control_height(self) -> Dimension:  # type: ignore[override]
        line_count = self.default_buffer.document.line_count
        return Dimension.exact(max(1, line_count))


def _prompt_divider_window() -> Window:
    return Window(
        FormattedTextControl(
            lambda: FormattedText([("class:prompt-border", _prompt_rule())])
        ),
        height=1,
        style="class:prompt-border",
        dont_extend_height=True,
    )


def _force_utf8_stdout() -> None:
    """Reconfigure stdout to UTF-8 on Windows so brand glyphs render."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                # Best-effort — a redirected pipe may refuse encoding swaps.
                pass


def _has_unbalanced_brackets(text: str) -> bool:
    """Return True if ``text`` contains unbalanced ``()``/``[]``/``{}`` pairs.

    Used to decide whether a plain Enter should submit or insert a
    newline. Strings inside ``"..."`` / ``'...'`` are skipped so a user
    typing ``"hello (world)"`` does not get stuck in multi-line mode.
    """
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    openers = set(pairs.values())
    in_str: Optional[str] = None
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if in_str is not None:
            if ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"'):
            in_str = ch
            continue
        if ch in openers:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return True
            stack.pop()
    return bool(stack) or in_str is not None


class _CtrlCState:
    """Track Ctrl+C presses so the outer loop can implement two-press exit.

    Attributes:
        previous_press_ts: Monotonic timestamp of the press *before* the
            most recent one. ``0.0`` means "no prior press".
        last_window_hit: Set by :meth:`record_press_and_check_window` —
            ``True`` iff the press that just landed was inside the
            configured window relative to ``previous_press_ts``. Cached
            so :func:`ctrl_c_within_window` does not re-read the clock
            and decide independently of the keybinding.

    The two-press semantics live here (not in the outer loop) because
    the keybinding fires *before* the EOFError propagates, and we want
    the outer loop's view of "are we inside the window?" to reflect the
    decision made at the exact press moment — not whatever ``time.monotonic()``
    reads a few microseconds later.
    """

    __slots__ = ("previous_press_ts", "last_window_hit")

    def __init__(self) -> None:
        self.previous_press_ts: float = 0.0
        self.last_window_hit: bool = False

    def record_press_and_check_window(self, window_sec: float = _EXIT_HINT_GAP_SEC) -> bool:
        """Record the current press, return True iff inside the window.

        Args:
            window_sec: Two-press window in seconds.

        Returns:
            ``False`` for the very first press (``previous_press_ts == 0``).
            ``True`` if the gap between the prior press and this one is
            below ``window_sec``. Otherwise ``False`` (treated as a fresh
            first press for the next round).
        """
        now = time.monotonic()
        prev = self.previous_press_ts
        self.previous_press_ts = now
        if prev == 0.0:
            self.last_window_hit = False
            return False
        hit = (now - prev) < window_sec
        self.last_window_hit = hit
        return hit


def _build_keybindings(state: _CtrlCState) -> KeyBindings:
    """Wire Ctrl+C + multi-line submit semantics.

    State machine (idle / typing):

        Ctrl+C with text     → clear the buffer and stay at the prompt
        Ctrl+C empty (first) → exit with ``EOFError``; caller prints hint
                                and records the press timestamp.
        Ctrl+C empty (twice) → caller sees the timestamp inside 2 s and
                                actually exits the loop.

        Enter on balanced buffer    → submit
        Enter on unbalanced buffer  → insert newline
        Alt-Enter / Esc-Enter       → insert newline unconditionally
    """
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event) -> None:  # noqa: ANN001 — prompt_toolkit event
        buf = event.app.current_buffer
        if buf.text:
            buf.reset()
            event.app.invalidate()
            return
        # Empty buffer → record the press (this updates the state so the
        # outer loop's two-press check has the right prior timestamp) and
        # propagate EOF so the outer loop can decide whether to print the
        # exit hint or actually exit.
        state.record_press_and_check_window(_EXIT_HINT_GAP_SEC)
        event.app.exit(exception=EOFError())

    @kb.add("enter")
    def _(event) -> None:  # noqa: ANN001
        buf = event.app.current_buffer
        text = buf.text
        if _has_unbalanced_brackets(text):
            buf.insert_text("\n")
            return
        buf.validate_and_handle()

    # Alt+Enter / Esc-Enter — unconditional newline.
    @kb.add("escape", "enter")
    def _(event) -> None:  # noqa: ANN001
        event.app.current_buffer.insert_text("\n")

    return kb


def _default_history_path() -> Path:
    """Where ``~/.vibe-trading/history`` lives by default."""
    home = Path.home() / ".vibe-trading"
    return home / "history"


def make_session(history_path: Optional[Path] = None) -> PromptSession:
    """Construct a configured :class:`PromptSession`.

    Args:
        history_path: Override for the persistent history file. ``None``
            uses ``~/.vibe-trading/history``.

    Returns:
        A ready-to-use ``PromptSession`` wired to the slash completer,
        Ctrl+C bindings, multi-line editing, and a surrogate-safe
        history file. The session exposes ``vibe_ctrl_c_state`` on the
        returned object so callers can implement the two-press exit
        confirmation.
    """
    _force_utf8_stdout()

    path = history_path or _default_history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Touch the file so FileHistory's first read does not fail on a fresh
    # install.
    if not path.exists():
        path.touch(mode=0o600)

    # Lazy import so unit tests can import this module without instantiating
    # the slash registry side-effects.
    from cli.completer import SlashCompleter

    ctrl_c_state = _CtrlCState()
    session = _VibePromptSession(
        history=SafeFileHistory(str(path)),
        completer=SlashCompleter(),
        complete_while_typing=True,
        key_bindings=_build_keybindings(ctrl_c_state),
        enable_history_search=True,
        mouse_support=False,
        multiline=True,
        reserve_space_for_menu=0,
        style=Style.from_dict(
            {
                "prompt": "#258bff bold",
                "prompt-border": "#4b5563",
            }
        ),
    )
    # Expose the state so the outer loop can implement two-press exit.
    setattr(session, "vibe_ctrl_c_state", ctrl_c_state)
    return session


# ---------------------------------------------------------------- helpers ----


def get_user_input(
    prompt_message: str = "❯ ",
    *,
    session: Optional[PromptSession] = None,
) -> str:
    """Prompt the user with the configured session and return the input.

    Convenience for one-shot callers. Reuses ``session`` when supplied so
    the persistent history and completer carry across calls — otherwise
    a fresh session is built (and torn down).

    Raises:
        EOFError: When the user hits Ctrl+D, or Ctrl+C on an empty line.
    """
    sess = session or make_session()
    formatted = FormattedText(
        [
            ("class:prompt-border", _prompt_rule() + "\n"),
            ("class:prompt", prompt_message),
        ]
    )
    return sess.prompt(formatted)


def _prompt_rule() -> str:
    cols = shutil.get_terminal_size((88, 24)).columns
    return "─" * max(10, cols)


def ctrl_c_within_window(session: PromptSession, window_sec: float = _EXIT_HINT_GAP_SEC) -> bool:
    """Return True if the most recent Ctrl+C press was a "second press".

    A "second press" means the user pressed Ctrl+C twice within
    ``window_sec`` on an empty buffer — that's the signal to actually
    exit. The decision is made at *press time* by
    :meth:`_CtrlCState.record_press_and_check_window` and cached on the
    state object; the outer loop reads the cached flag here.

    Falls back to a timestamp comparison against ``previous_press_ts``
    for two cases:

    * ``SimpleNamespace`` test doubles that set ``last_press_ts`` directly
      (legacy test fixtures predate the two-timestamp design).
    * ``vibe_ctrl_c_state`` being absent entirely (defensive — returns
      ``False`` so the caller treats it as "no exit").

    Args:
        session: The active prompt_toolkit session (or a duck-typed
            stand-in exposing ``vibe_ctrl_c_state``).
        window_sec: Window length in seconds. Only used by the fallback
            paths described above; the primary path trusts the cached
            ``last_window_hit`` already computed against the configured
            window.

    Returns:
        ``True`` iff the loop should now exit.
    """
    state = getattr(session, "vibe_ctrl_c_state", None)
    if state is None:
        return False
    # Primary path — the keybinding cached the press-time decision.
    if hasattr(state, "last_window_hit"):
        return bool(state.last_window_hit)
    # Legacy fallback for test doubles that only set ``last_press_ts``.
    last_ts = getattr(state, "last_press_ts", 0.0)
    if last_ts <= 0.0:
        return False
    return (time.monotonic() - last_ts) < window_sec


__all__ = [
    "SafeFileHistory",
    "make_session",
    "get_user_input",
    "ctrl_c_within_window",
]
