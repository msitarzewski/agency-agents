"""Skill loader tests against real persona files in this repo."""

from pathlib import Path

from agency.skills import SkillRegistry, discover_repo_root, load_skills

REPO = discover_repo_root()


def test_discover_repo_root_finds_engineering_dir():
    assert (REPO / "engineering").is_dir()


def test_load_skills_picks_up_at_least_one_per_category():
    skills = load_skills(REPO)
    cats_with_skills = {s.category for s in skills}
    # We expect at least these high-volume categories to be populated.
    for required in ("engineering", "design", "marketing", "product"):
        assert required in cats_with_skills, f"missing skills for {required}"


def test_registry_basic_operations():
    reg = SkillRegistry.load(REPO)
    assert len(reg) > 0
    # Slug uniqueness
    slugs = [s.slug for s in reg]
    assert len(slugs) == len(set(slugs))
    # Lookup
    first = reg.all()[0]
    assert reg.by_slug(first.slug) is first
    # Categories includes a known one
    assert "engineering" in reg.categories()


def test_search_returns_relevant_results():
    reg = SkillRegistry.load(REPO)
    results = reg.search("frontend")
    assert results, "expected at least one frontend-related skill"
    # The frontend developer should be in the top results
    assert any("frontend" in s.slug.lower() for s in results)


def test_system_prompt_is_non_empty():
    reg = SkillRegistry.load(REPO)
    for skill in reg.all()[:5]:
        assert skill.system_prompt.strip(), f"empty system prompt for {skill.slug}"


def test_default_categories_matches_repo_layout():
    """Every category folder on disk that contains *.md should be in DEFAULT_CATEGORIES,
    and every entry in DEFAULT_CATEGORIES should correspond to a real folder.

    Catches the case where someone adds a new top-level category dir and
    forgets to teach the loader about it (or vice versa)."""
    from agency.skills import DEFAULT_CATEGORIES

    # Top-level dirs that are NOT category folders and should never be scanned.
    SKIP_DIRS = {".git", ".github", "scripts", "integrations", "examples", "runtime"}

    # Every entry in DEFAULT_CATEGORIES exists as a real directory.
    for cat in DEFAULT_CATEGORIES:
        assert (REPO / cat).is_dir(), f"DEFAULT_CATEGORIES has '{cat}' but no dir"

    # Every top-level dir that contains .md persona files (with YAML frontmatter)
    # must be in DEFAULT_CATEGORIES.
    import re
    for entry in REPO.iterdir():
        if not entry.is_dir() or entry.name.startswith(".") or entry.name in SKIP_DIRS:
            continue
        # Does the folder contain persona-shaped .md files?
        has_persona = False
        for md in entry.rglob("*.md"):
            if md.name.lower() == "readme.md":
                continue
            text = md.read_text(encoding="utf-8", errors="ignore")[:200]
            if re.match(r"^---\r?\n", text):
                has_persona = True
                break
        if has_persona:
            assert entry.name in DEFAULT_CATEGORIES, (
                f"folder '{entry.name}' has persona files but isn't in "
                f"DEFAULT_CATEGORIES — add it to runtime/agency/skills.py"
            )
