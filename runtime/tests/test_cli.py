"""CLI tests using click.testing.CliRunner.

Tests the offline commands (list, plan with keyword fallback) and verifies
run() surfaces a useful error message when no API key is set.
"""

from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from agency.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_list_prints_skills(runner, no_api_key):
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "skill(s):" in result.output
    assert "engineering-" in result.output  # at least one engineering skill shows


def test_list_filters_by_category(runner, no_api_key):
    result = runner.invoke(main, ["list", "--category", "engineering"])
    assert result.exit_code == 0
    lines = result.output.splitlines()
    # Every shown skill line (not the header) should be from engineering/
    skill_lines = [l for l in lines if l.startswith("  ") and "(" in l]
    assert skill_lines
    for line in skill_lines:
        assert "(engineering)" in line, line


def test_list_filters_by_search(runner, no_api_key):
    result = runner.invoke(main, ["list", "--search", "frontend"])
    assert result.exit_code == 0
    assert "frontend" in result.output.lower()


def test_plan_uses_keyword_fallback_when_no_key(runner, no_api_key):
    result = runner.invoke(main, ["plan", "build a React component"])
    assert result.exit_code == 0
    assert "Picked:" in result.output
    assert "Reason:" in result.output


def test_plan_honors_hint_skill(runner, no_api_key):
    result = runner.invoke(
        main, ["plan", "anything", "--skill", "engineering-frontend-developer"]
    )
    assert result.exit_code == 0
    assert "engineering-frontend-developer" in result.output
    assert "explicit user choice" in result.output


def test_run_without_api_key_gives_useful_error(runner, no_api_key):
    result = runner.invoke(main, ["run", "hello"])
    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output


def test_init_scaffolds_new_persona(runner, no_api_key, tmp_path):
    # Point at a fake repo that looks like the real one.
    (tmp_path / "engineering").mkdir()
    (tmp_path / "engineering" / "existing.md").write_text("placeholder")
    (tmp_path / "README.md").write_text("fake repo")

    result = runner.invoke(main, [
        "--repo", str(tmp_path),
        "init", "rocket-scientist",
        "--name", "Rocket Scientist",
        "--category", "specialized",
        "--emoji", "🚀",
        "--description", "Builds rockets.",
    ])
    assert result.exit_code == 0, result.output
    created = tmp_path / "specialized" / "rocket-scientist.md"
    assert created.exists()
    text = created.read_text()
    assert "name: Rocket Scientist" in text
    assert "🚀" in text
    assert "Builds rockets" in text


def test_doctor_reports_skill_counts_and_env(runner, no_api_key):
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0, result.output
    assert "Agency Runtime Doctor" in result.output
    assert "skills loaded:" in result.output
    assert "engineering" in result.output  # a category should appear
    assert "ANTHROPIC_API_KEY" in result.output
    assert "AGENCY_ENABLE_COMPUTER_USE" in result.output
    assert "optional deps" in result.output
    assert "tool context" in result.output


def test_init_refuses_to_overwrite(runner, no_api_key, tmp_path):
    (tmp_path / "engineering").mkdir()
    (tmp_path / "engineering" / "existing.md").write_text("x")
    (tmp_path / "README.md").write_text("fake")
    (tmp_path / "specialized").mkdir()
    (tmp_path / "specialized" / "taken.md").write_text("y")

    result = runner.invoke(main, [
        "--repo", str(tmp_path),
        "init", "taken", "--category", "specialized",
    ])
    assert result.exit_code != 0
    assert "exists" in result.output.lower()
