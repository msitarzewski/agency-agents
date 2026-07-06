"""Tests for PersistentMemory: file-based cross-session memory."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.memory.persistent import (
    MAX_ENTRY_CHARS,
    MemoryEntry,
    PersistentMemory,
    _coerce_str,
    _sanitize_body,
    _tokenize,
    _truncate_body,
)


class TestCoerceStr:
    def test_passthrough_string(self) -> None:
        assert _coerce_str("hello") == "hello"

    def test_none_uses_default(self) -> None:
        assert _coerce_str(None, default="fallback") == "fallback"

    def test_list_joined_with_comma(self) -> None:
        # `description: [red]inject[/red]` would parse to a single-element list
        # because the frontmatter parser treats ``[...]`` as a list literal.
        assert _coerce_str(["red]inject[/red"]) == "red]inject[/red"
        assert _coerce_str(["a", "b"]) == "a, b"

    def test_bool_lowercased(self) -> None:
        assert _coerce_str(True) == "true"
        assert _coerce_str(False) == "false"


class TestScanEntriesCoercesFrontmatter:
    def test_bracketed_description_renders_as_string(self, tmp_path) -> None:
        # Regression: a description like ``[red]x[/red]`` parsed as a list used
        # to leak through MemoryEntry.description and crash any downstream
        # consumer that called string ops on it (e.g. rich.markup.escape).
        entry_path = tmp_path / "user_bracket-desc.md"
        entry_path.write_text(
            "---\nname: bracket-desc\ndescription: [red]inject[/red]\ntype: user\n---\n\nbody\n",
            encoding="utf-8",
        )
        pm = PersistentMemory(memory_dir=tmp_path)
        entries = pm.list_entries()
        assert len(entries) == 1
        assert isinstance(entries[0].description, str)


# ---------------------------------------------------------------------------
# _tokenize
# ---------------------------------------------------------------------------


class TestTokenize:
    def test_ascii_words(self) -> None:
        tokens = _tokenize("hello world testing")
        assert "hello" in tokens
        assert "world" in tokens
        assert "testing" in tokens

    def test_short_words_excluded(self) -> None:
        tokens = _tokenize("I am ok no")
        # All < 3 chars, should be excluded
        assert len(tokens) == 0

    def test_cjk_characters(self) -> None:
        tokens = _tokenize("比特币价格分析")
        assert "比" in tokens
        assert "币" in tokens
        assert "价" in tokens

    def test_mixed(self) -> None:
        tokens = _tokenize("AAPL 苹果 stock analysis")
        assert "aapl" in tokens
        assert "苹" in tokens
        assert "stock" in tokens
        assert "analysis" in tokens

    def test_empty(self) -> None:
        assert _tokenize("") == set()

    def test_underscores_split(self) -> None:
        # snake_case titles must match natural-language queries.
        # Regression: previously _tokenize treated underscores as word chars,
        # so "mcp_wiring_test" became a single token and queries like
        # "mcp wiring" never matched.
        tokens = _tokenize("mcp_wiring_test")
        assert tokens == {"mcp", "wiring", "test"}

    def test_thai_characters(self) -> None:
        # Thai script (฀-๿) was not tokenized — recall on Thai
        # queries always returned the empty set. Char-level like CJK.
        tokens = _tokenize("นโยบายการเทรด")
        assert "น" in tokens
        assert "เ" in tokens
        assert "ท" in tokens

    def test_arabic_characters(self) -> None:
        tokens = _tokenize("التداول")
        assert "ا" in tokens
        assert "ل" in tokens

    def test_hebrew_characters(self) -> None:
        tokens = _tokenize("מסחר")
        assert "מ" in tokens
        assert "ס" in tokens

    def test_cyrillic_characters(self) -> None:
        tokens = _tokenize("торговля")
        assert "т" in tokens
        assert "о" in tokens


# ---------------------------------------------------------------------------
# PersistentMemory.add
# ---------------------------------------------------------------------------


class TestAdd:
    def test_creates_file_and_index(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add("test-mem", "Some content", "project", description="Test desc")
        assert path.exists()
        assert "test-mem" in path.read_text(encoding="utf-8")
        index = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "test-mem" in index

    def test_slug_sanitization(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add("My Fancy Skill!", "body", "user")
        assert "my_fancy_skill_" in path.name

    def test_frontmatter_structure(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add("meta-test", "body here", "feedback", description="one line")
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "name: meta-test" in text
        assert "type: feedback" in text
        assert "description: one line" in text
        assert "body here" in text

    def test_multiple_adds(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("mem-a", "aaa", "project")
        pm.add("mem-b", "bbb", "user")
        pm.add("mem-c", "ccc", "reference")
        md_files = list(tmp_path.glob("*.md"))
        # 3 entries + MEMORY.md = 4
        assert len(md_files) == 4

    def test_overwrite_same_name(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("overwrite", "v1", "project")
        pm.add("overwrite", "v2", "project")
        # Should overwrite the same file
        path = tmp_path / "project_overwrite.md"
        assert "v2" in path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("title", ["นโยบาย", "التداول", "מסחר", "торговля"])
    def test_slug_preserves_non_latin_chars(self, tmp_path: Path, title: str) -> None:
        # Regression: non-Latin chars used to collapse to "_" in slug,
        # causing two distinct titles of equal length to collide.
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add(title, "body", "user")
        assert title in path.name

    def test_slug_distinguishes_two_thai_titles(self, tmp_path: Path) -> None:
        # Two different Thai titles must produce different files. Without the
        # fix both would collapse to "user________.md".
        pm = PersistentMemory(memory_dir=tmp_path)
        a = pm.add("นโยบาย", "rule a", "user")
        b = pm.add("กลยุทธ์", "rule b", "user")
        assert a != b
        assert "rule a" in a.read_text(encoding="utf-8")
        assert "rule b" in b.read_text(encoding="utf-8")

    def test_index_update_not_duplicate(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("dup-check", "v1", "project")
        pm.add("dup-check", "v2", "project")
        index = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert index.count("[dup-check]") == 1

    def test_cjk_names_get_distinct_filenames(self, tmp_path: Path) -> None:
        # Regression: previously every non-ASCII char was replaced with `_`, so
        # any two CJK-only names of the same length collapsed to the same slug
        # (e.g. "上证指数" and "黄金价格" both → "____") and the second add
        # silently overwrote the first.
        pm = PersistentMemory(memory_dir=tmp_path)
        path1 = pm.add("上证指数", "A股大盘", "project", description="A股市场")
        path2 = pm.add("黄金价格", "黄金现货", "project", description="贵金属")
        assert path1 != path2
        assert path1.exists()
        assert path2.exists()
        # Both bodies preserved on disk.
        assert "A股大盘" in path1.read_text(encoding="utf-8")
        assert "黄金现货" in path2.read_text(encoding="utf-8")
        # Index lists both.
        index = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "上证指数" in index
        assert "黄金价格" in index

    def test_cjk_name_is_findable_after_add(self, tmp_path: Path) -> None:
        # The frontmatter name still carries the original CJK title, so search
        # by CJK token still hits even though the filename slug is mangled.
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("人民币汇率", "USD/CNY 中间价", "project", description="汇率播报")
        results = pm.find_relevant("人民币")
        assert len(results) == 1
        assert results[0].title == "人民币汇率"


# ---------------------------------------------------------------------------
# PersistentMemory.find_relevant
# ---------------------------------------------------------------------------


class TestFindRelevant:
    def test_basic_search(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("btc-strategy", "Bitcoin mean reversion", "project", description="BTC trading strategy")
        pm.add("aapl-analysis", "Apple earnings report", "project", description="AAPL fundamental analysis")
        results = pm.find_relevant("Bitcoin trading")
        assert len(results) >= 1
        assert results[0].title == "btc-strategy"

    def test_cjk_search(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("a-share", "上证指数分析报告", "project", description="A股市场分析")
        results = pm.find_relevant("上证指数")
        assert len(results) >= 1

    def test_no_match(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("something", "unrelated content", "project")
        results = pm.find_relevant("xyznonexistent999")
        assert len(results) == 0

    def test_max_results(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        for i in range(10):
            pm.add(f"stock-{i}", f"stock analysis number {i}", "project", description=f"stock {i}")
        results = pm.find_relevant("stock analysis", max_results=3)
        assert len(results) == 3

    def test_metadata_weighted_higher(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        # "bitcoin" in description (metadata) → weighted 2x
        pm.add("meta-match", "unrelated body text", "project", description="bitcoin trading strategy")
        # "bitcoin" only in body → weighted 1x
        pm.add("body-match", "bitcoin analysis deep dive", "project", description="some other topic")
        results = pm.find_relevant("bitcoin")
        assert len(results) == 2
        assert results[0].title == "meta-match"

    def test_empty_query(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("anything", "content", "project")
        results = pm.find_relevant("")
        assert results == []


# ---------------------------------------------------------------------------
# PersistentMemory.remove
# ---------------------------------------------------------------------------


class TestRemove:
    def test_remove_existing(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("to-remove", "gone soon", "project")
        assert pm.remove("to-remove") is True
        # File gone
        assert not list(tmp_path.glob("*to_remove*"))
        # Index rebuilt without it
        index = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "to-remove" not in index

    def test_remove_nonexistent(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        assert pm.remove("ghost") is False

    def test_remove_then_find(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("ephemeral", "temporary data", "project", description="temp")
        pm.remove("ephemeral")
        results = pm.find_relevant("temporary")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# PersistentMemory.snapshot
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_snapshot_loaded_at_init(self, tmp_path: Path) -> None:
        pm1 = PersistentMemory(memory_dir=tmp_path)
        pm1.add("snap-test", "content", "project", description="snapshot check")
        # New instance should load snapshot from MEMORY.md
        pm2 = PersistentMemory(memory_dir=tmp_path)
        assert "snap-test" in pm2.snapshot

    def test_snapshot_frozen(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        pm.add("after-init", "new content", "project")
        # Snapshot was frozen at init time (before add), so it should NOT contain "after-init"
        # unless the dir was empty at init (then snapshot is empty string)
        # In either case, snapshot should not update after add
        snap_before_check = pm.snapshot
        pm.add("another", "more content", "project")
        assert pm.snapshot == snap_before_check

    def test_empty_dir_snapshot(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        assert pm.snapshot == ""


class TestSanitizeBody:
    """Regression for #108 — strip C0/C1 control bytes from agent-supplied content."""

    def test_strips_ansi_escape(self) -> None:
        assert _sanitize_body("hello\x1b[31mred\x1b[0m world") == "hello[31mred[0m world"

    def test_strips_null_and_bell(self) -> None:
        assert _sanitize_body("a\x00b\x07c") == "abc"

    def test_preserves_tab_and_newline(self) -> None:
        assert _sanitize_body("line1\nline2\tindented") == "line1\nline2\tindented"

    def test_strips_c1_range(self) -> None:
        # U+0080 to U+009F are C1 controls (PAD, NEL, etc.)
        assert _sanitize_body("a\x80b\x9fc") == "abc"

    def test_empty_passthrough(self) -> None:
        assert _sanitize_body("") == ""


