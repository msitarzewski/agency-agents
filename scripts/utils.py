"""
Shared utilities for the agency-agents Python scripts.

Provides colour output, YAML frontmatter parsing, slug generation,
and agent-file discovery — all with zero third-party dependencies.

Compatible with Python 3.7+.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Canonical agent category directories (same order as the bash scripts)
# ---------------------------------------------------------------------------
AGENT_DIRS: List[str] = [
    "design",
    "engineering",
    "game-development",
    "marketing",
    "paid-media",
    "sales",
    "product",
    "project-management",
    "testing",
    "support",
    "spatial-computing",
    "specialized",
]

# ---------------------------------------------------------------------------
# Colour helpers — auto-disabled when stdout is not a TTY, NO_COLOR is set,
# or TERM is "dumb".  On Windows, attempt to enable ANSI via the console API.
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    """Return True if stdout can render ANSI escape codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM", "") == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    # On Windows, enable virtual-terminal processing if possible.
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            # STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(-11)
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                return True
            return False
        except Exception:
            return False
    return True


_COLOR = _supports_color()

GREEN  = "\033[0;32m" if _COLOR else ""
YELLOW = "\033[1;33m" if _COLOR else ""
RED    = "\033[0;31m" if _COLOR else ""
CYAN   = "\033[0;36m" if _COLOR else ""
BOLD   = "\033[1m"    if _COLOR else ""
DIM    = "\033[2m"    if _COLOR else ""
RESET  = "\033[0m"    if _COLOR else ""


def info(msg: str) -> None:
    """Print a green [OK] message."""
    print(f"{GREEN}[OK]{RESET}  {msg}")


def warn(msg: str) -> None:
    """Print a yellow [!!] warning message."""
    print(f"{YELLOW}[!!]{RESET}  {msg}")


def error(msg: str) -> None:
    """Print a red [ERR] error message to stderr."""
    print(f"{RED}[ERR]{RESET} {msg}", file=sys.stderr)


def header(msg: str) -> None:
    """Print a bold header line (with a blank line above)."""
    print(f"\n{BOLD}{msg}{RESET}")


def dim(msg: str) -> None:
    """Print a dimmed message."""
    print(f"{DIM}{msg}{RESET}")


# ---------------------------------------------------------------------------
# YAML frontmatter helpers
# ---------------------------------------------------------------------------

def get_field(field: str, filepath: str) -> str:
    """
    Extract a single ``field: value`` from the YAML frontmatter of *filepath*.

    Returns the value as a stripped string, or ``""`` if the field is absent.
    The frontmatter is the block between the first and second ``---`` lines.
    """
    with open(filepath, encoding="utf-8") as fh:
        in_frontmatter = False
        for line in fh:
            stripped = line.rstrip("\n")
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    # reached closing ---
                    break
            if in_frontmatter:
                prefix = field + ": "
                if stripped.startswith(prefix):
                    return stripped[len(prefix):].strip()
    return ""


def get_body(filepath: str) -> str:
    """
    Return file content after the closing ``---`` of the frontmatter block.

    Leading/trailing whitespace on the whole body is preserved (matching the
    bash ``awk`` behaviour), but a single leading newline is stripped if present.
    """
    with open(filepath, encoding="utf-8") as fh:
        content = fh.read()

    dashes_count = 0
    lines = content.split("\n")
    body_start = 0
    for i, line in enumerate(lines):
        if line.rstrip("\r") == "---":
            dashes_count += 1
            if dashes_count == 2:
                body_start = i + 1
                break

    body = "\n".join(lines[body_start:])
    # Strip exactly one leading newline to match bash heredoc output
    if body.startswith("\n"):
        body = body[1:]
    return body


def slugify(name: str) -> str:
    """
    Convert a human-readable name to a lowercase kebab-case slug.

    ``"Frontend Developer"`` → ``"frontend-developer"``
    """
    s = name.lower()
    s = re.sub(r"[^a-z0-9]", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s


# ---------------------------------------------------------------------------
# Agent file discovery
# ---------------------------------------------------------------------------

def find_agent_files(
    repo_root: str,
    agent_dirs: Optional[List[str]] = None,
) -> Iterator[Tuple[str, Path]]:
    """
    Yield ``(category_dir_name, path)`` for every agent ``.md`` file.

    A file qualifies if its first line is ``---`` and it has a ``name:`` field
    in its frontmatter.  Files are yielded in sorted order within each
    category directory.
    """
    if agent_dirs is None:
        agent_dirs = AGENT_DIRS

    root = Path(repo_root)
    for dirname in agent_dirs:
        dirpath = root / dirname
        if not dirpath.is_dir():
            continue
        md_files = sorted(dirpath.rglob("*.md"))
        for md in md_files:
            try:
                with open(md, encoding="utf-8") as fh:
                    first_line = fh.readline().rstrip("\n\r")
            except (OSError, UnicodeDecodeError):
                continue
            if first_line != "---":
                continue
            name = get_field("name", str(md))
            if not name:
                continue
            yield dirname, md
