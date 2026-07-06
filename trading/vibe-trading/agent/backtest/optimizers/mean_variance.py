"""Mean-variance (max Sharpe) optimizer: max (w'mu - r_f) / sqrt(w'Sigma w), w>=0, sum(w)=1."""

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backtest.optimizers.base import BaseOptimizer


class MeanVarianceOptimizer(BaseOptimizer):
    """Maximize Sharpe ratio subject to long-only simplex."""

    def __init__(self, lookback: int = 60, risk_free: float = 0.0, **kwargs: Any) -> None:
        super().__init__(lookback=lookback, **kwargs)
        self.risk_free = risk_free

    def _build_context(
        self, window: pd.DataFrame, active: List[str]
    ) -> "Dict[str, Any] | None":
        """Mean vector and covariance."""
        mu = window.mean().values
        cov = window.cov().values
        if np.isnan(cov).any() or np.isnan(mu).any():
            return None
        return {"cov": cov, "mu": mu}

    def _calc_weights(self, ctx: Dict[str, Any]) -> np.ndarray:
        """SLSQP max-Sharpe weights."""
        from scipy.optimize import minimize

        mu, cov = ctx["mu"], ctx["cov"]
        n = len(mu)
        if n == 0:
            return self._equal_weight(0)

        rf = self.risk_free

        def neg_sharpe(w: np.ndarray) -> float:
            port_vol = np.sqrt(w @ cov @ w)
            if port_vol < 1e-12:
                return 0.0
            return -(w @ mu - rf) / port_vol

        result = minimize(
            neg_sharpe,
            self._equal_weight(n),
            method="SLSQP",
            bounds=[(0.0, 1.0)] * n,
            constraints={"type": "eq", "fun": lambda w: w.sum() - 1.0},
            options={"maxiter": 200, "ftol": 1e-10},
        )

        if result.success:
            return self._normalize(result.x)
        return self._equal_weight(n)


def optimize(
    ret: pd.DataFrame,
    pos: pd.DataFrame,
    dates: pd.DatetimeIndex,
    lookback: int = 60,
    risk_free: float = 0.0,
) -> pd.DataFrame:
    """Module-level entry: max-Sharpe-adjusted positions."""
    return MeanVarianceOptimizer(
        lookback=lookback, risk_free=risk_free
    ).optimize(ret, pos, dates)
