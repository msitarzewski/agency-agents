#!/usr/bin/env python3
"""
convert.py — Convert agency agent .md files into tool-specific formats.

Reads all agent files from the standard category directories and outputs
converted files to integrations/<tool>/. Run this to regenerate all
integration files after adding or modifying agents.

Usage:
    python scripts/convert.py [--tool <name>] [--out <dir>] [--help]

Tools:
    antigravity  — Antigravity skill files (~/.gemini/antigravity/skills/)
    gemini-cli   — Gemini CLI extension (skills/ + gemini-extension.json)
    opencode     — OpenCode agent files (.opencode/agent/*.md)
    cursor       — Cursor rule files (.cursor/rules/*.mdc)
    aider        — Single CONVENTIONS.md for Aider
    windsurf     — Single .windsurfrules for Windsurf
    openclaw     — OpenClaw SOUL.md files (openclaw_workspace/<agent>/SOUL.md)
    qwen         — Qwen Code SubAgent files (~/.qwen/agents/*.md)
    all          — All tools (default)

Output is written to integrations/<tool>/ relative to the repo root.
This script never touches user config dirs — see install.py for that.

Compatible with Python 3.7+.  No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

# Resolve this script's own directory so we can import the sibling module.
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from utils import (  # noqa: E402
    AGENT_DIRS,
    find_agent_files,
    get_body,
    get_field,
    header,
    info,
    error,
    slugify,
)

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
VALID_TOOLS = [
    "antigravity",
    "gemini-cli",
    "opencode",
    "cursor",
    "aider",
    "windsurf",
    "openclaw",
    "qwen",
    "all",
]

TODAY = date.today().isoformat()  # YYYY-MM-DD


# ---------------------------------------------------------------------------
# OpenCode colour resolution
# ---------------------------------------------------------------------------
_OPENCODE_COLOR_MAP: Dict[str, str] = {
    "cyan":          "#00FFFF",
    "blue":          "#3498DB",
    "green":         "#2ECC71",
    "red":           "#E74C3C",
    "purple":        "#9B59B6",
    "orange":        "#F39C12",
    "teal":          "#008080",
    "indigo":        "#6366F1",
    "pink":          "#E84393",
    "gold":          "#EAB308",
    "amber":         "#F59E0B",
    "neon-green":    "#10B981",
    "neon-cyan":     "#06B6D4",
    "metallic-blue": "#3B82F6",
    "yellow":        "#EAB308",
    "violet":        "#8B5CF6",
    "rose":          "#F43F5E",
    "lime":          "#84CC16",
    "gray":          "#6B7280",
    "fuchsia":       "#D946EF",
}

_HEX6_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def resolve_opencode_color(raw: str) -> str:
    """Map a named colour or hex string to an OpenCode-safe ``#RRGGBB``."""
    c = raw.strip().lower()
    mapped = _OPENCODE_COLOR_MAP.get(c, c)

    bare = mapped.lstrip("#")
    if _HEX6_RE.match(bare):
        return f"#{bare.upper()}"

    return "#6B7280"  # fallback grey


# ---------------------------------------------------------------------------
# Per-tool converters
# ---------------------------------------------------------------------------

def convert_antigravity(filepath: str, out_dir: Path) -> None:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    slug = f"agency-{slugify(name)}"
    body = get_body(filepath)

    dest = out_dir / "antigravity" / slug
    dest.mkdir(parents=True, exist_ok=True)

    (dest / "SKILL.md").write_text(
        f"---\n"
        f"name: {slug}\n"
        f"description: {description}\n"
        f"risk: low\n"
        f"source: community\n"
        f"date_added: '{TODAY}'\n"
        f"---\n"
        f"{body}\n",
        encoding="utf-8",
    )


def convert_gemini_cli(filepath: str, out_dir: Path) -> None:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    slug = slugify(name)
    body = get_body(filepath)

    dest = out_dir / "gemini-cli" / "skills" / slug
    dest.mkdir(parents=True, exist_ok=True)

    (dest / "SKILL.md").write_text(
        f"---\n"
        f"name: {slug}\n"
        f"description: {description}\n"
        f"---\n"
        f"{body}\n",
        encoding="utf-8",
    )


