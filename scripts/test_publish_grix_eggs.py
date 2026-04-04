#!/usr/bin/env python3

import tempfile
import unittest
import zipfile
from pathlib import Path

from publish_grix_eggs import (
    EXCLUDED_PERSONA_FILENAMES,
    build_publish_artifacts,
    discover_agent_packages,
    extract_csrf_token,
    fit_text,
    normalize_color,
)


class PublishGrixEggsTests(unittest.TestCase):
    def test_discover_agent_packages_finds_real_repo_pairs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        packages = discover_agent_packages(repo_root)
        self.assertTrue(packages)
        egg_ids = {package.egg_id for package in packages}
        self.assertIn("engineering-ai-engineer", egg_ids)

    def test_build_publish_artifacts_keeps_skill_and_filters_persona_reports(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        package = next(
            package
            for package in discover_agent_packages(repo_root)
            if package.egg_id == "engineering-ai-engineer"
        )
        temp_dir = Path(tempfile.mkdtemp(prefix="publish-grix-eggs-test-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(temp_dir, ignore_errors=True))

        artifacts = build_publish_artifacts(package, temp_dir)

        with zipfile.ZipFile(artifacts.skill_zip) as archive:
            self.assertEqual(archive.namelist(), ["skill.md"])
            content = archive.read("skill.md").decode("utf-8")
            self.assertIn("AI Engineer", content)

        with zipfile.ZipFile(artifacts.openclaw_zip) as archive:
            entries = set(archive.namelist())
            self.assertIn("AGENTS.md", entries)
            self.assertIn("IDENTITY.md", entries)
            self.assertIn("SOUL.md", entries)
            self.assertFalse(any(Path(name).name in EXCLUDED_PERSONA_FILENAMES for name in entries))

    def test_extract_csrf_token(self) -> None:
        html = '<input type="hidden" name="csrf_token" value="abc123">'
        self.assertEqual(extract_csrf_token(html), "abc123")

    def test_normalize_color(self) -> None:
        self.assertEqual(normalize_color("blue"), "#3498DB")
        self.assertEqual(normalize_color("#abcdef"), "#ABCDEF")
        self.assertEqual(normalize_color("unknown"), "#D97706")

    def test_fit_text_truncates_with_ellipsis(self) -> None:
        self.assertEqual(fit_text("abc", 5), "abc")
        self.assertEqual(fit_text("abcdef", 5), "abcd…")


if __name__ == "__main__":
    unittest.main()
