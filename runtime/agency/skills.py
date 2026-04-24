"""Discover and load persona files from the Agency repo as Skills."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

# Folders in the repo root that contain agent persona markdown files.
DEFAULT_CATEGORIES: tuple[str, ...] = (
    "academic",
    "design",
    "engineering",
    "finance",
    "game-development",
    "marketing",
    "paid-media",
    "product",
    "project-management",
    "sales",
    "spatial-computing",
    "specialized",
    "strategy",
    "support",
    "testing",
)

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)


@dataclass(frozen=True)
class Skill:
    """A persona file parsed into a runnable skill."""

    slug: str
    name: str
    description: str
    category: str
    color: str
    emoji: str
    vibe: str
    body: str
    path: Path
    extra: dict = field(default_factory=dict)

    @property
    def system_prompt(self) -> str:
        """The text we send to the LLM as the system prompt for this skill."""
        return self.body.strip()

    def summary(self) -> str:
        return f"{self.emoji} {self.name} ({self.category}) — {self.description}"


def _slugify(path: Path) -> str:
    return path.stem


def _parse_one(path: Path, category: str) -> Skill | None:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER.match(text)
    if not match:
        return None

    raw_meta, body = match.groups()
    try:
        meta = yaml.safe_load(raw_meta) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None

    name = str(meta.get("name") or path.stem.replace("-", " ").title()).strip()
    description = str(meta.get("description") or "").strip()
    color = str(meta.get("color") or "white").strip()
    emoji = str(meta.get("emoji") or "🤖").strip()
    vibe = str(meta.get("vibe") or "").strip()

    known = {"name", "description", "color", "emoji", "vibe"}
    extra = {k: v for k, v in meta.items() if k not in known}

    return Skill(
        slug=_slugify(path),
        name=name,
        description=description,
        category=category,
        color=color,
        emoji=emoji,
        vibe=vibe,
        body=body,
        path=path,
        extra=extra,
    )


def discover_repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` until we find a folder that looks like the Agency repo."""
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if candidate.is_dir() and (candidate / "engineering").is_dir() and (candidate / "README.md").is_file():
            return candidate
    raise FileNotFoundError("Could not locate Agency repo root (no engineering/ found above this file).")


def load_skills(
    repo_root: Path | None = None,
    categories: Iterable[str] | None = None,
) -> list[Skill]:
    """Load every persona markdown file under the configured category folders."""
    root = (repo_root or discover_repo_root()).resolve()
    cats = list(categories) if categories is not None else list(DEFAULT_CATEGORIES)

    skills: list[Skill] = []
    seen: set[str] = set()
    for category in cats:
        cat_dir = root / category
        if not cat_dir.is_dir():
            continue
        for md in sorted(cat_dir.rglob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            skill = _parse_one(md, category)
            if skill is None or skill.slug in seen:
                continue
            seen.add(skill.slug)
            skills.append(skill)
    return skills


class SkillRegistry:
    """In-memory index of loaded skills with simple lookup helpers."""

    def __init__(self, skills: list[Skill]):
        self._skills = list(skills)
        self._by_slug = {s.slug: s for s in self._skills}

    @classmethod
    def load(cls, repo_root: Path | None = None) -> "SkillRegistry":
        return cls(load_skills(repo_root))

    def __len__(self) -> int:
        return len(self._skills)

    def __iter__(self):
        return iter(self._skills)

    def all(self) -> list[Skill]:
        return list(self._skills)

    def by_slug(self, slug: str) -> Skill | None:
        return self._by_slug.get(slug)

    def by_category(self, category: str) -> list[Skill]:
        return [s for s in self._skills if s.category == category]

    def categories(self) -> list[str]:
        return sorted({s.category for s in self._skills})

    def search(self, query: str, limit: int = 10) -> list[Skill]:
        """Naive keyword scoring over name + description + vibe."""
        q = query.lower().strip()
        if not q:
            return []
        terms = [t for t in re.split(r"\s+", q) if t]
        scored: list[tuple[int, Skill]] = []
        for s in self._skills:
            hay = f"{s.name}\n{s.description}\n{s.vibe}\n{s.slug}".lower()
            score = sum(hay.count(t) for t in terms)
            if score > 0:
                scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]
