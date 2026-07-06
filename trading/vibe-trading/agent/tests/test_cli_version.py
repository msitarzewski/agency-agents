"""Regression tests for issue #156 — CLI version must track pyproject.toml.

The shipped 0.1.8 wheel reported ``0.1.7`` because a hardcoded constant was
not bumped on release. ``cli/_version.py`` now derives the version from package
metadata, falling back to reading ``pyproject.toml`` directly, so there is no
constant left to drift. These tests pin both invariants.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from cli import _version

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _declared_version() -> str:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def test_pyproject_fallback_matches_declared_version() -> None:
    # The fallback is the single source of truth for an un-installed checkout;
    # it must reproduce pyproject.toml exactly (never a stale hardcoded value).
    assert _version._version_from_pyproject() == _declared_version()


def test_exposed_version_is_resolved_not_unknown() -> None:
    assert _version.__version__
    assert _version.__version__ != "unknown"


def test_no_hardcoded_version_constant_in_source() -> None:
    # Guards against reintroducing a literal version string that can drift
    # (the root cause of #156). The only version literal allowed is the
    # "unknown" sentinel for a moved/un-installed tree.
    import re

    source = Path(_version.__file__).read_text(encoding="utf-8")
    literals = re.findall(r"\"\d+\.\d+\.\d+\"", source)
    assert not literals, f"hardcoded version literal(s) found in _version.py: {literals}"
