#!/usr/bin/env python3
"""
lint-agents.py — Validate agent markdown files.

Checks:
  1. YAML frontmatter must exist with name, description, color  (ERROR)
  2. Recommended sections checked but only warned               (WARN)
  3. File must have meaningful content                           (WARN)

Usage:
    python scripts/lint-agents.py [file ...]
    If no files given, scans all agent directories.

Compatible with Python 3.7+.  No third-party dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Resolve this script's own directory so we can import the sibling module.
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from utils import AGENT_DIRS, get_body, get_field  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REQUIRED_FRONTMATTER = ["name", "description", "color"]
RECOMMENDED_SECTIONS = ["Identity", "Core Mission", "Critical Rules"]

# ---------------------------------------------------------------------------
# Linter
# ---------------------------------------------------------------------------

def lint_file(filepath: str) -> Tuple[int, int]:
    """
    Lint a single agent file.

    Returns ``(errors, warnings)`` counts.
    """
    errors = 0
    warnings = 0

    # 1.  Check frontmatter opening
    try:
        with open(filepath, encoding="utf-8") as fh:
            first_line = fh.readline().rstrip("\n\r")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR {filepath}: cannot read file ({exc})")
        return 1, 0

    if first_line != "---":
        print(f"ERROR {filepath}: missing frontmatter opening ---")
        return 1, 0

    # Extract frontmatter (between first and second ---)
    frontmatter_lines: List[str] = []
    try:
        with open(filepath, encoding="utf-8") as fh:
            fh.readline()  # skip first ---
            for line in fh:
                stripped = line.rstrip("\n\r")
                if stripped == "---":
                    break
                frontmatter_lines.append(stripped)
    except (OSError, UnicodeDecodeError):
        pass

    if not frontmatter_lines:
        print(f"ERROR {filepath}: empty or malformed frontmatter")
        return 1, 0

    # 2.  Check required frontmatter fields
    for field in REQUIRED_FRONTMATTER:
        # Match field at the start of a line
        if not any(line.startswith(f"{field}:") for line in frontmatter_lines):
            print(f"ERROR {filepath}: missing frontmatter field '{field}'")
            errors += 1

    # 3.  Check recommended sections (warn only)
    body = get_body(filepath)
    body_lower = body.lower()
    for section in RECOMMENDED_SECTIONS:
        if section.lower() not in body_lower:
            print(f"WARN  {filepath}: missing recommended section '{section}'")
            warnings += 1

    # 4.  Check file has meaningful content
    word_count = len(body.split())
    if word_count < 50:
        print(f"WARN  {filepath}: body seems very short (< 50 words)")
        warnings += 1

    return errors, warnings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    files: List[str] = []
    if argv:
        files = argv
    else:
        # Scan all agent directories (relative to repo root)
        repo_root = _SCRIPT_DIR.parent
        for dirname in AGENT_DIRS:
            dirpath = repo_root / dirname
            if not dirpath.is_dir():
                continue
            for md in sorted(dirpath.rglob("*.md")):
                files.append(str(md))

    if not files:
        print("No agent files found.")
        sys.exit(1)

    print(f"Linting {len(files)} agent files...")
    print()

    total_errors = 0
    total_warnings = 0
    for filepath in files:
        e, w = lint_file(filepath)
        total_errors += e
        total_warnings += w

    print()
    print(f"Results: {total_errors} error(s), {total_warnings} warning(s) in {len(files)} files.")

    if total_errors > 0:
        print("FAILED: fix the errors above before merging.")
        sys.exit(1)
    else:
        print("PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
