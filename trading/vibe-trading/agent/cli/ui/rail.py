"""Codex-style rail renderer for agent activity."""

from __future__ import annotations

import json
import re
import shutil
import textwrap
import threading
import time
from dataclasses import dataclass, field
from pathlib import PureWindowsPath
from typing import Any, Literal
from urllib.parse import urlparse

from rich.console import Group
from rich.text import Text

from cli.theme import Theme
from cli.utils.thinking_verbs import pick_thinking_verb

StepStatus = Literal["active", "done", "error", "warning"]

_MARKER = "#8a8f98"
_MARKER_ACTIVE = "#d1d5db"
_ACTION = "bold white"
_CMD = "bold #3b82f6"
_ARG = "#7dd3fc"
_PATH = "#f0abfc"
_DETAIL = "#6b7280"
_DONE = "bold #22c55e"
_ERROR = "bold #ef4444"
_WARNING = "bold #f59e0b"
_PLAIN_TAG = re.compile(
    r"\[/?(?:#[0-9a-fA-F]{3,6}|[a-zA-Z][a-zA-Z0-9_ -]*)(?:\s+[^\]]+)?\]"
)
_PATH_TOKEN = re.compile(
    r'("[^"]*[\\/][^"]*"|[A-Za-z]:[\\/][^\s,)]+|(?:\.{1,2}[\\/])?[^\s"]*[\\/][^\s"]+)'
)


@dataclass
class RailStep:
    title: str
    tool: str = ""
    args: Any = None
    status: StepStatus = "active"
    lines: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.monotonic)
    duration_s: float = 0.0


def _strip_markup(value: Any) -> str:
    return _PLAIN_TAG.sub("", str(value or "")).replace("\r\n", "\n").strip()


def _collapse_ws(value: Any) -> str:
    return re.sub(r"\s+", " ", _strip_markup(value)).strip()


def _coerce_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _format_tool_name(name: str) -> str:
    cleaned = str(name or "tool").strip().replace("-", " ").replace("_", " ")
    if cleaned.lower().startswith("get "):
        cleaned = cleaned[4:]
    return " ".join(part[:1].upper() + part[1:] for part in cleaned.split()) or "Tool"


def _tool_title(tool: str, args: Any) -> str:
    lower = str(tool or "tool").lower()
    if lower in {"bash", "background_run", "shell"}:
        return "shell command"
    if lower == "load_skill":
        return "skill"
    if lower in {"read_file", "file_read"}:
        return "file"
    if lower in {"write_file", "edit_file"}:
        return "file"
    if lower in {"read_url", "web_fetch", "fetch", "read_url_tool"}:
        return "url"
    if "search" in lower:
        return "web"
    if lower in {"get_market_data", "market_data", "stock_price", "get_stock_price"}:
        return "market data"
    if lower in {"answer", "final_answer"}:
        return "answer"
    return _format_tool_name(tool)


def _arg_value(args: Any, *keys: str) -> str:
    if not isinstance(args, dict):
        return ""
    for key in keys:
        value = args.get(key)
        if value:
            return _collapse_ws(value)
    return ""


def _initial_detail(tool: str, args: Any) -> str | None:
    if not isinstance(args, dict):
        return None
    lower = str(tool or "").lower()
    if lower in {"bash", "background_run", "shell"}:
        return None
    if lower in {"read_file", "file_read", "write_file", "edit_file"}:
        return _arg_value(args, "path", "file_path") or None
    if lower in {"read_url", "web_fetch", "fetch", "read_url_tool"}:
        url = _arg_value(args, "url")
        return f"fetching {_short_url(url)}" if url else None
    if "search" in lower:
        query = _arg_value(args, "query", "q")
        return query or None
    symbol = _arg_value(args, "symbol", "ticker", "code", "asset")
    return symbol or None


