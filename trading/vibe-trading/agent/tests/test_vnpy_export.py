"""Tests for the vnpy-export skill — SKILL.md integrity and template validity."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent / "src" / "skills" / "vnpy-export"
SKILL_MD = SKILL_DIR / "SKILL.md"
TEMPLATE_PY = SKILL_DIR / "scripts" / "cta_template.py"


# ---------------------------------------------------------------------------
# SKILL.md structure
# ---------------------------------------------------------------------------


class TestSkillMd:
    def test_skill_md_exists(self):
        assert SKILL_MD.exists(), "SKILL.md not found in agent/src/skills/vnpy-export/"

    def test_frontmatter_present(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        assert content.startswith("---"), "SKILL.md must begin with YAML frontmatter (---)"
        assert content.count("---") >= 2, "SKILL.md frontmatter must be closed with ---"

    def test_required_frontmatter_fields(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        # extract frontmatter block
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Could not parse frontmatter"
        frontmatter = parts[1]
        assert "name:" in frontmatter
        assert "description:" in frontmatter
        assert "category:" in frontmatter

    def test_name_field_value(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        assert "name: vnpy-export" in content

    def test_required_sections_present(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        required = [
            "## Overview",
            "## Workflow",
            "## CtaTemplate Structure",
            "## Full Template",
            "## Quality Checklist",
        ]
        for section in required:
            assert section in content, f"Missing section: {section}"

    def test_ctatemplate_methods_documented(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        for method in ("on_init", "on_start", "on_bar", "on_tick", "on_order", "on_trade"):
            assert method in content, f"Method {method} not documented in SKILL.md"

    def test_indicator_mapping_table_present(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        assert "ArrayManager" in content
        assert "am.sma" in content
        assert "am.ema" in content
        assert "am.rsi" in content

    def test_signal_order_mapping_present(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        for direction in ("self.buy", "self.sell", "self.short", "self.cover"):
            assert direction in content, f"Order direction {direction} missing from SKILL.md"

    def test_quality_checklist_present(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        assert "cancel_all" in content
        assert "put_event" in content
        assert "am.inited" in content


# ---------------------------------------------------------------------------
# cta_template.py — syntax and structure
# ---------------------------------------------------------------------------


class TestCtaTemplate:
    def test_template_file_exists(self):
        assert TEMPLATE_PY.exists(), "scripts/cta_template.py not found"

    def test_template_is_valid_python(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"cta_template.py has a syntax error: {exc}")

    def test_strategy_class_defined(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        class_names = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]
        assert any(name.endswith("Strategy") for name in class_names), (
            "No class ending in 'Strategy' found in cta_template.py"
        )

    def test_required_methods_defined(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        methods: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.add(node.name)
        for required in ("on_init", "on_start", "on_stop", "on_tick", "on_bar", "on_order", "on_trade"):
            assert required in methods, f"Method {required} missing from cta_template.py"

    def test_parameters_list_defined(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        assert "parameters" in source, "Class-level 'parameters' list missing"

    def test_variables_list_defined(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        assert "variables" in source, "Class-level 'variables' list missing"

    def test_bar_generator_used(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        assert "BarGenerator" in source

    def test_array_manager_used(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        assert "ArrayManager" in source

    def test_cancel_all_called_in_on_bar(self):
        source = TEMPLATE_PY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "on_bar":
                on_bar_src = ast.unparse(node)
                assert "cancel_all" in on_bar_src, "on_bar must call self.cancel_all()"
                assert "put_event" in on_bar_src, "on_bar must call self.put_event()"
                return
        pytest.fail("on_bar method not found in cta_template.py")
