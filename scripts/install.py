#!/usr/bin/env python3
"""
install.py — Install The Agency agents into your local agentic tool(s).

Reads converted files from integrations/ and copies them to the appropriate
config directory for each tool.  Run ``python scripts/convert.py`` first if
integrations/ is missing or stale.

Usage:
    python scripts/install.py [--tool <name>] [--interactive] [--no-interactive] [--help]

Tools:
    claude-code  — Copy agents to ~/.claude/agents/
    copilot      — Copy agents to ~/.github/agents/ and ~/.copilot/agents/
    antigravity  — Copy skills to ~/.gemini/antigravity/skills/
    gemini-cli   — Install extension to ~/.gemini/extensions/agency-agents/
    opencode     — Copy agents to .opencode/agent/ in current directory
    cursor       — Copy rules to .cursor/rules/ in current directory
    aider        — Copy CONVENTIONS.md to current directory
    windsurf     — Copy .windsurfrules to current directory
    openclaw     — Copy workspaces to ~/.openclaw/agency-agents/
    qwen         — Copy SubAgents to ~/.qwen/agents/ (user-wide) or .qwen/agents/ (project)
    all          — Install for all detected tools (default)

Flags:
    --tool <name>     Install only the specified tool
    --interactive     Show interactive selector (default when run in a terminal)
    --no-interactive  Skip interactive selector, install all detected tools
    --help            Show this help

Platform support: Windows, macOS, Linux (Python 3.7+, no dependencies).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# Resolve this script's own directory so we can import the sibling module.
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from utils import (  # noqa: E402
    AGENT_DIRS,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    dim,
    error,
    header,
    info,
    warn,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = _SCRIPT_DIR.parent
INTEGRATIONS = REPO_ROOT / "integrations"
HOME = Path.home()

ALL_TOOLS: List[str] = [
    "claude-code",
    "copilot",
    "antigravity",
    "gemini-cli",
    "opencode",
    "openclaw",
    "cursor",
    "aider",
    "windsurf",
    "qwen",
]

# ---------------------------------------------------------------------------
# Box drawing (pure ASCII, fixed 52-char wide — matches bash version)
# ---------------------------------------------------------------------------
_BOX_INNER = 48


def _box_line() -> str:
    return "  +" + "-" * _BOX_INNER + "+"


def _box_row(text: str) -> str:
    """Content row, right-padded to fit.  *text* may contain ANSI escapes."""
    visible = re.sub(r"\033\[[0-9;]*m", "", text)
    pad = _BOX_INNER - 2 - len(visible)
    if pad < 0:
        pad = 0
    return f"  | {text}{' ' * pad} |"


# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------

def _detect_claude_code() -> bool:
    return (HOME / ".claude").is_dir()


def _detect_copilot() -> bool:
    return (
        shutil.which("code") is not None
        or (HOME / ".github").is_dir()
        or (HOME / ".copilot").is_dir()
    )


def _detect_antigravity() -> bool:
    return (HOME / ".gemini" / "antigravity" / "skills").is_dir()


def _detect_gemini_cli() -> bool:
    return shutil.which("gemini") is not None or (HOME / ".gemini").is_dir()


def _detect_cursor() -> bool:
    return shutil.which("cursor") is not None or (HOME / ".cursor").is_dir()


def _detect_opencode() -> bool:
    return (
        shutil.which("opencode") is not None
        or (HOME / ".config" / "opencode").is_dir()
    )


def _detect_aider() -> bool:
    return shutil.which("aider") is not None


def _detect_openclaw() -> bool:
    return shutil.which("openclaw") is not None or (HOME / ".openclaw").is_dir()


def _detect_windsurf() -> bool:
    return shutil.which("windsurf") is not None or (HOME / ".codeium").is_dir()


def _detect_qwen() -> bool:
    return shutil.which("qwen") is not None or (HOME / ".qwen").is_dir()


_DETECTORS: Dict[str, Callable[[], bool]] = {
    "claude-code": _detect_claude_code,
    "copilot":     _detect_copilot,
    "antigravity": _detect_antigravity,
    "gemini-cli":  _detect_gemini_cli,
    "opencode":    _detect_opencode,
    "openclaw":    _detect_openclaw,
    "cursor":      _detect_cursor,
    "aider":       _detect_aider,
    "windsurf":    _detect_windsurf,
    "qwen":        _detect_qwen,
}


def is_detected(tool: str) -> bool:
    fn = _DETECTORS.get(tool)
    if fn is None:
        return False
    try:
        return fn()
    except Exception:
        return False


# Fixed-width labels — mirrors the bash version
_TOOL_LABELS: Dict[str, Tuple[str, str]] = {
    "claude-code": ("Claude Code",  "(claude.ai/code)"),
    "copilot":     ("Copilot",      "(~/.github + ~/.copilot)"),
    "antigravity": ("Antigravity",  "(~/.gemini/antigravity)"),
    "gemini-cli":  ("Gemini CLI",   "(gemini extension)"),
    "opencode":    ("OpenCode",     "(opencode.ai)"),
    "openclaw":    ("OpenClaw",     "(~/.openclaw)"),
    "cursor":      ("Cursor",       "(.cursor/rules)"),
    "aider":       ("Aider",        "(CONVENTIONS.md)"),
    "windsurf":    ("Windsurf",     "(.windsurfrules)"),
    "qwen":        ("Qwen Code",    "(~/.qwen/agents)"),
}


def tool_label(tool: str) -> str:
    name, detail = _TOOL_LABELS.get(tool, (tool, ""))
    return f"{name:<14}  {detail}"


# ---------------------------------------------------------------------------
# Interactive selector
# ---------------------------------------------------------------------------

def interactive_select() -> List[str]:
    """Show an interactive TUI and return the list of selected tool names."""
    selected = [is_detected(t) for t in ALL_TOOLS]
    detected_map = list(selected)
    n = len(ALL_TOOLS)

    while True:
        # Header
        print()
        print(_box_line())
        print(_box_row(f"{BOLD}  The Agency -- Tool Installer{RESET}"))
        print(_box_line())
        print()
        print(f"  {DIM}System scan:  [*] = detected on this machine{RESET}")
        print()

        # Tool rows
        for i, t in enumerate(ALL_TOOLS):
            num = i + 1
            label = tool_label(t)
            dot = f"{GREEN}[*]{RESET}" if detected_map[i] else f"{DIM}[ ]{RESET}"
            chk = f"{GREEN}[x]{RESET}" if selected[i] else f"{DIM}[ ]{RESET}"
            print(f"  {chk}  {num})  {dot}  {label}")

        # Controls
        print()
        print("  " + "-" * 48)
        print(
            f"  {CYAN}[1-{n}]{RESET} toggle   "
            f"{CYAN}[a]{RESET} all   "
            f"{CYAN}[n]{RESET} none   "
            f"{CYAN}[d]{RESET} detected"
        )
        print(f"  {GREEN}[Enter]{RESET} install   {RED}[q]{RESET} quit")
        print()

        try:
            user_input = input("  >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            info("Aborted.")
            sys.exit(0)

        # Total lines we printed (for clear / redraw)
        total_lines = n + 14

        if user_input.lower() == "q":
            print()
            info("Aborted.")
            sys.exit(0)
        elif user_input.lower() == "a":
            selected = [True] * n
        elif user_input.lower() == "n":
            selected = [False] * n
        elif user_input.lower() == "d":
            selected = list(detected_map)
        elif user_input == "":
            if any(selected):
                break
            else:
                print(f"  {YELLOW}Nothing selected -- pick a tool or press q to quit.{RESET}")
                time.sleep(1)
                total_lines += 1
        else:
            toggled = False
            for token in user_input.split():
                if token.isdigit():
                    idx = int(token) - 1
                    if 0 <= idx < n:
                        selected[idx] = not selected[idx]
                        toggled = True
            if not toggled:
                print(f"  {RED}Invalid. Enter a number 1-{n}, or a command.{RESET}")
                time.sleep(1)
                total_lines += 1

        # Clear previous UI for redraw (move cursor up + clear lines)
        for _ in range(total_lines):
            print("\033[1A\033[2K", end="")

    return [t for i, t in enumerate(ALL_TOOLS) if selected[i]]


# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------

def _copy_agent_sources(dest: Path) -> int:
    """Copy raw agent .md files from category dirs into *dest*. Return count."""
    count = 0
    for dirname in AGENT_DIRS:
        dirpath = REPO_ROOT / dirname
        if not dirpath.is_dir():
            continue
        for md in sorted(dirpath.rglob("*.md")):
            try:
                with open(md, encoding="utf-8") as fh:
                    first_line = fh.readline().rstrip("\n\r")
            except (OSError, UnicodeDecodeError):
                continue
            if first_line != "---":
                continue
            shutil.copy2(str(md), str(dest / md.name))
            count += 1
    return count


def install_claude_code() -> None:
    dest = HOME / ".claude" / "agents"
    dest.mkdir(parents=True, exist_ok=True)
    count = _copy_agent_sources(dest)
    info(f"Claude Code: {count} agents -> {dest}")


def install_copilot() -> None:
    dest_github = HOME / ".github" / "agents"
    dest_copilot = HOME / ".copilot" / "agents"
    dest_github.mkdir(parents=True, exist_ok=True)
    dest_copilot.mkdir(parents=True, exist_ok=True)
    count = _copy_agent_sources(dest_github)
    # Copy the same files to the second location
    _copy_agent_sources(dest_copilot)
    info(f"Copilot: {count} agents -> {dest_github}")
    info(f"Copilot: {count} agents -> {dest_copilot}")


def install_antigravity() -> None:
    src = INTEGRATIONS / "antigravity"
    dest = HOME / ".gemini" / "antigravity" / "skills"
    if not src.is_dir():
        error("integrations/antigravity missing. Run convert.py first.")
        return
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for skill_dir in sorted(src.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        target = dest / skill_dir.name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(skill_file), str(target / "SKILL.md"))
        count += 1
    info(f"Antigravity: {count} skills -> {dest}")


def install_gemini_cli() -> None:
    src = INTEGRATIONS / "gemini-cli"
    dest = HOME / ".gemini" / "extensions" / "agency-agents"
    if not src.is_dir():
        error("integrations/gemini-cli missing. Run convert.py first.")
        return
    manifest = src / "gemini-extension.json"
    skills_dir = src / "skills"
    if not manifest.is_file():
        error("integrations/gemini-cli/gemini-extension.json missing. Run convert.py first.")
        return
    if not skills_dir.is_dir():
        error("integrations/gemini-cli/skills missing. Run convert.py first.")
        return
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "skills").mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(manifest), str(dest / "gemini-extension.json"))
    count = 0
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        target = dest / "skills" / skill_dir.name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(skill_file), str(target / "SKILL.md"))
        count += 1
    info(f"Gemini CLI: {count} skills -> {dest}")


def install_opencode() -> None:
    src = INTEGRATIONS / "opencode" / "agents"
    dest = Path.cwd() / ".opencode" / "agents"
    if not src.is_dir():
        error("integrations/opencode missing. Run convert.py first.")
        return
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for md in sorted(src.glob("*.md")):
        shutil.copy2(str(md), str(dest / md.name))
        count += 1
    info(f"OpenCode: {count} agents -> {dest}")
    warn("OpenCode: project-scoped. Run from your project root to install there.")


def install_openclaw() -> None:
    src = INTEGRATIONS / "openclaw"
    dest = HOME / ".openclaw" / "agency-agents"
    if not src.is_dir():
        error("integrations/openclaw missing. Run convert.py first.")
        return
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for ws_dir in sorted(src.iterdir()):
        if not ws_dir.is_dir():
            continue
        target = dest / ws_dir.name
        target.mkdir(parents=True, exist_ok=True)
        for fname in ("SOUL.md", "AGENTS.md", "IDENTITY.md"):
            src_f = ws_dir / fname
            if src_f.is_file():
                shutil.copy2(str(src_f), str(target / fname))
        # Register with OpenClaw if available
        if shutil.which("openclaw"):
            try:
                subprocess.run(
                    ["openclaw", "agents", "add", ws_dir.name,
                     "--workspace", str(target), "--non-interactive"],
                    check=False,
                    capture_output=True,
                )
            except Exception:
                pass
        count += 1
    info(f"OpenClaw: {count} workspaces -> {dest}")
    if shutil.which("openclaw"):
        warn("OpenClaw: run 'openclaw gateway restart' to activate new agents")


def install_cursor() -> None:
    src = INTEGRATIONS / "cursor" / "rules"
    dest = Path.cwd() / ".cursor" / "rules"
    if not src.is_dir():
        error("integrations/cursor missing. Run convert.py first.")
        return
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for mdc in sorted(src.glob("*.mdc")):
        shutil.copy2(str(mdc), str(dest / mdc.name))
        count += 1
    info(f"Cursor: {count} rules -> {dest}")
    warn("Cursor: project-scoped. Run from your project root to install there.")


def install_aider() -> None:
    src = INTEGRATIONS / "aider" / "CONVENTIONS.md"
    dest = Path.cwd() / "CONVENTIONS.md"
    if not src.is_file():
        error("integrations/aider/CONVENTIONS.md missing. Run convert.py first.")
        return
    if dest.is_file():
        warn(f"Aider: CONVENTIONS.md already exists at {dest} (remove to reinstall).")
        return
    shutil.copy2(str(src), str(dest))
    info(f"Aider: installed -> {dest}")
    warn("Aider: project-scoped. Run from your project root to install there.")


def install_windsurf() -> None:
    src = INTEGRATIONS / "windsurf" / ".windsurfrules"
    dest = Path.cwd() / ".windsurfrules"
    if not src.is_file():
        error("integrations/windsurf/.windsurfrules missing. Run convert.py first.")
        return
    if dest.is_file():
        warn(f"Windsurf: .windsurfrules already exists at {dest} (remove to reinstall).")
        return
    shutil.copy2(str(src), str(dest))
    info(f"Windsurf: installed -> {dest}")
    warn("Windsurf: project-scoped. Run from your project root to install there.")


def install_qwen() -> None:
    src = INTEGRATIONS / "qwen" / "agents"
    dest = Path.cwd() / ".qwen" / "agents"
    if not src.is_dir():
        error("integrations/qwen missing. Run convert.py first.")
        return
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for md in sorted(src.glob("*.md")):
        shutil.copy2(str(md), str(dest / md.name))
        count += 1
    info(f"Qwen Code: installed {count} agents to {dest}")
    warn("Qwen Code: project-scoped. Run from your project root to install there.")
    warn("Tip: Run '/agents manage' in Qwen Code to refresh, or restart session")


_INSTALLERS: Dict[str, Callable[[], None]] = {
    "claude-code": install_claude_code,
    "copilot":     install_copilot,
    "antigravity": install_antigravity,
    "gemini-cli":  install_gemini_cli,
    "opencode":    install_opencode,
    "openclaw":    install_openclaw,
    "cursor":      install_cursor,
    "aider":       install_aider,
    "windsurf":    install_windsurf,
    "qwen":        install_qwen,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Install The Agency agents into your local agentic tool(s).",
    )
    parser.add_argument(
        "--tool",
        default="all",
        choices=ALL_TOOLS + ["all"],
        help="Install only the specified tool (default: all)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help="Show interactive selector (default when run in a terminal)",
    )
    group.add_argument(
        "--no-interactive",
        action="store_true",
        default=False,
        help="Skip interactive selector, install all detected tools",
    )
    args = parser.parse_args(argv)

    # Preflight
    if not INTEGRATIONS.is_dir():
        error("integrations/ not found. Run 'python scripts/convert.py' first.")
        sys.exit(1)

    # Decide interactive mode
    interactive_mode: Optional[bool] = None
    if args.interactive:
        interactive_mode = True
    elif args.no_interactive:
        interactive_mode = False
    elif args.tool != "all":
        interactive_mode = False

    # If auto, show interactive when stdin/stdout are TTYs and tool is "all"
    if interactive_mode is None:
        interactive_mode = (
            sys.stdin.isatty()
            and sys.stdout.isatty()
            and args.tool == "all"
        )

    selected_tools: List[str] = []

    if interactive_mode:
        selected_tools = interactive_select()
    elif args.tool != "all":
        selected_tools = [args.tool]
    else:
        # Non-interactive: auto-detect
        header("The Agency -- Scanning for installed tools...")
        print()
        for t in ALL_TOOLS:
            if is_detected(t):
                selected_tools.append(t)
                print(f"  {GREEN}[*]{RESET}  {tool_label(t)}  {DIM}detected{RESET}")
            else:
                print(f"  {DIM}[ ]  {tool_label(t)}  not found{RESET}")

    if not selected_tools:
        warn("No tools selected or detected. Nothing to install.")
        print()
        dim("  Tip: use --tool <name> to force-install a specific tool.")
        dim(f"  Available: {' '.join(ALL_TOOLS)}")
        sys.exit(0)

    print()
    header("The Agency -- Installing agents")
    print(f"  Repo:       {REPO_ROOT}")
    print(f"  Installing: {' '.join(selected_tools)}")
    print()

    installed = 0
    for t in selected_tools:
        fn = _INSTALLERS.get(t)
        if fn:
            fn()
            installed += 1

    # Done box
    msg = f"  Done!  Installed {installed} tool(s)."
    print()
    print(_box_line())
    print(_box_row(f"{GREEN}{BOLD}{msg}{RESET}"))
    print(_box_line())
    print()
    dim("  Run 'python scripts/convert.py' to regenerate after adding or editing agents.")
    print()


if __name__ == "__main__":
    main()