def convert_opencode(filepath: str, out_dir: Path) -> None:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    color = resolve_opencode_color(get_field("color", filepath))
    slug = slugify(name)
    body = get_body(filepath)

    dest = out_dir / "opencode" / "agents"
    dest.mkdir(parents=True, exist_ok=True)

    (dest / f"{slug}.md").write_text(
        f"---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"mode: subagent\n"
        f"color: '{color}'\n"
        f"---\n"
        f"{body}\n",
        encoding="utf-8",
    )


def convert_cursor(filepath: str, out_dir: Path) -> None:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    slug = slugify(name)
    body = get_body(filepath)

    dest = out_dir / "cursor" / "rules"
    dest.mkdir(parents=True, exist_ok=True)

    (dest / f"{slug}.mdc").write_text(
        f"---\n"
        f"description: {description}\n"
        f'globs: ""\n'
        f"alwaysApply: false\n"
        f"---\n"
        f"{body}\n",
        encoding="utf-8",
    )


def convert_openclaw(filepath: str, out_dir: Path) -> None:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    slug = slugify(name)
    body = get_body(filepath)

    dest = out_dir / "openclaw" / slug
    dest.mkdir(parents=True, exist_ok=True)

    # Split body into SOUL (persona) vs AGENTS (operations) by ## header keywords.
    soul_keywords = re.compile(
        r"identity|communication|style|critical.rule|rules.you.must.follow",
        re.IGNORECASE,
    )

    soul_content: List[str] = []
    agents_content: List[str] = []
    current_section: List[str] = []
    current_target = "agents"  # default bucket

    for line in body.split("\n"):
        if line.startswith("## "):
            # Flush previous section
            if current_section:
                if current_target == "soul":
                    soul_content.extend(current_section)
                else:
                    agents_content.extend(current_section)
                current_section = []

            # Classify header
            if soul_keywords.search(line):
                current_target = "soul"
            else:
                current_target = "agents"

        current_section.append(line)

    # Flush final section
    if current_section:
        if current_target == "soul":
            soul_content.extend(current_section)
        else:
            agents_content.extend(current_section)

    (dest / "SOUL.md").write_text("\n".join(soul_content) + "\n", encoding="utf-8")
    (dest / "AGENTS.md").write_text("\n".join(agents_content) + "\n", encoding="utf-8")

    # IDENTITY.md — emoji + name + vibe, or fallback to description
    emoji = get_field("emoji", filepath)
    vibe = get_field("vibe", filepath)

    if emoji and vibe:
        identity = f"# {emoji} {name}\n{vibe}\n"
    else:
        identity = f"# {name}\n{description}\n"

    (dest / "IDENTITY.md").write_text(identity, encoding="utf-8")


