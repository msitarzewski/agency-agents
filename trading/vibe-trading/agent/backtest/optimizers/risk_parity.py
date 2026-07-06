"""Risk parity: equalize marginal risk contributions.

Iterative refinement so w_i * MRC_i is approximately equal across assets.
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

from backtest.optimizers.base import BaseOptimizer


class RiskParityOptimizer(BaseOptimizer):
    """Spinu (2013)-style inverse-vol seed + Newton-style refinement."""

    def _calc_weights(self, ctx: Dict[str, Any]) -> np.ndarray:
        """Equal risk contribution weights."""
        cov = ctx["cov"]
        n = cov.shape[0]
        if n == 0:
            return self._equal_weight(0)

        vols = np.sqrt(np.diag(cov))
        if np.any(vols < 1e-12):
            return self._equal_weight(n)

        inv_vol = 1.0 / vols
        w = inv_vol / inv_vol.sum()

        for _ in range(5):
            port_vol = np.sqrt(w @ cov @ w)
            if port_vol < 1e-12:
                break
            mrc = (cov @ w) / port_vol
            rc = w * mrc
            target = port_vol / n
            w = w * (target / (rc + 1e-12))
            w = w / w.sum()

        return w


def optimize(
    ret: pd.DataFrame,
    pos: pd.DataFrame,
    dates: pd.DatetimeIndex,
    lookback: int = 60,
) -> pd.DataFrame:
    """Module-level entry: risk-parity-adjusted positions."""
    return RiskParityOptimizer(lookback=lookback).optimize(ret, pos, dates)
