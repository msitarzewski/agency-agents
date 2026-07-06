"""Security regression tests for default tool exposure."""

from __future__ import annotations

import pytest

from src.tools import build_registry


def test_shell_tools_absent_from_default_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", raising=False)

    registry = build_registry()

    assert "bash" not in registry.tool_names
    assert "background_run" not in registry.tool_names


def test_shell_tools_require_registry_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIBE_TRADING_ENABLE_SHELL_TOOLS", raising=False)

    registry = build_registry(include_shell_tools=True)

    assert "bash" in registry.tool_names
    assert "background_run" in registry.tool_names
