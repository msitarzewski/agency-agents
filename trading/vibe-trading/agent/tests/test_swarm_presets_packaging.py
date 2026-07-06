"""Regression tests for swarm preset discovery.

These guard against the v0.1.5 packaging bug (issue #55), where preset
YAMLs were declared via ``[tool.setuptools.data-files]`` and ended up at
``<venv>/config/swarm/`` while the loader looked under
``<site-packages>/config/swarm/``. Moving the YAMLs into the
``src.swarm.presets`` package keeps source-installs and built wheels in
sync; these tests fail fast if either side drifts again.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.swarm.presets import PRESETS_DIR, list_presets, load_preset


# Lock to the canonical roster shipped today. Bump intentionally if a preset
# is added or removed so a release that silently drops files is caught here.
EXPECTED_PRESET_COUNT = 29


def test_presets_dir_lives_inside_swarm_package() -> None:
    """PRESETS_DIR must be a sibling of presets.py so wheels can find it."""
    import src.swarm.presets as presets_module

    module_dir = Path(presets_module.__file__).resolve().parent
    assert PRESETS_DIR == module_dir / "presets"
    assert PRESETS_DIR.is_dir(), f"presets dir missing: {PRESETS_DIR}"


def test_list_presets_returns_full_roster() -> None:
    presets = list_presets()
    assert len(presets) == EXPECTED_PRESET_COUNT, (
        f"expected {EXPECTED_PRESET_COUNT} presets, got {len(presets)} — "
        "check pyproject package-data and that YAMLs were not dropped"
    )


def test_every_preset_yaml_is_loadable() -> None:
    """Every YAML in the bundle must parse and expose required keys."""
    for entry in list_presets():
        name = entry["name"]
        data = load_preset(name)
        assert isinstance(data, dict), f"preset {name} did not parse to dict"
        assert data.get("agents"), f"preset {name} has no agents"
        assert data.get("tasks"), f"preset {name} has no tasks"


@pytest.mark.parametrize(
    "preset_name",
    ["investment_committee", "quant_strategy_desk", "risk_committee"],
)
def test_known_presets_load(preset_name: str) -> None:
    """Spot-check a few headline presets advertised in docs/UI."""
    data = load_preset(preset_name)
    assert data["agents"], f"{preset_name} has no agents"
