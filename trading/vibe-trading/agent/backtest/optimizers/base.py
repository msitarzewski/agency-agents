"""Shared base class for portfolio optimizers.

Handles preprocessing, rolling covariance windows, and weight normalization;
subclasses implement ``_calc_weights``.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

import numpy as np
import pandas as pd


class BaseOptimizer(ABC):
    """Abstract portfolio optimizer.

    Subclasses implement ``_calc_weights``; the base handles:
    - active asset selection
    - rolling window slicing and sanity checks
    - covariance matrix + NaN checks
    - applying weights while preserving signal sign

    Attributes:
        lookback: Lookback days for covariance / mean.
        params: Extra keyword args for subclasses.
    """

    def __init__(self, lookback: int = 60, **kwargs: Any) -> None:
        self.lookback = lookback
        self.params = kwargs

    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------

    def optimize(
        self,
        ret: pd.DataFrame,
        pos: pd.DataFrame,
        dates: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        """Apply optimizer to position weights.

        Args:
            ret: Return matrix (dates x codes).
            pos: Raw signal positions.
            dates: Date index aligned with ``pos``.

        Returns:
            Adjusted position matrix (not dollar-normalized).
        """
        codes = pos.columns.tolist()
        if len(codes) <= 1:
            return pos

        result = pos.copy()
        for i, dt in enumerate(dates):
            active = [c for c in codes if abs(pos.at[dt, c]) > 1e-9]
            if not active or i < self.lookback:
                continue

            window = ret.loc[:dt, active].tail(self.lookback)
            if len(window) < max(self.lookback // 2, 5):
                continue

            ctx = self._build_context(window, active)
            if ctx is None:
                continue

            weights = self._calc_weights(ctx)
            if weights is None or len(weights) != len(active):
                continue

            for j, c in enumerate(active):
                sign = np.sign(pos.at[dt, c])
                result.at[dt, c] = sign * weights[j]

        return result

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def _build_context(
        self, window: pd.DataFrame, active: List[str]
    ) -> "Dict[str, Any] | None":
        """Build context dict for ``_calc_weights``.

        Default: covariance only. Override to add means, vols, etc.
        Return None to skip the date.

        Args:
            window: Return window for active assets.
            active: Active asset codes.

        Returns:
            Context dict with at least ``cov``, or None.
        """
        cov = window.cov().values
        if np.isnan(cov).any():
            return None
        return {"cov": cov}

    # ------------------------------------------------------------------
    # Subclass API
    # ------------------------------------------------------------------

    @abstractmethod
    def _calc_weights(self, ctx: Dict[str, Any]) -> np.ndarray:
        """Compute target weights from context.

        Args:
            ctx: Dict from ``_build_context``.

        Returns:
            Weight vector (n,) summing to 1.
        """

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(w: np.ndarray) -> np.ndarray:
        """Normalize nonnegative weights to sum 1."""
        w = np.maximum(w, 0.0)
        s = w.sum()
        if s > 1e-12:
            return w / s
        return np.ones(len(w)) / len(w)

    @staticmethod
    def _equal_weight(n: int) -> np.ndarray:
        """Equal weights for n assets."""
        if n == 0:
            return np.array([])
        return np.ones(n) / n
