"""Tests for the bundled dividend-analysis skill."""

from __future__ import annotations

from pathlib import Path

from src.agent.skills import SkillsLoader, _parse_frontmatter


SKILL_DIR = Path(__file__).resolve().parents[1] / "src" / "skills" / "dividend-analysis"
SKILL_MD = SKILL_DIR / "SKILL.md"


def test_dividend_analysis_skill_metadata() -> None:
    """Dividend analysis skill ships with valid frontmatter."""
    text = SKILL_MD.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)

    assert meta["name"] == "dividend-analysis"
    assert meta["category"] == "analysis"
    assert "Dividend stock analysis" in meta["description"]
    assert "Yield-Trap Checklist" in body


def test_dividend_analysis_skill_contains_required_frameworks() -> None:
    """Skill includes the decision frameworks needed for agent answers."""
    text = SKILL_MD.read_text(encoding="utf-8")
    lower_text = text.lower()

    assert "free-cash-flow payout" in lower_text
    for needle in [
        "Dividend Growth",
        "High-Yield Quality",
        "Shareholder Yield",
        "Dividend Capture",
        "Data Sources",
        "Output Template",
        "not live trading advice",
    ]:
        assert needle in text


def test_dividend_analysis_skill_loads_with_bundled_skills(tmp_path: Path) -> None:
    """Bundled loader exposes the new skill in the analysis category."""
    bundled_dir = Path(__file__).resolve().parents[1] / "src" / "skills"
    loader = SkillsLoader(bundled_dir, user_skills_dir=tmp_path)

    content = loader.get_content("dividend-analysis")
    descriptions = loader.get_descriptions()

    assert '<skill name="dividend-analysis">' in content
    assert "Dividend stock analysis" in descriptions
    assert "### analysis" in descriptions