def convert_qwen(filepath: str, out_dir: Path) -> None:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    tools = get_field("tools", filepath)
    slug = slugify(name)
    body = get_body(filepath)

    dest = out_dir / "qwen" / "agents"
    dest.mkdir(parents=True, exist_ok=True)

    frontmatter = f"---\nname: {slug}\ndescription: {description}\n"
    if tools:
        frontmatter += f"tools: {tools}\n"
    frontmatter += "---\n"

    (dest / f"{slug}.md").write_text(
        frontmatter + body + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Aider / Windsurf accumulators (single-file outputs)
# ---------------------------------------------------------------------------

_AIDER_HEADER = """\
# The Agency — AI Agent Conventions
#
# This file provides Aider with the full roster of specialized AI agents from
# The Agency (https://github.com/msitarzewski/agency-agents).
#
# To activate an agent, reference it by name in your Aider session prompt, e.g.:
#   "Use the Frontend Developer agent to review this component."
#
# Generated by scripts/convert.py — do not edit manually.
"""

_WINDSURF_HEADER = """\
# The Agency — AI Agent Rules for Windsurf
#
# Full roster of specialized AI agents from The Agency.
# To activate an agent, reference it by name in your Windsurf conversation.
#
# Generated by scripts/convert.py — do not edit manually.
"""


def _accumulate_aider(filepath: str) -> str:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    body = get_body(filepath)
    return f"\n---\n\n## {name}\n\n> {description}\n\n{body}\n"


def _accumulate_windsurf(filepath: str) -> str:
    name = get_field("name", filepath)
    description = get_field("description", filepath)
    body = get_body(filepath)
    sep = "=" * 80
    return f"\n{sep}\n## {name}\n{description}\n{sep}\n\n{body}\n\n"


# ---------------------------------------------------------------------------
# Main conversion loop
# ---------------------------------------------------------------------------

def run_conversions(
    tool: str,
    repo_root: str,
    out_dir: Path,
    aider_parts: List[str],
    windsurf_parts: List[str],
) -> int:
    """Run conversions for *tool*, returning the number of agents processed."""
    count = 0
    for _category, filepath in find_agent_files(repo_root):
        fp = str(filepath)
        if tool == "antigravity":
            convert_antigravity(fp, out_dir)
        elif tool == "gemini-cli":
            convert_gemini_cli(fp, out_dir)
        elif tool == "opencode":
            convert_opencode(fp, out_dir)
        elif tool == "cursor":
            convert_cursor(fp, out_dir)
        elif tool == "openclaw":
            convert_openclaw(fp, out_dir)
        elif tool == "qwen":
            convert_qwen(fp, out_dir)
        elif tool == "aider":
            aider_parts.append(_accumulate_aider(fp))
        elif tool == "windsurf":
            windsurf_parts.append(_accumulate_windsurf(fp))
        count += 1
    return count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Convert agency agent .md files into tool-specific formats.",
    )
    parser.add_argument(
        "--tool",
        default="all",
        choices=VALID_TOOLS,
        help="Convert for a specific tool (default: all)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: <repo>/integrations)",
    )
    args = parser.parse_args(argv)

    repo_root = str(_SCRIPT_DIR.parent)
    out_dir = Path(args.out) if args.out else Path(repo_root) / "integrations"

    header("The Agency -- Converting agents to tool-specific formats")
    print(f"  Repo:   {repo_root}")
    print(f"  Output: {out_dir}")
    print(f"  Tool:   {args.tool}")
    print(f"  Date:   {TODAY}")

    tools_to_run: List[str]
    if args.tool == "all":
        tools_to_run = [t for t in VALID_TOOLS if t != "all"]
    else:
        tools_to_run = [args.tool]

    total = 0
    aider_parts: List[str] = []
    windsurf_parts: List[str] = []

    for t in tools_to_run:
        header(f"Converting: {t}")
        count = run_conversions(t, repo_root, out_dir, aider_parts, windsurf_parts)
        total += count

        # Gemini CLI also needs the extension manifest
        if t == "gemini-cli":
            manifest_dir = out_dir / "gemini-cli"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            (manifest_dir / "gemini-extension.json").write_text(
                json.dumps(
                    {"name": "agency-agents", "version": "1.0.0"},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            info("Wrote gemini-extension.json")

        info(f"Converted {count} agents for {t}")

    # Write single-file outputs after accumulation
    if args.tool in ("all", "aider"):
        aider_dir = out_dir / "aider"
        aider_dir.mkdir(parents=True, exist_ok=True)
        (aider_dir / "CONVENTIONS.md").write_text(
            _AIDER_HEADER + "".join(aider_parts),
            encoding="utf-8",
        )
        info("Wrote integrations/aider/CONVENTIONS.md")

    if args.tool in ("all", "windsurf"):
        ws_dir = out_dir / "windsurf"
        ws_dir.mkdir(parents=True, exist_ok=True)
        (ws_dir / ".windsurfrules").write_text(
            _WINDSURF_HEADER + "".join(windsurf_parts),
            encoding="utf-8",
        )
        info("Wrote integrations/windsurf/.windsurfrules")

    print()
    info(f"Done. Total conversions: {total}")


if __name__ == "__main__":
    main()
