#!/usr/bin/env python3
"""test_loader.py — deterministic tests for load_agent / list_agents.
No LLM call required. Run: python3 test/test_loader.py
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add parent dir to path so we can import dispatcher
sys.path.insert(0, str(Path(__file__).parent.parent))
from dispatcher import load_agent, list_agents  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


class TestLoader(unittest.TestCase):
    def test_full_frontmatter_agent(self):
        a = load_agent(str(FIXTURES / "sample-agent.md"))
        self.assertEqual(a.name, "Sample Agent")
        self.assertEqual(
            a.description,
            "Test fixture used by the dispatcher loader tests",
        )
        self.assertEqual(a.frontmatter["color"], "blue")
        self.assertEqual(a.frontmatter["emoji"], "🧪")
        self.assertIn("UNIQUE_BODY_MARKER_FOR_TEST_42", a.body)

    def test_no_frontmatter_fallback(self):
        a = load_agent(str(FIXTURES / "no-frontmatter.md"))
        self.assertEqual(a.name, "no-frontmatter")
        self.assertEqual(a.description, "")
        self.assertIn("UNIQUE_PLAIN_MARKER_FOR_TEST_43", a.body)

    def test_directory_with_multiple_mds_raises(self):
        with self.assertRaises(ValueError) as ctx:
            load_agent(str(FIXTURES))
        self.assertIn("multiple .md files", str(ctx.exception))

    def test_path_without_extension(self):
        a = load_agent(str(FIXTURES / "sample-agent"))
        self.assertEqual(a.name, "Sample Agent")

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_agent(str(FIXTURES / "does-not-exist.md"))

    def test_list_agents_finds_both(self):
        items = list_agents(str(FIXTURES))
        self.assertEqual(len(items), 2)
        names = sorted(i["name"] for i in items)
        self.assertEqual(names, ["Sample Agent", "no-frontmatter"])

    def test_list_agents_on_non_directory_raises(self):
        with self.assertRaises(NotADirectoryError):
            list_agents(str(FIXTURES / "sample-agent.md"))

    def test_quoted_frontmatter_values_stripped(self):
        a = load_agent(str(FIXTURES / "sample-agent.md"))
        self.assertFalse(a.description.startswith('"'))
        self.assertFalse(a.description.endswith('"'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