def _result_summary(tool: str, status: str, preview: Any) -> list[str]:
    text = _strip_markup(preview)
    lower = str(tool or "").lower()
    if lower == "load_skill":
        match = re.search(r"<skill\s+name=[\"']?([^\"'>\s]+)", text)
        if match:
            return [f"loaded {match.group(1)}"]

    payload: Any = None
    compact = _collapse_ws(text)
    source = text.strip()
    if source.startswith("{") or source.startswith("["):
        try:
            payload = json.loads(source)
        except json.JSONDecodeError:
            try:
                payload = json.loads(compact)
            except json.JSONDecodeError:
                payload = None

    if isinstance(payload, dict):
        if status != "ok":
            detail = payload.get("error") or payload.get("stderr") or payload.get("message") or compact
            return _compact_lines(f"Error: {_collapse_ws(detail)}", max_lines=3)
        if lower in {"bash", "background_run", "shell"}:
            stdout = payload.get("stdout")
            stderr = payload.get("stderr")
            if stdout:
                return _compact_lines(str(stdout), max_lines=5)
            if stderr:
                return _compact_lines(str(stderr), max_lines=4)
            return ["completed"]
        if lower in {"read_file", "file_read"}:
            content = str(payload.get("content") or "")
            return [f"read {len(content):,} chars"] if content else ["read file"]
        if lower == "load_skill":
            content = str(payload.get("content") or "")
            match = re.search(r"<skill\s+name=[\"']([^\"']+)[\"']", content)
            return [f"loaded {match.group(1)}"] if match else ["loaded skill"]
        if lower in {"read_url", "web_fetch", "fetch", "read_url_tool"}:
            title = payload.get("title")
            if title:
                return [_clip(_collapse_ws(title), 96)]
            content = payload.get("content") or payload.get("markdown") or payload.get("text")
            if content:
                return [f"read {len(str(content)):,} chars"]
        results = payload.get("results")
        if isinstance(results, list):
            return [f"Did 1 search · {len(results)} results"]
        for key in ("summary", "message", "stdout", "content"):
            if payload.get(key):
                return _compact_lines(str(payload[key]), max_lines=4)

    if not compact:
        return []
    if status != "ok":
        return _compact_lines(f"Error: {compact}", max_lines=3)
    return _compact_lines(text, max_lines=4)


