"""Guard the AI contributor guide against silent path rot.

``AGENT_CONTRIBUTOR_GUIDE.md`` names specific test files, entry points, and
directories so agent-assisted contributors run the right targeted checks. Those
references rot silently when files are renamed or moved, leaving the guide
quietly wrong. This test parses the guide for in-repo paths and asserts each one
still exists, turning a stale reference into a red CI run.

Two kinds of referenced path are excluded because a clean checkout omits them by
design:

* ``pytest --ignore=`` targets — the heavy e2e suites are gitignored and absent
  in CI, and pytest tolerates their absence, so the guide may name them safely.
* ``.env`` files — gitignored secret files the guide cites as do-not-write
  targets.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPO_ROOT / "AGENT_CONTRIBUTOR_GUIDE.md"

# Tokens that look like in-repo paths rooted at a real top-level directory.
_PATH_RE = re.compile(r"(?:agent|frontend|wiki)/[\w./-]+")
# Paths handed to ``pytest --ignore=`` are tolerated-absent by design.
_IGNORED_RE = re.compile(r"--ignore=((?:agent|frontend|wiki)/[\w./-]+)")


def _is_intentionally_absent(path: str) -> bool:
    """Return True for gitignored secret files the guide cites as do-not-write targets."""
    return Path(path).name.startswith(".env")


def test_guide_referenced_paths_exist() -> None:
    """Every required in-repo path referenced by the contributor guide must exist."""
    text = GUIDE.read_text(encoding="utf-8")
    ignored = set(_IGNORED_RE.findall(text))
    referenced = set(_PATH_RE.findall(text)) - ignored
    assert referenced, "no repo paths parsed from AGENT_CONTRIBUTOR_GUIDE.md — regex broke?"

    missing = [
        path
        for path in sorted(referenced)
        if not _is_intentionally_absent(path) and not (REPO_ROOT / path).exists()
    ]
    assert not missing, (
        "AGENT_CONTRIBUTOR_GUIDE.md references repo paths that no longer exist: "
        f"{missing}. Update the guide or restore the paths."
    )
