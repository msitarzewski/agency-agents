"""Tests for skill loading, frontmatter parsing, and category grouping."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.agent.skills import Skill, SkillsLoader, _parse_frontmatter


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_basic(self) -> None:
        text = "---\nname: test-skill\ndescription: A test\n---\nBody here."
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "test-skill"
        assert meta["description"] == "A test"
        assert body == "Body here."

    def test_category_field(self) -> None:
        text = "---\nname: foo\ncategory: strategy\n---\nContent"
        meta, body = _parse_frontmatter(text)
        assert meta["category"] == "strategy"

    def test_boolean_values(self) -> None:
        text = "---\nname: foo\nactive: true\narchived: false\n---\nBody"
        meta, _ = _parse_frontmatter(text)
        assert meta["active"] is True
        assert meta["archived"] is False

    def test_list_values(self) -> None:
        text = "---\nname: foo\ntags: [a, b, c]\n---\nBody"
        meta, _ = _parse_frontmatter(text)
        assert meta["tags"] == ["a", "b", "c"]

    def test_empty_list(self) -> None:
        text = "---\nname: foo\ntags: []\n---\nBody"
        meta, _ = _parse_frontmatter(text)
        assert meta["tags"] == []

    def test_no_frontmatter(self) -> None:
        text = "Just plain text, no frontmatter."
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == text.strip()

    def test_multiline_body(self) -> None:
        text = "---\nname: x\n---\nLine 1\nLine 2\nLine 3"
        _, body = _parse_frontmatter(text)
        assert "Line 1" in body
        assert "Line 3" in body


# ---------------------------------------------------------------------------
# Skill dataclass
# ---------------------------------------------------------------------------


class TestSkill:
    def test_defaults(self) -> None:
        s = Skill(name="test")
        assert s.category == "other"
        assert s.description == ""
        assert s.body == ""
        assert s.metadata == {}

    def test_load_support_file_no_dir(self) -> None:
        s = Skill(name="test")
        assert s.load_support_file("missing.md") is None

    def test_load_support_file(self, tmp_path: Path) -> None:
        (tmp_path / "extra.md").write_text("extra content", encoding="utf-8")
        s = Skill(name="test", dir_path=tmp_path)
        assert s.load_support_file("extra.md") == "extra content"

    def test_load_support_file_missing(self, tmp_path: Path) -> None:
        s = Skill(name="test", dir_path=tmp_path)
        assert s.load_support_file("nope.md") is None


# ---------------------------------------------------------------------------
# SkillsLoader
# ---------------------------------------------------------------------------


class TestSkillsLoader:
    @pytest.fixture()
    def empty_user_dir(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Isolated empty user-skills dir so tests don't pick up real user skills."""
        return tmp_path_factory.mktemp("user_skills_empty")

    @pytest.fixture()
    def skills_dir(self, tmp_path: Path) -> Path:
        """Create a minimal skills directory with 3 skills in 2 categories."""
        for name, cat, desc in [
            ("alpha", "strategy", "Alpha strategy"),
            ("beta", "data-source", "Beta source"),
            ("gamma", "strategy", "Gamma strategy"),
        ]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(
                f"---\nname: {name}\ncategory: {cat}\ndescription: {desc}\n---\nBody of {name}.",
                encoding="utf-8",
            )
        return tmp_path

    def test_loads_all_skills(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        assert len(loader.skills) == 3

    def test_category_assignment(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        cats = {s.name: s.category for s in loader.skills}
        assert cats["alpha"] == "strategy"
        assert cats["beta"] == "data-source"

    def test_get_descriptions_grouped(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        desc = loader.get_descriptions()
        # data-source comes before strategy in _CATEGORY_ORDER
        ds_pos = desc.index("data-source")
        st_pos = desc.index("strategy")
        assert ds_pos < st_pos

    def test_get_descriptions_contains_all(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        desc = loader.get_descriptions()
        assert "alpha" in desc
        assert "beta" in desc
        assert "gamma" in desc

    def test_get_content_existing(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        content = loader.get_content("alpha")
        assert '<skill name="alpha">' in content
        assert "Body of alpha" in content

    def test_get_content_missing(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        content = loader.get_content("nonexistent")
        assert "Error" in content
        assert "nonexistent" in content

    def test_empty_dir(self, tmp_path: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir)
        assert loader.skills == []
        assert loader.get_descriptions() == "(no skills)"

    def test_dir_without_skill_md_skipped(self, tmp_path: Path, empty_user_dir: Path) -> None:
        (tmp_path / "empty_skill").mkdir()
        loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir)
        assert len(loader.skills) == 0

    def test_nonexistent_dir(self, tmp_path: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(tmp_path / "nope", user_skills_dir=empty_user_dir)
        assert loader.skills == []
