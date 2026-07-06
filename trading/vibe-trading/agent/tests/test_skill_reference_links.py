"""Regression tests: every ``references/`` link in data-source SKILL.md files
resolves through the ``read_file`` tool.

Background:
    ``read_file`` roots reads at the bundled ``skills/`` directory, so a link
    must carry the skill-name prefix (e.g. ``tushare/references/...``) to be
    reachable. Bare ``references/...`` links silently fail because
    ``skills/references/`` does not exist. These tests lock in the prefixed
    convention so the bug cannot regress.

No live API is touched: ``read_file`` performs local filesystem reads of the
bundled skill docs only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

import pytest

from src.tools.read_file_tool import ReadFileTool

# Bundled skills root (mirrors ReadFileTool's own allowed-root computation).
_SKILLS_DIR = Path(__file__).resolve().parents[1] / "src" / "skills"

# Skills whose SKILL.md links into a references/ and/or scripts/ tree.
_SKILLS_UNDER_TEST = ("tushare", "okx-market", "eastmoney", "sec-edgar", "yfinance")

# Markdown link whose target is a references/*.md or scripts/*.py path, e.g.
# "[label](tushare/references/foo/bar.md)" or "[ex](sec-edgar/scripts/x.py)".
# The target itself may contain parentheses (some tushare filenames do, e.g.
# "社融增量(月度).md"), so anchor on the trailing ".md)"/".py)" rather than the
# first ")".
_MD_LINK_RE = re.compile(
    r"\]\((?P<target>[^(]*(?:references/.+?\.md|scripts/.+?\.py))\)"
)


def _extract_reference_links(skill: str) -> List[str]:
    """Return every markdown link target containing ``references/``.

    Args:
        skill: Skill directory name (e.g. ``tushare``).

    Returns:
        List of raw link targets as written in SKILL.md.
    """
    text = (_SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
    return [m.group("target") for m in _MD_LINK_RE.finditer(text)]


def _read(path: str) -> dict:
    """Resolve a path through the read_file tool and return the parsed body.

    Args:
        path: Path argument passed to read_file (no run_dir; skills/ root).

    Returns:
        Parsed JSON response from ReadFileTool.execute.
    """
    return json.loads(ReadFileTool().execute(path=path))


def _all_links() -> List[Tuple[str, str]]:
    """Collect (skill, link) pairs across all skills under test."""
    pairs: List[Tuple[str, str]] = []
    for skill in _SKILLS_UNDER_TEST:
        for link in _extract_reference_links(skill):
            pairs.append((skill, link))
    return pairs


def test_skills_have_reference_links() -> None:
    """Sanity: each skill under test exposes references/ links to validate."""
    for skill in _SKILLS_UNDER_TEST:
        assert _extract_reference_links(skill), f"{skill} has no references/ links"


@pytest.mark.parametrize("skill,link", _all_links())
def test_reference_links_carry_skill_prefix(skill: str, link: str) -> None:
    """Every references/ or scripts/ link is written with its skill-name prefix.

    A bare ``references/...`` / ``scripts/...`` link is unreachable because
    read_file roots at ``skills/`` and ``skills/references/`` does not exist.
    """
    assert link.startswith(f"{skill}/"), (
        f"{skill}/SKILL.md link must carry the '{skill}/' prefix, got: {link}"
    )


@pytest.mark.parametrize("skill,link", _all_links())
def test_reference_links_resolve_through_read_file(skill: str, link: str) -> None:
    """Every references/ link resolves to an existing file via read_file."""
    body = _read(link)
    assert body["status"] == "ok", f"{link} did not resolve: {body}"
    assert body["content"], f"{link} resolved to empty content"


def test_bare_reference_link_would_fail() -> None:
    """Guard: a bare references/ path (no prefix) is NOT resolvable.

    This documents the exact failure mode the prefix convention prevents.
    """
    skill, link = _all_links()[0]
    bare = link[len(f"{skill}/"):]  # strip the skill-name prefix
    body = _read(bare)
    assert body["status"] == "error"
