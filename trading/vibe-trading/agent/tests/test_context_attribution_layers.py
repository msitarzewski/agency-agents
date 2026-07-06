"""Tests for the post-backtest attribution layers in system prompt."""

from __future__ import annotations

import builtins

import pytest

from backtest.loaders.registry import VALID_SOURCES
from src.agent.context import ContextBuilder


@pytest.mark.unit
class TestAttributionLayersPresence:
    """Verify all 4 attribution layers exist in system prompt."""

    def test_system_prompt_contains_layer1_trade_attribution(self):
        from src.agent.context import _SYSTEM_PROMPT

        assert "Layer 1" in _SYSTEM_PROMPT
        assert "Trade Attribution" in _SYSTEM_PROMPT

    def test_system_prompt_contains_layer2_beta_regression(self):
        from src.agent.context import _SYSTEM_PROMPT

        assert "Layer 2" in _SYSTEM_PROMPT
        assert "Beta Regression" in _SYSTEM_PROMPT

    def test_system_prompt_contains_layer3_regime_analysis(self):
        from src.agent.context import _SYSTEM_PROMPT

        assert "Layer 3" in _SYSTEM_PROMPT
        assert "Regime Analysis" in _SYSTEM_PROMPT

    def test_system_prompt_contains_layer4_monte_carlo(self):
        from src.agent.context import _SYSTEM_PROMPT

        assert "Layer 4" in _SYSTEM_PROMPT
        assert "Monte Carlo" in _SYSTEM_PROMPT


@pytest.mark.unit
class TestAttributionSkillReferences:
    """Verify skill routing references in attribution layers."""

    def test_layer3_references_correlation_analysis_skill(self):
        """Layer 3 should delegate regime classification to correlation-analysis skill."""
        from src.agent.context import _SYSTEM_PROMPT

        assert 'load_skill("correlation-analysis")' in _SYSTEM_PROMPT

    def test_layer2_references_performance_attribution_skill(self):
        """Layer 2 should reference performance-attribution for deep analysis."""
        from src.agent.context import _SYSTEM_PROMPT

        assert 'load_skill("performance-attribution")' in _SYSTEM_PROMPT

    def test_at_risk_references_backtest_diagnose_skill(self):
        """At-risk routing should reference backtest-diagnose for code-level diagnosis."""
        from src.agent.context import _SYSTEM_PROMPT

        assert 'load_skill("backtest-diagnose")' in _SYSTEM_PROMPT


@pytest.mark.unit
class TestAttributionPromptIntegrity:
    """Verify prompt formatting and structural integrity."""

    def test_system_prompt_format_succeeds(self):
        """Verify .format() with all required placeholders doesn't raise KeyError."""
        from src.agent.context import _SYSTEM_PROMPT

        result = _SYSTEM_PROMPT.format(
            tool_count=10,
            skill_count=5,
            data_source_count=18,
            tool_descriptions="[test tools]",
            skill_descriptions="[test skills]",
            memory_summary="[test memory]",
            memory_section="[test section]",
            current_datetime="2025-01-01 12:00:00",
        )
        assert len(result) > 1000
        # Ensure no unformatted placeholders remain
        # (JSON braces are OK, but single { } with names are not)
        assert "{tool_count}" not in result
        assert "{skill_count}" not in result
        assert "{data_source_count}" not in result

    def test_strategy_routing_thresholds_present(self):
        """Verify strategy routing classification is defined."""
        from src.agent.context import _SYSTEM_PROMPT

        assert "Sharpe" in _SYSTEM_PROMPT
        assert "MaxDD" in _SYSTEM_PROMPT

    def test_override_mechanism_present(self):
        """Verify user can override routing to run all layers."""
        from src.agent.context import _SYSTEM_PROMPT

        assert "Override" in _SYSTEM_PROMPT or "override" in _SYSTEM_PROMPT

    def test_threshold_rationale_self_contained(self):
        """Threshold rationale is documented inline, not via a gitignored docs/ path."""
        from pathlib import Path
        import src.agent.context as ctx_module

        source = Path(ctx_module.__file__).read_text(encoding="utf-8")
        # The rationale comment must be present and self-contained.
        assert "attribution thresholds" in source.lower()
        # The internal docs/ tree is gitignored and never published; the module
        # must not point at a file that won't exist in the distributed repo.
        assert "docs/" not in source


@pytest.mark.unit
class TestCountDataSources:
    """Regression tests for dynamic data-source count in the system prompt."""

    def test_count_data_sources_matches_registry(self) -> None:
        """Live count derives from VALID_SOURCES minus the auto selector."""
        assert ContextBuilder._count_data_sources() == len(VALID_SOURCES - {"auto"})

    def test_count_data_sources_import_failure_returns_18(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Import failures fall back to 18 without propagating."""
        real_import = builtins.__import__

        def failing_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001
            if name == "backtest.loaders.registry":
                raise ImportError("simulated registry import failure")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", failing_import)
        assert ContextBuilder._count_data_sources() == 18
