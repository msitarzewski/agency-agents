"""PersistentMemory: file-based cross-session memory, zero external dependencies.

Storage layout:
    ~/.vibe-trading/memory/
    +-- MEMORY.md          # Index (< 200 lines)
    +-- user_prefs.md      # Individual memory entries with YAML frontmatter
    +-- project_btc.md
    +-- ...
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from src.agent.frontmatter import parse_frontmatter as _parse_frontmatter
from typing import List, Optional

logger = logging.getLogger(__name__)

MEMORY_BASE = Path.home() / ".vibe-trading" / "memory"
MAX_INDEX_LINES = 200
MAX_ENTRY_CHARS = 8000
MAX_RESULTS = 5
METADATA_WEIGHT = 2.0
MEMORY_TYPES = ("user", "feedback", "project", "reference")

# Script ranges tokenized and slugged at char level (no word-boundary
# whitespace). Arabic/Hebrew narrowed to letter blocks to exclude bidi
# controls and combining marks from on-disk slugs.
_NON_LATIN_SCRIPT_RANGES = (
    "一-鿿"   # CJK Unified Ideographs   (U+4E00-U+9FFF)
    "㐀-䶿"   # CJK Extension A          (U+3400-U+4DBF)
    "฀-๿"   # Thai                     (U+0E00-U+0E7F)
    "ؠ-ي"   # Arabic letters           (U+0620-U+064A)
    "א-ת"   # Hebrew letters           (U+05D0-U+05EA)
    "Ѐ-ӿ"   # Cyrillic                 (U+0400-U+04FF)
)

_TOKEN_RE = re.compile(rf"[a-zA-Z0-9]{{3,}}|[{_NON_LATIN_SCRIPT_RANGES}]")
_SLUG_DISALLOWED_RE = re.compile(rf"[^a-z0-9_\-{_NON_LATIN_SCRIPT_RANGES}]")


@dataclass(frozen=True)
class MemoryEntry:
    """A single memory entry on disk.

    Attributes:
        path: File path.
        title: Memory title.
        description: One-line description (used for retrieval scoring).
        memory_type: Category (user/feedback/project/reference).
        body: Body text content.
        modified_at: File modification timestamp.
    """

    path: Path
    title: str
    description: str
    memory_type: str
    body: str
    modified_at: float


def _tokenize(text: str) -> set[str]:
    """Split text into searchable tokens.

    ASCII words >= 3 chars + individual characters from non-Latin scripts
    listed in ``_NON_LATIN_SCRIPT_RANGES`` (CJK, Thai, Arabic, Hebrew,
    Cyrillic). Underscores are
    treated as word boundaries so snake_case titles (e.g. ``mcp_wiring_test``)
    match natural-language queries (``"mcp wiring"``) as well as verbatim
    lookups.

    Args:
        text: Input text.

    Returns:
        Set of tokens.
    """
    return set(_TOKEN_RE.findall(text.lower()))


# Strip C0 (U+0000-U+001F except \t \n) and C1 (U+0080-U+009F) bytes from
# user-supplied body content. These never carry useful payload from agent
# writes but can be replayed back through `memory show` to inject ANSI
# escape sequences into the user's terminal (see issue #108).
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Truncation marker appended when content exceeds MAX_ENTRY_CHARS. Read
# semantics are unchanged (clipped at MAX_ENTRY_CHARS), but the marker
# makes the silent clip surfaceable to anyone inspecting the file directly
# (see issue #109).
_TRUNCATION_MARKER = "\n\n[truncated at {limit} chars]\n"


def _sanitize_body(content: str) -> str:
    """Strip C0/C1 control bytes from `content` while keeping ``\n`` and ``\t``."""
    return _CONTROL_CHAR_RE.sub("", content)


def _truncate_body(content: str, limit: int = None) -> str:
    """Clip `content` to `limit` chars total, leaving room for the marker.

    The marker is reserved inside the limit (not appended on top) so the on-
    disk body length stays <= MAX_ENTRY_CHARS and the marker survives the
    matching read-side clip in `_scan_entries`. Callers that inspect
    `entry.body` see the marker; the original tail content past the head
    window is dropped.
    """
    if limit is None:
        limit = MAX_ENTRY_CHARS
    if len(content) <= limit:
        return content
    marker = _TRUNCATION_MARKER.format(limit=limit)
    head_len = max(0, limit - len(marker))
    return content[:head_len] + marker


def _coerce_str(value: object, default: str = "") -> str:
    """Coerce frontmatter values to a display string.

    ``parse_frontmatter`` returns lists for ``[a, b]`` syntax and bools for
    ``true``/``false``. ``MemoryEntry`` annotates these fields as ``str`` so
    callers (CLI rendering, recall scoring) can rely on string operations.
    """
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


class PersistentMemory:
    """File-based persistent memory that survives across sessions.

    Design:
        - Frozen snapshot injected into system prompt at session start (preserves prompt cache).
        - Disk writes via add()/remove() update files immediately but do NOT change the snapshot.
        - Next session picks up the updated state.

    Attributes:
        snapshot: Frozen memory index text for system prompt injection.
    """

    def __init__(self, memory_dir: Optional[Path] = None) -> None:
        """Initialize PersistentMemory.

        Args:
            memory_dir: Override memory directory (default: ~/.vibe-trading/memory/).
        """
        self._dir = memory_dir or MEMORY_BASE
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "MEMORY.md"
        self._snapshot: str = ""
        self._load_snapshot()

    def _load_snapshot(self) -> None:
        """Load index as frozen snapshot. Called once at init."""
        if self._index_path.exists():
            try:
                text = self._index_path.read_text(encoding="utf-8")
                lines = text.split("\n")[:MAX_INDEX_LINES]
                self._snapshot = "\n".join(lines)
            except OSError:
                self._snapshot = ""

    @property
    def snapshot(self) -> str:
        """Frozen memory index for system prompt injection."""
        return self._snapshot

    def _scan_entries(self) -> List[MemoryEntry]:
        """Scan all .md files (except MEMORY.md) and parse frontmatter.

        Returns:
            List of parsed memory entries.
        """
        entries: List[MemoryEntry] = []
        for path in sorted(self._dir.glob("*.md")):
            if path.name == "MEMORY.md":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            meta, body = _parse_frontmatter(text)
            entries.append(MemoryEntry(
                path=path,
                title=_coerce_str(meta.get("name"), default=path.stem),
                description=_coerce_str(meta.get("description")),
                memory_type=_coerce_str(meta.get("type"), default="project"),
                body=body[:MAX_ENTRY_CHARS],
                modified_at=path.stat().st_mtime,
            ))
        return entries

    def list_entries(self) -> List[MemoryEntry]:
        """Return all persisted memory entries, filename-sorted."""
        return self._scan_entries()

    def find(self, name: str) -> Optional[MemoryEntry]:
        """Resolve a memory by exact title, then by on-disk filename stem.

        Stem fallback accepts both the full ``{type}_{slug}`` form and the
        bare ``slug`` suffix so users can paste either form from the index.
        """
        needle = name.strip()
        if not needle:
            return None
        entries = self._scan_entries()
        for entry in entries:
            if entry.title == needle:
                return entry
        for entry in entries:
            stem = entry.path.stem
            if stem == needle or stem.endswith(f"_{needle}"):
                return entry
        return None

    def remove_entry(self, entry: MemoryEntry) -> bool:
        """Delete a resolved entry without re-scanning to find it again."""
        try:
            entry.path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Failed to remove memory entry %s: %s", entry.path, exc)
            return False
        self._rebuild_index()
        return True

    def find_relevant(self, query: str, max_results: int = MAX_RESULTS) -> List[MemoryEntry]:
        """Keyword search across all memory entries.

        Scoring: metadata_hits * 2.0 + body_hits * 1.0.

        Args:
            query: Search query.
            max_results: Maximum entries to return.

        Returns:
            Top-scoring memory entries.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, MemoryEntry]] = []
        for entry in self._scan_entries():
            meta_tokens = _tokenize(f"{entry.title} {entry.description}")
            body_tokens = _tokenize(entry.body)
            score = len(query_tokens & meta_tokens) * METADATA_WEIGHT + len(query_tokens & body_tokens)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: (-x[0], -x[1].modified_at))
        return [entry for _, entry in scored[:max_results]]

    def add(self, name: str, content: str, memory_type: str = "project",
            description: str = "") -> Path:
        """Save a new memory entry and update the index.

        Args:
            name: Memory name (used as filename slug). Empty or whitespace-
                only names are rejected.
            content: Memory body text. C0/C1 control bytes (other than
                ``\n`` and ``\t``) are stripped; the body is truncated to
                ``MAX_ENTRY_CHARS`` with a visible marker.
            memory_type: One of user/feedback/project/reference.
            description: One-line description for retrieval scoring.

        Returns:
            Path to the created memory file.

        Raises:
            ValueError: If `name` is empty or whitespace-only.
        """
        # Reject empty / whitespace-only names so they cannot all collapse
        # to the same `{type}_.md` filename and silently overwrite each
        # other (issue #110).
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("memory name must not be empty or whitespace-only")

        if memory_type not in MEMORY_TYPES:
            allowed = ", ".join(MEMORY_TYPES)
            raise ValueError(f"memory_type must be one of: {allowed}")

        # Preserve non-Latin script characters in the slug — collapsing
        # them all to ``_`` caused two same-length non-Latin names to share a
        # filename and silently overwrite each other (PR #95 + #104).
        slug = _SLUG_DISALLOWED_RE.sub("_", stripped_name.lower())[:60]

        # If the slug normalized to all underscores (emoji-only, punctuation-
        # only, etc.) the on-disk filename would still collide between any
        # two such names. Append a short deterministic hash so distinct
        # inputs produce distinct files (issue #110).
        if slug.strip("_") == "":
            digest = hashlib.sha256(stripped_name.encode("utf-8")).hexdigest()[:6]
            slug = f"{slug}_{digest}" if slug else digest

        filename = f"{memory_type}_{slug}.md"
        path = self._dir / filename

        safe_name = stripped_name.replace("\n", " ").replace("\r", " ")
        safe_desc = (description or stripped_name).replace("\n", " ").replace("\r", " ")

        # Strip control bytes (#108) before truncation (#109) so the marker
        # is computed against the user-visible content length.
        clean_content = _truncate_body(_sanitize_body(content))

        frontmatter = (
            f"---\nname: {safe_name}\n"
            f"description: {safe_desc}\n"
            f"type: {memory_type}\n---\n\n"
            f"{clean_content}"
        )
        path.write_text(frontmatter, encoding="utf-8")
        self._update_index(stripped_name, filename, description or stripped_name)
        return path

    def remove(self, name: str) -> bool:
        """Remove a memory entry by name.

        Args:
            name: Memory name to remove.

        Returns:
            True if found and removed.
        """
        for entry in self._scan_entries():
            if entry.title == name:
                entry.path.unlink(missing_ok=True)
                self._rebuild_index()
                return True
        return False

    def _update_index(self, title: str, filename: str, description: str) -> None:
        """Append or update an entry in MEMORY.md."""
        new_line = f"- [{title}]({filename}) — {description}"

        if self._index_path.exists():
            lines = self._index_path.read_text(encoding="utf-8").split("\n")
            updated = False
            for i, line in enumerate(lines):
                if f"[{title}]" in line:
                    lines[i] = new_line
                    updated = True
                    break
            if not updated:
                lines.append(new_line)
            text = "\n".join(lines[:MAX_INDEX_LINES])
        else:
            text = new_line

        self._index_path.write_text(text, encoding="utf-8")

    def _rebuild_index(self) -> None:
        """Rebuild MEMORY.md from all existing entry files."""
        entries = self._scan_entries()
        lines = [f"- [{e.title}]({e.path.name}) — {e.description}" for e in entries]
        self._index_path.write_text("\n".join(lines[:MAX_INDEX_LINES]), encoding="utf-8")
