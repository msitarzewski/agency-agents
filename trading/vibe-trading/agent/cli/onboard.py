"""First-launch onboarding wizard.

Triggered automatically when ``~/.vibe-trading/.env`` does not exist. Five
back-steppable steps (provider → model → key → timeout → optional Tushare),
matching §3.2 of the 2026-05-19 UI/UX design proposal.

Each step persists immediately to ``~/.vibe-trading/.env.partial`` and the
file is atomically renamed to ``.env`` only on completion, so a crash mid-
wizard never leaves a corrupt ``.env`` behind. API key entry is masked.

Prefers ``questionary`` when available; otherwise drives prompt_toolkit
directly so Esc / Left-arrow can be bound to a back-step sentinel.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Sequence

from rich.console import Console
from rich.text import Text

from cli.theme import Theme, get_console

# Sentinels for back-navigation / cancel returned by selectors.
BACK = object()
CANCEL = object()


# ---------------------------------------------------------------------------
# Provider catalogue — mirrors _PROVIDER_CHOICES in cli/_legacy.py
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Provider:
    """One selectable LLM provider option shown in step 1."""

    key: str
    label: str
    description: str
    default_model: str
    key_env: str | None
    base_env: str
    base_url: str
    key_prefix: str | None
    suggested_models: tuple[str, ...]


PROVIDERS: Final[tuple[Provider, ...]] = (
    Provider("openrouter", "OpenRouter", "recommended — 200+ models, one key",
             "deepseek/deepseek-v4-pro",
             "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL",
             "https://openrouter.ai/api/v1", "sk-or-",
             ("deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-flash",
              "openai/gpt-5.5-pro", "google/gemini-3.5-flash")),
    Provider("openai", "OpenAI", "GPT-5.5 direct",
             "gpt-5.5", "OPENAI_API_KEY", "OPENAI_BASE_URL",
             "https://api.openai.com/v1", "sk-",
             ("gpt-5.5", "gpt-5.5-pro", "gpt-5.5-instant")),
    Provider("deepseek", "DeepSeek",
             "cheapest tier — good for batch backtest research",
             "deepseek-v4-pro", "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL",
             "https://api.deepseek.com/v1", "sk-",
             ("deepseek-v4-pro", "deepseek-v4-flash")),
    Provider("ollama", "Ollama", "local, free, no API key",
             "qwen2.5:32b", None, "OLLAMA_BASE_URL",
             "http://localhost:11434", None,
             ("qwen2.5:32b", "llama3.3:70b", "deepseek-r1:14b")),
)

TIMEOUT_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    ("2400", "2400s (4 minutes — research mode, recommended)"),
    ("600", "600s (10 minutes — large backtests / swarm runs)"),
    ("120", "120s (2 minutes — quick lookup mode)"),
)


# ---------------------------------------------------------------------------
# Filesystem helpers (atomic partial save → final rename)
# ---------------------------------------------------------------------------


def _env_dir() -> Path: return Path.home() / ".vibe-trading"
def _env_path() -> Path: return _env_dir() / ".env"
def _partial_path() -> Path: return _env_dir() / ".env.partial"


def _render_env(values: dict[str, str]) -> str:
    """Render values as a stable ``.env`` body (KEY=value lines)."""
    return "\n".join(f"{k}={v}" for k, v in values.items() if v) + "\n"


def _save_partial(values: dict[str, str]) -> None:
    """Best-effort write to ``.env.partial`` (crash-resilience nicety)."""
    try:
        _env_dir().mkdir(parents=True, exist_ok=True)
        _partial_path().write_text(_render_env(values), encoding="utf-8")
        try:
            _partial_path().chmod(0o600)
        except OSError:
            pass
    except OSError:
        pass


def _finalize(values: dict[str, str]) -> Path:
    """Atomically write ``.env``. Returns the final path."""
    _env_dir().mkdir(parents=True, exist_ok=True)
    content = _render_env(values)
    fd, tmp_name = tempfile.mkstemp(prefix=".env.", dir=str(_env_dir()))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        tmp_path = Path(tmp_name)
        try:
            tmp_path.chmod(0o600)
        except OSError:
            pass
        tmp_path.replace(_env_path())
    finally:
        try:
            Path(tmp_name).unlink()
        except (FileNotFoundError, OSError):
            pass
    try:
        _partial_path().unlink()
    except (FileNotFoundError, OSError):
        pass
    return _env_path()


# ---------------------------------------------------------------------------
# Selector with back-step (custom prompt_toolkit Application)
# ---------------------------------------------------------------------------


def _select_with_back(prompt: str, choices: Sequence[tuple[str, str]], *,
                       default_index: int = 0,
                       console: Console | None = None) -> str | object:
    """Vertically-scrollable selector. Returns chosen value, BACK, or CANCEL.

    Keybindings: ↑/↓ navigate, Enter confirm, Esc/← back, Ctrl+C cancel.
    Falls back to a numeric stdin prompt if prompt_toolkit is unavailable.
    """
    cons = console or get_console()
    cons.print()
    cons.print(Text(f"? {prompt}", style=Theme.label))

    try:
        from prompt_toolkit import Application
        from prompt_toolkit.formatted_text import FormattedText
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import HSplit, Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style as PTStyle
    except ImportError:
        return _select_numeric(choices, default_index, cons)

    state = {"index": max(0, min(default_index, len(choices) - 1)), "result": None}

    def _format() -> FormattedText:
        out: list[tuple[str, str]] = []
        for i, (_, label) in enumerate(choices):
            if i == state["index"]:
                out.append(("class:cursor", "  > "))
                out.append(("class:selected", f"{label}\n"))
            else:
                out.append(("", "    "))
                out.append(("class:option", f"{label}\n"))
        out.append(("class:hint",
                    "\n  ↑/↓ navigate · Enter select · Esc/← back · Ctrl+C cancel"))
        return FormattedText(out)

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("c-p")
    def _(event):  # type: ignore[no-redef]
        state["index"] = (state["index"] - 1) % len(choices)
        event.app.invalidate()

    @kb.add("down")
    @kb.add("c-n")
    def _(event):  # type: ignore[no-redef]
        state["index"] = (state["index"] + 1) % len(choices)
        event.app.invalidate()

    @kb.add("enter")
    def _(event):  # type: ignore[no-redef]
        state["result"] = choices[state["index"]][0]
        event.app.exit()

    @kb.add("escape", eager=True)
    @kb.add("left")
    def _(event):  # type: ignore[no-redef]
        state["result"] = BACK
        event.app.exit()

    @kb.add("c-c")
    @kb.add("c-d")
    def _(event):  # type: ignore[no-redef]
        state["result"] = CANCEL
        event.app.exit()

    style = PTStyle.from_dict({
        "cursor": f"{Theme.brand_hex} bold",
        "selected": f"{Theme.brand_hex} bold",
        "option": "",
        "hint": "#808080",
    })
    layout = Layout(HSplit([Window(FormattedTextControl(_format), wrap_lines=False)]))
    app: Application = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)
    try:
        app.run()
    except (EOFError, KeyboardInterrupt):
        return CANCEL
    return state["result"] if state["result"] is not None else CANCEL


def _select_numeric(choices: Sequence[tuple[str, str]], default_index: int,
                     console: Console) -> str | object:
    """Stdin-only fallback selector."""
    for i, (_, label) in enumerate(choices, start=1):
        marker = ">" if (i - 1) == default_index else " "
        console.print(f"  {marker} [{i}] {label}", style=Theme.muted)
    console.print(Text("  (type number, b=back, q=cancel)", style=Theme.muted))
    try:
        raw = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return CANCEL
    if raw in {"b", "back"}:
        return BACK
    if raw in {"q", "quit", "cancel"}:
        return CANCEL
    if not raw:
        return choices[default_index][0]
    try:
        idx = int(raw)
        if 1 <= idx <= len(choices):
            return choices[idx - 1][0]
    except ValueError:
        pass
    console.print(Text("  invalid selection, try again", style=Theme.danger))
    return _select_numeric(choices, default_index, console)


# ---------------------------------------------------------------------------
# Masked / plain prompts
# ---------------------------------------------------------------------------


def _prompt_secret(prompt: str, *, console: Console) -> str | object:
    """Read a masked secret. Returns string, BACK, or CANCEL."""
    console.print()
    console.print(Text(f"? {prompt}", style=Theme.label))
    console.print(Text(
        "  (input hidden · Enter to submit · Esc to go back · Ctrl+C to cancel)",
        style=Theme.muted,
    ))
    try:
        from prompt_toolkit import prompt as pt_prompt
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()
        sentinel: dict[str, object] = {"action": None}

        @kb.add("escape", eager=True)
        def _(event):  # type: ignore[no-redef]
            sentinel["action"] = BACK
            event.app.exit(result="")

        try:
            value = pt_prompt("> ", is_password=True, key_bindings=kb)
        except (EOFError, KeyboardInterrupt):
            return CANCEL
        if sentinel["action"] is BACK:
            return BACK
        return value.strip()
    except ImportError:
        import getpass
        try:
            return getpass.getpass("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return CANCEL


def _prompt_text(prompt: str, *, default: str = "",
                  console: Console) -> str | object:
    """Read a plain string. Returns string, BACK, or CANCEL."""
    console.print()
    console.print(Text(f"? {prompt}", style=Theme.label))
    if default:
        console.print(Text(f"  (Enter for default: {default} · Esc to go back)",
                            style=Theme.muted))
    else:
        console.print(Text("  (Enter to skip · Esc to go back)", style=Theme.muted))

    try:
        from prompt_toolkit import prompt as pt_prompt
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()
        sentinel: dict[str, object] = {"action": None}

        @kb.add("escape", eager=True)
        def _(event):  # type: ignore[no-redef]
            sentinel["action"] = BACK
            event.app.exit(result="")

        try:
            value = pt_prompt("> ", key_bindings=kb)
        except (EOFError, KeyboardInterrupt):
            return CANCEL
        if sentinel["action"] is BACK:
            return BACK
        v = value.strip()
        return v if v else default
    except ImportError:
        try:
            raw = input("> ").strip()
            return raw if raw else default
        except (EOFError, KeyboardInterrupt):
            return CANCEL


# ---------------------------------------------------------------------------
# Wizard
# ---------------------------------------------------------------------------


def _validate_key(provider: Provider, key: str) -> str | None:
    """Return error message or None if key looks plausible."""
    if not key:
        return "API key cannot be empty."
    if provider.key_prefix and not key.startswith(provider.key_prefix):
        return f"Expected key to start with '{provider.key_prefix}'."
    if len(key) < 12:
        return "That key looks too short."
    return None


def _intro_header(console: Console) -> None:
    console.print()
    console.print(Text("  Vibe-Trading setup", style=Theme.primary))
    console.print(Text(
        "  We didn't find a config at ~/.vibe-trading/.env.\n"
        "  Let's set up in under a minute.",
        style=Theme.muted,
    ))


def run_onboarding(*, console: Console | None = None) -> Path | None:
    """Run the 5-step wizard. Returns the written ``.env`` path or None.

    Returns ``None`` when the user cancels (Ctrl+C / Esc at step 1) so the
    caller can exit cleanly without writing a partial config.
    """
    cons = console or get_console()
    _intro_header(cons)

    values: dict[str, str] = {"LANGCHAIN_TEMPERATURE": "0.0", "MAX_RETRIES": "2"}
    state: dict[str, object] = {"provider": None, "model": None, "key": None}

    def step_provider() -> object:
        choices = [(p.key, f"{p.label:<14}  {p.description}") for p in PROVIDERS]
        result = _select_with_back("Pick a model provider", choices,
                                    default_index=0, console=cons)
        if result is BACK or result is CANCEL:
            return result
        provider = next(p for p in PROVIDERS if p.key == result)
        state["provider"] = provider
        values["LANGCHAIN_PROVIDER"] = provider.key
        values[provider.base_env] = provider.base_url
        _save_partial(values)
        return "ok"

    def step_model() -> object:
        provider: Provider = state["provider"]  # type: ignore[assignment]
        choices: list[tuple[str, str]] = [
            (m, f"{m}{' (default)' if m == provider.default_model else ''}")
            for m in provider.suggested_models
        ]
        choices.append(("__custom__", "other (type custom model id)"))
        default_idx = next(
            (i for i, (v, _) in enumerate(choices) if v == provider.default_model),
            0,
        )
        choice = _select_with_back("Pick a model", choices,
                                    default_index=default_idx, console=cons)
        if choice is BACK or choice is CANCEL:
            return choice
        if choice == "__custom__":
            custom = _prompt_text("Type the model id",
                                   default=provider.default_model, console=cons)
            if custom is BACK or custom is CANCEL:
                return custom
            model = str(custom) or provider.default_model
        else:
            model = str(choice)
        state["model"] = model
        values["LANGCHAIN_MODEL_NAME"] = model
        _save_partial(values)
        return "ok"

    def step_key() -> object:
        provider: Provider = state["provider"]  # type: ignore[assignment]
        if provider.key_env is None:
            cons.print()
            cons.print(Text("  Ollama runs locally — no API key needed.",
                             style=Theme.success))
            return "ok"
        while True:
            key = _prompt_secret(
                f"Paste your {provider.label} API key "
                "(saved to ~/.vibe-trading/.env, never logged)",
                console=cons,
            )
            if key is BACK or key is CANCEL:
                return key
            err = _validate_key(provider, str(key))
            if err is None:
                state["key"] = key
                values[provider.key_env] = str(key)
                _save_partial(values)
                return "ok"
            cons.print(Text(f"  {err}  Try again, or press Esc to go back.",
                             style=Theme.danger))

    def step_timeout() -> object:
        choice = _select_with_back("Default request timeout",
                                    list(TIMEOUT_CHOICES),
                                    default_index=0, console=cons)
        if choice is BACK or choice is CANCEL:
            return choice
        values["TIMEOUT_SECONDS"] = str(choice)
        _save_partial(values)
        return "ok"

    def step_tushare() -> object:
        choices = [
            ("__skip__", "No, skip (most users)"),
            ("__paste__", "Yes — paste my Tushare token"),
        ]
        decision = _select_with_back(
            "Enable Tushare for China A-share data? (optional)",
            choices, default_index=0, console=cons,
        )
        if decision is BACK or decision is CANCEL:
            return decision
        if decision == "__paste__":
            token = _prompt_secret("Tushare token", console=cons)
            if token is BACK or token is CANCEL:
                return token
            if str(token).strip():
                values["TUSHARE_TOKEN"] = str(token).strip()
                _save_partial(values)
        return "ok"

    steps: list[Callable[[], object]] = [
        step_provider, step_model, step_key, step_timeout, step_tushare,
    ]

    i = 0
    while i < len(steps):
        result = steps[i]()
        if result is CANCEL:
            cons.print()
            cons.print(Text("  Setup cancelled. No config written.",
                             style=Theme.warning))
            return None
        if result is BACK:
            if i == 0:
                cons.print()
                cons.print(Text("  Setup cancelled. No config written.",
                                 style=Theme.warning))
                return None
            i -= 1
            continue
        i += 1

    final_path = _finalize(values)

    cons.print()
    cons.print(Text(f"  ✓ Wrote {final_path}", style=Theme.success))
    cons.print()

    tour = _select_with_back(
        "Want a quick tour? (or jump straight in)",
        [("__skip__", "Skip — drop me in chat"),
         ("__tour__", "Show me a 30-second sample run")],
        default_index=0, console=cons,
    )
    if tour == "__tour__":
        cons.print()
        cons.print(Text(
            "  Tip: try `analyze AAPL last 30 days` as your first prompt.\n"
            "  Type /help any time to see all commands.",
            style=Theme.muted,
        ))

    return final_path


__all__ = ["run_onboarding", "PROVIDERS", "Provider", "BACK", "CANCEL"]
