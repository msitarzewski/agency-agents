"""Transcript helpers for the interactive CLI."""

from __future__ import annotations

import re
import shutil
from typing import Any

from rich import box
from rich.console import Group
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

from cli.theme import Theme

_PIPE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
# Standalone markdown horizontal rule (---, ***, ___). Stripped from
# assistant answers so they don't render as full-width terminal lines.
_HR_LINE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_PROMPT_BORDER = "#4b5563"
_MUTED = "#6b7280"


def render_prompt_footer(width: int | None = None) -> Text:
    """Bottom border printed after prompt_toolkit accepts the user input."""

    cols = width or shutil.get_terminal_size((88, 24)).columns
    return Text("─" * max(10, cols), style=_PROMPT_BORDER)


def render_recap(history: list[dict[str, str]]) -> Text | None:
    """Return a deterministic dim recap of the previous turn."""

    user = ""
    assistant = ""
    for message in reversed(history):
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if not content:
            continue
        if role == "assistant" and not assistant:
            assistant = content
        elif role == "user" and not user:
            user = content
        if user and assistant:
            break
    if not user and not assistant:
        return None

    parts = []
    if user:
        parts.append(f"Last request: {_sentence(user, 92)}")
    if assistant:
        parts.append(f"Result: {_sentence(assistant, 128)}")
    line = Text("※ recap: ", style=Theme.muted)
    line.append("; ".join(parts), style=Theme.muted)
    return line


def render_elapsed_status(elapsed: float) -> Text:
    """Render the post-run timing line."""

    line = Text("✻ ", style=_MUTED)
    line.append("Analyzed", style=Theme.muted)
    line.append(f" for {_format_duration(elapsed)}", style=Theme.muted)
    return line


def render_answer(content: str) -> Group:
    """Render assistant Markdown, upgrading pipe tables to Rich tables."""

    blocks: list[Any] = []
    pending: list[str] = []

    def flush_pending() -> None:
        if pending:
            blocks.append(Markdown("\n".join(pending).strip()))
            pending.clear()

    lines = content.splitlines()
    index = 0
    while index < len(lines):
        if _is_table_start(lines, index):
            flush_pending()
            table_lines = [lines[index], lines[index + 1]]
            index += 2
            while index < len(lines) and _is_pipe_row(lines[index]):
                table_lines.append(lines[index])
                index += 1
            table = _parse_table(table_lines)
            if table is not None:
                blocks.append(table)
            else:
                pending.extend(table_lines)
            continue
        if _HR_LINE.match(lines[index]):
            # Drop standalone horizontal rules — Rich renders them as a
            # full-width terminal line that looks like a separator border.
            index += 1
            continue
        pending.append(lines[index])
        index += 1

    flush_pending()
    return Group(*blocks) if blocks else Group(Text(content))


def _is_table_start(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and _is_pipe_row(lines[index])
        and bool(_PIPE_SEPARATOR.match(lines[index + 1]))
    )


def _is_pipe_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _parse_table(lines: list[str]) -> Table | None:
    if len(lines) < 2:
        return None
    headers = _split_row(lines[0])
    rows = [_split_row(line) for line in lines[2:] if _is_pipe_row(line)]
    if not headers or not rows:
        return None

    table = Table(
        box=box.SQUARE,
        show_header=True,
        show_lines=True,
        header_style="bold white",
        border_style="dim",
        padding=(0, 1),
    )
    for header in headers:
        table.add_column(_clean_inline_markdown(header), overflow="fold")
    for row in rows:
        cells = list(row[: len(headers)])
        while len(cells) < len(headers):
            cells.append("")
        table.add_row(*[_clean_inline_markdown(cell) for cell in cells])
    return table


def _split_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _clean_inline_markdown(text: str) -> str:
    cleaned = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    cleaned = re.sub(r"(\*|_)(.*?)\1", r"\2", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def _sentence(text: str, limit: int) -> str:
    collapsed = re.sub(r"\s+", " ", _clean_inline_markdown(text)).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(1, limit - 1)].rstrip() + "…"


def _format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m {secs:02d}s"
