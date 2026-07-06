"""Shared YAML-like frontmatter parser for skills and memory files."""

from __future__ import annotations

import re
from typing import Any, Dict


def parse_frontmatter(text: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML-like frontmatter and body from a markdown file.

    Supports string, list (``[a, b]``), and boolean values.

    Args:
        text: Markdown text with optional ``---`` delimited frontmatter.

    Returns:
        Tuple of (metadata dict, body text).
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text.strip()

    meta: Dict[str, Any] = {}
    for line in match.group(1).strip().split("\n"):
        line = line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("'\"") for item in value[1:-1].split(",")]
            meta[key] = [i for i in items if i]
        elif value.lower() in ("true", "false"):
            meta[key] = value.lower() == "true"
        else:
            meta[key] = value

    return meta, match.group(2).strip()
