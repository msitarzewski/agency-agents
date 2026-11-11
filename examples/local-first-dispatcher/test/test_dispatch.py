#!/usr/bin/env python3
"""test_dispatch.py — live dispatch test against a local OpenAI-compatible
runtime. Skips cleanly if no runtime is reachable.
"""
from __future__ import annotations

import os
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dispatcher import load_agent, dispatch_agent  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
BASE_URL = os.environ.get("AGENCY_BASE_URL", "http://127.0.0.1:11434/v1")
MODEL = os.environ.get("AGENCY_MODEL", "llama3.1:8b")


def _runtime_reachable() -> bool:
    url = BASE_URL.rstrip("/") + "/models"
    try:
        with urllib.request.urlopen(url, timeout=3):
            return True
    except (urllib.error.URLError, OSError):
        return False


class TestDispatch(unittest.TestCase):
    def test_dispatch_sample_agent(self):
        if not _runtime_reachable():
            self.skipTest(f"runtime not reachable at {BASE_URL}")
        agent = load_agent(str(FIXTURES / "sample-agent.md"))
        result = dispatch_agent(
            agent=agent,
            task='Say only the word "OK" and stop.',
            base_url=BASE_URL,
            model=MODEL,
            max_tokens=8,
        )
        self.assertTrue(result["ok"], f"dispatch failed: {result}")
        self.assertEqual(result["agent"], "Sample Agent")
        self.assertGreater(len(result["content"]), 0)
        self.assertGreater(result["latency_ms"], 0)

    def test_empty_task_returns_error(self):
        agent = load_agent(str(FIXTURES / "sample-agent.md"))
        result = dispatch_agent(
            agent=agent, task="", base_url=BASE_URL, model=MODEL
        )
        self.assertFalse(result["ok"])
        self.assertIn("task required", result["error"])

    def test_missing_agent_returns_error(self):
        result = dispatch_agent(
            agent=None, task="hi", base_url=BASE_URL, model=MODEL
        )
        self.assertFalse(result["ok"])
        self.assertIn("agent required", result["error"])

    def test_unreachable_url_returns_unreachable(self):
        agent = load_agent(str(FIXTURES / "sample-agent.md"))
        result = dispatch_agent(
            agent=agent,
            task="hi",
            base_url="http://127.0.0.1:1/v1",  # port 1 closed
            model=MODEL,
            timeout_s=2.0,
        )
        self.assertFalse(result["ok"])
        # Either runtime_unreachable or runtime_http_*
        self.assertTrue(
            result["error"].startswith("runtime_"),
            f"unexpected error: {result['error']}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