class TestTruncateBody:
    """Regression for #109 — enforce MAX_ENTRY_CHARS at write with visible marker."""

    def test_short_passthrough(self) -> None:
        assert _truncate_body("short") == "short"

    def test_at_limit_passthrough(self) -> None:
        text = "x" * MAX_ENTRY_CHARS
        assert _truncate_body(text) == text

    def test_over_limit_truncated_with_marker(self) -> None:
        text = "x" * (MAX_ENTRY_CHARS + 100)
        out = _truncate_body(text)
        # Total body length stays within MAX_ENTRY_CHARS so the marker survives
        # the read-side clip in _scan_entries.
        assert len(out) <= MAX_ENTRY_CHARS
        # Marker is at the tail; head still starts with content.
        assert out.startswith("x")
        assert out.endswith("chars]\n")
        assert "[truncated at" in out
        assert str(MAX_ENTRY_CHARS) in out

    def test_custom_limit(self) -> None:
        # Custom limit must be large enough to fit the marker plus some head.
        text = "abcdef" * 100  # 600 chars
        out = _truncate_body(text, limit=100)
        assert len(out) <= 100
        assert out.startswith("abc")
        assert "[truncated at 100 chars]" in out


class TestAddRejectsEmptyName:
    """Regression for #110 — reject empty / whitespace-only names."""

    def test_empty_raises(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        with pytest.raises(ValueError, match="empty or whitespace"):
            pm.add("", "body", "user")

    def test_whitespace_only_raises(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        with pytest.raises(ValueError, match="empty or whitespace"):
            pm.add("   ", "body", "user")

    def test_tab_only_raises(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        with pytest.raises(ValueError):
            pm.add("\t\n  ", "body", "user")


class TestAddHashSuffixForCollapsedSlug:
    """Regression for #110 — distinct emoji-only / punctuation-only names must
    produce distinct files via deterministic hash suffix."""

    def test_two_distinct_emoji_names_no_collision(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        p1 = pm.add("🚀", "rocket body", "reference")  # 🚀
        p2 = pm.add("🎯", "target body", "reference")  # 🎯
        assert p1 != p2
        assert "rocket body" in p1.read_text(encoding="utf-8")
        assert "target body" in p2.read_text(encoding="utf-8")

    def test_hash_is_deterministic(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        p1 = pm.add("🚀", "v1", "reference")
        p2 = pm.add("🚀", "v2", "reference")
        # Same name → same slug → overwrite (this is expected and desired
        # for the "edit memory" workflow).
        assert p1 == p2
        assert "v2" in p1.read_text(encoding="utf-8")

    def test_punctuation_only_name_gets_hash(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add("???", "body", "user")
        # Slug ??? -> _ after sanitization; hash appended.
        # File name must not be just "user_.md".
        assert path.name != "user_.md"
        assert path.exists()


class TestAddSanitizesAndTruncates:
    """Regression for #108 + #109 wired into `PersistentMemory.add()`."""

    def test_add_strips_control_bytes_in_body(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add("ctrl-test", "before\x1b[31mred\x1b[0mafter", "user")
        body_on_disk = path.read_text(encoding="utf-8")
        # ESC byte must be gone; surrounding text preserved.
        assert "\x1b" not in body_on_disk
        assert "before" in body_on_disk and "after" in body_on_disk
        assert "[31m" in body_on_disk  # the textual remainder is fine

    def test_add_truncates_long_body_with_marker(self, tmp_path: Path) -> None:
        pm = PersistentMemory(memory_dir=tmp_path)
        path = pm.add("long-content", "x" * (MAX_ENTRY_CHARS + 500), "reference")
        body_on_disk = path.read_text(encoding="utf-8").split("---\n\n", 1)[1]
        assert len(body_on_disk) <= MAX_ENTRY_CHARS + len("\n\n[truncated at  chars]\n") + 20
        assert "[truncated at" in body_on_disk
