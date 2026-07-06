"""Tests for skill writer tools: SaveSkillTool, PatchSkillTool, DeleteSkillTool, SkillFileTool."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.tools.skill_writer_tool import (
    SaveSkillTool,
    PatchSkillTool,
    DeleteSkillTool,
    SkillFileTool,
    _sanitize_skill_name,
    USER_SKILLS_DIR,
)


# ---------------------------------------------------------------------------
# _sanitize_skill_name
# ---------------------------------------------------------------------------


class TestSanitizeSkillName:
    def test_lowercase(self) -> None:
        assert _sanitize_skill_name("My-Skill") == "my-skill"

    def test_special_chars(self) -> None:
        assert _sanitize_skill_name("a b!c@d") == "a-b-c-d"

    def test_truncation(self) -> None:
        long = "x" * 100
        assert len(_sanitize_skill_name(long)) <= 60

    def test_empty(self) -> None:
        assert _sanitize_skill_name("") == ""


# ---------------------------------------------------------------------------
# SaveSkillTool
# ---------------------------------------------------------------------------


class TestSaveSkillTool:
    @pytest.fixture()
    def tool(self, tmp_path: Path) -> SaveSkillTool:
        with patch("src.tools.skill_writer_tool.USER_SKILLS_DIR", tmp_path):
            yield SaveSkillTool()

    @pytest.fixture()
    def user_dir(self, tmp_path: Path) -> Path:
        return tmp_path

    def test_save_basic(self, tool: SaveSkillTool, user_dir: Path) -> None:
        result = json.loads(tool.execute(name="test-skill", content="# My Skill\nBody text"))
        assert result["status"] == "ok"
        skill_dir = user_dir / "test-skill"
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()

    def test_save_adds_frontmatter(self, tool: SaveSkillTool, user_dir: Path) -> None:
        result = json.loads(tool.execute(name="no-fm", content="Plain body without frontmatter"))
        assert result["status"] == "ok"
        text = (user_dir / "no-fm" / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "name: no-fm" in text

    def test_save_preserves_existing_frontmatter(self, tool: SaveSkillTool, user_dir: Path) -> None:
        content = "---\nname: custom\ndescription: Custom skill\ncategory: strategy\n---\nBody"
        result = json.loads(tool.execute(name="custom", content=content))
        assert result["status"] == "ok"
        text = (user_dir / "custom" / "SKILL.md").read_text(encoding="utf-8")
        assert "description: Custom skill" in text

    def test_save_missing_name(self, tool: SaveSkillTool) -> None:
        result = json.loads(tool.execute(content="body"))
        assert result["status"] == "error"

    def test_save_missing_content(self, tool: SaveSkillTool) -> None:
        result = json.loads(tool.execute(name="empty"))
        assert result["status"] == "error"

    def test_save_overwrite(self, tool: SaveSkillTool, user_dir: Path) -> None:
        tool.execute(name="overwrite", content="v1")
        tool.execute(name="overwrite", content="---\nname: overwrite\n---\nv2")
        text = (user_dir / "overwrite" / "SKILL.md").read_text(encoding="utf-8")
        assert "v2" in text


# ---------------------------------------------------------------------------
# PatchSkillTool
# ---------------------------------------------------------------------------


class TestPatchSkillTool:
    @pytest.fixture()
    def setup(self, tmp_path: Path):
        user_dir = tmp_path / "user"
        bundled_dir = tmp_path / "bundled"
        with patch("src.tools.skill_writer_tool.USER_SKILLS_DIR", user_dir):
            tool = PatchSkillTool()
            yield tool, user_dir, bundled_dir

    def test_patch_user_skill(self, setup) -> None:
        tool, user_dir, _ = setup
        skill_dir = user_dir / "patchme"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("old_api_call()", encoding="utf-8")

        result = json.loads(tool.execute(name="patchme", find="old_api_call()", replace="new_api_call()"))
        assert result["status"] == "ok"
        assert "new_api_call()" in (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    def test_patch_text_not_found(self, setup) -> None:
        tool, user_dir, _ = setup
        skill_dir = user_dir / "nofind"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("some content", encoding="utf-8")

        result = json.loads(tool.execute(name="nofind", find="MISSING", replace="X"))
        assert result["status"] == "error"

    def test_patch_nonexistent_skill(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(name="ghost", find="x", replace="y"))
        assert result["status"] == "error"

    def test_patch_missing_params(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(name="", find="x", replace="y"))
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# DeleteSkillTool
# ---------------------------------------------------------------------------


class TestDeleteSkillTool:
    @pytest.fixture()
    def setup(self, tmp_path: Path):
        with patch("src.tools.skill_writer_tool.USER_SKILLS_DIR", tmp_path):
            tool = DeleteSkillTool()
            yield tool, tmp_path

    def test_delete_existing(self, setup) -> None:
        tool, user_dir = setup
        skill_dir = user_dir / "deleteme"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("body", encoding="utf-8")

        result = json.loads(tool.execute(name="deleteme"))
        assert result["status"] == "ok"
        assert not skill_dir.exists()

    def test_delete_nonexistent(self, setup) -> None:
        tool, _ = setup
        result = json.loads(tool.execute(name="ghost"))
        assert result["status"] == "error"

    def test_delete_empty_name(self, setup) -> None:
        tool, _ = setup
        result = json.loads(tool.execute(name=""))
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# SkillFileTool
# ---------------------------------------------------------------------------


class TestSkillFileTool:
    @pytest.fixture()
    def setup(self, tmp_path: Path):
        with patch("src.tools.skill_writer_tool.USER_SKILLS_DIR", tmp_path):
            tool = SkillFileTool()
            # Pre-create a skill directory
            skill_dir = tmp_path / "file-test"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("body", encoding="utf-8")
            yield tool, tmp_path, skill_dir

    def test_list_files(self, setup) -> None:
        tool, _, skill_dir = setup
        (skill_dir / "templates").mkdir()
        (skill_dir / "templates" / "sma.py").write_text("code", encoding="utf-8")
        result = json.loads(tool.execute(action="list", skill_name="file-test"))
        assert result["status"] == "ok"
        paths = [f["path"] for f in result["files"]]
        assert any("sma.py" in p for p in paths)

    def test_write_file(self, setup) -> None:
        tool, _, skill_dir = setup
        result = json.loads(tool.execute(
            action="write", skill_name="file-test",
            path="templates/strategy.py", content="def run(): pass",
        ))
        assert result["status"] == "ok"
        assert (skill_dir / "templates" / "strategy.py").exists()

    def test_write_invalid_subdir(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(
            action="write", skill_name="file-test",
            path="invalid_dir/file.py", content="code",
        ))
        assert result["status"] == "error"

    def test_write_missing_path(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(
            action="write", skill_name="file-test", content="code",
        ))
        assert result["status"] == "error"

    def test_remove_file(self, setup) -> None:
        tool, _, skill_dir = setup
        (skill_dir / "assets").mkdir()
        (skill_dir / "assets" / "data.csv").write_text("1,2,3", encoding="utf-8")
        result = json.loads(tool.execute(
            action="remove", skill_name="file-test", path="assets/data.csv",
        ))
        assert result["status"] == "ok"
        assert not (skill_dir / "assets" / "data.csv").exists()

    def test_remove_skill_md_blocked(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(
            action="remove", skill_name="file-test", path="SKILL.md",
        ))
        assert result["status"] == "error"

    def test_remove_nonexistent_file(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(
            action="remove", skill_name="file-test", path="assets/ghost.txt",
        ))
        assert result["status"] == "error"

    def test_nonexistent_skill(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(action="list", skill_name="nope"))
        assert result["status"] == "error"

    def test_unknown_action(self, setup) -> None:
        tool, _, _ = setup
        result = json.loads(tool.execute(action="explode", skill_name="file-test"))
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# Full CRUD lifecycle
# ---------------------------------------------------------------------------


class TestSkillCRUDLifecycle:
    def test_create_patch_file_delete(self, tmp_path: Path) -> None:
        with patch("src.tools.skill_writer_tool.USER_SKILLS_DIR", tmp_path):
            save = SaveSkillTool()
            patch_tool = PatchSkillTool()
            file_tool = SkillFileTool()
            delete = DeleteSkillTool()

            # 1. Create
            r = json.loads(save.execute(name="lifecycle", content="---\nname: lifecycle\n---\nold_code()"))
            assert r["status"] == "ok"

            # 2. Patch
            r = json.loads(patch_tool.execute(name="lifecycle", find="old_code()", replace="new_code()"))
            assert r["status"] == "ok"
            text = (tmp_path / "lifecycle" / "SKILL.md").read_text(encoding="utf-8")
            assert "new_code()" in text

            # 3. Add auxiliary file
            r = json.loads(file_tool.execute(
                action="write", skill_name="lifecycle",
                path="templates/helper.py", content="def helper(): pass",
            ))
            assert r["status"] == "ok"

            # 4. List files
            r = json.loads(file_tool.execute(action="list", skill_name="lifecycle"))
            assert r["status"] == "ok"
            assert len(r["files"]) >= 2  # SKILL.md + helper.py

            # 5. Delete
            r = json.loads(delete.execute(name="lifecycle"))
            assert r["status"] == "ok"
            assert not (tmp_path / "lifecycle").exists()
