"""Tests for risk parity optimizer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtest.optimizers.risk_parity import RiskParityOptimizer


class TestRiskParityCalcWeights:
    """Unit tests for the core weight calculation."""

    def test_equal_vol_gives_equal_weight(self) -> None:
        """Assets with identical volatility → equal weights."""
        n = 3
        vol = 0.02
        cov = np.eye(n) * vol**2
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        np.testing.assert_allclose(w, np.ones(n) / n, atol=1e-6)

    def test_weights_sum_to_one(self) -> None:
        rng = np.random.default_rng(42)
        n = 5
        A = rng.standard_normal((100, n))
        cov = np.cov(A.T)
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        assert abs(w.sum() - 1.0) < 1e-10

    def test_weights_nonnegative(self) -> None:
        rng = np.random.default_rng(7)
        n = 4
        A = rng.standard_normal((100, n))
        cov = np.cov(A.T)
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        assert np.all(w >= -1e-12)

    def test_higher_vol_gets_lower_weight(self) -> None:
        """Asset with higher volatility should get lower weight."""
        cov = np.diag([0.01, 0.04])  # vol = 0.1 vs 0.2
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        assert w[0] > w[1], "Lower-vol asset should have higher weight"

    def test_zero_vol_fallback(self) -> None:
        """Zero volatility → equal weight fallback."""
        cov = np.zeros((3, 3))
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        np.testing.assert_allclose(w, np.ones(3) / 3, atol=1e-10)

    def test_single_asset(self) -> None:
        cov = np.array([[0.04]])
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        np.testing.assert_allclose(w, [1.0], atol=1e-10)

    def test_empty_portfolio(self) -> None:
        cov = np.empty((0, 0))
        opt = RiskParityOptimizer()
        w = opt._calc_weights({"cov": cov})
        assert len(w) == 0


class TestRiskParityOptimize:
    """Integration test for the module-level optimize function."""

    def test_optimize_preserves_sign(self) -> None:
        """Optimizer should preserve signal direction (long/short)."""
        dates = pd.bdate_range("2025-01-01", periods=100)
        codes = ["A", "B"]
        rng = np.random.default_rng(42)
        ret = pd.DataFrame(rng.normal(0, 0.02, (100, 2)), index=dates, columns=codes)
        pos = pd.DataFrame(0.0, index=dates, columns=codes)
        # A is long, B is short after lookback period
        pos.iloc[60:, 0] = 1.0
        pos.iloc[60:, 1] = -1.0

        opt = RiskParityOptimizer(lookback=60)
        result = opt.optimize(ret, pos, dates)

        # After lookback, signs should be preserved
        assert (result.iloc[61:, 0] >= 0).all(), "A should remain long"
        assert (result.iloc[61:, 1] <= 0).all(), "B should remain short"

    def test_single_asset_unchanged(self) -> None:
        """Optimizer with 1 asset returns input unchanged."""
        dates = pd.bdate_range("2025-01-01", periods=100)
        ret = pd.DataFrame(np.random.default_rng(1).normal(0, 0.02, (100, 1)), index=dates, columns=["A"])
        pos = pd.DataFrame(1.0, index=dates, columns=["A"])

        opt = RiskParityOptimizer(lookback=60)
        result = opt.optimize(ret, pos, dates)
        pd.testing.assert_frame_equal(result, pos)
