#!/usr/bin/env python3
"""Vibe-Trading CLI for natural-language finance research and backtesting.

Usage:
    vibe-trading                           Interactive mode (default)
    vibe-trading -p "Backtest AAPL MACD"   Single run
    vibe-trading serve --port 8899         Start API server
    vibe-trading chat                      Interactive mode
    vibe-trading list                      List runs
    vibe-trading show <run_id>             Show run details
"""

from __future__ import annotations

# ruff: noqa: E402

import argparse
import csv
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import warnings
warnings.filterwarnings("ignore", message=".*Importing verbose from langchain.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

for _s in ("stdout", "stderr"):
    _r = getattr(getattr(sys, _s, None), "reconfigure", None)
    if callable(_r):
        _r(encoding="utf-8", errors="replace")

from rich import box
from rich.columns import Columns
from rich.live import Live
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from cli.theme import get_console

console = get_console()
AGENT_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = AGENT_DIR / "runs"
SWARM_DIR = AGENT_DIR / ".swarm" / "runs"
SESSIONS_DIR = AGENT_DIR / "sessions"
UPLOADS_DIR = AGENT_DIR / "uploads"

EXIT_SUCCESS = 0
EXIT_RUN_FAILED = 1
EXIT_USAGE_ERROR = 2
RICH_TAG_PATTERN = re.compile(r"\[/?[^\]]+\]")

from cli._version import __version__ as _VERSION  # noqa: E402 — single source of truth

if TYPE_CHECKING:
    from src.agent.loop import AgentLoop

# Agent color assignments for swarm display
_AGENT_STYLES = ["cyan", "magenta", "green", "yellow", "blue", "bright_red", "bright_cyan", "bright_magenta"]
_agent_color_map: dict[str, str] = {}

_HAS_PROMPT_TOOLKIT = False
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.history import InMemoryHistory

    _HAS_PROMPT_TOOLKIT = True
except ImportError:
    pass


class _SessionStats:
    """Mutable container for interactive session statistics.

    Shared between the status bar renderer and the agent loop so that
    tool callbacks can update counters in-place.
    """

    __slots__ = ("session_start", "last_elapsed", "total_tool_ms", "tool_count")

    def __init__(self, session_start: float) -> None:
        self.session_start = session_start
        self.last_elapsed: Optional[float] = None
        self.total_tool_ms = 0
        self.tool_count = 0


def _build_status_parts(stats: _SessionStats) -> list[str]:
    """Build plain-text status bar segments.

    Args:
        stats: Session statistics.

    Returns:
        List of status text segments.
    """
    provider = os.getenv("LANGCHAIN_PROVIDER", "")
    model = os.getenv("LANGCHAIN_MODEL_NAME", "")
    model_short = model.split("/")[-1] if "/" in model else model
    label = f"{provider}/{model_short}" if provider else model_short or "unknown"

    session_s = int(time.monotonic() - stats.session_start)
    mins, secs = divmod(session_s, 60)
    session_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"

    parts = [label, session_str]

    if stats.last_elapsed is not None:
        parts.append(f"last {stats.last_elapsed:.1f}s")

    if stats.tool_count > 0:
        total_s = stats.total_tool_ms / 1000
        parts.append(f"{stats.tool_count} tools ({total_s:.1f}s)")

    return parts


def _ptk_toolbar(stats: _SessionStats) -> FormattedText:
    """prompt_toolkit bottom_toolbar callback — called on every render.

    Args:
        stats: Session statistics.

    Returns:
        FormattedText for the toolbar.
    """
    segments = _build_status_parts(stats)
    text = " │ ".join(segments)
    return FormattedText([("class:bottom-toolbar.text", f" {text} ")])


def _print_status_bar(stats: _SessionStats) -> None:
    """Print a static status bar using Rich (fallback without prompt_toolkit).

    Args:
        stats: Session statistics.
    """
    parts = _build_status_parts(stats)
    bar = "[dim] │ [/dim]".join(
        f"[bold]{parts[0]}[/bold]" if i == 0 else p for i, p in enumerate(parts)
    )
    console.print(bar)


def _create_prompt_session(stats: _SessionStats) -> Any:
    """Create a prompt_toolkit PromptSession with history and live toolbar.

    Args:
        stats: Session statistics for the live bottom toolbar.

    Returns:
        A PromptSession instance, or None if prompt_toolkit is not available.
    """
    if not _HAS_PROMPT_TOOLKIT:
        return None
    return PromptSession(
        history=InMemoryHistory(),
        bottom_toolbar=lambda: _ptk_toolbar(stats),
        refresh_interval=1.0,
    )


def _read_input(prompt_session: Any, prompt_str: str = "> ") -> str:
    """Read user input with arrow key support if prompt_toolkit is available.

    Falls back to Rich Prompt.ask() when prompt_toolkit is not installed or
    when stdin is not a tty.

    Args:
        prompt_session: A prompt_toolkit PromptSession, or None.
        prompt_str: Prompt text to display.

    Returns:
        User input string (not stripped).

    Raises:
        EOFError: When the user presses Ctrl-D.
        KeyboardInterrupt: When the user presses Ctrl-C.
    """
    if prompt_session is not None and sys.stdin.isatty():
        return prompt_session.prompt(prompt_str)
    return Prompt.ask(f"[bold]{prompt_str}[/bold]")


def serve_main(argv: list[str] | None = None) -> int:
    """Delegate server startup to api_server."""
    from api_server import serve_main as api_serve_main

    return api_serve_main(argv)


def _strip_rich_tags(text: str) -> str:
    """Remove Rich markup from plain-text output."""
    return RICH_TAG_PATTERN.sub("", text)


def _print_json_result(result: dict) -> None:
    """Print a machine-readable run summary."""
    payload = {
        "status": result.get("status", "unknown"),
        "run_id": result.get("run_id"),
        "run_dir": result.get("run_dir"),
        "reason": result.get("reason"),
    }
    print(json.dumps(payload, ensure_ascii=False))


def _result_exit_code(result: dict) -> int:
    """Map run results to stable exit codes."""
    return EXIT_SUCCESS if result.get("status") == "success" else EXIT_RUN_FAILED


def _coerce_exit_code(value: Optional[int]) -> int:
    """Normalize command return values to an integer exit code."""
    return EXIT_SUCCESS if value is None else int(value)


def _read_prompt_source(
    prompt: Optional[str],
    prompt_file: Optional[Path],
    *,
    no_rich: bool,
    allow_interactive: bool = True,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve prompt text from CLI args, file, stdin, or interactive input."""
    if prompt is not None:
        return prompt.strip(), None

    if prompt_file is not None:
        try:
            return prompt_file.read_text(encoding="utf-8").strip(), None
        except OSError as exc:
            return None, f"Failed to read prompt file: {exc}"

    if not sys.stdin.isatty():
        return sys.stdin.read().strip(), None

    if not allow_interactive:
        return None, "A prompt is required."

    try:
        if no_rich:
            return input("Enter strategy request: ").strip(), None
        return Prompt.ask("Enter strategy request").strip(), None
    except (EOFError, KeyboardInterrupt):
        return None, "Prompt input cancelled."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    """Safely read JSON."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_metrics(path: Path) -> dict:
    """Read metrics from metrics.csv, return formatted string dict."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return {}
        out = {}
        for k, v in rows[0].items():
            if not v:
                continue
            try:
                fv = float(v)
                out[k] = f"{fv:.4f}" if abs(fv) < 100 else f"{fv:.0f}"
            except ValueError:
                out[k] = v
        return out
    except Exception:
        return {}


def _status_style(status: str) -> str:
    """Return a consistent Rich color for status labels."""
    return {
        "success": "green",
        "completed": "green",
        "ready": "green",
        "running": "cyan",
        "failed": "red",
        "error": "red",
        "cancelled": "yellow",
        "warning": "yellow",
    }.get((status or "").lower(), "dim")


def _format_seconds(seconds: float) -> str:
    """Format elapsed seconds for compact terminal display."""
    total = max(0, int(seconds))
    mins, secs = divmod(total, 60)
    if mins >= 60:
        hours, mins = divmod(mins, 60)
        return f"{hours:d}h {mins:02d}m"
    if mins:
        return f"{mins:d}m {secs:02d}s"
    return f"{secs:d}s"


def _configured_label(value: str | None) -> str:
    """Render a masked configuration state."""
    return "[green]configured[/green]" if value else "[yellow]not set[/yellow]"


def _state_badge(value: str | None, *, ready_label: str = "READY") -> str:
    """Render a compact terminal status badge."""
    return f"[black on green] {ready_label} [/]" if value else "[black on yellow] MISSING [/]"


def _terminal_width() -> int:
    """Return the active console width with a conservative fallback."""
    try:
        return max(40, int(console.size.width))
    except Exception:
        return 80


def _ensure_cli_env() -> None:
    """Load dotenv values before rendering CLI-only settings."""
    try:
        from src.providers.llm import _ensure_dotenv

        _ensure_dotenv()
    except Exception:
        pass


def _provider_key_env(provider: str | None) -> str | None:
    """Return the credential environment variable for a provider."""
    return {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "zhipu": "ZHIPU_API_KEY",
        "moonshot": "MOONSHOT_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "mimo": "MIMO_API_KEY",
        "zai": "ZAI_API_KEY",
    }.get((provider or "").lower())


def _provider_base_env(provider: str | None) -> str | None:
    """Return the base URL environment variable for a provider."""
    return {
        "openrouter": "OPENROUTER_BASE_URL",
        "openai": "OPENAI_BASE_URL",
        "openai-codex": "OPENAI_CODEX_BASE_URL",
        "deepseek": "DEEPSEEK_BASE_URL",
        "gemini": "GEMINI_BASE_URL",
        "groq": "GROQ_BASE_URL",
        "dashscope": "DASHSCOPE_BASE_URL",
        "qwen": "DASHSCOPE_BASE_URL",
        "zhipu": "ZHIPU_BASE_URL",
        "moonshot": "MOONSHOT_BASE_URL",
        "minimax": "MINIMAX_BASE_URL",
        "mimo": "MIMO_BASE_URL",
        "zai": "ZAI_BASE_URL",
        "ollama": "OLLAMA_BASE_URL",
    }.get((provider or "").lower())


def _clip_inline(text: str, limit: int) -> str:
    """Collapse whitespace and clip text for single-line terminal cells."""
    clipped = " ".join(str(text or "").split())
    if len(clipped) <= limit:
        return clipped
    return clipped[: max(0, limit - 3)] + "..."


def _fit_cell(text: str, width: int) -> str:
    """Clip and pad text to an exact display cell width."""
    width = max(1, width)
    return _clip_inline(text, width).ljust(width)


def _styled_line(parts: list[tuple[str, int | None, str]]) -> Text:
    """Build one fixed-width line with per-cell styling."""
    line = Text()
    for value, width, style in parts:
        rendered = value if width is None else _fit_cell(value, width)
        line.append(rendered, style=style)
    return line


def _stack_text(lines: list[Text]) -> Text:
    """Join Text lines while preserving segment styles."""
    out = Text()
    for idx, line in enumerate(lines):
        if idx:
            out.append("\n")
        out.append_text(line)
    return out


def _welcome_widths(term_width: int) -> dict[str, int]:
    """Calculate welcome-screen column widths from the terminal width."""
    content_width = max(34, term_width - 8)
    label = 10
    right_label = 10
    right_value = 8
    gap = 2 if term_width < 86 else 4
    left_value = max(10, content_width - label - gap - right_label - right_value)

    command_gap = 2 if term_width < 86 else 6
    pair_width = max(20, (content_width - command_gap) // 2)
    action = min(16, max(12, pair_width // 2))
    use = max(7, pair_width - action - 1)

    return {
        "content": content_width,
        "label": label,
        "left_value": left_value,
        "gap": gap,
        "right_label": right_label,
        "right_value": right_value,
        "action": action,
        "use": use,
        "command_gap": command_gap,
    }


def _metric_value_style(key: str, value: str) -> str:
    """Return a compact color style for numeric metric values."""
    if key in {"total_return", "sharpe", "excess_return", "information_ratio"}:
        try:
            return "green" if float(value) >= 0 else "red"
        except (TypeError, ValueError):
            return "white"
    if key == "max_drawdown":
        return "yellow"
    return "white"


_SPINNER_GLYPHS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class _RunDashboard:
    """Render a compact live view for a single agent run."""

    def __init__(self, prompt: str, max_iter: int) -> None:
        self.prompt = prompt
        self.max_iter = max_iter
        self.start_time = time.monotonic()
        self.iterations = 0
        self.current_tool = "thinking"
        self.current_args = ""
        self.latest_text = ""
        self.timeline: list[tuple[str, str, str, float, str]] = []
        self.status = "running"
        self.live: Optional[Live] = None
        # Per-tool live feedback keyed by tool name. Supports parallel
        # readonly batches (loop._execute_parallel runs up to 8 tools in
        # ThreadPoolExecutor and each gets its own HeartbeatTimer). Each
        # entry: {start_ts, elapsed_s, stage, current, total, message,
        # prev_stage, stage_started_at}.
        self.tool_active: dict[str, dict[str, Any]] = {}
        self._spinner_idx = 0
        self._last_progress_render: float = 0.0

    def refresh(self) -> None:
        """Refresh the live display when attached to a Rich Live context."""
        if self.live is not None:
            self.live.update(self.render())

    def _ensure_entry(self, tool: str) -> dict[str, Any]:
        """Return the active per-tool entry, creating it on first use."""
        entry = self.tool_active.get(tool)
        if entry is None:
            entry = {
                "start_ts": time.monotonic(),
                "elapsed_s": 0.0,
                "stage": "",
                "current": None,
                "total": None,
                "message": "",
                "prev_stage": None,
                "stage_started_at": time.monotonic(),
            }
            self.tool_active[tool] = entry
        return entry

    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Update the dashboard from AgentLoop UI events."""
        if event_type == "text_delta":
            delta = data.get("delta", "")
            if delta:
                self.latest_text = (self.latest_text + delta).strip()[-260:]
                self.refresh()
            return

        if event_type == "thinking_done":
            self.current_tool = "thinking"
            self.current_args = ""
            self.refresh()
            return

        if event_type == "tool_call":
            tool = data.get("tool", "")
            args = data.get("arguments", {})
            self.iterations += 1
            self.current_tool = tool or "tool"
            self.current_args = _strip_rich_tags(_format_tool_call_args(tool, args)).strip()
            # If the prior timeline row is still "running" with no active
            # entry in self.tool_active (i.e. its HeartbeatTimer is gone but
            # no tool_result arrived), downgrade it to a warning (H2). Skip
            # this when a parallel batch is still in flight — sibling tools
            # legitimately remain "running" while a new call lands.
            if self.timeline and self.timeline[-1][0] == "running":
                prev_status, prev_tool, prev_args, _prev_el, _prev_pre = self.timeline[-1]
                if prev_tool not in self.tool_active:
                    self.timeline[-1] = (
                        "warning",
                        prev_tool,
                        prev_args,
                        0.0,
                        "no result event",
                    )
            # Reset per-tool state on each call (handles repeat invocations).
            now = time.monotonic()
            self.tool_active[self.current_tool] = {
                "start_ts": now,
                "elapsed_s": 0.0,
                "stage": "",
                "current": None,
                "total": None,
                "message": "",
                "prev_stage": None,
                "stage_started_at": now,
            }
            self.timeline.append(("running", self.current_tool, self.current_args, 0.0, ""))
            self.timeline = self.timeline[-8:]
            self.refresh()
            return

        if event_type == "tool_heartbeat":
            # Keepalive while a long tool runs. Updates elapsed in-place.
            tool = data.get("tool") or self.current_tool
            entry = self._ensure_entry(tool)
            entry["elapsed_s"] = float(data.get("elapsed_s", 0) or 0)
            self.refresh()
            return

        if event_type == "tool_progress":
            # Structured stage/current/total emitted from the tool.
            tool = data.get("tool") or self.current_tool
            entry = self._ensure_entry(tool)
            stage = str(data.get("stage", "") or "")
            if stage and stage != entry.get("stage"):
                entry["prev_stage"] = entry.get("stage") or None
                entry["stage_started_at"] = time.monotonic()
            entry["stage"] = stage
            entry["current"] = data.get("current")
            entry["total"] = data.get("total")
            entry["message"] = str(data.get("message", "") or "")
            elapsed = data.get("elapsed_s")
            if elapsed is not None:
                entry["elapsed_s"] = float(elapsed)
            # Throttle redraws so a chatty tool can't peg the renderer (M1).
            now = time.monotonic()
            if now - self._last_progress_render >= 0.25:
                self._last_progress_render = now
                self.refresh()
            return

        if event_type == "tool_result":
            tool = data.get("tool", self.current_tool)
            status = data.get("status", "ok")
            elapsed_s = float(data.get("elapsed_ms", 0) or 0) / 1000
            preview = _strip_rich_tags(_format_tool_result_preview(tool, status, data.get("preview", "")))
            row_status = "success" if status == "ok" else "failed"
            # Find the matching running row for this tool (may not be the last
            # row when tools run in parallel).
            matched = False
            for idx in range(len(self.timeline) - 1, -1, -1):
                row = self.timeline[idx]
                if row[0] == "running" and row[1] == tool:
                    self.timeline[idx] = (row_status, tool, row[2], elapsed_s, preview)
                    matched = True
                    break
            if not matched:
                self.timeline.append((row_status, tool, "", elapsed_s, preview))
            self.timeline = self.timeline[-8:]
            # Drop the per-tool entry so it disappears from the active list.
            self.tool_active.pop(tool, None)
            if not self.tool_active:
                self.current_tool = "thinking"
                self.current_args = ""
            self.refresh()
            return

        if event_type == "compact":
            tokens = data.get("tokens_before", "?")
            self.timeline.append(("warning", "context", "", 0.0, f"compressed after {tokens} tokens"))
            self.timeline = self.timeline[-8:]
            self.refresh()

    def _render_progress_row(
        self,
        tool: str,
        entry: Dict[str, Any],
        spinner: str,
        bar_width: int,
        compact: bool,
        detail_width: int,
    ) -> str:
        """Render a single active-tool progress row for the Current grid."""
        stage = str(entry.get("stage") or "")
        current_val = entry.get("current")
        total_val = entry.get("total")
        message = str(entry.get("message") or "")
        elapsed_s = float(entry.get("elapsed_s") or 0.0)
        has_count = (
            isinstance(current_val, int)
            and isinstance(total_val, int)
            and total_val > 0
        )
        has_structured = bool(stage or has_count or message)
        if not has_structured and elapsed_s <= 0:
            return ""
        if not has_structured:
            # Heartbeat-only fallback. No bar, no decimal precision (L4).
            plain = f"{spinner} {tool} · still running… {elapsed_s:.0f}s elapsed"
            return f"[dim]{_clip_inline(plain, detail_width)}[/dim]"
        # Build a plain prefix + dim suffix so markup survives clipping.
        prefix_plain_parts: list[str] = [spinner]
        prefix_styled_parts: list[str] = [f"[cyan]{spinner}[/cyan]"]
        if stage:
            prefix_plain_parts.append(stage)
            prefix_styled_parts.append(f"[bold cyan]{stage}[/bold cyan]")
        if has_count:
            filled = max(0, min(bar_width, int(bar_width * current_val / total_val)))
            bar = "#" * filled + "-" * (bar_width - filled)
            prefix_plain_parts.append(f"[{bar}]")
            prefix_styled_parts.append(f"[cyan]\\[{bar}][/cyan]")
            count_str = f"{current_val}/{total_val}"
            prefix_plain_parts.append(count_str)
            prefix_styled_parts.append(f"[cyan]{count_str}[/cyan]")
        else:
            prefix_plain_parts.append(f"{elapsed_s:.1f}s")
            prefix_styled_parts.append(f"[cyan]{elapsed_s:.1f}s[/cyan]")
        prefix_plain = " ".join(prefix_plain_parts)
        prefix_styled = " ".join(prefix_styled_parts)
        suffix_plain_parts: list[str] = []
        if message:
            suffix_plain_parts.append(f"· {message}")
        # ETA: only when count is known, we're past ~10% and at least 3 units,
        # and the stage hasn't just changed (L1). Suppressed in compact mode.
        if has_count and not compact and current_val >= 3 and current_val >= total_val * 0.1:
            stage_started_at = entry.get("stage_started_at")
            prev_stage = entry.get("prev_stage")
            stable_stage = (
                prev_stage is None
                or (
                    stage_started_at is not None
                    and (time.monotonic() - float(stage_started_at)) >= 1.0
                )
            )
            if stable_stage and elapsed_s > 0:
                try:
                    eta = (elapsed_s / current_val) * (total_val - current_val)
                except ZeroDivisionError:
                    eta = 0.0
                if eta > 0 and eta == eta:  # NaN check
                    suffix_plain_parts.append(f"· ~{eta:.0f}s left")
        suffix_plain = " ".join(suffix_plain_parts)
        # Clip the dim suffix to whatever space is left after the prefix.
        remaining = max(0, detail_width - len(prefix_plain) - 1)
        if suffix_plain and remaining > 4:
            clipped_suffix = _clip_inline(suffix_plain, remaining)
            return f"{prefix_styled} [dim]{clipped_suffix}[/dim]"
        return prefix_styled

    def render(self) -> Panel:
        """Build the Rich renderable shown while the run is active."""
        term_width = _terminal_width()
        compact = term_width < 86
        content_width = max(32, term_width - (6 if compact else 10))
        elapsed = _format_seconds(time.monotonic() - self.start_time)
        prompt_preview = _clip_inline(self.prompt, min(96, max(22, content_width - 12)))

        meta = Table.grid(expand=True)
        meta.add_column(ratio=1)
        progress = min(1.0, self.iterations / max(1, self.max_iter))
        bar_width = 12 if compact else 20
        filled = max(1, int(progress * bar_width)) if self.iterations else 0
        bar = "#" * filled + "-" * (bar_width - filled)
        progress_text = f"[cyan]{elapsed}[/cyan]  [dim]{bar} {self.iterations}/{self.max_iter}[/dim]"
        if compact:
            meta.add_row("[bold cyan]Running agent[/bold cyan]")
            meta.add_row(progress_text)
            meta.add_row(f"[dim]Request: {prompt_preview}[/dim]")
        else:
            meta.add_column(justify="right")
            meta.add_row("[bold cyan]Running agent[/bold cyan]", progress_text)
            meta.add_row(f"[dim]Request: {prompt_preview}[/dim]", "")

        current = Table.grid(expand=True)
        current.add_column(width=8 if compact else 9, style="dim")
        current.add_column(ratio=1)
        tool_label = self.current_tool
        if self.current_args:
            tool_label = f"{tool_label} [dim]{_clip_inline(self.current_args, max(20, content_width - 18))}[/dim]"
        current.add_row("Current", f"[cyan]{tool_label}[/cyan]")
        # One row per active tool (caps at 3 to keep dashboard height bounded).
        # Snapshot via list(...) first: Rich's refresh thread calls render()
        # concurrently with heartbeat/worker threads mutating self.tool_active,
        # so a bare ``.items()`` would race and may raise "dictionary changed
        # size during iteration". list() materialization is GIL-atomic.
        active_entries = sorted(
            list(self.tool_active.items()), key=lambda kv: kv[1].get("start_ts", 0.0)
        )
        if len(active_entries) > 3:
            active_entries = active_entries[:3]
        # Advance the spinner once per render so all active rows step together.
        self._spinner_idx = (self._spinner_idx + 1) % len(_SPINNER_GLYPHS)
        spinner = _SPINNER_GLYPHS[self._spinner_idx]
        bar_width = 6 if compact else 8
        detail_width = max(20, content_width - 18)
        for tool, entry in active_entries:
            row_text = self._render_progress_row(
                tool, entry, spinner, bar_width, compact, detail_width
            )
            if row_text:
                current.add_row("Progress", row_text)

        timeline = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="dim",
            padding=(0, 1),
            expand=True,
        )
        timeline.add_column("State", width=7 if compact else 8, no_wrap=True)
        timeline.add_column("Tool", width=12 if compact else 20, no_wrap=True)
        timeline.add_column("Time", width=6 if compact else 8, justify="right")
        timeline.add_column("Detail", ratio=1, overflow="fold")
        rows = self.timeline[-6:] or [("running", "waiting", "", 0.0, "starting")]
        for status, tool, args, elapsed_s, preview in rows:
            style = _status_style(status)
            label = "running" if status == "running" else ("ok" if status == "success" else "check")
            detail = _clip_inline(preview or args, max(18, content_width - (35 if compact else 48)))
            timeline.add_row(
                f"[{style}]{label}[/{style}]",
                _clip_inline(tool, 12 if compact else 20),
                f"{elapsed_s:.1f}s" if elapsed_s else "",
                detail,
            )

        latest = self.latest_text.replace("\n", " ").strip()
        latest = _clip_inline(latest[-220:], max(24, content_width - 4))
        body = Table.grid(expand=True)
        body.add_row(meta)
        body.add_row("")
        body.add_row(current)
        body.add_row("")
        body.add_row(timeline)
        if latest:
            body.add_row("")
            body.add_row(Panel(Text(latest, style="dim"), title="Latest answer", border_style="dim", padding=(0, 1)))

        return Panel(body, title="Vibe-Trading", border_style="cyan", padding=(1, 1 if compact else 2))


from cli.ui.rail import RailRunDashboard as _RunDashboard  # noqa: E402,F811


# ---------------------------------------------------------------------------
# Agent execution core
# ---------------------------------------------------------------------------

def _format_tool_call_args(tool: str, args: Dict[str, str]) -> str:
    """Smart-format tool argument summary."""
    if tool == "load_skill":
        return f'("{args.get("name", "")}")'
    if tool in ("write_file", "read_file", "edit_file"):
        return f' {args.get("path", args.get("file_path", ""))}'
    if tool in ("bash", "background_run"):
        cmd = args.get("command", "")[:80]
        return f' [yellow]{cmd}[/yellow]'
    if tool == "check_background":
        tid = args.get("task_id", "")
        return f' {tid}' if tid else ""
    if tool in ("backtest", "compact"):
        return ""
    for v in args.values():
        if v and v != "None":
            return f" {v[:60]}"
    return ""


def _format_tool_result_preview(tool: str, status: str, preview: str) -> str:
    """Smart-format tool result preview."""
    if status != "ok":
        return f"[red]{preview[:80]}[/red]"
    if tool == "backtest":
        sharpe = re.search(r'"sharpe":\s*([\d.eE+-]+)', preview)
        ret = re.search(r'"total_return":\s*([\d.eE+-]+)', preview)
        parts = []
        if sharpe:
            parts.append(f"sharpe={sharpe.group(1)}")
        if ret:
            parts.append(f"return={float(ret.group(1))*100:.1f}%")
        return ", ".join(parts) if parts else ""
    if tool == "render_shadow_report":
        url = re.search(r'"report_url":\s*"([^"]+)"', preview)
        if url:
            return f"[bold cyan]report:[/bold cyan] [link]{url.group(1)}[/link]"
        return ""
    if tool in ("extract_shadow_strategy", "run_shadow_backtest"):
        sid = re.search(r'"shadow_id":\s*"([^"]+)"', preview)
        return f"shadow_id={sid.group(1)}" if sid else ""
    if tool in ("bash", "background_run"):
        if "OK" in preview[:50]:
            return "OK"
        return preview[:60].replace("\n", " ")
    if tool in ("read_file", "load_skill", "compact"):
        return ""
    return ""


# ---------------------------------------------------------------------------
# In-process mandate.proposal relay (CLI mirror of api_server's
# _mandate_proposal_frame_from_tool_result, SPEC.md Consent §1/§2)
# ---------------------------------------------------------------------------
#
# The agent loop emits the propose tool's output only as a generic
# ``tool_result`` event (``loop.py`` ``_finalize_tool_result`` → preview =
# result[:200]); it NEVER emits a top-level ``mandate.proposal`` event. So in
# the in-process REPL path nothing ever arms ``ctx.pending_proposal`` and the
# user's numeric pick falls through to the model as chat. The frontend solved
# the same gap server-side by relaying the propose-tool ``tool_result`` into a
# top-level ``mandate.proposal`` SSE frame (api_server
# ``_mandate_proposal_frame_from_tool_result``). The CLI needs the identical
# relay in its own ``on_event`` handler — done below, WITHOUT touching the
# protected ``loop.py``.

_PROPOSAL_TOOL_NAME = "propose_mandate_profiles"
_PROPOSAL_ID_RE = re.compile(r'"proposal_id"\s*:\s*"(mp_[0-9a-f]{32})"')


def _load_full_proposal(proposal_id: str) -> Optional[Dict[str, Any]]:
    """Reload a persisted ``mandate.proposal`` payload by id, broker-agnostic.

    The propose tool persists the full proposal under
    ``<runtime_root>/live/<broker>/proposals/<proposal_id>.json`` before
    returning. The ``tool_result`` preview is only the first 200 chars of the
    JSON body, far too short to carry the full proposal, so the relay reloads it
    from disk. The broker segment is unknown from the preview alone, so every
    broker's proposals directory is searched (mirrors api_server).

    Args:
        proposal_id: The ``mp_...`` id parsed from the tool_result preview.

    Returns:
        The full proposal dict, or ``None`` when not found / unreadable.
    """
    try:
        from src.live.paths import live_root

        for proposal_path in live_root().glob(f"*/proposals/{proposal_id}.json"):
            try:
                data = json.loads(proposal_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("type") == "mandate.proposal":
                return data
    except Exception:  # noqa: BLE001 — relay must never break the turn
        pass
    return None


def _mandate_proposal_from_tool_result(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recover a full ``mandate.proposal`` payload from a propose-tool result.

    Detection mirrors api_server's ``_mandate_proposal_frame_from_tool_result``:
    the event must be a successful ``tool_result`` for ``propose_mandate_profiles``
    whose preview carries a ``proposal_id``. The full proposal is then reloaded
    from disk (the preview is truncated).

    Args:
        data: The ``tool_result`` event payload (``tool`` / ``status`` /
            ``preview``).

    Returns:
        The full proposal dict ready to feed ``proposal_sink`` (arming
        ``ctx.pending_proposal``), or ``None`` when this is not a recoverable
        propose-tool result.
    """
    if data.get("tool") != _PROPOSAL_TOOL_NAME or data.get("status") != "ok":
        return None
    match = _PROPOSAL_ID_RE.search(str(data.get("preview") or ""))
    if not match:
        return None
    return _load_full_proposal(match.group(1))


def _run_agent(
    prompt: str,
    history: Optional[List[Dict]] = None,
    run_dir_override: Optional[str] = None,
    max_iter: int = 50,
    *,
    no_rich: bool = False,
    stream_output: bool = True,
    dashboard: Optional[_RunDashboard] = None,
    session_id: str = "",
    proposal_sink: Optional[Any] = None,
) -> dict:
    """Build AgentLoop and execute, return result dict.

    Args:
        proposal_sink: Optional callable invoked with the payload of every
            ``mandate.proposal`` event the agent emits. The interactive REPL
            uses this to capture an outstanding live-trading mandate proposal so
            it can intercept the user's numeric pick *before* the model — a pick
            is a privileged surface action (commit), never a tool the model can
            call (SPEC.md Consent §2).
    """
    from src.tools import build_registry
    from src.providers.chat import ChatLLM
    from src.agent.loop import AgentLoop

    # Closure-level state for the no-rich path so dots and progress lines
    # don't shoulder-bump each other (M3) and progress prints are throttled
    # to ≤1/0.5s per tool (M1).
    no_rich_state: dict[str, Any] = {
        "dot_pending": False,
        "last_progress_ts": {},  # type: ignore[var-annotated]
    }

    def on_event(event_type: str, data: Dict[str, Any]) -> None:
        # Live mandate proposals are surfaced to the REPL out-of-band so the
        # user's pick is intercepted before the model (SPEC.md Consent §2).
        # This fires regardless of stream_output / rich state — capturing the
        # proposal must not depend on rendering.
        if event_type == "mandate.proposal" and proposal_sink is not None:
            try:
                proposal_sink(data)
            except Exception:  # noqa: BLE001 — capture must never kill the turn
                pass
            return
        # The agent loop never emits a top-level ``mandate.proposal`` — it only
        # emits the propose tool's output as a generic ``tool_result``. Relay it
        # here (CLI mirror of api_server's SSE relay) so the REPL arms
        # ``ctx.pending_proposal`` and intercepts the pick before the model
        # (SPEC.md Consent §1/§2). Fires regardless of stream_output / rich
        # state — arming must not depend on rendering — and does NOT return:
        # the tool_result still flows on to the dashboard / no-rich printers.
        if event_type == "tool_result" and proposal_sink is not None:
            proposal = _mandate_proposal_from_tool_result(data)
            if proposal is not None:
                try:
                    proposal_sink(proposal)
                except Exception:  # noqa: BLE001 — relay must never kill the turn
                    pass
        if not stream_output:
            return
        if dashboard is not None and not no_rich:
            dashboard.handle_event(event_type, data)
            return
        if no_rich and event_type == "thinking_done":
            print()
            return
        if no_rich and event_type == "tool_call":
            tool = data.get("tool", "")
            args = data.get("arguments", {})
            args_preview = _format_tool_call_args(tool, args)
            print(f"  - {tool}{_strip_rich_tags(args_preview)}", end="")
            no_rich_state["dot_pending"] = False
            return
        if no_rich and event_type == "tool_result":
            tool = data.get("tool", "")
            status = data.get("status", "ok")
            elapsed_ms = data.get("elapsed_ms", 0)
            elapsed_s = elapsed_ms / 1000
            preview = _format_tool_result_preview(tool, status, data.get("preview", ""))
            suffix = f"  {preview}" if preview else ""
            mark = "OK" if status == "ok" else "FAIL"
            # If a heartbeat dot is open on the line, break it cleanly.
            if no_rich_state["dot_pending"]:
                no_rich_state["dot_pending"] = False
            print(f"  {mark} {elapsed_s:.1f}s{_strip_rich_tags(suffix)}")
            no_rich_state["last_progress_ts"].pop(tool, None)
            return
        if no_rich and event_type == "compact":
            tokens = data.get("tokens_before", "?")
            if no_rich_state["dot_pending"]:
                no_rich_state["dot_pending"] = False
                print()
            print(f"\n  context compressed ({tokens} tokens -> summary)\n")
            return
        if no_rich and event_type == "tool_heartbeat":
            # Print a dot per tick so the user sees the tool is alive.
            print(".", end="", flush=True)
            no_rich_state["dot_pending"] = True
            return
        if no_rich and event_type == "tool_progress":
            tool = data.get("tool", "") or ""
            now = time.monotonic()
            last_ts = no_rich_state["last_progress_ts"].get(tool, 0.0)
            if now - last_ts < 0.5:
                # Throttle: max one progress line per 0.5s per tool (M1).
                return
            no_rich_state["last_progress_ts"][tool] = now
            stage = data.get("stage", "")
            current_idx = data.get("current")
            total = data.get("total")
            message = data.get("message", "")
            bits = [stage]
            if isinstance(current_idx, int) and isinstance(total, int) and total > 0:
                bits.append(f"{current_idx}/{total}")
            if message:
                bits.append(message)
            label = " · ".join(b for b in bits if b)
            if label:
                # Break a pending dot line before printing the progress detail.
                if no_rich_state["dot_pending"]:
                    no_rich_state["dot_pending"] = False
                    print()
                print(f"    {label}", flush=True)
            return
        if event_type == "text_delta":
            if no_rich:
                print(data.get("delta", ""), end="")
            else:
                console.print(data.get("delta", ""), end="", style="dim")
        elif event_type == "thinking_done":
            console.print()
        elif event_type == "tool_call":
            tool = data.get("tool", "")
            args = data.get("arguments", {})
            args_preview = _format_tool_call_args(tool, args)
            console.print(f"  [cyan]\u25b6 {tool}[/cyan]{args_preview}", end="")
        elif event_type == "tool_result":
            tool = data.get("tool", "")
            status = data.get("status", "ok")
            elapsed_ms = data.get("elapsed_ms", 0)
            elapsed_s = elapsed_ms / 1000
            ok = status == "ok"
            mark = "[green]\u2713[/green]" if ok else "[red]\u2717[/red]"
            preview = _format_tool_result_preview(tool, status, data.get("preview", ""))
            suffix = f"  {preview}" if preview else ""
            console.print(f"  {mark} [dim]{elapsed_s:.1f}s[/dim]{suffix}")
        elif event_type == "compact":
            tokens = data.get("tokens_before", "?")
            console.print(f"\n  [yellow]\u27f3 context compressed[/yellow] [dim]({tokens} tokens \u2192 summary)[/dim]\n")

    from src.memory.persistent import PersistentMemory

    pm = PersistentMemory()
    from src.config.loader import load_agent_config

    agent_config = load_agent_config()

    def _mcp_warn(msg: str) -> None:
        if no_rich:
            print(f"WARNING: {msg}", flush=True)
        else:
            console.print(f"[yellow]WARNING:[/yellow] {msg}")

    agent = AgentLoop(
        registry=build_registry(
            persistent_memory=pm,
            include_shell_tools=True,
            agent_config=agent_config,
            session_id=session_id or None,
            warn_callback=_mcp_warn,
        ),
        llm=ChatLLM(),
        event_callback=on_event,
        max_iterations=max_iter,
        persistent_memory=pm,
    )
    if run_dir_override:
        agent.memory.run_dir = run_dir_override

    return _run_with_graceful_cancel(
        agent,
        prompt,
        history,
        no_rich=no_rich,
        session_id=session_id,
    )


def _run_with_graceful_cancel(
    agent: "AgentLoop",
    prompt: str,
    history: Optional[List[Dict]],
    *,
    no_rich: bool,
    session_id: str = "",
) -> dict:
    """Run an agent loop with first-Ctrl+C = graceful cancel.

    First SIGINT during the run sets ``agent._cancelled`` so the loop exits
    cleanly after the current LLM/tool step finishes. A second SIGINT within
    two seconds restores the default handler and re-raises ``KeyboardInterrupt``
    for hard quit. Outside of a run the parent CLI's normal SIGINT handling
    (exit on input prompt) is unaffected — the handler is restored in
    ``finally``.

    Args:
        agent: AgentLoop instance ready to ``run()``.
        prompt: User prompt.
        history: Recent message history.
        no_rich: Whether the parent caller is rendering with Rich Live.

    Returns:
        AgentLoop result dict.
    """
    import signal as _signal

    state = {"requested": False, "last_ts": 0.0}
    try:
        original = _signal.getsignal(_signal.SIGINT)
    except (ValueError, AttributeError):
        # Not on a thread that can receive signals — skip the handler swap.
        return agent.run(user_message=prompt, history=history, session_id=session_id)

    def _on_sigint(_signum, _frame) -> None:
        now = time.time()
        if state["requested"] and (now - state["last_ts"]) < 2.0:
            # Second Ctrl+C within 2s — hand control back to the default handler.
            _signal.signal(_signal.SIGINT, original)
            raise KeyboardInterrupt
        state["requested"] = True
        state["last_ts"] = now
        agent.cancel()
        notice = "Cancelling… current step will finish, then exit. Ctrl+C again to force quit."
        if no_rich:
            print(f"\n[{notice}]", flush=True)
        else:
            console.print(f"\n[yellow]{notice}[/yellow]")

    try:
        _signal.signal(_signal.SIGINT, _on_sigint)
    except (ValueError, OSError):
        # signal.signal only works on the main thread of the main interpreter.
        return agent.run(user_message=prompt, history=history, session_id=session_id)

    try:
        return agent.run(user_message=prompt, history=history, session_id=session_id)
    finally:
        try:
            _signal.signal(_signal.SIGINT, original)
        except (ValueError, OSError):
            pass


def _build_benchmark_table(m: dict) -> Optional[Table]:
    """Build a benchmark comparison table from metrics dict.

    Args:
        m: Metrics dictionary (from _read_metrics or result dict).

    Returns:
        Rich Table, or None if no benchmark data is present.
    """
    bench_ticker  = m.get("benchmark_ticker")
    bench_ret_str = m.get("benchmark_return")
    bench_ret_raw = m.get("_benchmark_return_raw")

    # Fall back to equity.csv if benchmark cols not in metrics.csv yet
    if not bench_ticker:
        return None

    # Parse benchmark return
    if bench_ret_raw is not None:
        bench_ret = bench_ret_raw
    elif bench_ret_str is not None:
        try:
            bench_ret = float(bench_ret_str)
        except (ValueError, TypeError):
            bench_ret = None
    else:
        bench_ret = None

    strategy_ret_str = m.get("total_return")
    strategy_ret     = float(strategy_ret_str) if strategy_ret_str else None

    table = Table(show_header=False, padding=(0, 2))
    table.add_column("Label", style="dim", width=20)
    table.add_column("Value", style="white no_wrap")

    table.add_row("[dim]Benchmark[/dim]",  bench_ticker)

    if bench_ret is not None:
        table.add_row("[dim]Benchmark Return[/dim]", f"{bench_ret * 100:+.2f}%")

    if strategy_ret is not None and bench_ret is not None:
        excess = strategy_ret - bench_ret
        sign   = "+" if excess >= 0 else ""
        style  = "green" if excess >= 0 else "red"
        table.add_row(
            "[dim]vs Benchmark[/dim]",
            f"[{style}]{sign}{excess * 100:+.2f}%[/{style}]",
        )

    ir_str = m.get("information_ratio")
    if ir_str:
        table.add_row("[dim]Info Ratio[/dim]", ir_str)

    excess_str = m.get("excess_return")
    if excess_str and excess_str != "0" and excess_str != "0.0000":
        table.add_row("[dim]Excess Return[/dim]", f"{float(excess_str) * 100:+.2f}%")

    return table


def _print_result(result: dict, elapsed: float, *, no_rich: bool = False) -> None:
    """Print execution result panel."""
    status = result.get("status", "unknown")
    style = _status_style(status)
    run_dir = result.get("run_dir")
    m = _read_metrics(Path(run_dir) / "artifacts" / "metrics.csv") if run_dir else {}

    if no_rich:
        print(f"Status: {status.upper()}")
        print(f"Elapsed: {_format_seconds(elapsed)}")
        if result.get("run_id"):
            print(f"Run ID: {result['run_id']}")
        review = result.get("review")
        if review and review.get("overall_score") is not None:
            review_status = "PASS" if review.get("passed") else "FAIL"
            print(f"Review: {review_status} {review['overall_score']}pts")
        if run_dir:
            print(f"Run dir: {run_dir}")
        if result.get("reason"):
            print(f"Reason: {result['reason']}")
        metric_parts = [f"{label}={m[key]}" for key, label in (
            ("total_return", "return"),
            ("sharpe", "sharpe"),
            ("max_drawdown", "max_dd"),
            ("trade_count", "trades"),
        ) if key in m]
        if metric_parts:
            print(f"Metrics: {', '.join(metric_parts)}")
        content = result.get("content", "").strip()
        if content:
            print(f"\n{content}")
        return

    summary = Table.grid(expand=True)
    summary.add_column(width=12, style="dim")
    summary.add_column(ratio=1)
    summary.add_row("Status", f"[bold {style}]{status.upper()}[/bold {style}]")
    summary.add_row("Elapsed", _format_seconds(elapsed))
    if result.get("run_id"):
        summary.add_row("Run ID", f"[cyan]{result['run_id']}[/cyan]")
    review = result.get("review")
    if review and review.get("overall_score") is not None:
        review_status = "PASS" if review.get("passed") else "FAIL"
        review_style = "green" if review.get("passed") else "red"
        summary.add_row("Review", f"[{review_style}]{review_status}[/{review_style}] {review['overall_score']}pts")
    if run_dir:
        summary.add_row("Run dir", f"[dim]{run_dir}[/dim]")

    if result.get("reason"):
        summary.add_row("Reason", f"[red]{result['reason']}[/red]")

    panels = [Panel(summary, border_style=style, title="Summary", padding=(0, 1))]

    metric_table = Table.grid(expand=True)
    metric_table.add_column(width=12, style="dim")
    metric_table.add_column(ratio=1)
    has_metrics = False
    for key, label in (
        ("total_return", "Return"),
        ("sharpe", "Sharpe"),
        ("max_drawdown", "Max DD"),
        ("trade_count", "Trades"),
    ):
        if key not in m:
            continue
        value = m[key]
        value_style = _metric_value_style(key, value)
        metric_table.add_row(label, f"[{value_style}]{value}[/{value_style}]")
        has_metrics = True
    if has_metrics:
        panels.append(Panel(metric_table, border_style="cyan", title="Metrics", padding=(0, 1)))

    if result.get("run_id"):
        rid = result["run_id"]
        actions = Table(box=None, show_header=False, padding=(0, 1))
        actions.add_column(style="cyan", no_wrap=True)
        actions.add_column(style="dim")
        actions.add_row(f"vibe-trading show {rid}", "details")
        actions.add_row(f"vibe-trading code {rid}", "generated Python")
        actions.add_row(f"vibe-trading continue {rid} \"...\"", "refine this run")
        panels.append(Panel(actions, border_style="dim", title="Next", padding=(0, 1)))

    if _terminal_width() < 104:
        for panel in panels:
            console.print(panel)
    else:
        console.print(Columns(panels, expand=True, equal=True))

    # Benchmark comparison panel.
    bench_table = _build_benchmark_table(m)
    if bench_table:
        console.print(Panel(
            bench_table,
            border_style="cyan",
            title="Benchmark Comparison",
            padding=(0, 1),
        ))
    # End benchmark comparison panel.

    content = result.get("content", "").strip()
    if content:
        console.print(f"\n{content}")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_run(prompt: str, max_iter: int, *, json_mode: bool = False, no_rich: bool = False) -> int:
    """Single run."""
    if not json_mode:
        from src.preflight import run_preflight
        results = run_preflight(console)
        if any(r.critical and r.status != "ready" for r in results):
            return EXIT_RUN_FAILED

    if not json_mode:
        preview = prompt[:120]
        suffix = "..." if len(prompt) > 120 else ""
        if no_rich:
            print(f"Prompt: {preview}{suffix}\n")
        else:
            console.print(f"[dim]Prompt:[/dim] {preview}{suffix}\n")
    start = time.perf_counter()
    try:
        if json_mode or no_rich:
            result = _run_agent(prompt, max_iter=max_iter, no_rich=no_rich, stream_output=not json_mode)
        else:
            dashboard = _RunDashboard(prompt, max_iter)
            with Live(dashboard.render(), console=console, refresh_per_second=6, transient=True) as live:
                dashboard.live = live
                result = _run_agent(prompt, max_iter=max_iter, dashboard=dashboard)
                dashboard.finish(result, time.perf_counter() - start)
    except KeyboardInterrupt:
        if json_mode:
            _print_json_result({"status": "cancelled", "run_id": None, "run_dir": None, "reason": "Interrupted"})
            return EXIT_RUN_FAILED
        if no_rich:
            print("\nInterrupted")
            return EXIT_RUN_FAILED
        console.print("\n[yellow]Interrupted[/yellow]")
        return EXIT_RUN_FAILED
    if json_mode:
        _print_json_result(result)
        return _result_exit_code(result)
    _print_result(result, time.perf_counter() - start, no_rich=no_rich)
    if result.get("run_id"):
        tip = f"--show {result['run_id']}  |  --continue {result['run_id']} \"...\"  |  --code {result['run_id']}  |  --pine {result['run_id']}"
        if no_rich:
            print(tip)
        else:
            console.print(f"[dim]{tip}[/dim]")
    return _result_exit_code(result)


def _build_history_from_trace(run_dir: Path) -> List[Dict[str, str]]:
    """Build conversation history from trace.jsonl."""
    from src.agent.trace import TraceWriter

    trace_dir = TraceWriter.find_trace_dir(run_dir.name, runs_dir=RUNS_DIR, sessions_dir=SESSIONS_DIR)
    if trace_dir is None:
        return []
    entries = TraceWriter.read(
        trace_dir,
        resolve_offloads=True,
        resolve_fields={"prompt", "content"},
    )
    history: List[Dict[str, str]] = []
    for e in entries:
        if e.get("type") == "start" and e.get("prompt"):
            history.append({"role": "user", "content": e["prompt"]})
        elif e.get("type") == "answer" and e.get("content"):
            history.append({"role": "assistant", "content": e["content"]})
    return history


def cmd_continue(
    run_id: str,
    prompt: str,
    max_iter: int,
    *,
    json_mode: bool = False,
    no_rich: bool = False,
) -> int:
    """Continue an existing run."""
    run_dir = RUNS_DIR / run_id
    session_trace_dir = SESSIONS_DIR / run_id
    if not run_dir.exists() and not session_trace_dir.exists():
        if no_rich:
            print(f"Run {run_id} not found")
            return EXIT_USAGE_ERROR
        console.print(f"[red]Run {run_id} not found[/red]")
        return EXIT_USAGE_ERROR
    if not run_dir.exists():
        run_dir.mkdir(parents=True, exist_ok=True)

    history = _build_history_from_trace(run_dir)
    if not json_mode and no_rich:
        print(f"Continue {run_id}: {prompt[:120]}\n")
    if json_mode or no_rich:
        start = time.perf_counter()
        try:
            result = _run_agent(
                prompt,
                history=history,
                run_dir_override=str(run_dir),
                max_iter=max_iter,
                no_rich=no_rich,
                stream_output=not json_mode,
            )
        except KeyboardInterrupt:
            if json_mode:
                _print_json_result(
                    {"status": "cancelled", "run_id": run_id, "run_dir": str(run_dir), "reason": "Interrupted"}
                )
            else:
                print("\nInterrupted")
            return EXIT_RUN_FAILED
        if json_mode:
            _print_json_result(result)
            return _result_exit_code(result)
        _print_result(result, time.perf_counter() - start, no_rich=True)
        return _result_exit_code(result)

    console.print(f"[dim]Continue {run_id}:[/dim] {prompt[:120]}\n")
    start = time.perf_counter()
    try:
        dashboard = _RunDashboard(prompt, max_iter)
        with Live(dashboard.render(), console=console, refresh_per_second=6, transient=True) as live:
            dashboard.live = live
            result = _run_agent(
                prompt,
                history=history,
                run_dir_override=str(run_dir),
                max_iter=max_iter,
                dashboard=dashboard,
            )
            dashboard.finish(result, time.perf_counter() - start)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return EXIT_RUN_FAILED
    _print_result(result, time.perf_counter() - start)
    return _result_exit_code(result)


# ---------------------------------------------------------------------------
# Interactive mode (Welcome + Slash commands + Swarm streaming)
# ---------------------------------------------------------------------------

def _build_welcome_panel(term_width: Optional[int] = None) -> Panel:
    """Build the welcome screen for the given terminal width."""
    _ensure_cli_env()
    term_width = term_width or _terminal_width()
    compact = term_width < 64
    widths = _welcome_widths(term_width)
    provider = os.getenv("LANGCHAIN_PROVIDER", "(not set)")
    model = os.getenv("LANGCHAIN_MODEL_NAME", "(not set)")
    key_env = _provider_key_env(provider)
    key_value = os.getenv(key_env or "")
    credential_ready = provider in {"ollama", "openai-codex"} or bool(key_value)
    key_state = "READY" if credential_ready else "MISSING"
    recent_runs = len([d for d in RUNS_DIR.iterdir() if d.is_dir()]) if RUNS_DIR.exists() else 0
    recent_swarms = len([d for d in SWARM_DIR.iterdir() if d.is_dir()]) if SWARM_DIR.exists() else 0
    content_width = widths["content"]

    header_lines: list[Text] = []
    title = f"Vibe-Trading v{_VERSION}"
    subtitle = "finance agent CLI"
    if term_width < 78:
        header_lines.append(Text(title, style="bold cyan"))
        header_lines.append(Text(subtitle, style="dim"))
    else:
        header_lines.append(
            _styled_line(
                [
                    (title, content_width - len(subtitle), "bold cyan"),
                    (subtitle, None, "dim"),
                ]
            )
        )
    header_lines.append(Text(_clip_inline("Research, backtest, inspect runs, and coordinate swarm presets.", content_width), style="dim"))

    config_lines: list[Text] = []
    if compact:
        value_width = max(10, content_width - widths["label"] - 1)
        rows = [
            ("Provider", str(provider), "bold cyan"),
            ("Model", str(model), "white"),
            ("Credential", key_state, "bold green" if credential_ready else "bold yellow"),
            ("Runs", str(recent_runs), "cyan"),
            ("Swarms", str(recent_swarms), "cyan"),
            ("Workspace", str(AGENT_DIR), "dim"),
        ]
        for label, value, value_style in rows:
            config_lines.append(
                _styled_line(
                    [
                        (label, widths["label"], "dim"),
                        (" ", None, ""),
                        (value, value_width, value_style),
                    ]
                )
            )
    else:
        gap = " " * widths["gap"]
        rows = [
            ("Provider", str(provider), "bold cyan", "Credential", key_state, "bold green" if credential_ready else "bold yellow"),
            ("Model", str(model), "white", "Runs", str(recent_runs), "cyan"),
            ("Workspace", str(AGENT_DIR), "dim", "Swarms", str(recent_swarms), "cyan"),
        ]
        for left_label, left_value, left_style, right_label, right_value, right_style in rows:
            config_lines.append(
                _styled_line(
                    [
                        (left_label, widths["label"], "dim"),
                        (" ", None, ""),
                        (left_value, widths["left_value"], left_style),
                        (gap, None, ""),
                        (right_label, widths["right_label"], "dim"),
                        (" ", None, ""),
                        (right_value, widths["right_value"], right_style),
                    ]
                )
            )

    action_lines: list[Text] = []
    if compact:
        actions = [
            ("type a request", "start a run"),
            ("/settings", "check config"),
            ("/list", "recent runs"),
            ("/swarm", "team presets"),
            ("/help", "all commands"),
            ("/quit", "exit"),
        ]
        action_width = min(16, max(12, content_width // 2 - 1))
        use_width = max(8, content_width - action_width - 1)
        for action, use in actions:
            action_lines.append(
                _styled_line(
                    [
                        (action, action_width, "bold cyan"),
                        (" ", None, ""),
                        (use, use_width, "white"),
                    ]
                )
            )
    else:
        gap = " " * widths["command_gap"]
        rows = [
            ("type a request", "start a run", "/settings", "check config"),
            ("/list", "recent runs", "/swarm", "team presets"),
            ("/help", "all commands", "/quit", "exit"),
        ]
        for left_action, left_use, right_action, right_use in rows:
            action_lines.append(
                _styled_line(
                    [
                        (left_action, widths["action"], "bold cyan"),
                        (" ", None, ""),
                        (left_use, widths["use"], "white"),
                        (gap, None, ""),
                        (right_action, widths["action"], "bold cyan"),
                        (" ", None, ""),
                        (right_use, widths["use"], "white"),
                    ]
                )
            )

    body = Table.grid(expand=True)
    body.add_row(_stack_text(header_lines))
    body.add_row("")
    body.add_row(
        Panel(
            _stack_text(config_lines),
            title="[bold green]Current Config[/bold green]",
            border_style="green" if credential_ready else "yellow",
            padding=(0, 1),
        )
    )
    body.add_row("")
    body.add_row(
        Panel(
            _stack_text(action_lines),
            title="[bold magenta]Actions[/bold magenta]",
            border_style="magenta",
            padding=(0, 1),
        )
    )
    body.add_row("")
    body.add_row(Text(_clip_inline("Example: analyze AAPL momentum with risk controls", content_width), style="dim"))

    return Panel(body, title="[bold cyan]Vibe-Trading[/bold cyan]", border_style="cyan", padding=(1, 1))


def _print_welcome() -> None:
    """Print the welcome screen."""
    console.print(_build_welcome_panel())


def _print_help() -> None:
    """Print all available slash commands."""
    table = Table(title="Commands", show_lines=False, border_style="dim", box=box.SIMPLE_HEAVY)
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description")

    cmds = [
        ("/help", "Show this command list"),
        ("/skills", "List available trading skills"),
        ("/list", "List recent backtest and research runs"),
        ("/show <run_id>", "Open a compact run summary"),
        ("/code <run_id>", "Show generated Python"),
        ("/pine <run_id>", "Show exported Pine Script"),
        ("/trace <run_id>", "Replay tool calls and answer events"),
        ("/continue <run_id> <prompt>", "Refine an existing run"),
        ("/swarm", "List multi-agent team presets"),
        ("/swarm run <preset> {vars}", "Run a team preset"),
        ("/swarm inspect <preset>", "Inspect preset DAG and validation"),
        ("/swarm list", "List team run history"),
        ("/swarm show <run_id>", "Show a team run"),
        ("/swarm cancel <run_id>", "Cancel a team run"),
        ("/sessions", "List chat sessions"),
        ("/settings", "Show provider, model, timeout, and credentials"),
        ("/stop", "How to gracefully cancel a running agent"),
        ("/clear", "Clear the terminal"),
        ("/quit", "Exit"),
        ("", ""),
        ("[dim]Natural language[/dim]", ""),
        ('"analyze journal.csv"', "Parse a broker export and diagnose trading behavior"),
        ('"train my shadow"', "Extract a strategy, backtest it, and create a report"),
    ]
    for cmd, desc in cmds:
        table.add_row(cmd, desc)

    console.print(table)


def _show_settings() -> None:
    """Show current runtime settings."""
    _ensure_cli_env()
    term_width = _terminal_width()
    compact = term_width < 104
    value_limit = max(18, min(56, term_width - 28))
    provider = os.getenv("LANGCHAIN_PROVIDER", "(not set)")
    model = os.getenv("LANGCHAIN_MODEL_NAME", "(not set)")
    provider_key_env = _provider_key_env(provider)
    provider_base_env = _provider_base_env(provider)
    provider_key = os.getenv(provider_key_env or "")
    provider_base_url = os.getenv(provider_base_env or "") or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "(not set)"

    provider_table = Table.grid(expand=True)
    provider_table.add_column(width=12, style="dim")
    provider_table.add_column(ratio=1)
    provider_table.add_row("Provider", f"[bold]{provider}[/bold]")
    provider_table.add_row("Model", _clip_inline(model, value_limit))
    provider_table.add_row("Base URL", _clip_inline(provider_base_url, value_limit))

    runtime_table = Table.grid(expand=True)
    runtime_table.add_column(width=13, style="dim")
    runtime_table.add_column(ratio=1)
    runtime_table.add_row("Temperature", os.getenv("LANGCHAIN_TEMPERATURE", "0.0"))
    runtime_table.add_row("Timeout", os.getenv("TIMEOUT_SECONDS", "2400") + "s")
    runtime_table.add_row("Retries", os.getenv("MAX_RETRIES", "(not set)"))

    credential_table = Table.grid(expand=True)
    credential_table.add_column(width=21, style="dim")
    credential_table.add_column(ratio=1)

    if provider in {"ollama", "openai-codex"}:
        credential_table.add_row("Provider key", "[green]not required[/green]")
        credential_ready = True
    elif provider_key_env:
        credential_table.add_row(provider_key_env, "***" if provider_key else "(not set)")
        credential_ready = bool(provider_key)
    else:
        credential_table.add_row("Provider key", "(unknown provider)")
        credential_ready = False
    credential_table.add_row("TUSHARE_TOKEN", "***" if os.getenv("TUSHARE_TOKEN") else "(optional)")

    panels = [
        Panel(provider_table, title=f"Provider {_state_badge(provider if provider != '(not set)' else None)}", border_style="cyan", padding=(0, 1)),
        Panel(runtime_table, title="Runtime", border_style="dim", padding=(0, 1)),
        Panel(credential_table, title=f"Credentials {_state_badge('ok' if credential_ready else None)}", border_style="green" if credential_ready else "yellow", padding=(0, 1)),
    ]
    if compact:
        for panel in panels:
            console.print(panel)
    else:
        console.print(Columns(panels, expand=True, equal=True))
    console.print("[dim]Edit configuration in ~/.vibe-trading/.env, or run vibe-trading init.[/dim]")


def _handle_slash_command(input_str: str, *, max_iter: int) -> None:
    """Parse and route a slash command."""
    parts = input_str.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        _print_help()
    elif cmd == "/skills":
        cmd_skills()
    elif cmd == "/list":
        cmd_list()
    elif cmd == "/show":
        if arg:
            cmd_show(arg)
        else:
            console.print("[red]Usage: /show <run_id>[/red]")
    elif cmd == "/code":
        if arg:
            cmd_code(arg)
        else:
            console.print("[red]Usage: /code <run_id>[/red]")
    elif cmd == "/pine":
        if arg:
            cmd_pine(arg)
        else:
            console.print("[red]Usage: /pine <run_id>[/red]")
    elif cmd == "/trace":
        if arg:
            cmd_trace(arg)
        else:
            console.print("[red]Usage: /trace <run_id>[/red]")
    elif cmd == "/continue":
        cont_parts = arg.split(maxsplit=1)
        if len(cont_parts) >= 2:
            cmd_continue(cont_parts[0], cont_parts[1], max_iter)
        else:
            console.print("[red]Usage: /continue <run_id> <prompt>[/red]")
    elif cmd == "/swarm":
        _handle_swarm_command(arg)
    elif cmd == "/sessions":
        cmd_sessions()
    elif cmd == "/settings":
        _show_settings()
    elif cmd == "/stop":
        console.print(
            "[dim]No agent is running. Press [bold]Ctrl+C[/bold] during a run "
            "to gracefully cancel — the current step finishes, then the loop "
            "exits cleanly. Press Ctrl+C twice within 2 seconds to force quit.[/dim]"
        )
    elif cmd == "/clear":
        console.clear()
        _print_welcome()
    elif cmd in ("/quit", "/exit"):
        raise EOFError
    else:
        console.print(f"[red]Unknown command: {cmd}[/red] - type [cyan]/help[/cyan] for available commands")


def _handle_swarm_command(arg: str) -> None:
    """Route swarm sub-commands."""
    if not arg:
        cmd_swarm_presets()
        return

    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    sub_arg = parts[1].strip() if len(parts) > 1 else ""

    if sub == "run":
        run_parts = sub_arg.split(maxsplit=1)
        if not run_parts:
            console.print("[red]Usage: /swarm run <preset> [vars_json][/red]")
            return
        preset = run_parts[0]
        vars_json = run_parts[1] if len(run_parts) > 1 else None
        cmd_swarm_run_live(preset, vars_json)
    elif sub == "inspect":
        if sub_arg:
            cmd_swarm_inspect(sub_arg)
        else:
            console.print("[red]Usage: /swarm inspect <preset>[/red]")
    elif sub == "list":
        cmd_swarm_list()
    elif sub == "show":
        if sub_arg:
            cmd_swarm_show(sub_arg)
        else:
            console.print("[red]Usage: /swarm show <run_id>[/red]")
    elif sub == "cancel":
        if sub_arg:
            cmd_swarm_cancel(sub_arg)
        else:
            console.print("[red]Usage: /swarm cancel <run_id>[/red]")
    else:
        console.print(f"[red]Unknown swarm command: {sub}[/red]")


def cmd_interactive(max_iter: int) -> None:
    """Interactive mode with welcome screen, slash commands, and agent conversation."""
    _print_welcome()

    from src.preflight import run_preflight
    results = run_preflight(console)
    if any(r.critical and r.status != "ready" for r in results):
        return

    history: List[Dict[str, str]] = []
    stats = _SessionStats(session_start=time.monotonic())
    prompt_session = _create_prompt_session(stats)

    while True:
        if prompt_session is None:
            _print_status_bar(stats)
        try:
            user_input = _read_input(prompt_session).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input.lower() in ("q", "quit", "exit"):
            break

        # Slash commands
        if user_input.startswith("/"):
            try:
                _handle_slash_command(user_input, max_iter=max_iter)
            except EOFError:
                break
            continue

        # Natural language -> agent
        start = time.perf_counter()
        try:
            dashboard = _RunDashboard(user_input, max_iter)
            with Live(dashboard.render(), console=console, refresh_per_second=6, transient=True) as live:
                dashboard.live = live
                result = _run_agent(user_input, history=history[-6:], max_iter=max_iter, dashboard=dashboard)
                dashboard.finish(result, time.perf_counter() - start)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            continue
        stats.last_elapsed = time.perf_counter() - start
        stats.tool_count += dashboard.iterations
        _print_result(result, stats.last_elapsed)
        history.append({"role": "user", "content": user_input})
        if result.get("content"):
            history.append({"role": "assistant", "content": result["content"]})

    console.print("[dim]Goodbye[/dim]")


# ---------------------------------------------------------------------------
# Swarm live streaming (Rich Live panel)
# ---------------------------------------------------------------------------

def _get_agent_style(agent_id: str) -> str:
    """Assign a consistent color to each agent."""
    if agent_id not in _agent_color_map:
        idx = len(_agent_color_map) % len(_AGENT_STYLES)
        _agent_color_map[agent_id] = _AGENT_STYLES[idx]
    return _agent_color_map[agent_id]


class _SwarmDashboard:
    """Track swarm state and render a Rich Live panel."""

    def __init__(self, preset: str, run_id: str) -> None:
        self.preset = preset
        self.run_id = run_id
        self.start_time = time.monotonic()
        self.current_layer = 0
        self.total_layers = 0
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_order: List[str] = []
        self.completed_summaries: List[tuple[str, str]] = []
        self.finished = False
        self.final_status = ""

    def _ensure_agent(self, agent_id: str) -> str:
        """Register an agent by its ID if not already tracked. Return its key."""
        if agent_id in self.agents:
            return agent_id
        self.agents[agent_id] = {
            "name": agent_id, "status": "waiting",
            "tool": "\u2014", "elapsed": 0.0, "iters": 0,
            "started_at": 0.0, "layer": self.current_layer,
            "last_text": "",
        }
        self.agent_order.append(agent_id)
        return agent_id

    def handle_event(self, event) -> None:
        """Process a swarm event and update internal state."""
        agent_id = event.agent_id or ""
        etype = event.type
        data = event.data

        if etype == "layer_started":
            self.current_layer = data.get("layer", 0)
            self.total_layers = max(self.total_layers, self.current_layer + 1)
            return

        if etype == "run_completed":
            self.finished = True
            self.final_status = data.get("status", "unknown")
            return

        if not agent_id:
            return

        key = self._ensure_agent(agent_id)
        agent = self.agents[key]

        if etype == "task_started":
            agent["status"] = "running"
            agent["started_at"] = time.monotonic()
        elif etype == "tool_call":
            agent["tool"] = data.get("tool", "?")
            agent["iters"] += 1
        elif etype == "tool_result":
            agent["elapsed"] = (time.monotonic() - agent["started_at"]) if agent["started_at"] else 0
            tool_name = agent["tool"]
            status_char = "\u2713" if data.get("status", "ok") == "ok" else "\u2717"
            agent["tool"] = f"{tool_name} {status_char}"
        elif etype == "task_completed":
            agent["status"] = "done"
            agent["elapsed"] = (time.monotonic() - agent["started_at"]) if agent["started_at"] else 0
            agent["iters"] = data.get("iterations", agent["iters"])
            summary = data.get("summary", "")
            if summary:
                self.completed_summaries.append((agent["name"], summary))
        elif etype == "task_failed":
            agent["status"] = "failed"
            agent["elapsed"] = (time.monotonic() - agent["started_at"]) if agent["started_at"] else 0
            error = data.get("error", "")[:80]
            self.completed_summaries.append((agent["name"], f"[red]FAILED: {error}[/red]"))
        elif etype == "task_blocked":
            agent["status"] = "blocked"
            blocked_by = ", ".join(data.get("blocked_by", []))
            self.completed_summaries.append(
                (agent["name"], f"[yellow]BLOCKED by: {blocked_by}[/yellow]")
            )
        elif etype == "task_retry":
            attempt = data.get("attempt", "?")
            agent["status"] = "retry"
            agent["tool"] = f"retry {attempt}"
        elif etype == "worker_text":
            content = data.get("content", "").strip()
            if content:
                # Keep last non-empty line for display
                last_line = content.split("\n")[-1].strip()
                if last_line:
                    agent["last_text"] = last_line[:60]

    def build_table(self) -> Table:
        """Build the Rich Table for the live panel."""
        elapsed_total = time.monotonic() - self.start_time
        mins, secs = divmod(int(elapsed_total), 60)

        if self.finished:
            color = "green" if self.final_status == "completed" else "red"
            title_status = f"[{color}]{self.final_status.upper()}[/{color}]"
        else:
            title_status = "[cyan]RUNNING[/cyan]"

        title = f"{self.preset}  {title_status}  {mins}:{secs:02d}"

        table = Table(
            title=title,
            border_style="cyan" if not self.finished else ("green" if self.final_status == "completed" else "red"),
            show_lines=False,
            pad_edge=True,
            expand=True,
        )
        table.add_column("Agent", style="bold", width=20, no_wrap=True)
        table.add_column("Status", width=12, justify="center")
        table.add_column("Tool", width=14, no_wrap=True)
        table.add_column("Time", width=7, justify="right")
        table.add_column("Iters", width=5, justify="right")
        table.add_column("Output", no_wrap=True, style="dim")

        for agent_key in self.agent_order:
            agent = self.agents[agent_key]
            name = agent["name"]
            style = _get_agent_style(name)
            styled_name = f"[{style}]{name}[/{style}]"

            status = agent["status"]
            if status == "running":
                status_str = "[\u25b6 running]"
                elapsed = time.monotonic() - agent["started_at"] if agent["started_at"] else 0
            elif status == "done":
                status_str = "[green][\u2713 done  ][/green]"
                elapsed = agent["elapsed"]
            elif status == "failed":
                status_str = "[red][\u2717 failed][/red]"
                elapsed = agent["elapsed"]
            elif status == "retry":
                status_str = "[yellow][\u21bb retry ][/yellow]"
                elapsed = time.monotonic() - agent["started_at"] if agent["started_at"] else 0
            else:
                status_str = "[dim][\u25cb waiting][/dim]"
                elapsed = 0

            time_str = f"{elapsed:.1f}s" if elapsed > 0 else "\u2014"
            iter_str = str(agent["iters"]) if agent["iters"] > 0 else "\u2014"
            last_text = agent.get("last_text", "")

            table.add_row(styled_name, status_str, agent["tool"], time_str, iter_str, last_text)

        # Progress bar row
        done_count = sum(1 for a in self.agents.values() if a["status"] in ("done", "failed"))
        total_count = len(self.agents) or 1
        pct = int(done_count / total_count * 100)
        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = "\u2501" * filled + "[dim]" + "\u2501" * (bar_width - filled) + "[/dim]"

        if self.finished:
            bar_color = "green" if self.final_status == "completed" else "red"
            progress_label = f"[{bar_color}]{self.final_status.upper()}[/{bar_color}]"
        else:
            progress_label = f"Layer {self.current_layer}"

        table.add_section()
        table.add_row(
            progress_label,
            f"{bar}",
            f"[bold]{pct}%[/bold]",
            f"{mins}:{secs:02d}",
            "",
            "",
        )

        return table


def cmd_swarm_run_live(preset: str, vars_json: Optional[str] = None) -> None:
    """Run a swarm preset with Rich Live dashboard."""
    from rich.live import Live
    from src.config import load_swarm_agent_config
    from src.swarm.runtime import SwarmRuntime
    from src.swarm.store import SwarmStore
    from src.swarm.models import RunStatus

    user_vars: Dict[str, str] = {}
    if vars_json:
        try:
            user_vars = json.loads(vars_json)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON: {exc}[/red]")
            return

    store = SwarmStore(base_dir=SWARM_DIR)
    agent_config = load_swarm_agent_config()
    runtime = SwarmRuntime(store=store, agent_config=agent_config)
    _agent_color_map.clear()

    console.print(f"\n[dim]Starting swarm:[/dim] [cyan]{preset}[/cyan]")
    if user_vars:
        console.print(f"[dim]Variables:[/dim] {json.dumps(user_vars, ensure_ascii=False)}")

    dashboard = _SwarmDashboard(preset, "")

    try:
        run = runtime.start_run(
            preset,
            user_vars,
            live_callback=dashboard.handle_event,
            include_shell_tools=True,
        )
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        return
    except ValueError as exc:
        console.print(f"[red]DAG validation failed: {exc}[/red]")
        return

    dashboard.run_id = run.id

    with Live(dashboard.build_table(), console=console, refresh_per_second=4, transient=False) as live:
        try:
            while True:
                time.sleep(0.25)
                live.update(dashboard.build_table())
                current = store.load_run(run.id)
                if current is None:
                    console.print("[red]Run record lost[/red]")
                    return
                if current.status in (RunStatus.completed, RunStatus.failed, RunStatus.cancelled):
                    dashboard.finished = True
                    dashboard.final_status = current.status.value
                    live.update(dashboard.build_table())
                    break
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelling...[/yellow]")
            runtime.cancel_run(run.id)
            time.sleep(1)
            current = store.load_run(run.id)

    if current is None:
        return

    # Print completed agent summaries
    for agent_name, summary in dashboard.completed_summaries:
        style = _get_agent_style(agent_name)
        console.print(f"\n[{style}]\u2500\u2500 {agent_name} \u2500\u2500[/{style}]")
        # Truncate to first meaningful chunk
        lines = summary.strip().split("\n")
        preview = "\n".join(lines[:8])
        if len(lines) > 8:
            preview += "\n[dim]...[/dim]"
        console.print(preview)

    # Final report
    status_color = {
        RunStatus.completed: "green",
        RunStatus.failed: "red",
        RunStatus.cancelled: "yellow",
    }.get(current.status, "dim")

    elapsed_total = time.monotonic() - dashboard.start_time
    mins, secs = divmod(int(elapsed_total), 60)

    tokens_in = current.total_input_tokens
    tokens_out = current.total_output_tokens
    token_str = ""
    if tokens_in or tokens_out:
        token_str = f"\nTokens: ~{tokens_in + tokens_out:,} (in: {tokens_in:,} out: {tokens_out:,})"

    if current.final_report:
        console.print("\n[bold]\u2500\u2500 Final Report \u2500\u2500[/bold]")
        console.print(current.final_report[:2000])

    console.print(f"\n[{status_color}]{current.status.value.upper()}[/{status_color}]  Time: {mins}m {secs}s{token_str}")


# ---------------------------------------------------------------------------
# Legacy subcommands (used by flags and slash commands)
# ---------------------------------------------------------------------------

def cmd_chat(max_iter: int) -> None:
    """Interactive mode (delegates to cmd_interactive)."""
    cmd_interactive(max_iter)


def cmd_list(limit: int = 20) -> None:
    """List run history."""
    if not RUNS_DIR.exists():
        console.print("[dim]No runs yet[/dim]")
        return
    dirs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()], key=lambda d: d.name, reverse=True)[:limit]
    if not dirs:
        console.print("[dim]No runs yet[/dim]")
        return

    table = Table(title="Recent Runs", show_lines=False, border_style="dim", box=box.SIMPLE_HEAVY)
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Status", width=10)
    table.add_column("Return", width=10)
    table.add_column("Sharpe", width=8)
    table.add_column("Prompt", max_width=58)

    for d in dirs:
        st = _read_json(d / "state.json").get("status", "?")
        m = _read_metrics(d / "artifacts" / "metrics.csv")
        c = _status_style(st)
        prompt = (_read_json(d / "req.json").get("prompt") or "").replace("\n", " ")
        if len(prompt) > 58:
            prompt = prompt[:55] + "..."
        table.add_row(
            d.name,
            f"[{c}]{st.upper()}[/{c}]",
            m.get("total_return", ""),
            m.get("sharpe", ""),
            prompt,
        )

    console.print(table)
    console.print("[dim]Use /show <run_id>, /code <run_id>, or /continue <run_id> <prompt>.[/dim]")


def cmd_show(run_id: str) -> None:
    """Show run details."""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        console.print(f"[red]{run_id} not found[/red]")
        return

    state = _read_json(run_dir / "state.json")
    req = _read_json(run_dir / "req.json")
    metrics = _read_metrics(run_dir / "artifacts" / "metrics.csv")

    st = state.get("status", "unknown")
    c = _status_style(st)
    lines = [f"[bold]Status:[/bold] [{c}]{st.upper()}[/{c}]"]
    if req.get("prompt"):
        lines.append(f"[bold]Prompt:[/bold] {req['prompt'][:500]}{'...' if len(req['prompt']) > 500 else ''}")
    if metrics:
        lines.append("\n[bold]Metrics:[/bold]")
        lines.extend(f"  {k}: {v}" for k, v in metrics.items())

    from src.agent.trace import TraceWriter
    trace_dir = TraceWriter.find_trace_dir(run_id, runs_dir=RUNS_DIR, sessions_dir=SESSIONS_DIR)
    entries = (
        TraceWriter.read(trace_dir, resolve_offloads=True, resolve_fields={"content"})
        if trace_dir
        else []
    )
    answers = [e["content"] for e in entries if e.get("type") == "answer" and e.get("content")]
    if answers:
        summary = answers[-1][:200]
        lines.append(f"\n[bold]Answer:[/bold] {summary}{'...' if len(answers[-1]) > 200 else ''}")

    if state.get("reason"):
        lines.append(f"\n[bold]Reason:[/bold] {state['reason']}")

    console.print(Panel("\n".join(lines), border_style=c, title=run_id))
    console.print(f"[dim]{run_dir}[/dim]")


def cmd_code(run_id: str) -> None:
    """Show generated code."""
    code_dir = RUNS_DIR / run_id / "code"
    if not code_dir.exists():
        console.print(f"[red]{run_id}/code not found[/red]")
        return
    for name in ("signal_engine.py",):
        path = code_dir / name
        if path.exists():
            code = path.read_text(encoding="utf-8")
            console.print(Syntax(code, "python", theme="monokai", line_numbers=True), width=120)
            console.print()


def cmd_pine(run_id: str) -> None:
    """Show Pine Script for a run."""
    pine_path = RUNS_DIR / run_id / "artifacts" / "strategy.pine"
    if not pine_path.exists():
        console.print(f"[red]{run_id}/artifacts/strategy.pine not found[/red]")
        console.print("[dim]Ask the agent: \"export this strategy to Pine Script\"[/dim]")
        return
    code = pine_path.read_text(encoding="utf-8")
    console.print(Syntax(code, "javascript", theme="monokai", line_numbers=True), width=120)
    console.print()
    console.print("[dim]Copy and paste into TradingView Pine Editor, then Add to Chart[/dim]")


def cmd_skills() -> None:
    """List available skills."""
    from src.agent.skills import SkillsLoader
    loader = SkillsLoader()

    table = Table(title="Skills", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Description")

    for s in loader.skills:
        table.add_row(s.name, s.description)

    console.print(table)


def cmd_trace(run_id: str) -> None:
    """Replay trace.jsonl to show full execution."""
    from src.agent.trace import TraceWriter

    trace_dir = TraceWriter.find_trace_dir(run_id, runs_dir=RUNS_DIR, sessions_dir=SESSIONS_DIR)
    if trace_dir is None:
        console.print(f"[red]{run_id}/trace.jsonl not found[/red]")
        return

    entries = TraceWriter.read(
        trace_dir,
        resolve_offloads=True,
        resolve_fields={"prompt", "content", "summary"},
    )
    if not entries:
        console.print(f"[red]{run_id}/trace.jsonl is empty or missing[/red]")
        return

    console.print(Panel(f"[bold]Trace replay: {run_id}[/bold]  ({len(entries)} entries)", border_style="cyan"))

    for entry in entries:
        etype = entry.get("type", "?")
        ts = entry.get("ts", 0)
        ts_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
        it = entry.get("iter", "")
        iter_tag = f"[dim]#{it}[/dim] " if it else ""

        if etype == "start":
            console.print(f"\n[bold cyan]{ts_str}[/bold cyan] {iter_tag}[bold]START[/bold]  {entry.get('prompt', '')[:120]}")
        elif etype == "thinking":
            content = entry.get("content", "")
            console.print(f"[dim]{ts_str}[/dim] {iter_tag}[dim italic]{content[:200]}[/dim italic]")
        elif etype == "tool_call":
            tool = entry.get("tool", "")
            args = entry.get("args", {})
            args_str = ", ".join(f"{k}={str(v)[:40]}" for k, v in args.items()) if args else ""
            console.print(f"[dim]{ts_str}[/dim] {iter_tag}[cyan]\u25b6 {tool}[/cyan]({args_str})")
        elif etype == "tool_result":
            tool = entry.get("tool", "")
            status = entry.get("status", "ok")
            elapsed = entry.get("elapsed_ms", 0)
            ok = status == "ok"
            mark = "\u2713" if ok else "\u2717"
            color = "green" if ok else "red"
            preview = (entry.get("preview") or entry.get("result_preview") or entry.get("result") or "")[:80]
            size_hint = ""
            if entry.get("result_path"):
                size_hint = f" [{int(entry.get('result_size') or 0) // 1024}K offloaded]"
            console.print(f"[dim]{ts_str}[/dim] {iter_tag}[{color}]{mark} {tool}[/{color}] [dim]{elapsed}ms[/dim]  {preview}{size_hint}")
        elif etype == "tool_skipped":
            console.print(f"[dim]{ts_str}[/dim] {iter_tag}[yellow]\u2298 {entry.get('tool', '')} (skipped)[/yellow]")
        elif etype == "message":
            role = entry.get("role", "?")
            content = entry.get("content") or entry.get("content_preview") or ""
            role_color = "cyan" if role == "user" else "green"
            console.print(f"\n[dim]{ts_str}[/dim] {iter_tag}[bold {role_color}]{role.upper()}[/bold {role_color}] {content[:120]}")
        elif etype == "answer":
            content = entry.get("content", "")
            console.print(f"\n[dim]{ts_str}[/dim] {iter_tag}[bold green]ANSWER[/bold green]\n{content}")
        elif etype == "end":
            status = entry.get("status", "?")
            iters = entry.get("iterations", "?")
            color = "green" if status == "success" else "red"
            console.print(f"\n[bold {color}]{ts_str} END[/bold {color}]  status={status}  iterations={iters}")

    console.print()


# ---------------------------------------------------------------------------
# Swarm subcommands
# ---------------------------------------------------------------------------

def cmd_swarm_presets() -> None:
    """List available swarm presets."""
    from src.swarm.presets import list_presets

    presets = list_presets()
    if not presets:
        console.print("[dim]No presets available[/dim]")
        return

    table = Table(title="Swarm Presets", show_lines=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Agents", width=8, justify="right")
    table.add_column("Variables")
    table.add_column("Description", max_width=40)

    for p in presets:
        raw_vars = p.get("variables", [])
        var_names = [
            v["name"] if isinstance(v, dict) else str(v) for v in raw_vars
        ]
        vars_str = ", ".join(var_names)
        table.add_row(
            p["name"],
            p.get("title", ""),
            str(p.get("agent_count", 0)),
            vars_str,
            p.get("description", "")[:40],
        )

    console.print(table)


def cmd_swarm_run(preset: str, vars_json: Optional[str] = None) -> None:
    """Run swarm preset (legacy polling mode, use cmd_swarm_run_live for streaming)."""
    cmd_swarm_run_live(preset, vars_json)


def cmd_swarm_inspect(preset: str) -> int:
    """Inspect a swarm preset without starting workers."""
    from src.swarm.presets import inspect_preset

    try:
        report = inspect_preset(preset)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        return EXIT_USAGE_ERROR
    except Exception as exc:
        console.print(f"[red]Failed to inspect preset:[/red] {exc}")
        return EXIT_RUN_FAILED

    status = "OK" if report["valid"] else "INVALID"
    status_color = "green" if report["valid"] else "red"
    lines = [
        f"[bold]Preset:[/bold] {report['name']}",
        f"[bold]Title:[/bold] {report.get('title') or '-'}",
        f"[bold]Status:[/bold] [{status_color}]{status}[/{status_color}]",
        f"[bold]Agents:[/bold] {len(report['agents'])}",
        f"[bold]Tasks:[/bold] {len(report['tasks'])}",
        f"[bold]Variables:[/bold] {', '.join(report['variables']) or '-'}",
    ]
    if report.get("description"):
        lines.append(f"[bold]Description:[/bold] {report['description']}")
    console.print(Panel("\n".join(lines), border_style=status_color, title="Swarm Preset Inspect"))

    agent_table = Table(title="Agents", show_lines=False)
    agent_table.add_column("ID", style="cyan", no_wrap=True)
    agent_table.add_column("Role")
    agent_table.add_column("Tools", max_width=40)
    for agent in report["agents"]:
        agent_table.add_row(
            agent["id"],
            agent.get("role", ""),
            ", ".join(agent.get("tools", [])),
        )
    console.print(agent_table)

    dag_table = Table(title="DAG Execution Plan", show_lines=False)
    dag_table.add_column("Layer", justify="right", width=6)
    dag_table.add_column("Task", style="cyan")
    dag_table.add_column("Agent")
    dag_table.add_column("Depends On")
    task_details = {task["id"]: task for task in report["tasks"]}
    for idx, layer in enumerate(report["layers"], start=1):
        for item in layer:
            task = task_details[item["task_id"]]
            dag_table.add_row(
                str(idx),
                item["task_id"],
                item["agent_id"],
                ", ".join(task.get("depends_on", [])) or "-",
            )
    console.print(dag_table)

    validation_table = Table(title="Validation", show_lines=False)
    validation_table.add_column("Level", width=8)
    validation_table.add_column("Message")
    if report["errors"]:
        for error in report["errors"]:
            validation_table.add_row("[red]ERROR[/red]", error)
    if report["warnings"]:
        for warning in report["warnings"]:
            validation_table.add_row("[yellow]WARN[/yellow]", warning)
    if not report["errors"] and not report["warnings"]:
        validation_table.add_row("[green]OK[/green]", "No issues found")
    console.print(validation_table)

    return EXIT_SUCCESS if report["valid"] else EXIT_RUN_FAILED


def cmd_swarm_list() -> None:
    """List swarm run history."""
    from src.swarm.store import SwarmStore

    store = SwarmStore(base_dir=SWARM_DIR)
    runs = store.list_runs()

    if not runs:
        console.print("[dim]No swarm runs yet[/dim]")
        return

    table = Table(title="Swarm Runs", show_lines=False)
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Preset")
    table.add_column("Status", width=12)
    table.add_column("Tasks", width=6, justify="right")
    table.add_column("Created", width=20)

    for run in runs:
        sc = {
            "completed": "green",
            "failed": "red",
            "cancelled": "yellow",
            "running": "blue",
        }.get(run.status.value, "dim")
        table.add_row(
            run.id,
            run.preset_name,
            f"[{sc}]{run.status.value}[/{sc}]",
            str(len(run.tasks)),
            run.created_at[:19],
        )

    console.print(table)


def cmd_swarm_show(run_id: str) -> None:
    """Show swarm run details."""
    from src.swarm.store import SwarmStore
    from src.swarm.models import TaskStatus

    store = SwarmStore(base_dir=SWARM_DIR)
    run = store.load_run(run_id)

    if run is None:
        console.print(f"[red]Swarm run {run_id} not found[/red]")
        return

    status_color = {
        "completed": "green",
        "failed": "red",
        "cancelled": "yellow",
        "running": "blue",
    }.get(run.status.value, "dim")

    lines = [
        f"[bold]Status:[/bold] [{status_color}]{run.status.value.upper()}[/{status_color}]",
        f"[bold]Preset:[/bold] {run.preset_name}",
        f"[bold]Created:[/bold] {run.created_at}",
    ]
    if run.completed_at:
        lines.append(f"[bold]Completed:[/bold] {run.completed_at}")
    if run.user_vars:
        lines.append(f"[bold]Variables:[/bold] {json.dumps(run.user_vars, ensure_ascii=False)}")

    tokens_in = run.total_input_tokens
    tokens_out = run.total_output_tokens
    if tokens_in or tokens_out:
        lines.append(f"[bold]Tokens:[/bold] ~{tokens_in + tokens_out:,} (in: {tokens_in:,} out: {tokens_out:,})")

    lines.append(f"\n[bold]Tasks ({len(run.tasks)}):[/bold]")
    for task in run.tasks:
        tc = "green" if task.status == TaskStatus.completed else "red" if task.status == TaskStatus.failed else "dim"
        dep_str = f" (deps: {', '.join(task.depends_on)})" if task.depends_on else ""
        task_line = f"  [{tc}]{task.id}[/{tc}] -> {task.agent_id}{dep_str} [{task.status.value}]"
        lines.append(task_line)
        if task.summary:
            lines.append(f"    {task.summary[:100]}")
        if task.error:
            lines.append(f"    [red]{task.error[:100]}[/red]")

    if run.final_report:
        lines.append(f"\n[bold]Final Report:[/bold]\n{run.final_report[:800]}")

    console.print(Panel("\n".join(lines), border_style=status_color, title=run_id))


def cmd_swarm_cancel(run_id: str) -> None:
    """Cancel a swarm run."""
    from src.swarm.runtime import SwarmRuntime
    from src.swarm.store import SwarmStore

    store = SwarmStore(base_dir=SWARM_DIR)
    runtime = SwarmRuntime(store=store)

    if runtime.cancel_run(run_id):
        console.print(f"[yellow]Cancel signal sent: {run_id}[/yellow]")
    else:
        console.print(f"[red]Run {run_id} not found or already finished[/red]")


# ---------------------------------------------------------------------------
# Session subcommands
# ---------------------------------------------------------------------------

def cmd_sessions() -> None:
    """List chat sessions."""
    from src.session.store import SessionStore

    store = SessionStore(base_dir=SESSIONS_DIR)
    sessions = store.list_sessions()

    if not sessions:
        console.print("[dim]No sessions yet[/dim]")
        return

    table = Table(title="Sessions", show_lines=False)
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Title", max_width=30)
    table.add_column("Status", width=10)
    table.add_column("Messages", width=8, justify="right")
    table.add_column("Updated", width=20)

    for s in sessions:
        messages = store.get_messages(s.session_id)
        sc = "green" if s.status.value == "active" else "dim"
        table.add_row(
            s.session_id,
            s.title or "[dim]untitled[/dim]",
            f"[{sc}]{s.status.value}[/{sc}]",
            str(len(messages)),
            s.updated_at[:19],
        )

    console.print(table)


def cmd_session_chat(session_id: str, max_iter: int) -> None:
    """Continue a session chat."""
    from src.session.store import SessionStore

    store = SessionStore(base_dir=SESSIONS_DIR)
    session = store.get_session(session_id)

    if session is None:
        console.print(f"[red]Session {session_id} not found[/red]")
        return

    messages = store.get_messages(session_id)
    history: List[Dict[str, str]] = []
    for msg in messages:
        if msg.role in ("user", "assistant") and msg.content.strip():
            history.append({"role": msg.role, "content": msg.content})

    console.print(Panel(
        f"[bold cyan]Session: {session.title or session_id}[/bold cyan]\n"
        f"[dim]History: {len(messages)} messages | Type q to exit[/dim]",
        border_style="cyan",
    ))

    stats = _SessionStats(session_start=time.monotonic())
    prompt_session = _create_prompt_session(stats)

    while True:
        if prompt_session is None:
            _print_status_bar(stats)
        try:
            prompt = _read_input(prompt_session).strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not prompt or prompt.lower() in ("q", "quit", "exit"):
            break

        run_start = time.perf_counter()
        _run_state = {"label": "running"}
        _stop_timer = threading.Event()

        def _session_event_timer(status_ref: Any) -> None:
            while not _stop_timer.is_set():
                elapsed = time.perf_counter() - run_start
                label = _run_state["label"]
                try:
                    status_ref.update(f"[bold cyan]\u23f3 {label}... {elapsed:.1f}s[/bold cyan]")
                except Exception:
                    pass
                _stop_timer.wait(1.0)

        with console.status("[bold cyan]\u23f3 Running...[/bold cyan]") as spinner:
            _timer = threading.Thread(target=_session_event_timer, args=(spinner,), daemon=True)
            _timer.start()
            try:
                result = _run_agent(prompt, history=history[-6:], max_iter=max_iter)
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                continue
            finally:
                _stop_timer.set()
                _timer.join(timeout=1)

        stats.last_elapsed = time.perf_counter() - run_start
        _print_result(result, stats.last_elapsed)
        history.append({"role": "user", "content": prompt})
        if result.get("content"):
            history.append({"role": "assistant", "content": result["content"]})

    console.print("[dim]Goodbye[/dim]")


# ---------------------------------------------------------------------------
# Upload subcommand
# ---------------------------------------------------------------------------

def cmd_upload(file_path: str) -> None:
    """Upload a file to the server."""
    src = Path(file_path)
    if not src.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return
    if not src.is_file():
        console.print(f"[red]Not a file: {file_path}[/red]")
        return

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = src.suffix
    dest_name = f"{uuid.uuid4().hex[:12]}{ext}"
    dest = UPLOADS_DIR / dest_name

    shutil.copy2(str(src), str(dest))
    console.print(f"[green]Uploaded:[/green] {dest}")


def cmd_provider_login(provider: str) -> int:
    """Authenticate OAuth-backed LLM providers."""
    normalized = provider.strip().lower().replace("_", "-")
    if normalized != "openai-codex":
        console.print("[red]Unknown OAuth provider.[/red] Supported: openai-codex")
        return EXIT_USAGE_ERROR
    try:
        from src.providers.openai_codex import login_openai_codex

        console.print("[cyan]Starting OpenAI Codex OAuth login...[/cyan]\n")
        token = login_openai_codex(
            print_fn=lambda text: console.print(text),
            prompt_fn=lambda text: Prompt.ask(text),
        )
        account = getattr(token, "account_id", None) or "ChatGPT"
        console.print(f"[green]Authenticated with OpenAI Codex[/green]  [dim]{account}[/dim]")
        return EXIT_SUCCESS
    except Exception as exc:
        console.print(f"[red]Authentication error:[/red] {exc}")
        return EXIT_RUN_FAILED


# ---------------------------------------------------------------------------
# Live connector runtime internals.
#
# Every state-changing verb here is a PRIVILEGED USER-SIDE action: none is
# reachable from the agent loop / tool registry. There is deliberately NO
# `live commit` verb — committing a mandate happens only through the consent
# flow's `POST /mandate/commit`, never a CLI command (the CLI cannot create or
# widen a mandate). The public CLI surface is `vibe-trading connector ...`;
# `cmd_live_*` helpers remain only as the broker-runtime implementation behind
# connector profiles.
# ---------------------------------------------------------------------------

_DEFAULT_LIVE_BROKER = "robinhood"
_LIVE_AUTHORIZE_INIT_TIMEOUT_SECONDS = 300.0
_LIVE_AUTHORIZE_TIMEOUT_ENV = "VIBE_LIVE_AUTHORIZE_TIMEOUT_SECONDS"


def _authorize_timeout_seconds() -> float:
    """Resolve the OAuth authorize handshake deadline in seconds.

    Reads ``VIBE_LIVE_AUTHORIZE_TIMEOUT_SECONDS`` and falls back to
    :data:`_LIVE_AUTHORIZE_INIT_TIMEOUT_SECONDS` (300 s) when it is unset,
    empty, non-numeric, or not strictly positive. This deadline bounds the
    interactive ``list_tools`` handshake that drives the broker OAuth flow, so
    a multi-minute human sign-in (e.g. Robinhood's face scan) has room to
    complete.

    Returns:
        The authorize deadline in seconds (a positive float).
    """
    raw = os.getenv(_LIVE_AUTHORIZE_TIMEOUT_ENV)
    if raw:
        try:
            value = float(raw)
        except ValueError:
            return _LIVE_AUTHORIZE_INIT_TIMEOUT_SECONDS
        if value > 0:
            return value
    return _LIVE_AUTHORIZE_INIT_TIMEOUT_SECONDS


def _live_api_base() -> str:
    """Return the base URL of the running API server for runner-control calls.

    Mirrors :func:`cli.main._commit_mandate`: the base is read from
    ``VIBE_TRADING_API_URL`` (falling back to ``http://127.0.0.1:8000``). The
    persistent runner (SPEC §7.5) is controlled through the R6 surface endpoints
    (``POST /live/runner/start|stop`` / ``GET /live/status``), never from the
    agent loop, so the CLI only ever relays intent.

    Returns:
        The API base URL with any trailing slash removed.
    """
    return os.environ.get("VIBE_TRADING_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _live_api_call(method: str, path: str, *, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call an R6 live-runner endpoint and decode the JSON response.

    Args:
        method: HTTP verb (``"GET"`` or ``"POST"``).
        path: Endpoint path beginning with ``/`` (e.g. ``"/live/runner/start"``).
        body: JSON request body for ``POST`` calls.

    Returns:
        The decoded response object on success, or an ``{"status": "error",
        "error": ...}`` envelope when the server is unreachable / returns a
        non-2xx status — so a caller can surface a clean message instead of a
        traceback when no server is running.
    """
    import httpx

    url = f"{_live_api_base()}{path}"
    try:
        if method.upper() == "GET":
            response = httpx.get(url, timeout=30.0)
        else:
            response = httpx.post(url, json=body or {}, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001 — surface a clean error to the user
        return {"status": "error", "error": str(exc)}


def _live_server_config(broker: str):
    """Resolve the protected MCP server config for ``broker``.

    The config is read at boot from the user-side protected agent config file
    (never from caller input / agent tool args / ``variables``), exactly as the
    #142 swarm-config trust template requires.

    Args:
        broker: Broker key, e.g. ``"robinhood"``.

    Returns:
        The :class:`MCPServerConfig` for ``broker``, or ``None`` when the broker
        has no entry in the protected config.
    """
    from src.config.loader import load_agent_config

    agent_config = load_agent_config()
    servers = getattr(agent_config, "mcp_servers", {}) or {}
    return servers.get(broker.strip().lower())


def _raw_live_server_config_entry(broker: str) -> dict[str, Any] | None:
    """Best-effort raw lookup used only to explain invalid live config."""
    from src.config.loader import _read_config_file
    from src.config.paths import get_config_path
    from src.config.schema import live_broker_key_for_url

    try:
        path = get_config_path()
        if not path.exists():
            return None
        raw = _read_config_file(path)
    except Exception:  # noqa: BLE001 — diagnostics must not mask the real CLI error
        return None

    servers = raw.get("mcpServers")
    if not isinstance(servers, dict):
        servers = raw.get("mcp_servers")
    if not isinstance(servers, dict):
        return None

    key = broker.strip().lower()
    for server_key, server in servers.items():
        if isinstance(server, dict) and str(server_key).strip().lower() == key:
            return server

    if key != "robinhood":
        return None

    for server in servers.values():
        if isinstance(server, dict) and live_broker_key_for_url(str(server.get("url") or "")) == key:
            return server
    return None


def _raw_server_entry_uses_wildcard(entry: dict[str, Any] | None) -> bool:
    """Return whether a raw MCP server entry uses a wildcard enabledTools list."""
    if entry is None:
        return False
    enabled_tools = entry.get("enabledTools", entry.get("enabled_tools"))
    if not isinstance(enabled_tools, list):
        return False
    return "*" in {str(tool).strip() for tool in enabled_tools}


def _print_missing_live_channel_config(key: str) -> None:
    """Print actionable guidance when a live broker config cannot be loaded."""
    if key == "robinhood":
        from src.config.schema import format_robinhood_mcp_config_guidance

        reason = "wildcard" if _raw_server_entry_uses_wildcard(_raw_live_server_config_entry(key)) else "missing"
        console.print("[red]Robinhood live channel is not configured safely.[/red]")
        console.print(format_robinhood_mcp_config_guidance(reason=reason), markup=False, soft_wrap=True)
        return

    console.print(
        f"[red]No live channel configured for '{key}'.[/red] "
        "Add the broker's mcpServers entry to ~/.vibe-trading/agent.json first."
    )


def cmd_live_authorize(broker: str) -> int:
    """Bootstrap the OAuth handshake for a live broker channel (desktop only).

    Builds the broker's MCP tool wrappers, which forces a connection and — when
    no valid token is cached — triggers the native FastMCP OAuth flow: a browser
    opens to the broker's authorize page and the token is persisted to the
    protected cache. This is the only way to turn the channel on.

    Args:
        broker: Broker key, e.g. ``"robinhood"``.

    Returns:
        Process exit code.
    """
    key = broker.strip().lower()
    server_config = _live_server_config(key)
    if server_config is None:
        _print_missing_live_channel_config(key)
        return EXIT_USAGE_ERROR
    if getattr(server_config, "auth", None) is None:
        console.print(
            f"[red]Live channel '{key}' has no OAuth auth configured[/red] — "
            "cannot authorize."
        )
        return EXIT_USAGE_ERROR

    console.print(f"[cyan]Opening browser to authorize {key}…[/cyan]")
    console.print(
        "[dim]Complete the sign-in in your browser; this terminal will continue "
        "once the broker redirects back.[/dim]"
    )
    try:
        from src.tools.mcp import build_mcp_tool_wrappers

        # The OAuth flow is driven lazily by the first request to the server —
        # the `list_tools` discovery handshake — which is bounded by the
        # per-call `tool_timeout` (default 30 s), NOT `init_timeout`. Raise both
        # to the authorize deadline so a multi-minute human sign-in (e.g.
        # Robinhood's face scan) does not trip the handshake. Raise-only: never
        # shrink an already-larger user-configured timeout.
        authorize_timeout = _authorize_timeout_seconds()
        if hasattr(server_config, "model_copy"):
            updates: dict[str, float] = {}
            configured_init_timeout = getattr(server_config, "init_timeout", None)
            if (
                configured_init_timeout is None
                or float(configured_init_timeout) < authorize_timeout
            ):
                updates["init_timeout"] = authorize_timeout
            configured_tool_timeout = getattr(server_config, "tool_timeout", None)
            if (
                configured_tool_timeout is None
                or float(configured_tool_timeout) < authorize_timeout
            ):
                updates["tool_timeout"] = authorize_timeout
            if updates:
                server_config = server_config.model_copy(update=updates)

        # Single attempt: a transient-retry would open a fresh client context
        # that starts a SECOND OAuth callback server on a new port, orphaning
        # the sign-in the user just completed against the first one (see #259).
        tools = build_mcp_tool_wrappers(
            key, server_config, max_list_tools_attempts=1
        )
    except Exception as exc:  # noqa: BLE001 — surface any handshake failure
        console.print(f"[red]Authorization failed:[/red] {exc}")
        return EXIT_RUN_FAILED

    console.print(
        f"[green]Authorized {key}[/green] "
        f"[dim]({len(tools)} read-only tool(s) available)[/dim]"
    )
    console.print(
        "[dim]The channel is read-only until you commit a mandate and enable "
        "order tools. Use `vibe-trading connector status` to check state.[/dim]"
    )
    return EXIT_SUCCESS


def cmd_provider_doctor() -> int:
    """Print redacted provider diagnostics."""
    from src.providers.llm import provider_diagnostics

    console.print_json(data=provider_diagnostics())
    return EXIT_SUCCESS


def _format_expiry_countdown(expires_at: str) -> str:
    """Return a human-readable countdown to ``expires_at`` (ISO-8601 UTC)."""
    from datetime import datetime, timezone

    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return f"{expires_at} (unparseable)"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = parsed - datetime.now(timezone.utc)
    secs = int(delta.total_seconds())
    if secs <= 0:
        return f"{expires_at} (EXPIRED)"
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        human = f"{days}d {hours}h"
    elif hours:
        human = f"{hours}h {minutes}m"
    else:
        human = f"{minutes}m"
    return f"{expires_at} (in {human})"


def _runner_id_for(broker: str) -> str:
    """Return the persistent-runner identity key for ``broker`` (SPEC §7.5)."""
    return f"live-{broker}"


def _add_runner_liveness_rows(table: Table, broker: str) -> None:
    """Append persistent-runner liveness rows to a ``live status`` table.

    Liveness is reported from the local heartbeat files via the runtime
    contract (:func:`src.live.runtime.liveness.is_runner_alive` /
    :func:`~src.live.runtime.liveness.last_tick`), so it works without a running
    API server. If the liveness module is not yet present (it lands concurrently
    with this parcel), the rows degrade to ``unknown`` rather than crashing the
    read-only status command.

    Args:
        table: The Rich table being built by :func:`cmd_live_status`.
        broker: Broker key the runner is bound to.
    """
    runner_id = _runner_id_for(broker)
    try:
        from src.live.runtime.liveness import is_runner_alive, last_tick
    except Exception:  # noqa: BLE001 — liveness lands concurrently; degrade cleanly
        table.add_row("Runner", "[dim]unknown (runtime not available)[/dim]")
        return

    try:
        alive = is_runner_alive(runner_id)
    except Exception as exc:  # noqa: BLE001 — never let a status read raise
        table.add_row("Runner", f"[dim]unknown ({exc})[/dim]")
        return

    if alive:
        table.add_row("Runner", "[green]running[/green]")
    else:
        table.add_row("Runner", "[yellow]stopped[/yellow]")

    try:
        tick = last_tick(runner_id)
    except Exception:  # noqa: BLE001
        tick = None
    if tick is not None:
        table.add_row("  Last tick", _format_last_tick(tick))


def _format_last_tick(tick: Any) -> str:
    """Render a runner's last-tick timestamp as an absolute + relative string.

    Args:
        tick: A ``datetime`` or ISO-8601 string from the liveness heartbeat.

    Returns:
        Human-readable ``"<iso> (<n>s ago)"`` (or the raw value if unparseable).
    """
    from datetime import datetime, timezone

    if isinstance(tick, datetime):
        parsed = tick
    else:
        try:
            parsed = datetime.fromisoformat(str(tick).replace("Z", "+00:00"))
        except ValueError:
            return str(tick)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    ago = int((datetime.now(timezone.utc) - parsed).total_seconds())
    iso = parsed.isoformat()
    if ago < 0:
        return iso
    if ago < 60:
        return f"{iso} ({ago}s ago)"
    if ago < 3600:
        return f"{iso} ({ago // 60}m ago)"
    return f"{iso} ({ago // 3600}h ago)"


def cmd_live_status(broker: Optional[str] = None) -> int:
    """Show auth state, active mandate, and halt state for live channels.

    Read-only: it loads the mandate via :func:`src.live.mandate.store.load_mandate`
    and checks the halt sentinel via :func:`src.live.halt.halt_flag_set`; it never
    writes anything.

    Args:
        broker: Limit the report to a single broker. ``None`` reports the
            default broker (``robinhood``).

    Returns:
        Process exit code.
    """
    from src.live.halt import halt_flag_set, read_halt
    from src.live.mandate.model import MANDATE_SCHEMA_VERSION
    from src.live.mandate.store import load_mandate

    key = (broker or _DEFAULT_LIVE_BROKER).strip().lower()

    table = Table(title=f"Live channel: {key}", box=box.SIMPLE)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")

    server_config = _live_server_config(key)
    authorized = server_config is not None and getattr(server_config, "auth", None) is not None
    table.add_row("Configured", "yes" if server_config is not None else "[red]no[/red]")
    table.add_row("OAuth auth", "yes" if authorized else "no")

    halted = halt_flag_set(key)
    if halted:
        meta = read_halt(key) or read_halt() or {}
        reason = meta.get("reason", "")
        by = meta.get("by", "")
        detail = f" [dim]({by}: {reason})[/dim]" if (by or reason) else ""
        table.add_row("Halt", f"[bold red]HALTED[/bold red]{detail}")
    else:
        table.add_row("Halt", "[green]clear[/green]")

    _add_runner_liveness_rows(table, key)

    mandate = load_mandate(key)
    if mandate is None:
        table.add_row("Mandate", "[yellow]none on file[/yellow] (read-only)")
    elif mandate.schema_version != MANDATE_SCHEMA_VERSION:
        table.add_row(
            "Mandate",
            f"[red]unknown schema v{mandate.schema_version}[/red] (gate fail-closed)",
        )
    else:
        caps = mandate.hard_caps
        table.add_row("Mandate", "[green]active[/green]")
        table.add_row("  Max order", f"${caps.max_order_notional_usd:,.0f}")
        table.add_row("  Max exposure", f"${caps.max_total_exposure_usd:,.0f}")
        table.add_row("  Max leverage", f"{caps.max_leverage:g}x")
        table.add_row("  Trades/day", str(caps.max_trades_per_day))
        table.add_row(
            "  Instruments",
            ", ".join(i.value for i in caps.allowed_instruments) or "[red]none[/red]",
        )
        table.add_row("  Expires", _format_expiry_countdown(mandate.consent.expires_at))

    console.print(table)
    return EXIT_SUCCESS


def cmd_live_mandate(broker: Optional[str] = None) -> int:
    """Print the committed mandate for a broker (read-only).

    Args:
        broker: Broker key. ``None`` uses the default broker (``robinhood``).

    Returns:
        Process exit code. ``EXIT_RUN_FAILED`` when no mandate is on file.
    """
    from dataclasses import asdict

    from src.live.mandate.store import load_mandate

    key = (broker or _DEFAULT_LIVE_BROKER).strip().lower()
    mandate = load_mandate(key)
    if mandate is None:
        console.print(
            f"[yellow]No committed mandate for '{key}'.[/yellow] "
            "The channel is read-only until a mandate is committed via the consent flow."
        )
        return EXIT_RUN_FAILED

    payload = asdict(mandate)
    # asdict leaves enums as Enum members; render their string values.
    caps = payload["hard_caps"]
    caps["allowed_instruments"] = [i.value for i in mandate.hard_caps.allowed_instruments]
    payload["universe"]["asset_classes"] = [a.value for a in mandate.universe.asset_classes]
    console.print_json(data=payload)
    return EXIT_SUCCESS


def cmd_live_halt(broker: Optional[str] = None) -> int:
    """Trip the kill switch — write the HALT sentinel (privileged).

    With no broker, trips the global switch (halts all brokers); with a broker,
    trips only that broker's sentinel. The gate rejects all order attempts until
    the switch is cleared with ``vibe-trading connector resume``.

    Args:
        broker: Broker key, or ``None`` for the global switch.

    Returns:
        Process exit code.
    """
    from src.live.halt import trip_halt

    target = broker.strip().lower() if broker else None
    path = trip_halt(by="cli", reason="cli live halt", broker=target)
    scope = target or "ALL brokers"
    console.print(f"[bold red]Live trading halted[/bold red] for {scope}.")
    console.print(f"[dim]Sentinel: {path}[/dim]")
    console.print("[dim]Run `vibe-trading connector resume` to re-enable.[/dim]")
    return EXIT_SUCCESS


def cmd_live_resume(broker: Optional[str] = None) -> int:
    """Clear a tripped kill switch (privileged, explicit re-enable).

    Args:
        broker: Broker key, or ``None`` for the global switch. Each scope is
            cleared independently.

    Returns:
        Process exit code.
    """
    from src.live.halt import clear_halt

    target = broker.strip().lower() if broker else None
    cleared = clear_halt(broker=target)
    scope = target or "ALL brokers"
    if cleared:
        console.print(f"[green]Halt cleared[/green] for {scope}.")
    else:
        console.print(f"[dim]No active halt for {scope}.[/dim]")
    return EXIT_SUCCESS


def cmd_live_revoke(broker: str) -> int:
    """Revoke the OAuth token and delete the mandate — full channel off.

    Deletes the broker's OAuth token cache directory and its ``mandate.json``
    so the channel reverts to fully off. This is a privileged user-side action.

    Args:
        broker: Broker key, e.g. ``"robinhood"``.

    Returns:
        Process exit code.
    """
    from src.live.paths import broker_dir

    key = broker.strip().lower()
    try:
        base = broker_dir(key)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return EXIT_USAGE_ERROR

    removed: list[str] = []

    # OAuth token cache. Prefer the configured cache_dir; fall back to the
    # canonical per-broker oauth/ subtree.
    server_config = _live_server_config(key)
    cache_dir: Optional[Path] = None
    auth = getattr(server_config, "auth", None) if server_config is not None else None
    if auth is not None and getattr(auth, "cache_dir", None):
        cache_dir = Path(auth.cache_dir).expanduser()
    if cache_dir is None or not cache_dir.exists():
        cache_dir = base / "oauth"
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
        removed.append(f"OAuth token cache ({cache_dir})")

    mandate_path = base / "mandate.json"
    if mandate_path.exists():
        try:
            mandate_path.unlink()
            removed.append(f"mandate ({mandate_path})")
        except OSError as exc:
            console.print(f"[red]Failed to delete mandate: {exc}[/red]")
            return EXIT_RUN_FAILED

    if removed:
        console.print(f"[green]Revoked live channel '{key}'.[/green]")
        for item in removed:
            console.print(f"  [dim]- removed {item}[/dim]")
    else:
        console.print(f"[dim]Nothing to revoke for '{key}' (no token or mandate on file).[/dim]")
    return EXIT_SUCCESS


def cmd_live_start(broker: Optional[str] = None) -> int:
    """Start the persistent live runner in the background (SPEC §7.5).

    Relays a start request to the R6 surface endpoint
    (``POST /live/runner/start``); the server owns the durable scheduler + job
    store. This never touches the agent loop. The runner is read-only until a
    mandate is committed (the consent flow), so starting it is safe even before
    any mandate exists.

    Args:
        broker: Broker key, or ``None`` for the default broker (``robinhood``).

    Returns:
        Process exit code. ``EXIT_RUN_FAILED`` when the server is unreachable.
    """
    key = (broker or _DEFAULT_LIVE_BROKER).strip().lower()
    result = _live_api_call(
        "POST", "/live/runner/start", body={"broker": key, "foreground": False}
    )
    if result.get("status") == "error":
        console.print(f"[red]Could not start the live runner:[/red] {result.get('error')}")
        console.print(
            "[dim]Is the API server running? Start it with `vibe-trading serve`.[/dim]"
        )
        return EXIT_RUN_FAILED

    runner_id = result.get("runner_id") or _runner_id_for(key)
    console.print(f"[green]Live runner started[/green] for {key} [dim]({runner_id})[/dim].")
    console.print("[dim]Check it with `vibe-trading connector status`.[/dim]")
    return EXIT_SUCCESS


def cmd_live_stop(broker: Optional[str] = None) -> int:
    """Stop the persistent live runner (SPEC §7.5).

    Relays a stop request to ``POST /live/runner/stop``. Stopping the runner
    halts autonomous activity but does NOT clear a tripped kill switch or revoke
    the mandate — use ``connector resume`` / ``connector revoke`` for those.

    Args:
        broker: Broker key, or ``None`` for the default broker (``robinhood``).

    Returns:
        Process exit code. ``EXIT_RUN_FAILED`` when the server is unreachable.
    """
    key = (broker or _DEFAULT_LIVE_BROKER).strip().lower()
    result = _live_api_call("POST", "/live/runner/stop", body={"broker": key})
    if result.get("status") == "error":
        console.print(f"[red]Could not stop the live runner:[/red] {result.get('error')}")
        console.print(
            "[dim]Is the API server running? Start it with `vibe-trading serve`.[/dim]"
        )
        return EXIT_RUN_FAILED

    console.print(f"[yellow]Live runner stopped[/yellow] for {key}.")
    return EXIT_SUCCESS


def cmd_live_run(broker: Optional[str] = None) -> int:
    """Run the persistent live runner in the foreground (SPEC §7.5).

    The foreground variant of ``live start``: it starts the runner via
    ``POST /live/runner/start`` and then tails its heartbeat in a Rich ``Live``
    panel until Ctrl+C, at which point it requests a clean stop. This mirrors
    how ``serve`` runs a long-lived process attached to the terminal. The runner
    is read-only until a mandate is committed through the consent flow.

    Args:
        broker: Broker key, or ``None`` for the default broker (``robinhood``).

    Returns:
        Process exit code.
    """
    key = (broker or _DEFAULT_LIVE_BROKER).strip().lower()
    runner_id = _runner_id_for(key)

    result = _live_api_call(
        "POST", "/live/runner/start", body={"broker": key, "foreground": True}
    )
    if result.get("status") == "error":
        console.print(f"[red]Could not start the live runner:[/red] {result.get('error')}")
        console.print(
            "[dim]Is the API server running? Start it with `vibe-trading serve`.[/dim]"
        )
        return EXIT_RUN_FAILED

    console.print(
        f"[green]Live runner running[/green] for {key} [dim]({runner_id})[/dim] — "
        "press Ctrl+C to stop."
    )

    try:
        from src.live.runtime.liveness import is_runner_alive, last_tick
    except Exception:  # noqa: BLE001 — runtime lands concurrently; fall back to a wait
        is_runner_alive = None  # type: ignore[assignment]
        last_tick = None  # type: ignore[assignment]

    def _panel() -> Panel:
        alive = bool(is_runner_alive(runner_id)) if is_runner_alive else True
        state = "[green]running[/green]" if alive else "[yellow]stopped[/yellow]"
        lines = [f"Runner: {state}", f"Broker: {key}"]
        if last_tick:
            try:
                tick = last_tick(runner_id)
            except Exception:  # noqa: BLE001
                tick = None
            if tick is not None:
                lines.append(f"Last tick: {_format_last_tick(tick)}")
        return Panel("\n".join(lines), title=f"live run · {key}", box=box.ROUNDED)

    try:
        with Live(_panel(), console=console, refresh_per_second=2, transient=False) as live:
            while True:
                time.sleep(1.0)
                live.update(_panel())
                if is_runner_alive and not is_runner_alive(runner_id):
                    break
    except KeyboardInterrupt:
        console.print("\n[dim]Stopping live runner…[/dim]")
    finally:
        stop = _live_api_call("POST", "/live/runner/stop", body={"broker": key})
        if stop.get("status") == "error":
            console.print(f"[red]Failed to stop the runner cleanly:[/red] {stop.get('error')}")
        else:
            console.print(f"[yellow]Live runner stopped[/yellow] for {key}.")
    return EXIT_SUCCESS


# ---------------------------------------------------------------------------
# Trading connector commands
# ---------------------------------------------------------------------------

def _profile_id(value: Optional[str]) -> Optional[str]:
    """Normalize an optional connector profile id."""
    if value is None:
        return None
    text = value.strip().lower()
    return text or None


def _selected_profile_or(value: Optional[str]):
    """Resolve the selected or explicit trading profile."""
    from src.trading.profiles import profile_by_id

    return profile_by_id(_profile_id(value))


def cmd_connector_list() -> int:
    """List selectable trading connector profiles."""
    from src.trading.profiles import list_profiles, load_selected_profile_id

    selected = load_selected_profile_id()
    table = Table(title="Trading Connectors", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Selected", justify="center", width=8)
    table.add_column("Profile")
    table.add_column("Connector")
    table.add_column("Env")
    table.add_column("Transport")
    table.add_column("Capabilities")
    for profile in list_profiles():
        table.add_row(
            "[green]*[/green]" if profile.id == selected else "",
            f"[cyan]{profile.id}[/cyan]\n[dim]{profile.label}[/dim]",
            profile.connector,
            profile.environment,
            profile.transport,
            ", ".join(profile.capabilities),
        )
    console.print(table)
    console.print("[dim]Use `vibe-trading connector use <profile>` to set the default profile.[/dim]")
    return EXIT_SUCCESS


def cmd_connector_use(profile_id: str) -> int:
    """Select the default trading connector profile."""
    from src.trading.profiles import profile_by_id, save_selected_profile_id

    try:
        profile = profile_by_id(profile_id)
        path = save_selected_profile_id(profile.id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return EXIT_USAGE_ERROR
    console.print(f"[green]Selected trading connector[/green] {profile.id}")
    console.print(f"[dim]{profile.label} · {profile.environment} · {profile.transport}[/dim]")
    console.print(f"[dim]Config: {path}[/dim]")
    return EXIT_SUCCESS


def cmd_connector_configure(
    profile_id: str,
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    client_id: int = 77,
    account: str | None = None,
    yes: bool = False,
) -> int:
    """Configure a local connector profile."""
    from src.trading.connectors.ibkr.local import IBKRLocalConfig, config_path, save_config

    try:
        profile = _selected_profile_or(profile_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return EXIT_USAGE_ERROR
    if profile.transport != "local_tws" or profile.connector != "ibkr":
        console.print(f"[red]{profile.id} is not a local TWS/Gateway profile.[/red]")
        return EXIT_USAGE_ERROR

    path = config_path()
    if path.exists() and not yes:
        console.print(f"[yellow]Local connector config already exists:[/yellow] {path}")
        try:
            if not Confirm.ask("Overwrite it?", default=False):
                console.print("[dim]Aborted.[/dim]")
                return EXIT_SUCCESS
        except EOFError:
            console.print("[dim]No input available; use --yes for non-interactive setup.[/dim]")
            return EXIT_USAGE_ERROR

    cfg = IBKRLocalConfig.from_mapping(
        {
            **profile.config,
            "host": host,
            "port": port or profile.config.get("port"),
            "clientId": client_id,
            "account": account,
            "readonly": True,
        }
    )
    path = save_config(cfg)
    console.print(f"[green]Configured[/green] {profile.id} [dim]({path})[/dim]")
    console.print(f"[dim]Run `vibe-trading connector check {profile.id}` to verify it.[/dim]")
    return EXIT_SUCCESS


def cmd_connector_check(
    profile_id: Optional[str] = None,
    *,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> int:
    """Check selected or explicit trading connector profile."""
    from src.trading.service import check_connection

    try:
        profile = _selected_profile_or(profile_id)
        report = check_connection(profile.id, host=host, port=port, client_id=client_id, account=account)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Connector check failed:[/red] {exc}")
        return EXIT_RUN_FAILED

    title = f"Trading Connector: {profile.id}"
    if profile.transport == "local_tws":
        table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
        table.add_column("Endpoint")
        table.add_column("Profile")
        table.add_column("Address")
        table.add_column("State")
        for row in report.get("ports", []):
            open_state = "[green]open[/green]" if row.get("open") else "[dim]closed[/dim]"
            table.add_row(
                str(row.get("label")),
                str(row.get("profile")),
                f"{row.get('host')}:{row.get('port')}",
                open_state,
            )
        console.print(table)
        target = report.get("target", {})
        target_state = "open" if target.get("open") else "closed"
        console.print(f"Target: [bold]{target.get('host')}:{target.get('port')}[/bold] ({target_state})")
        sdk = report.get("sdk", {})
        if not sdk.get("installed"):
            console.print("[yellow]Missing optional dependency:[/yellow] pip install 'ib_async>=2.0'")
        if report.get("account"):
            accounts = ", ".join(report["account"].get("accounts", [])) or "(none)"
            console.print(f"Accounts: [cyan]{rich_escape(accounts)}[/cyan]")
    else:
        table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        table.add_row("Connector", profile.connector)
        table.add_row("Environment", profile.environment)
        table.add_row("Transport", profile.transport)
        table.add_row("Configured", "yes" if report.get("configured") else "[red]no[/red]")
        table.add_row("OAuth token", "present" if report.get("oauth_token_present") else "[yellow]missing[/yellow]")
        table.add_row("Capabilities", ", ".join(report.get("capabilities", [])))
        console.print(table)

    if report.get("status") not in {"ok"}:
        console.print(f"[red]{rich_escape(str(report.get('error') or report.get('status') or 'not ready'))}[/red]")
        return EXIT_RUN_FAILED
    console.print("[green]Connector profile is ready.[/green]")
    return EXIT_SUCCESS


def _print_connector_account(result: dict[str, Any]) -> int:
    accounts = ", ".join(result.get("accounts", [])) or "(none)"
    console.print(f"Accounts: [cyan]{rich_escape(accounts)}[/cyan]")
    rows = result.get("summary", [])
    if not rows:
        console.print("[dim]No account summary returned.[/dim]")
        return EXIT_SUCCESS
    table = Table(title=f"Account Summary · {result.get('profile_id')}", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Account")
    table.add_column("Tag")
    table.add_column("Value", justify="right")
    table.add_column("Currency")
    for row in rows:
        table.add_row(
            str(row.get("account") or ""),
            str(row.get("tag") or ""),
            str(row.get("value") or ""),
            str(row.get("currency") or ""),
        )
    console.print(table)
    return EXIT_SUCCESS


def cmd_connector_account(
    profile_id: Optional[str] = None,
    *,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> int:
    """Print account summary from a connector profile."""
    from src.trading.service import get_account

    try:
        result = get_account(_profile_id(profile_id), host=host, port=port, client_id=client_id, account=account)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Connector account failed:[/red] {exc}")
        return EXIT_RUN_FAILED
    if result.get("status") == "error":
        console.print(f"[red]{rich_escape(str(result.get('error')))}[/red]")
        return EXIT_RUN_FAILED
    return _print_connector_account(result)


def cmd_connector_positions(
    profile_id: Optional[str] = None,
    *,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
) -> int:
    """Print positions from a connector profile."""
    from src.trading.service import get_positions

    try:
        result = get_positions(_profile_id(profile_id), host=host, port=port, client_id=client_id, account=account)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Connector positions failed:[/red] {exc}")
        return EXIT_RUN_FAILED
    if result.get("status") == "error":
        console.print(f"[red]{rich_escape(str(result.get('error')))}[/red]")
        return EXIT_RUN_FAILED
    rows = result.get("positions", [])
    if not rows:
        console.print("[dim]No positions returned.[/dim]")
        return EXIT_SUCCESS
    table = Table(title=f"Positions · {result.get('profile_id')}", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Account")
    table.add_column("Symbol")
    table.add_column("Type")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Currency")
    for row in rows:
        table.add_row(
            str(row.get("account") or ""),
            str(row.get("local_symbol") or row.get("symbol") or ""),
            str(row.get("sec_type") or ""),
            str(row.get("position") or ""),
            str(row.get("avg_cost") or ""),
            str(row.get("currency") or ""),
        )
    console.print(table)
    return EXIT_SUCCESS


def cmd_connector_orders(
    profile_id: Optional[str] = None,
    *,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
    include_executions: bool = False,
) -> int:
    """Print open orders from a connector profile."""
    from src.trading.service import get_open_orders

    try:
        result = get_open_orders(
            _profile_id(profile_id),
            host=host,
            port=port,
            client_id=client_id,
            account=account,
            include_executions=include_executions,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Connector orders failed:[/red] {exc}")
        return EXIT_RUN_FAILED
    if result.get("status") == "error":
        console.print(f"[red]{rich_escape(str(result.get('error')))}[/red]")
        return EXIT_RUN_FAILED
    orders = result.get("open_orders", [])
    if not orders:
        console.print("[dim]No open orders returned.[/dim]")
        return EXIT_SUCCESS
    table = Table(title=f"Open Orders · {result.get('profile_id')}", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Account")
    table.add_column("Symbol")
    table.add_column("Action")
    table.add_column("Type")
    table.add_column("Qty", justify="right")
    table.add_column("Limit", justify="right")
    table.add_column("Status")
    for row in orders:
        contract = row.get("contract") or {}
        order = row.get("order") or row
        order_status = row.get("status") or {}
        table.add_row(
            str(order.get("account") or ""),
            str(contract.get("local_symbol") or contract.get("symbol") or ""),
            str(order.get("action") or ""),
            str(order.get("order_type") or ""),
            str(order.get("total_quantity") or ""),
            str(order.get("limit_price") or ""),
            str(order_status.get("status") or ""),
        )
    console.print(table)
    return EXIT_SUCCESS


def cmd_connector_quote(
    symbol: str,
    profile_id: Optional[str] = None,
    *,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
) -> int:
    """Print a quote from a connector profile."""
    from src.trading.service import get_quote

    try:
        result = get_quote(
            symbol,
            _profile_id(profile_id),
            host=host,
            port=port,
            client_id=client_id,
            account=account,
            exchange=exchange,
            currency=currency,
            sec_type=sec_type,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Connector quote failed:[/red] {exc}")
        return EXIT_RUN_FAILED
    if result.get("status") == "error":
        console.print(f"[red]{rich_escape(str(result.get('error')))}[/red]")
        return EXIT_RUN_FAILED
    quote = result.get("quote", {})
    table = Table(title=f"Quote {result.get('symbol', symbol)} · {result.get('profile_id')}", box=box.SIMPLE_HEAVY)
    table.add_column("Bid", justify="right")
    table.add_column("Ask", justify="right")
    table.add_column("Last", justify="right")
    table.add_column("Close", justify="right")
    table.add_column("Volume", justify="right")
    table.add_row(
        str(quote.get("bid") or ""),
        str(quote.get("ask") or ""),
        str(quote.get("last") or ""),
        str(quote.get("close") or ""),
        str(quote.get("volume") or ""),
    )
    console.print(table)
    return EXIT_SUCCESS


def cmd_connector_history(
    symbol: str,
    profile_id: Optional[str] = None,
    *,
    host: str | None = None,
    port: int | None = None,
    client_id: int | None = None,
    account: str | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
    duration: str = "30 D",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    period: str = "1d",
    limit: int = 90,
) -> int:
    """Print historical bars from a connector profile."""
    from src.trading.service import get_history

    try:
        result = get_history(
            symbol,
            _profile_id(profile_id),
            host=host,
            port=port,
            client_id=client_id,
            account=account,
            exchange=exchange,
            currency=currency,
            sec_type=sec_type,
            duration=duration,
            bar_size=bar_size,
            what_to_show=what_to_show,
            use_rth=use_rth,
            period=period,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Connector history failed:[/red] {exc}")
        return EXIT_RUN_FAILED
    if result.get("status") == "error":
        console.print(f"[red]{rich_escape(str(result.get('error')))}[/red]")
        return EXIT_RUN_FAILED
    rows = result.get("bars", [])
    if not rows:
        console.print("[dim]No historical bars returned.[/dim]")
        return EXIT_SUCCESS
    table = Table(title=f"History {result.get('symbol', symbol)} · {result.get('profile_id')}", box=box.SIMPLE_HEAVY)
    table.add_column("Date")
    table.add_column("Open", justify="right")
    table.add_column("High", justify="right")
    table.add_column("Low", justify="right")
    table.add_column("Close", justify="right")
    table.add_column("Volume", justify="right")
    for row in rows[-20:]:
        table.add_row(
            str(row.get("date") or ""),
            str(row.get("open") or ""),
            str(row.get("high") or ""),
            str(row.get("low") or ""),
            str(row.get("close") or ""),
            str(row.get("volume") or ""),
        )
    console.print(table)
    return EXIT_SUCCESS


def _live_profile_connector(
    profile_id: Optional[str],
    *,
    require_runner: bool = False,
) -> tuple[int, Optional[str]]:
    """Resolve a profile to a live-capable connector key."""
    try:
        profile = _selected_profile_or(profile_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return EXIT_USAGE_ERROR, None
    if profile.environment != "live" or profile.transport != "remote_mcp":
        console.print(f"[red]{profile.id} is not a live remote MCP connector profile.[/red]")
        return EXIT_USAGE_ERROR, None
    if require_runner:
        from src.trading.service import profile_supports_live_runner

        if not profile_supports_live_runner(profile):
            console.print(f"[red]{profile.id} does not support live runner management.[/red]")
            return EXIT_USAGE_ERROR, None
    return EXIT_SUCCESS, profile.connector


def cmd_connector_authorize(profile_id: Optional[str]) -> int:
    """Authorize a remote MCP connector profile."""
    code, broker = _live_profile_connector(profile_id)
    if code != EXIT_SUCCESS or broker is None:
        return code
    return cmd_live_authorize(broker)


def cmd_connector_status(profile_id: Optional[str]) -> int:
    """Show connector status."""
    try:
        profile = _selected_profile_or(profile_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return EXIT_USAGE_ERROR
    if profile.environment == "live" and profile.transport == "remote_mcp":
        check_code = cmd_connector_check(profile.id)
        if check_code != EXIT_SUCCESS:
            return check_code
        return cmd_live_status(profile.connector)
    return cmd_connector_check(profile.id)


def cmd_connector_start(profile_id: Optional[str]) -> int:
    """Start a live remote MCP connector runner."""
    code, broker = _live_profile_connector(profile_id, require_runner=True)
    if code != EXIT_SUCCESS or broker is None:
        return code
    return cmd_live_start(broker)


def cmd_connector_stop(profile_id: Optional[str]) -> int:
    """Stop a live remote MCP connector runner."""
    code, broker = _live_profile_connector(profile_id, require_runner=True)
    if code != EXIT_SUCCESS or broker is None:
        return code
    return cmd_live_stop(broker)


def cmd_connector_halt(profile_id: Optional[str]) -> int:
    """Trip the halt switch for a live remote MCP connector profile."""
    code, broker = _live_profile_connector(profile_id, require_runner=True)
    if code != EXIT_SUCCESS or broker is None:
        return code
    return cmd_live_halt(broker)


def cmd_connector_resume(profile_id: Optional[str]) -> int:
    """Clear the halt switch for a live remote MCP connector profile."""
    code, broker = _live_profile_connector(profile_id, require_runner=True)
    if code != EXIT_SUCCESS or broker is None:
        return code
    return cmd_live_resume(broker)


def cmd_connector_revoke(profile_id: Optional[str]) -> int:
    """Revoke a live remote MCP connector profile."""
    code, broker = _live_profile_connector(profile_id)
    if code != EXIT_SUCCESS or broker is None:
        return code
    return cmd_live_revoke(broker)


def _dispatch_connector(args: argparse.Namespace) -> int:
    """Route parsed ``connector`` subcommands."""
    sub = getattr(args, "connector_command", None)
    if sub == "list":
        return cmd_connector_list()
    if sub == "use":
        return cmd_connector_use(args.profile)
    if sub == "configure":
        return cmd_connector_configure(
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
            yes=args.yes,
        )
    if sub == "check":
        return cmd_connector_check(
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
        )
    if sub == "account":
        return cmd_connector_account(
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
        )
    if sub == "positions":
        return cmd_connector_positions(
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
        )
    if sub == "orders":
        return cmd_connector_orders(
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
            include_executions=args.include_executions,
        )
    if sub == "quote":
        return cmd_connector_quote(
            args.symbol,
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
            exchange=args.exchange,
            currency=args.currency,
            sec_type=args.sec_type,
        )
    if sub == "history":
        return cmd_connector_history(
            args.symbol,
            args.profile,
            host=args.host,
            port=args.port,
            client_id=args.client_id,
            account=args.account,
            exchange=args.exchange,
            currency=args.currency,
            sec_type=args.sec_type,
            duration=args.duration,
            bar_size=args.bar_size,
            what_to_show=args.what_to_show,
            use_rth=not args.no_rth,
            period=args.period,
            limit=args.bar_limit,
        )
    if sub == "authorize":
        return cmd_connector_authorize(args.profile)
    if sub == "status":
        return cmd_connector_status(args.profile)
    if sub == "start":
        return cmd_connector_start(args.profile)
    if sub == "stop":
        return cmd_connector_stop(args.profile)
    if sub == "halt":
        return cmd_connector_halt(args.profile)
    if sub == "resume":
        return cmd_connector_resume(args.profile)
    if sub == "revoke":
        return cmd_connector_revoke(args.profile)
    console.print("[red]connector requires a subcommand.[/red] Try: vibe-trading connector list")
    return EXIT_USAGE_ERROR


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser with subcommands and compatibility flags."""
    parser = argparse.ArgumentParser(description="Vibe-Trading CLI")
    parser.add_argument("--version", action="version", version=f"vibe-trading {_VERSION}")
    parser.add_argument("-p", "--prompt", type=str, help="Prompt text")
    parser.add_argument("-f", "--prompt-file", type=Path, help="Read prompt text from a file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    parser.add_argument("--no-rich", action="store_true", help="Disable Rich formatting")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--continue", dest="cont", nargs=2, metavar=("RUN_ID", "PROMPT"), help="Continue a run")
    parser.add_argument("--list", action="store_true", help="List runs")
    parser.add_argument("--show", metavar="RUN_ID", help="Show run details")
    parser.add_argument("--code", metavar="RUN_ID", help="Show generated code")
    parser.add_argument("--pine", metavar="RUN_ID", help="Show Pine Script for TradingView")
    parser.add_argument("--trace", metavar="RUN_ID", help="Replay a run trace")
    parser.add_argument("--skills", action="store_true", help="List skills")
    parser.add_argument("--max-iter", type=int, default=50, help="Maximum agent iterations")

    parser.add_argument("--swarm-presets", action="store_true", help="List swarm presets")
    parser.add_argument("--swarm-inspect", metavar="PRESET", help="Inspect a swarm preset without running it")
    parser.add_argument("--swarm-run", nargs="+", metavar=("PRESET", "VARS"), help="Run a swarm preset")
    parser.add_argument("--swarm-list", action="store_true", help="List swarm runs")
    parser.add_argument("--swarm-show", metavar="RUN_ID", help="Show a swarm run")
    parser.add_argument("--swarm-cancel", metavar="RUN_ID", help="Cancel a swarm run")

    parser.add_argument("--sessions", action="store_true", help="List sessions")
    parser.add_argument("--session-chat", metavar="SESSION_ID", help="Continue a session chat")
    parser.add_argument("--upload", metavar="FILE_PATH", help="Upload a file")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a prompt")
    run_parser.add_argument("-p", "--prompt", dest="run_prompt", type=str, help="Prompt text")
    run_parser.add_argument("-f", "--prompt-file", dest="run_prompt_file", type=Path, help="Read prompt text from a file")
    run_parser.add_argument("--json", dest="run_json", action="store_true", help="Print machine-readable JSON output")
    run_parser.add_argument("--no-rich", dest="run_no_rich", action="store_true", help="Disable Rich formatting")
    run_parser.add_argument("--max-iter", dest="run_max_iter", type=int, default=50, help="Maximum agent iterations")

    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Listen port")
    serve_parser.add_argument("--dev", action="store_true", help="Start the Vite dev server")

    provider_parser = subparsers.add_parser("provider", help="Manage OAuth providers")
    provider_subparsers = provider_parser.add_subparsers(dest="provider_command")
    login_parser = provider_subparsers.add_parser("login", help="Authenticate with an OAuth provider")
    login_parser.add_argument("provider", help="OAuth provider name, e.g. openai-codex")
    provider_subparsers.add_parser("doctor", help="Print redacted provider diagnostics")

    list_parser = subparsers.add_parser("list", help="List runs")
    list_parser.add_argument("--limit", dest="list_limit", type=int, default=20, help="Maximum number of runs")

    show_parser = subparsers.add_parser("show", help="Show run details")
    show_parser.add_argument("run_id", help="Run identifier")

    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    chat_parser.add_argument("--max-iter", dest="chat_max_iter", type=int, default=50, help="Maximum agent iterations")

    subparsers.add_parser("init", help="Interactive setup: create ~/.vibe-trading/.env")

    # Cross-platform frontend setup. See cmd_setup() for details.
    setup_parser = subparsers.add_parser(
        "setup",
        help="Install frontend dependencies and build the production bundle",
    )
    setup_parser.add_argument(
        "--frontend-dir",
        default=str(AGENT_DIR.parent / "frontend"),
        help="Path to the frontend directory (default: <repo>/frontend)",
    )

    # Cross-platform dev mode. See cmd_dev() for details.
    dev_parser = subparsers.add_parser(
        "dev",
        help="Start backend + frontend dev servers in one process",
    )
    dev_parser.add_argument(
        "--port",
        type=int,
        default=8899,
        help="Backend port (default: 8899)",
    )
    dev_parser.add_argument(
        "--frontend-port",
        type=int,
        default=5899,
        help="Vite dev server port, must match vite.config.ts (default: 5899)",
    )
    dev_parser.add_argument(
        "--frontend-dir",
        default=str(AGENT_DIR.parent / "frontend"),
        help="Path to the frontend directory (default: <repo>/frontend)",
    )

    memory_parser = subparsers.add_parser("memory", help="Inspect persistent memory")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")

    memory_list_parser = memory_subparsers.add_parser("list", help="List memory entries")
    memory_list_parser.add_argument(
        "--type",
        dest="memory_type",
        choices=MEMORY_TYPES,
        help="Filter by memory type",
    )

    memory_show_parser = memory_subparsers.add_parser("show", help="Show a memory entry")
    memory_show_parser.add_argument("name", help="Memory title or filename stem")

    memory_search_parser = memory_subparsers.add_parser("search", help="Recall memories for a query")
    memory_search_parser.add_argument("query", help="Search text")
    memory_search_parser.add_argument(
        "--limit", dest="memory_limit", type=int, default=5, help="Maximum matches (default: 5)"
    )

    memory_forget_parser = memory_subparsers.add_parser("forget", help="Remove a memory entry")
    memory_forget_parser.add_argument("name", help="Memory title or filename stem")
    memory_forget_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    connector_parser = subparsers.add_parser("connector", help="Manage trading connector profiles")
    connector_subparsers = connector_parser.add_subparsers(dest="connector_command")

    connector_subparsers.add_parser("list", help="List selectable connector profiles")

    connector_use = connector_subparsers.add_parser("use", help="Select the default connector profile")
    connector_use.add_argument("profile", help="Profile id, e.g. ibkr-paper-local")

    def _add_connector_profile_arg(p: argparse.ArgumentParser, *, required: bool = False) -> None:
        if required:
            p.add_argument("profile", help="Connector profile id")
        else:
            p.add_argument("profile", nargs="?", default=None, help="Connector profile id (default: selected)")

    def _add_connector_local(p: argparse.ArgumentParser) -> None:
        p.add_argument("--host", default=None)
        p.add_argument("--port", type=int, default=None)
        p.add_argument("--client-id", dest="client_id", type=int, default=None)
        p.add_argument("--account", default=None, help="Optional account code")

    def _add_connector_contract(p: argparse.ArgumentParser) -> None:
        p.add_argument("--exchange", default="SMART")
        p.add_argument("--currency", default="USD")
        p.add_argument("--sec-type", dest="sec_type", default="STK")

    connector_configure = connector_subparsers.add_parser("configure", help="Configure a local connector profile")
    _add_connector_profile_arg(connector_configure, required=True)
    connector_configure.add_argument("--host", default="127.0.0.1")
    connector_configure.add_argument("--port", type=int, default=None)
    connector_configure.add_argument("--client-id", dest="client_id", type=int, default=77)
    connector_configure.add_argument("--account", default=None)
    connector_configure.add_argument("-y", "--yes", action="store_true", help="Overwrite without prompting")

    connector_check = connector_subparsers.add_parser("check", help="Check selected connector readiness")
    _add_connector_profile_arg(connector_check)
    _add_connector_local(connector_check)

    connector_status = connector_subparsers.add_parser("status", help="Show selected connector status")
    _add_connector_profile_arg(connector_status)

    connector_authorize = connector_subparsers.add_parser("authorize", help="Authorize a remote MCP connector profile")
    _add_connector_profile_arg(connector_authorize)

    connector_account = connector_subparsers.add_parser("account", help="Read account summary")
    _add_connector_profile_arg(connector_account)
    _add_connector_local(connector_account)

    connector_positions = connector_subparsers.add_parser("positions", help="Read current positions")
    _add_connector_profile_arg(connector_positions)
    _add_connector_local(connector_positions)

    connector_orders = connector_subparsers.add_parser("orders", help="Read open orders")
    _add_connector_profile_arg(connector_orders)
    _add_connector_local(connector_orders)
    connector_orders.add_argument("--include-executions", action="store_true")

    connector_quote = connector_subparsers.add_parser("quote", help="Read a quote snapshot")
    connector_quote.add_argument("symbol")
    _add_connector_profile_arg(connector_quote)
    _add_connector_local(connector_quote)
    _add_connector_contract(connector_quote)

    connector_history = connector_subparsers.add_parser("history", help="Read historical bars")
    connector_history.add_argument("symbol")
    _add_connector_profile_arg(connector_history)
    _add_connector_local(connector_history)
    _add_connector_contract(connector_history)
    connector_history.add_argument("--duration", default="30 D", help="IBKR (local_tws) duration string")
    connector_history.add_argument("--bar-size", dest="bar_size", default="1 day", help="IBKR (local_tws) bar size")
    connector_history.add_argument("--what-to-show", dest="what_to_show", default="TRADES")
    connector_history.add_argument("--no-rth", action="store_true", help="Include outside-regular-hours data when available")
    connector_history.add_argument("--period", default="1d", help="Bar interval for SDK connectors: 1m/5m/15m/30m/1h/4h/1d/1w/1M")
    connector_history.add_argument("--limit", dest="bar_limit", type=int, default=90, help="Number of bars for SDK connectors")

    for name, help_text in (
        ("start", "Start the selected live connector runner"),
        ("stop", "Stop the selected live connector runner"),
        ("halt", "Trip the selected live connector kill switch"),
        ("resume", "Clear the selected live connector kill switch"),
        ("revoke", "Revoke the selected live connector OAuth token and mandate"),
    ):
        p = connector_subparsers.add_parser(name, help=help_text)
        _add_connector_profile_arg(p)

    # Alpha Zoo subcommands (registered via cli_handlers.add_subparser)
    from src.factors.cli_handlers import add_subparser as _add_alpha_subparser
    _add_alpha_subparser(subparsers)

    # Hypothesis Registry subcommands
    from src.hypotheses.cli_handlers import add_subparser as _add_hypothesis_subparser
    _add_hypothesis_subparser(subparsers)

    return parser


def _handle_prompt_command(
    prompt: Optional[str],
    prompt_file: Optional[Path],
    *,
    max_iter: int,
    json_mode: bool,
    no_rich: bool,
) -> int:
    """Resolve a prompt and execute it."""
    resolved_prompt, error_message = _read_prompt_source(prompt, prompt_file, no_rich=no_rich)
    if error_message:
        if json_mode:
            _print_json_result({"status": "failed", "run_id": None, "run_dir": None, "reason": error_message})
        else:
            message = error_message if no_rich else f"[red]{error_message}[/red]"
            print(error_message) if no_rich else console.print(message)
        return EXIT_USAGE_ERROR
    if not resolved_prompt:
        if json_mode:
            _print_json_result({"status": "failed", "run_id": None, "run_dir": None, "reason": "Prompt cannot be empty"})
        else:
            print("Prompt cannot be empty") if no_rich else console.print("[red]Prompt cannot be empty[/red]")
        return EXIT_USAGE_ERROR
    return cmd_run(resolved_prompt, max_iter, json_mode=json_mode, no_rich=no_rich)


_INIT_ENV_PATH = Path.home() / ".vibe-trading" / ".env"

_PROVIDER_CHOICES: list[dict[str, str | None]] = [
    {
        "label": "OpenRouter (recommended - multiple models)",
        "provider": "openrouter",
        "key_env": "OPENROUTER_API_KEY",
        "base_env": "OPENROUTER_BASE_URL",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "deepseek/deepseek-v4-pro",
        "key_prefix": "sk-or-",
        "key_placeholder": "sk-or-v1-...",
    },
    {
        "label": "DeepSeek",
        "provider": "deepseek",
        "key_env": "DEEPSEEK_API_KEY",
        "base_env": "DEEPSEEK_BASE_URL",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-pro",
        "key_prefix": "sk-",
        "key_placeholder": "sk-...",
    },
    {
        "label": "OpenAI",
        "provider": "openai",
        "key_env": "OPENAI_API_KEY",
        "base_env": "OPENAI_BASE_URL",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.5",
        "key_prefix": "sk-",
        "key_placeholder": "sk-...",
    },
    {
        "label": "Gemini",
        "provider": "gemini",
        "key_env": "GEMINI_API_KEY",
        "base_env": "GEMINI_BASE_URL",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.5-flash",
        "key_prefix": None,
        "key_placeholder": "api-key...",
    },
    {
        "label": "Groq",
        "provider": "groq",
        "key_env": "GROQ_API_KEY",
        "base_env": "GROQ_BASE_URL",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "key_prefix": "gsk_",
        "key_placeholder": "gsk_...",
    },
    {
        "label": "DashScope / Qwen",
        "provider": "dashscope",
        "key_env": "DASHSCOPE_API_KEY",
        "base_env": "DASHSCOPE_BASE_URL",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus-latest",
        "key_prefix": "sk-",
        "key_placeholder": "sk-...",
    },
    {
        "label": "Zhipu",
        "provider": "zhipu",
        "key_env": "ZHIPU_API_KEY",
        "base_env": "ZHIPU_BASE_URL",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-5.1",
        "key_prefix": None,
        "key_placeholder": "api-key...",
    },
    {
        "label": "Moonshot / Kimi",
        "provider": "moonshot",
        "key_env": "MOONSHOT_API_KEY",
        "base_env": "MOONSHOT_BASE_URL",
        "base_url": "https://api.moonshot.ai/v1",
        "model": "kimi-k2.6",
        "key_prefix": "sk-",
        "key_placeholder": "sk-...",
    },
    {
        "label": "MiniMax",
        "provider": "minimax",
        "key_env": "MINIMAX_API_KEY",
        "base_env": "MINIMAX_BASE_URL",
        "base_url": "https://api.minimax.io/v1",
        "model": "MiniMax-M3",
        "key_prefix": None,
        "key_placeholder": "api-key...",
    },
    {
        "label": "Xiaomi MIMO",
        "provider": "mimo",
        "key_env": "MIMO_API_KEY",
        "base_env": "MIMO_BASE_URL",
        "base_url": "https://api.xiaomimimo.com/v1",
        "model": "MiMo-72B-A27B",
        "key_prefix": None,
        "key_placeholder": "api-key...",
    },
    {
        "label": "Z.ai (Coding platform)",
        "provider": "zai",
        "key_env": "ZAI_API_KEY",
        "base_env": "ZAI_BASE_URL",
        "base_url": "https://api.z.ai/api/coding/paas/v4",
        "model": "glm-5.1",
        "key_prefix": None,
        "key_placeholder": "api-key...",
    },
    {
        "label": "Ollama (local, free)",
        "provider": "ollama",
        "key_env": None,
        "base_env": "OLLAMA_BASE_URL",
        "base_url": "http://localhost:11434",
        "model": "qwen2.5:32b",
        "key_prefix": None,
        "key_placeholder": None,
    },
    {
        "label": "OpenAI Codex (ChatGPT OAuth)",
        "provider": "openai-codex",
        "key_env": None,
        "base_env": "OPENAI_CODEX_BASE_URL",
        "base_url": "https://chatgpt.com/backend-api/codex/responses",
        "model": "openai-codex/gpt-5.3-codex",
        "key_prefix": None,
        "key_placeholder": None,
    },
]


def _validate_api_key(api_key: str, expected_prefix: str | None) -> bool:
    """Basic API-key format validation used during interactive setup."""
    if expected_prefix is None:
        return True
    return api_key.startswith(expected_prefix)


def _render_env_content(config: dict[str, str]) -> str:
    """Render .env content with stable ordering."""
    ordered_keys = [
        "LANGCHAIN_TEMPERATURE",
        "LANGCHAIN_PROVIDER",
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_CODEX_BASE_URL",
        "GEMINI_API_KEY",
        "GEMINI_BASE_URL",
        "GROQ_API_KEY",
        "GROQ_BASE_URL",
        "DASHSCOPE_API_KEY",
        "DASHSCOPE_BASE_URL",
        "ZHIPU_API_KEY",
        "ZHIPU_BASE_URL",
        "MOONSHOT_API_KEY",
        "MOONSHOT_BASE_URL",
        "MINIMAX_API_KEY",
        "MINIMAX_BASE_URL",
        "MIMO_API_KEY",
        "MIMO_BASE_URL",
        "ZAI_API_KEY",
        "ZAI_BASE_URL",
        "OLLAMA_BASE_URL",
        "LANGCHAIN_MODEL_NAME",
        "TUSHARE_TOKEN",
        "TIMEOUT_SECONDS",
        "MAX_RETRIES",
    ]
    lines: list[str] = []
    for key in ordered_keys:
        value = config.get(key)
        if value:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


from src.memory.persistent import MEMORY_TYPES  # noqa: E402  source-of-truth for choices/invariants

_MEMORY_TYPE_STYLES = {
    "user": "cyan",
    "feedback": "yellow",
    "project": "green",
    "reference": "magenta",
}

# Invariant: every persisted memory type has a display style. If a new type
# is added in src.memory.persistent.MEMORY_TYPES, this assert fails fast
# instead of silently rendering it in fallback white.
assert set(_MEMORY_TYPE_STYLES) == set(MEMORY_TYPES), (
    f"MEMORY_TYPES vs _MEMORY_TYPE_STYLES drift: "
    f"types={sorted(MEMORY_TYPES)}, styles={sorted(_MEMORY_TYPE_STYLES)}"
)


def cmd_memory_list(memory_type: Optional[str] = None, *, memory_dir: Optional[Path] = None) -> int:
    """List persisted memory entries."""
    from src.memory.persistent import PersistentMemory

    pm = PersistentMemory(memory_dir=memory_dir)
    entries = pm.list_entries()
    if memory_type:
        entries = [e for e in entries if e.memory_type == memory_type]

    if not entries:
        scope = f" type={memory_type}" if memory_type else ""
        console.print(f"[dim]No memory entries found{scope}.[/dim]")
        return EXIT_SUCCESS

    entries.sort(key=lambda e: -e.modified_at)
    table = Table(title="Persistent Memory", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Title", style="bold")
    table.add_column("Type")
    table.add_column("Description", overflow="fold")
    table.add_column("Modified", style="dim")

    for e in entries:
        style = _MEMORY_TYPE_STYLES.get(e.memory_type, "white")
        modified = datetime.fromtimestamp(e.modified_at).strftime("%Y-%m-%d %H:%M")
        table.add_row(
            rich_escape(e.title),
            f"[{style}]{e.memory_type}[/{style}]",
            rich_escape(e.description) or "—",
            modified,
        )

    console.print(table)
    console.print(f"[dim]{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}[/dim]")
    return EXIT_SUCCESS


def cmd_memory_show(name: str, *, memory_dir: Optional[Path] = None) -> int:
    """Show full content of a single memory entry."""
    from src.memory.persistent import PersistentMemory

    pm = PersistentMemory(memory_dir=memory_dir)
    entry = pm.find(name)
    if entry is None:
        console.print(f"[red]Memory not found:[/red] {rich_escape(name)}")
        console.print("[dim]Run `vibe-trading memory list` to see available titles.[/dim]")
        return EXIT_USAGE_ERROR

    style = _MEMORY_TYPE_STYLES.get(entry.memory_type, "white")
    header = (
        f"[bold]{rich_escape(entry.title)}[/bold]\n"
        f"[{style}]{entry.memory_type}[/{style}]  •  [dim]{rich_escape(entry.path.name)}[/dim]\n"
        f"[dim]{rich_escape(entry.description)}[/dim]"
    )
    console.print(Panel(header, border_style="cyan"))
    console.print(rich_escape(entry.body.rstrip()) or "[dim](empty body)[/dim]")
    return EXIT_SUCCESS


def cmd_memory_search(query: str, max_results: int = 5, *, memory_dir: Optional[Path] = None) -> int:
    """Run keyword recall and display the top matches."""
    from src.memory.persistent import PersistentMemory

    pm = PersistentMemory(memory_dir=memory_dir)
    results = pm.find_relevant(query, max_results=max_results)
    if not results:
        console.print(f"[dim]No matches for[/dim] [bold]{rich_escape(query)}[/bold]")
        return EXIT_SUCCESS

    table = Table(title=f"Recall: {rich_escape(query)}", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Type")
    table.add_column("Description", overflow="fold")

    for rank, e in enumerate(results, start=1):
        style = _MEMORY_TYPE_STYLES.get(e.memory_type, "white")
        table.add_row(
            str(rank),
            rich_escape(e.title),
            f"[{style}]{e.memory_type}[/{style}]",
            rich_escape(e.description) or "—",
        )

    console.print(table)
    return EXIT_SUCCESS


def cmd_memory_forget(name: str, *, yes: bool = False, memory_dir: Optional[Path] = None) -> int:
    """Remove a memory entry by name."""
    from src.memory.persistent import PersistentMemory

    pm = PersistentMemory(memory_dir=memory_dir)
    entry = pm.find(name)
    if entry is None:
        console.print(f"[red]Memory not found:[/red] {rich_escape(name)}")
        return EXIT_USAGE_ERROR

    if not yes:
        style = _MEMORY_TYPE_STYLES.get(entry.memory_type, "white")
        console.print(
            f"About to forget [bold]{rich_escape(entry.title)}[/bold] "
            f"([{style}]{entry.memory_type}[/{style}], {rich_escape(entry.path.name)})."
        )
        try:
            proceed = Confirm.ask("Proceed?", default=False)
        except EOFError:
            console.print("[dim]No input available; use --yes for non-interactive deletes.[/dim]")
            return EXIT_USAGE_ERROR
        if not proceed:
            console.print("[dim]Aborted.[/dim]")
            return EXIT_SUCCESS

    if pm.remove_entry(entry):
        console.print(f"[green]Forgot[/green] {rich_escape(entry.title)}")
        return EXIT_SUCCESS
    console.print(f"[red]Failed to remove[/red] {rich_escape(entry.title)}")
    return EXIT_RUN_FAILED


def cmd_init() -> int:
    """Interactive setup: create ~/.vibe-trading/.env."""
    console.print(Panel("[bold cyan]Vibe-Trading setup[/bold cyan]\n[dim]Configure the default LLM provider and data tokens.[/dim]", border_style="cyan"))

    if _INIT_ENV_PATH.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {_INIT_ENV_PATH}")
        if not Confirm.ask("Overwrite it?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return 0

    provider_table = Table(title="LLM Providers", box=box.SIMPLE_HEAVY, show_lines=False, border_style="dim")
    provider_table.add_column("#", justify="right", style="dim", width=3)
    provider_table.add_column("Provider", style="cyan")
    provider_table.add_column("Default model", style="dim")
    provider_table.add_column("Credential", style="dim")
    for idx, option in enumerate(_PROVIDER_CHOICES, start=1):
        credential = "OAuth" if option["provider"] == "openai-codex" else "none" if option["key_env"] is None else str(option["key_env"])
        provider_table.add_row(str(idx), str(option["label"]), str(option["model"]), credential)
    console.print(provider_table)

    choice = IntPrompt.ask(
        "Provider",
        choices=[str(i) for i in range(1, len(_PROVIDER_CHOICES) + 1)],
        default=1,
        show_choices=False,
    )
    selected = _PROVIDER_CHOICES[choice - 1]

    provider = str(selected["provider"])
    key_env = selected["key_env"]
    base_env = str(selected["base_env"])
    default_base_url = str(selected["base_url"])
    default_model = str(selected["model"])
    key_prefix = selected["key_prefix"]
    key_placeholder = selected["key_placeholder"]

    env_values: dict[str, str] = {
        "LANGCHAIN_TEMPERATURE": "0.0",
        "LANGCHAIN_PROVIDER": provider,
        "LANGCHAIN_MODEL_NAME": default_model,
        "TIMEOUT_SECONDS": "120",
        "MAX_RETRIES": "2",
    }

    if key_env is not None:
        while True:
            api_key = Prompt.ask(
                f"Enter your {provider.capitalize()} API key",
                default=str(key_placeholder),
                password=True,
                show_default=False,
            ).strip()
            if _validate_api_key(api_key, str(key_prefix) if key_prefix is not None else None):
                env_values[str(key_env)] = api_key
                break
            console.print(
                f"[red]That key doesn't look right.[/red] Expected it to start with [bold]{key_prefix}[/bold]."
            )
    elif provider == "openai-codex":
        console.print("[dim]OpenAI Codex uses ChatGPT OAuth, not an API key.[/dim]")
        console.print("[dim]After setup, run: vibe-trading provider login openai-codex[/dim]")
    else:
        console.print("[dim]Ollama does not require an API key.[/dim]")

    env_values[base_env] = Prompt.ask(
        "Base URL",
        default=default_base_url,
        show_default=True,
    ).strip()

    env_values["LANGCHAIN_MODEL_NAME"] = Prompt.ask(
        "Select default model",
        default=default_model,
        show_default=True,
    ).strip()

    tushare_token = Prompt.ask(
        "(Optional) Enter Tushare token for China A-share data",
        default="",
        show_default=False,
    ).strip()
    if tushare_token:
        env_values["TUSHARE_TOKEN"] = tushare_token

    _INIT_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    _INIT_ENV_PATH.write_text(_render_env_content(env_values), encoding="utf-8")
    try:
        _INIT_ENV_PATH.chmod(0o600)
    except OSError:
        pass

    next_steps = Table.grid(expand=True)
    next_steps.add_column(width=10, style="dim")
    next_steps.add_column(ratio=1)
    next_steps.add_row("Config", f"[cyan]{_INIT_ENV_PATH}[/cyan]")
    next_steps.add_row("Run", "[bold]vibe-trading[/bold]")
    if provider == "openai-codex":
        next_steps.add_row("OAuth", "[bold]vibe-trading provider login openai-codex[/bold]")
    console.print(Panel(next_steps, title="Setup complete", border_style="green", padding=(0, 1)))
    return 0


# ---------------------------------------------------------------------------
# Cross-platform frontend setup / dev commands.
#
# These exist to bridge a real Windows footgun: the package's frontend uses
# TypeScript, but `npx tsc` on Windows does NOT resolve the locally-installed
# TypeScript binary. Instead, npx hits the npm registry and downloads an
# abandoned 10-year-old package called `tsc@2.0.4` that prints
# "This is not the tsc command you are looking for". The fix is to always
# invoke TypeScript via `npm exec --package=typescript tsc ...` (or
# `npx --package=typescript tsc ...`) on Windows; on POSIX, `npm run build`
# already works because npm prepends ./node_modules/.bin to PATH for local
# scripts.
# ---------------------------------------------------------------------------


def _is_windows() -> bool:
    """True when running on a Windows-like platform (win32, including Cygwin/MSYS)."""
    return sys.platform == "win32"


def _resolve_node_and_npm() -> tuple[Optional[str], Optional[str]]:
    """Return ``(node_path, npm_path)`` if both are on PATH, else ``(None, None)``.

    Used by ``cmd_setup`` to fail fast with a clear message instead of
    surfacing a cryptic ENOENT from npm itself.
    """
    node = shutil.which("node")
    npm = shutil.which("npm")
    return node, npm


def _build_frontend_cmd(frontend_dir: Path) -> list[list[str]]:
    """Return the ordered list of subprocess invocations needed to build the frontend.

    On Windows we explicitly pin ``--package=typescript`` / ``--package=vite``
    so npm cannot accidentally fetch the abandoned ``tsc`` package from the
    registry. On POSIX systems, ``npm run build`` is sufficient because npm
    prepends ``./node_modules/.bin`` to ``PATH`` for local scripts.

    Each inner list is a single ``subprocess.run`` invocation. Returned as a
    list of steps so the caller can stream progress.
    """
    is_win = _is_windows()
    if is_win:
        # `npm exec --package=typescript tsc -b` is the safe form on Windows;
        # plain `npx tsc` will fetch the abandoned `tsc@2.0.4` package.
        return [
            ["npm", "install", "--no-audit", "--no-fund"],
            ["npm", "exec", "--package=typescript", "--", "tsc", "-b"],
            ["npm", "exec", "--package=vite", "--", "vite", "build"],
        ]
    return [
        ["npm", "install", "--no-audit", "--no-fund"],
        ["npm", "run", "build"],
    ]


def _run_step(
    description: str,
    cmd: list[str],
    cwd: Path,
) -> bool:
    """Run one subprocess step, returning True on success.

    Decodes subprocess output as UTF-8 with ``errors="replace"`` so that
    non-ASCII bytes emitted by tools like Vite do not raise
    ``UnicodeDecodeError`` on platforms whose default codec is GBK/CP936
    (notably Windows). The captured text is only used to surface a
    friendly error message; lossy decoding is acceptable here.
    """
    console.print(f"[dim]  {description} …[/dim]")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
        )
    except FileNotFoundError as exc:
        console.print(f"[red]  failed:[/red] {exc}")
        return False
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        # Show the last 20 lines to keep noise manageable.
        tail = "\n".join(err.splitlines()[-20:]) if err else "(no output)"
        console.print(f"[red]  {description} failed:[/red]\n{tail}")
        return False
    return True


def cmd_setup(frontend_dir: Path) -> int:
    """Install frontend dependencies and build the production bundle.

    Cross-platform wrapper that hides the ``npx tsc`` / ``npm exec tsc``
    Windows footgun. Equivalent to running ``cd frontend && npm install
    && npm run build`` from a POSIX shell, but works on Windows without
    the user having to know about the abandoned ``tsc`` package on the
    npm registry.
    """
    console.print(
        Panel(
            f"[bold cyan]Vibe-Trading frontend setup[/bold cyan]\n"
            f"[dim]{frontend_dir}[/dim]",
            border_style="cyan",
            padding=(0, 1),
        )
    )

    if not frontend_dir.exists():
        console.print(
            f"[red]Frontend directory not found:[/red] {frontend_dir}\n"
            "[dim]Pass --frontend-dir to point at a different location.[/dim]"
        )
        return EXIT_USAGE_ERROR

    node, npm = _resolve_node_and_npm()
    if not node or not npm:
        missing = [name for name, path_ in (("node", node), ("npm", npm)) if not path_]
        console.print(
            f"[red]Required tool not on PATH:[/red] {', '.join(missing)}\n"
            "[dim]Install Node.js (>= 18) from https://nodejs.org and retry.[/dim]"
        )
        return EXIT_USAGE_ERROR

    # On Windows, ``npm`` is shipped as ``npm.cmd``; ``subprocess.run`` does
    # not consult ``PATHEXT`` for bare command names, so it would raise
    # ``FileNotFoundError`` even though ``shutil.which("npm")`` returned a
    # valid path. Resolve to the full path before invoking.
    npm_path = npm
    if _is_windows():
        steps = [
            [npm_path, *step[1:]] if step and step[0] == "npm" else step
            for step in _build_frontend_cmd(frontend_dir)
        ]
    else:
        steps = _build_frontend_cmd(frontend_dir)
    for step in steps:
        description = " ".join(step[:3])  # e.g. "npm install --no-audit"
        if not _run_step(description, step, frontend_dir):
            return EXIT_RUN_FAILED

    console.print(
        Panel(
            "[green]Frontend built.[/green]\n"
            f"  Artifacts: [cyan]{frontend_dir / 'dist'}[/cyan]\n"
            "[dim]Run [bold]vibe-trading serve[/bold] to serve everything on one port.[/dim]",
            border_style="green",
            padding=(0, 1),
        )
    )
    return EXIT_SUCCESS


def cmd_dev(
    backend_port: int = 8899,
    frontend_port: int = 5899,
    frontend_dir: Optional[Path] = None,
) -> int:
    """Start backend + Vite dev server in one foreground process.

    Spawns two child processes:

    * The FastAPI backend, launched from ``AGENT_DIR`` so that
      ``python -m cli._legacy serve`` resolves the in-repo ``cli`` package
      (launching it from the repo root would fail with
      ``ModuleNotFoundError: No module named 'cli'``).
    * The Vite dev server, launched from ``frontend_dir`` with the port
      from ``vite.config.ts`` (currently 5899). We do NOT hardcode
      ``5173`` — that would be wrong for this project.

    Both children inherit stdout/stderr so their logs are interleaved
    with the dev banner. ``Ctrl+C`` (SIGINT) and ``SIGTERM`` cleanly
    terminate both children.
    """
    frontend_dir = frontend_dir or (AGENT_DIR.parent / "frontend")
    if not frontend_dir.exists():
        console.print(
            f"[red]Frontend directory not found:[/red] {frontend_dir}\n"
            "[dim]Pass --frontend-dir to point at a different location.[/dim]"
        )
        return EXIT_USAGE_ERROR

    node, npm = _resolve_node_and_npm()
    if not node or not npm:
        missing = [name for name, path_ in (("node", node), ("npm", npm)) if not path_]
        console.print(
            f"[red]Required tool not on PATH:[/red] {', '.join(missing)}\n"
            "[dim]Install Node.js (>= 18) from https://nodejs.org and retry.[/dim]"
        )
        return EXIT_USAGE_ERROR

    backend_cmd = [sys.executable, "-m", "cli._legacy", "serve", "--port", str(backend_port)]
    # On Windows, ``npm`` is typically ``npm.cmd``. ``subprocess.Popen`` does
    # not consult ``PATHEXT`` for bare command names, so the call would fail
    # with ``FileNotFoundError`` even though ``shutil.which("npm")`` returned
    # a path. Use the resolved executable path directly.
    npm_executable = npm if _is_windows() else "npm"
    frontend_cmd = [npm_executable, "run", "dev", "--", "--port", str(frontend_port)]

    console.print(
        Panel(
            f"[bold cyan]Vibe-Trading dev[/bold cyan]\n"
            f"  Backend  → [cyan]http://127.0.0.1:{backend_port}[/cyan]  "
            f"(cwd: {AGENT_DIR})\n"
            f"  Frontend → [cyan]http://localhost:{frontend_port}[/cyan]  "
            f"(cwd: {frontend_dir})",
            border_style="cyan",
            padding=(0, 1),
        )
    )
    console.print("[dim]Press Ctrl+C to stop both servers.[/dim]\n")

    backend = subprocess.Popen(backend_cmd, cwd=str(AGENT_DIR))
    frontend = subprocess.Popen(frontend_cmd, cwd=str(frontend_dir))
    children = [backend, frontend]

    def _terminate_all() -> None:
        for child in children:
            if child.poll() is None:
                try:
                    child.terminate()
                except OSError:
                    pass

    # Wire signal handlers. On Windows, SIGTERM does not exist and signal
    # handlers must be installed from the main thread; KeyboardInterrupt is
    # the cross-platform path for Ctrl+C.
    if threading.current_thread() is threading.main_thread():
        try:
            signal.signal(signal.SIGINT, lambda *_: _terminate_all())
        except (ValueError, OSError):
            pass
        try:
            signal.signal(signal.SIGTERM, lambda *_: _terminate_all())
        except (AttributeError, ValueError, OSError):
            pass

    try:
        # Wait for whichever process exits first; if it's the backend we
        # bring the frontend down too, and vice versa.
        while True:
            time.sleep(0.5)
            if backend.poll() is not None or frontend.poll() is not None:
                break
    except KeyboardInterrupt:
        pass
    finally:
        _terminate_all()
        # Give the children a brief grace period, then force-kill.
        deadline = time.time() + 5
        for child in children:
            remaining = max(0.0, deadline - time.time())
            try:
                child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                try:
                    child.kill()
                except OSError:
                    pass

    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint returning a process exit code."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    try:
        args = parser.parse_args(raw_argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_USAGE_ERROR
    if not sys.stdout.isatty():
        args.no_rich = True
        if hasattr(args, "run_no_rich"):
            args.run_no_rich = True

    if args.command == "init":
        return cmd_init()
    if args.command == "setup":
        return _coerce_exit_code(
            cmd_setup(frontend_dir=Path(args.frontend_dir))
        )
    if args.command == "dev":
        return _coerce_exit_code(
            cmd_dev(
                backend_port=args.port,
                frontend_port=args.frontend_port,
                frontend_dir=Path(args.frontend_dir),
            )
        )
    if args.command == "serve":
        return serve_main(raw_argv[1:])
    if args.command == "provider":
        if args.provider_command == "login":
            return cmd_provider_login(args.provider)
        if args.provider_command == "doctor":
            return cmd_provider_doctor()
        console.print("[red]provider requires a subcommand.[/red] Try: vibe-trading provider doctor")
        return EXIT_USAGE_ERROR
    if args.command == "run":
        return _handle_prompt_command(
            args.run_prompt,
            args.run_prompt_file,
            max_iter=args.run_max_iter,
            json_mode=args.run_json,
            no_rich=args.run_no_rich,
        )
    if args.command == "list":
        return _coerce_exit_code(cmd_list(args.list_limit))
    if args.command == "show":
        return _coerce_exit_code(cmd_show(args.show))
    if args.command == "chat":
        return _coerce_exit_code(cmd_interactive(args.chat_max_iter))
    if args.command == "alpha":
        from src.factors.cli_handlers import dispatch as _alpha_dispatch
        return _coerce_exit_code(_alpha_dispatch(args))
    if args.command == "hypothesis":
        from src.hypotheses.cli_handlers import dispatch as _hyp_dispatch
        return _coerce_exit_code(_hyp_dispatch(args))
    if args.command == "connector":
        return _coerce_exit_code(_dispatch_connector(args))
    if args.command == "memory":
        if args.memory_command == "list":
            return _coerce_exit_code(cmd_memory_list(args.memory_type))
        if args.memory_command == "show":
            return _coerce_exit_code(cmd_memory_show(args.name))
        if args.memory_command == "search":
            return _coerce_exit_code(cmd_memory_search(args.query, args.memory_limit))
        if args.memory_command == "forget":
            return _coerce_exit_code(cmd_memory_forget(args.name, yes=args.yes))
        console.print("[red]memory requires a subcommand.[/red] Try: vibe-trading memory list")
        return EXIT_USAGE_ERROR

    if args.list:
        return _coerce_exit_code(cmd_list())
    if args.show:
        return _coerce_exit_code(cmd_show(args.show))
    if args.code:
        return _coerce_exit_code(cmd_code(args.code))
    if args.pine:
        return _coerce_exit_code(cmd_pine(args.pine))
    if args.trace:
        return _coerce_exit_code(cmd_trace(args.trace))
    if args.skills:
        return _coerce_exit_code(cmd_skills())

    if args.swarm_presets:
        return _coerce_exit_code(cmd_swarm_presets())
    if args.swarm_inspect:
        return _coerce_exit_code(cmd_swarm_inspect(args.swarm_inspect))
    if args.swarm_run:
        preset_name = args.swarm_run[0]
        vars_json = args.swarm_run[1] if len(args.swarm_run) > 1 else None
        return _coerce_exit_code(cmd_swarm_run_live(preset_name, vars_json))
    if args.swarm_list:
        return _coerce_exit_code(cmd_swarm_list())
    if args.swarm_show:
        return _coerce_exit_code(cmd_swarm_show(args.swarm_show))
    if args.swarm_cancel:
        return _coerce_exit_code(cmd_swarm_cancel(args.swarm_cancel))

    if args.sessions:
        return _coerce_exit_code(cmd_sessions())
    if args.session_chat:
        return _coerce_exit_code(cmd_session_chat(args.session_chat, args.max_iter))
    if args.upload:
        return _coerce_exit_code(cmd_upload(args.upload))
    if args.chat:
        return _coerce_exit_code(cmd_interactive(args.max_iter))
    if args.cont:
        return _coerce_exit_code(cmd_continue(args.cont[0], args.cont[1], args.max_iter, json_mode=args.json, no_rich=args.no_rich))

    # No flags and no subcommand: check for a prompt, otherwise enter interactive mode.
    if args.prompt or args.prompt_file or not sys.stdin.isatty():
        return _handle_prompt_command(
            args.prompt,
            args.prompt_file,
            max_iter=args.max_iter,
            json_mode=args.json,
            no_rich=args.no_rich,
        )

    # Default: interactive mode
    return _coerce_exit_code(cmd_interactive(args.max_iter))


if __name__ == "__main__":
    raise SystemExit(main())
