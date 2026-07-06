"""Large startup banner for the interactive CLI."""

from __future__ import annotations

from typing import Final

from rich.console import Console
from rich.text import Text

from cli._version import __version__ as _VERSION
from cli.theme import Theme

_LOGO: Final[tuple[str, ...]] = (
    r"__      ___ _             _______             _ _             ",
    r"\ \    / (_) |           |__   __|           | (_)            ",
    r" \ \  / / _| |__   ___      | |_ __ __ _  __| |_ _ __   __ _ ",
    r"  \ \/ / | | '_ \ / _ \     | | '__/ _` |/ _` | | '_ \ / _` |",
    r"   \  /  | | |_) |  __/     | | | | (_| | (_| | | | | | (_| |",
    r"    \/   |_|_.__/ \___|     |_|_|  \__,_|\__,_|_|_| |_|\__, |",
    r"                                                        __/ |",
    r"                                                       |___/ ",
)

_GRADIENT_START: Final[tuple[int, int, int]] = (0x25, 0x8B, 0xFF)
_GRADIENT_END: Final[tuple[int, int, int]] = (0xA5, 0xCF, 0xFF)


def _lerp(start: int, end: int, ratio: float) -> int:
    return round(start + (end - start) * ratio)


def _gradient_style(index: int, total: int) -> str:
    ratio = 0.0 if total <= 1 else index / (total - 1)
    red = _lerp(_GRADIENT_START[0], _GRADIENT_END[0], ratio)
    green = _lerp(_GRADIENT_START[1], _GRADIENT_END[1], ratio)
    blue = _lerp(_GRADIENT_START[2], _GRADIENT_END[2], ratio)
    return f"bold #{red:02x}{green:02x}{blue:02x}"


def _gradient_line(line: str) -> Text:
    text = Text()
    total = max(1, len(line.rstrip()))
    for idx, char in enumerate(line):
        text.append(char, style=_gradient_style(idx, total) if char != " " else None)
    return text


def _center_pad(console: Console, width: int) -> str:
    columns = console.size.width
    if columns >= width + 4:
        return " " * max(0, (columns - width) // 2)
    return "  "


def print_banner(
    console: Console,
    *,
    model: str,
    skills: int,
    tools: int,
    sessions: int,
    version: str = _VERSION,
    mode: str = "cli",
    **_: object,
) -> None:
    """Render the cold-start banner once before the prompt appears."""

    del skills, tools, sessions
    width = max(len(line.rstrip()) for line in _LOGO)
    pad = _center_pad(console, width)

    console.print()
    for line in _LOGO:
        rendered = Text(pad)
        rendered.append(_gradient_line(line.rstrip()))
        console.print(rendered)

    meta = Text(pad)
    meta.append(f"vibe-trading v{version}  ·  {mode}  ·  {model}", style=Theme.muted)
    console.print(meta)
    console.print()