def _compact_lines(value: str, *, max_lines: int) -> list[str]:
    raw_lines = [line.rstrip() for line in _strip_markup(value).splitlines() if line.strip()]
    if not raw_lines:
        return []
    clipped = [_clip_preserve(line, 112) for line in raw_lines]
    if len(clipped) <= max_lines:
        return clipped
    head_count = max(1, max_lines // 2)
    tail_count = max(1, max_lines - head_count - 1)
    hidden = len(clipped) - head_count - tail_count
    return [
        *clipped[:head_count],
        f"... +{hidden} lines (ctrl + t to view transcript)",
        *clipped[-tail_count:],
    ]


def _short_url(url: str, limit: int = 64) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
    except ValueError:
        return _clip(url, limit)
    if not parsed.netloc:
        return _clip(url, limit)
    display = parsed.netloc + parsed.path
    return _clip(display.rstrip("/") or parsed.netloc, limit)


def _clip(text: str, limit: int) -> str:
    text = _collapse_ws(text)
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def _clip_preserve(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def _wrap(text: str, width: int) -> list[str]:
    if width <= 8:
        return [_clip_preserve(text, max(1, width))]
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    ) or [""]


def _command_from_args(args: Any) -> str:
    return _arg_value(args, "command", "cmd")


def _split_command(command: str) -> tuple[str, str]:
    command = _collapse_ws(command)
    if not command:
        return "", ""
    if command.startswith('"'):
        end = command.find('"', 1)
        if end > 0:
            return _display_executable(command[1:end]), command[end + 1 :].strip()
    first, _, rest = command.partition(" ")
    return _display_executable(first.strip('"')), rest.strip()


def _display_executable(executable: str) -> str:
    if not executable:
        return ""
    cleaned = executable.strip('"')
    if "\\" in cleaned or "/" in cleaned:
        cleaned = PureWindowsPath(cleaned).name
    if cleaned.lower().endswith(".exe"):
        cleaned = cleaned[:-4]
    return cleaned or executable


def _append_arg_text(line: Text, args: str, *, limit: int) -> None:
    args = _clip(args, limit)
    if not args:
        return
    pos = 0
    for match in _PATH_TOKEN.finditer(args):
        if match.start() > pos:
            line.append(args[pos : match.start()], style=_ARG)
        line.append(match.group(0), style=_PATH)
        pos = match.end()
    if pos < len(args):
        line.append(args[pos:], style=_ARG)


class RailRunDashboard:
    """Compatibility dashboard that renders agent events like Codex transcripts."""

    def __init__(self, prompt: str, max_iter: int) -> None:
        self.prompt = prompt
        self.max_iter = max_iter
        self.start_time = time.monotonic()
        self.iterations = 0
        self.live: Any = None
        self.steps: list[RailStep] = []
        self.latest_text = ""
        self.thinking_active = True
        self.completion_summary: str | None = None
        self.status: str = "running"
        self.thinking_verb = pick_thinking_verb()
        self.input_tokens = 0
        self.output_tokens = 0
        self._last_progress_render = 0.0
        self._ticker_stop = threading.Event()
        self._ticker = threading.Thread(
            target=self._tick,
            daemon=True,
            name="vibe-rail-ticker",
        )
        self._ticker.start()

    def _tick(self) -> None:
        while not self._ticker_stop.wait(1.0):
            if self.status == "running" and self.live is not None:
                self.refresh()

    def close(self) -> None:
        self._ticker_stop.set()

    def refresh(self) -> None:
        if self.live is not None:
            self.live.update(self.render())

    def handle_event(self, event_type: str, data: dict[str, Any]) -> None:
        if event_type == "text_delta":
            delta = _collapse_ws(data.get("delta"))
            if delta:
                self.latest_text = (self.latest_text + delta).strip()[-500:]
                self._append_to_active(delta, throttle=True)
                self.refresh()
            return

        if event_type == "thinking_done":
            self.thinking_active = False
            self.refresh()
            return

        if event_type == "llm_usage":
            input_tokens = _coerce_int(data.get("input_tokens"))
            output_tokens = _coerce_int(data.get("output_tokens"))
            total_tokens = _coerce_int(data.get("total_tokens"))
            if input_tokens or output_tokens:
                self.input_tokens += input_tokens
                self.output_tokens += output_tokens
            else:
                self.output_tokens += total_tokens
            self.refresh()
            return

        if event_type == "tool_call":
            self.thinking_active = False
            tool = str(data.get("tool") or "tool")
            args = data.get("arguments") or {}
            self.iterations += 1
            step = RailStep(title=_tool_title(tool, args), tool=tool, args=args)
            detail = _initial_detail(tool, args)
            if detail:
                step.lines.append(detail)
            self.steps.append(step)
            self.steps = self.steps[-10:]
            self.refresh()
            return

        if event_type == "tool_progress":
            tool = str(data.get("tool") or "")
            step = self._active_step(tool)
            pieces: list[str] = []
            stage = _collapse_ws(data.get("stage"))
            current = data.get("current")
            total = data.get("total")
            message = _collapse_ws(data.get("message"))
            if stage:
                pieces.append(stage)
            if isinstance(current, int) and isinstance(total, int) and total > 0:
                pieces.append(f"{current}/{total}")
            if message:
                pieces.append(message)
            if pieces:
                step.lines.append(" · ".join(pieces))
                step.lines = step.lines[-6:]
            now = time.monotonic()
            if now - self._last_progress_render >= 0.2:
                self._last_progress_render = now
                self.refresh()
            return

        if event_type == "tool_heartbeat":
            tool = str(data.get("tool") or "")
            self._active_step(tool)
            self.refresh()
            return

        if event_type == "tool_result":
            tool = str(data.get("tool") or "")
            status = str(data.get("status") or "ok")
            step = self._active_step(tool)
            step.status = "done" if status == "ok" else "error"
            step.duration_s = float(data.get("elapsed_ms") or 0.0) / 1000
            for line in _result_summary(tool, status, data.get("preview")):
                if not step.lines or step.lines[-1] != line:
                    if step.lines and step.lines[-1].startswith("still running…"):
                        step.lines[-1] = line
                    else:
                        step.lines.append(line)
            step.lines = step.lines[-7:]
            self.refresh()
            return

        if event_type == "compact":
            tokens = data.get("tokens_before", "?")
            self.steps.append(
                RailStep(
                    title="context",
                    tool="compact",
                    status="warning",
                    lines=[f"{tokens} tokens summarized"],
                    duration_s=0.0,
                )
            )
            self.steps = self.steps[-10:]
            self.refresh()

    def finish(self, result: dict[str, Any], elapsed: float | None = None) -> None:
        self.status = str(result.get("status") or "done")
        for step in self.steps:
            if step.status == "active":
                step.status = "done"
                if not step.duration_s and elapsed is not None:
                    step.duration_s = max(0.0, elapsed)
        content = _collapse_ws(result.get("content"))
        reason = _collapse_ws(result.get("reason"))
        if content:
            self.completion_summary = "Done."
        elif reason:
            self.completion_summary = f"{self.status.title()}. {reason}"
        else:
            self.completion_summary = f"{self.status.title()}."
        self.thinking_active = False
        self.refresh()
        self.close()

    def render(self) -> Group:
        width = max(44, shutil.get_terminal_size((88, 24)).columns)
        detail_width = max(18, width - 7)
        rows: list[Text] = []

        for step in self.steps:
            rows.append(self._step_line(step, width=max(18, width - 3)))
            for line in self._render_lines(step):
                rows.extend(self._detail_lines(line, width=detail_width, active=step.status == "active"))

        if self.completion_summary is None:
            rows.append(self._activity_line())

        if self.completion_summary is not None:
            if rows:
                rows.append(Text(""))
            rows.append(self._finish_line(self.completion_summary))

        return Group(*rows)

    def _render_lines(self, step: RailStep) -> list[str]:
        lines = list(step.lines)
        return lines[-7:]

    def _active_step(self, tool: str) -> RailStep:
        raw_tool = str(tool or "")
        for step in reversed(self.steps):
            if step.status == "active" and (not raw_tool or step.tool == raw_tool):
                return step
        step = RailStep(title=_tool_title(raw_tool or "tool", None), tool=raw_tool)
        self.steps.append(step)
        self.steps = self.steps[-10:]
        return step

    def _append_to_active(self, text: str, *, throttle: bool) -> None:
        if not text:
            return
        now = time.monotonic()
        if throttle and now - self._last_progress_render < 0.2:
            return
        self._last_progress_render = now
        if self.steps and self.steps[-1].status == "active":
            self.steps[-1].lines.append(_clip(text, 112))
            self.steps[-1].lines = self.steps[-1].lines[-6:]

    def _activity_line(self) -> Text:
        elapsed = time.monotonic() - self.start_time
        line = Text()
        line.append("·", style=_MARKER_ACTIVE)
        line.append(" ")
        line.append(self.thinking_verb, style=Theme.muted)
        line.append(f" ({elapsed:.0f}s)", style=Theme.muted)
        return line

    def _step_line(self, step: RailStep, *, width: int) -> Text:
        marker_style = _MARKER_ACTIVE if step.status == "active" else _MARKER
        if step.status == "error":
            marker_style = _ERROR
        elif step.status == "warning":
            marker_style = _WARNING

        line = Text()
        line.append("•", style=marker_style)
        line.append(" ")

        lower = step.tool.lower()
        if lower in {"bash", "background_run", "shell"}:
            verb = "Running" if step.status == "active" else "Ran"
            command = _command_from_args(step.args)
            exe, rest = _split_command(command)
            duration = self._duration_label(step)
            budget = max(12, width - len(verb) - len(exe) - len(duration) - 7)
            line.append(verb, style=_ACTION)
            if exe:
                line.append(" ")
                line.append(exe, style=_CMD)
            if rest:
                line.append(" ")
                _append_arg_text(line, rest, limit=budget)
            elif not exe:
                line.append(" shell command", style=_ACTION)
            self._append_duration(line, duration)
            return line

        action = self._action_label(step)
        duration = self._duration_label(step)
        line.append(action, style=_ACTION)
        detail = self._title_detail(step)
        if detail:
            line.append(" ")
            if _looks_like_path(detail):
                line.append(_clip(detail, max(12, width - len(action) - len(duration) - 6)), style=_PATH)
            else:
                line.append(_clip(detail, max(12, width - len(action) - len(duration) - 6)), style=_ARG)
        self._append_duration(line, duration)
        return line

    def _duration_label(self, step: RailStep) -> str:
        return ""

    def _append_duration(self, line: Text, duration: str) -> None:
        if duration:
            line.append("  ")
            line.append(duration, style=Theme.muted)

    def _action_label(self, step: RailStep) -> str:
        lower = step.tool.lower()
        active = step.status == "active"
        if lower == "load_skill":
            return "Loading skill…" if active else "Loaded skill"
        if lower in {"read_file", "file_read"}:
            return "Reading file…" if active else "Read file"
        if lower in {"write_file", "edit_file"}:
            return "Writing file…" if active else "Wrote file"
        if lower in {"read_url", "web_fetch", "fetch", "read_url_tool"}:
            return "Fetching…" if active else "Fetched"
        if "search" in lower:
            return "Searching web…" if active else "Searched web"
        if lower in {"get_market_data", "market_data", "stock_price", "get_stock_price"}:
            return "Reading market data…" if active else "Read market data"
        if lower == "compact":
            return "Compacted context"
        return step.title

    def _title_detail(self, step: RailStep) -> str:
        args = step.args
        lower = step.tool.lower()
        if lower == "load_skill":
            return _arg_value(args, "name", "skill")
        if lower in {"read_file", "file_read", "write_file", "edit_file"}:
            return _arg_value(args, "path", "file_path")
        if lower in {"read_url", "web_fetch", "fetch", "read_url_tool"}:
            return _short_url(_arg_value(args, "url"))
        if "search" in lower:
            query = _arg_value(args, "query", "q")
            return f'"{query}"' if query else ""
        return _arg_value(args, "symbol", "ticker", "code", "asset")

    def _detail_lines(self, body: str, *, width: int, active: bool) -> list[Text]:
        style = _DETAIL
        parts = _wrap(_strip_markup(body), width)
        rows: list[Text] = []
        for index, part in enumerate(parts):
            line = Text("  ")
            if index == 0:
                line.append("└", style=style)
                line.append("  ")
            else:
                line.append("   ")
            line.append(part, style=style)
            rows.append(line)
        return rows

    def _finish_line(self, summary: str) -> Text:
        line = Text()
        line.append("•", style=_DONE if self.status in {"success", "ok", "done"} else _WARNING)
        line.append("  ")
        line.append(summary, style="bold")
        return line


def _looks_like_path(value: str) -> bool:
    return bool(_PATH_TOKEN.search(value))
