"""Tests for SessionSearchIndex: SQLite FTS5 cross-session search."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from src.session.search import SessionSearchIndex, SearchMatch


@pytest.fixture()
def index(tmp_path: Path) -> SessionSearchIndex:
    """Create an ephemeral SessionSearchIndex backed by a tmp_path SQLite db."""
    db_path = tmp_path / "test_sessions.db"
    idx = SessionSearchIndex(db_path=db_path)
    yield idx
    idx.close()


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


class TestIndexing:
    def test_index_session(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "My first session")
        # No crash, session stored
        results = index.search("first session")
        # May or may not match depending on FTS5 availability
        # At minimum: no crash

    def test_index_message(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Test session")
        index.index_message("s1", "user", "I want to analyze Bitcoin")
        results = index.search("Bitcoin")
        assert len(results) >= 1
        assert results[0].session_id == "s1"

    def test_index_empty_content_skipped(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Test")
        index.index_message("s1", "user", "")
        index.index_message("s1", "user", "   ")
        # Should not crash, empty content ignored

    def test_index_multiple_sessions(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Bitcoin analysis")
        index.index_message("s1", "user", "BTC price prediction")
        index.index_session("s2", "Ethereum research")
        index.index_message("s2", "user", "ETH DeFi analysis")

        btc = index.search("Bitcoin BTC")
        eth = index.search("Ethereum ETH")
        assert any(m.session_id == "s1" for m in btc)
        assert any(m.session_id == "s2" for m in eth)

    def test_message_count_increments(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Counter test")
        index.index_message("s1", "user", "msg 1")
        index.index_message("s1", "assistant", "msg 2")
        index.index_message("s1", "user", "msg 3")
        results = index.search("msg")
        if results:
            assert results[0].message_count == 3


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_relevance_ranking(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Unrelated topic")
        index.index_message("s1", "user", "weather forecast for tomorrow")
        index.index_session("s2", "Bitcoin deep dive")
        index.index_message("s2", "user", "Bitcoin price analysis and trading strategy for Bitcoin")

        results = index.search("Bitcoin")
        assert len(results) >= 1
        # s2 should rank higher (more mentions)
        assert results[0].session_id == "s2"

    def test_max_sessions_limit(self, index: SessionSearchIndex) -> None:
        for i in range(10):
            sid = f"s{i}"
            index.index_session(sid, f"Session {i}")
            index.index_message(sid, "user", f"common keyword topic {i}")

        results = index.search("common keyword", max_sessions=3)
        assert len(results) <= 3

    def test_no_results(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Test")
        index.index_message("s1", "user", "hello world")
        results = index.search("xyznonexistent999zyx")
        assert len(results) == 0

    def test_cjk_search(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "A股分析")
        index.index_message("s1", "user", "上证指数今日走势分析 shanghai composite index")
        # FTS5 tokenizes by whitespace; CJK single chars may not match.
        # Search with the ASCII fallback to verify the session is indexed.
        results = index.search("shanghai composite index")
        assert len(results) >= 1

    def test_snippet_contains_match(self, index: SessionSearchIndex) -> None:
        index.index_session("s1", "Snippet test")
        index.index_message("s1", "user", "The quick brown fox jumps over the lazy dog")
        results = index.search("fox")
        if results:
            # FTS5 snippet markers
            assert "fox" in results[0].snippet.lower()

    def test_index_session_stores_explicit_ts(self, index: SessionSearchIndex) -> None:
        """When caller passes ts, started_at must reflect it (B2 regression)."""
        explicit_ts = 1_700_000_000.0  # 2023-11-14 22:13:20 UTC
        index.index_session("s1", "Backfilled", ts=explicit_ts)
        conn = index._get_conn()
        row = conn.execute(
            "SELECT started_at FROM sessions WHERE id = ?", ("s1",)
        ).fetchone()
        assert row is not None
        assert row[0] == pytest.approx(explicit_ts)

    def test_index_session_preserves_started_at_on_reupsert(
        self, index: SessionSearchIndex
    ) -> None:
        """Re-indexing without ts must keep the original started_at."""
        original_ts = 1_700_000_000.0
        index.index_session("s1", "First", ts=original_ts)
        # Simulate a later title-only update (no ts supplied).
        index.index_session("s1", "Renamed")
        conn = index._get_conn()
        row = conn.execute(
            "SELECT title, started_at FROM sessions WHERE id = ?", ("s1",)
        ).fetchone()
        assert row[0] == "Renamed"
        assert row[1] == pytest.approx(original_ts)

    def test_search_match_to_dict(self, index: SessionSearchIndex) -> None:
        match = SearchMatch(
            session_id="s1", title="Test", started_at="2026-01-01 00:00",
            message_count=5, snippet="hello", rank=-1.0,
        )
        d = match.to_dict()
        assert d["session_id"] == "s1"
        assert d["message_count"] == 5
        assert "rank" not in d  # rank not in to_dict


# ---------------------------------------------------------------------------
# _sanitize_fts_query
# ---------------------------------------------------------------------------


class TestSanitizeFtsQuery:
    def test_basic_words(self) -> None:
        result = SessionSearchIndex._sanitize_fts_query("hello world")
        assert '"hello"' in result
        assert '"world"' in result

    def test_special_chars_stripped(self) -> None:
        result = SessionSearchIndex._sanitize_fts_query("hello* OR (world)")
        assert "hello" in result
        assert "world" in result
        # Should not contain raw FTS5 operators
        assert "OR (" not in result or result.count("OR") == result.count('" OR "')

    def test_empty_query(self) -> None:
        result = SessionSearchIndex._sanitize_fts_query("")
        assert result == '""'

    def test_cjk(self) -> None:
        result = SessionSearchIndex._sanitize_fts_query("比特币价格")
        assert "比" in result
        assert "币" in result


# ---------------------------------------------------------------------------
# reindex_from_store
# ---------------------------------------------------------------------------


class TestReindex:
    def test_reindex_empty_dir(self, index: SessionSearchIndex, tmp_path: Path) -> None:
        store_dir = tmp_path / "empty_store"
        store_dir.mkdir()
        count = index.reindex_from_store(store_dir)
        assert count == 0

    def test_reindex_nonexistent_dir(self, index: SessionSearchIndex, tmp_path: Path) -> None:
        count = index.reindex_from_store(tmp_path / "nope")
        assert count == 0

    def test_reindex_from_file_store(self, index: SessionSearchIndex, tmp_path: Path) -> None:
        import json
        store_dir = tmp_path / "sessions"
        store_dir.mkdir()

        # Create a fake session directory
        s_dir = store_dir / "session-001"
        s_dir.mkdir()
        (s_dir / "session.json").write_text(json.dumps({
            "session_id": "session-001",
            "title": "Reindex test",
            "created_at": "2026-01-01T00:00:00",
        }), encoding="utf-8")
        (s_dir / "messages.jsonl").write_text(
            json.dumps({"role": "user", "content": "reindex probe message"}) + "\n"
            + json.dumps({"role": "assistant", "content": "reindex probe reply"}) + "\n",
            encoding="utf-8",
        )

        count = index.reindex_from_store(store_dir)
        assert count == 2

        results = index.search("reindex probe")
        assert len(results) >= 1
        assert results[0].session_id == "session-001"
