"""Tests for RememberTool: save / recall / forget via PersistentMemory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.memory.persistent import PersistentMemory
from src.tools.remember_tool import RememberTool


@pytest.fixture()
def tool(tmp_path: Path) -> RememberTool:
    """Create a RememberTool backed by a tmp_path memory directory."""
    pm = PersistentMemory(memory_dir=tmp_path)
    return RememberTool(memory=pm)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


class TestSave:
    def test_save_basic(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="save", title="pref", content="risk=low"))
        assert result["status"] == "ok"
        assert "pref" in result["message"]

    def test_save_with_type(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="save", title="user-pref", content="likes TSLA", memory_type="user"))
        assert result["status"] == "ok"
        assert Path(result["path"]).name.startswith("user_")

    def test_save_missing_title(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="save", content="body"))
        assert result["status"] == "error"

    def test_save_missing_content(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="save", title="empty"))
        assert result["status"] == "error"

    def test_save_missing_both(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="save"))
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# recall
# ---------------------------------------------------------------------------


class TestRecall:
    def test_recall_finds_saved(self, tool: RememberTool) -> None:
        tool.execute(action="save", title="btc-insight", content="Bitcoin will rally in Q3", memory_type="project")
        result = json.loads(tool.execute(action="recall", query="Bitcoin rally"))
        assert result["status"] == "ok"
        assert result["count"] >= 1
        assert any("btc-insight" in m["title"] for m in result["memories"])

    def test_recall_no_match(self, tool: RememberTool) -> None:
        tool.execute(action="save", title="something", content="unrelated")
        result = json.loads(tool.execute(action="recall", query="xyznonexistent"))
        assert result["status"] == "ok"
        assert result["count"] == 0

    def test_recall_missing_query(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="recall"))
        assert result["status"] == "error"

    def test_recall_content_truncated(self, tool: RememberTool) -> None:
        tool.execute(action="save", title="long", content="x" * 5000)
        result = json.loads(tool.execute(action="recall", query="long"))
        if result["count"] > 0:
            assert len(result["memories"][0]["content"]) <= 2000

    def test_recall_multiple(self, tool: RememberTool) -> None:
        for i in range(5):
            tool.execute(action="save", title=f"stock-{i}", content=f"analysis of stock {i}")
        result = json.loads(tool.execute(action="recall", query="stock analysis"))
        assert result["count"] >= 2


# ---------------------------------------------------------------------------
# forget
# ---------------------------------------------------------------------------


class TestForget:
    def test_forget_existing(self, tool: RememberTool) -> None:
        tool.execute(action="save", title="forget-me", content="temporary")
        result = json.loads(tool.execute(action="forget", title="forget-me"))
        assert result["status"] == "ok"
        assert "Removed" in result["message"]
        # Confirm gone
        recall = json.loads(tool.execute(action="recall", query="temporary"))
        assert recall["count"] == 0

    def test_forget_nonexistent(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="forget", title="ghost"))
        assert result["status"] == "not_found"

    def test_forget_missing_title(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="forget"))
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------


class TestUnknownAction:
    def test_unknown_action(self, tool: RememberTool) -> None:
        result = json.loads(tool.execute(action="destroy"))
        assert result["status"] == "error"
        assert "Unknown" in result["error"]


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_save_recall_forget_recall(self, tool: RememberTool) -> None:
        tool.execute(action="save", title="lifecycle", content="full cycle test", memory_type="feedback")
        r1 = json.loads(tool.execute(action="recall", query="lifecycle"))
        assert r1["count"] >= 1

        tool.execute(action="forget", title="lifecycle")
        r2 = json.loads(tool.execute(action="recall", query="lifecycle"))
        assert r2["count"] == 0

    def test_overwrite_and_recall(self, tool: RememberTool) -> None:
        tool.execute(action="save", title="evolving", content="version 1")
        tool.execute(action="save", title="evolving", content="version 2 updated")
        result = json.loads(tool.execute(action="recall", query="evolving"))
        assert result["count"] >= 1
        assert "version 2" in result["memories"][0]["content"]
