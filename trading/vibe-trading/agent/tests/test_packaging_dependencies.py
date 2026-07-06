"""Packaging dependency regression tests."""

from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _normalized_requirement_name(requirement: str) -> str:
    name = requirement.split(";", 1)[0]
    for marker in ("[", "<", ">", "="):
        name = name.split(marker, 1)[0]
    return name.strip().lower()


def test_harmonic_backend_is_not_a_core_install_dependency() -> None:
    """Keep optional harmonic plotting deps from breaking baseline installs."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    core_dependencies = {
        _normalized_requirement_name(requirement)
        for requirement in pyproject["project"]["dependencies"]
    }
    requirements_txt = {
        _normalized_requirement_name(line)
        for line in (ROOT / "agent" / "requirements.txt").read_text().splitlines()
        if line and not line.startswith("#")
    }

    assert "pyharmonics" not in core_dependencies
    assert "pyharmonics" not in requirements_txt


def test_harmonic_backend_is_available_as_an_optional_extra() -> None:
    """Users who need harmonic pattern detection can still opt in explicitly."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    harmonic_extra = {
        _normalized_requirement_name(requirement)
        for requirement in pyproject["project"]["optional-dependencies"]["harmonic"]
    }

    assert "pyharmonics" in harmonic_extra
