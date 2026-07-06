"""Alpha Zoo: 4 zoos (alpha101 / gtja191 / qlib158 / academic) × ~450 alphas.

See `docs/alpha-zoo/spec.md` for the panel format contract and operator semantics.
"""

from src.factors.base import (
    Alpha,
    AlphaCompute,
    Market,
    decay_linear,
    delta,
    rank,
    safe_div,
    scale,
    signed_power,
    ts_argmax,
    ts_argmin,
    ts_corr,
    ts_cov,
    ts_max,
    ts_mean,
    ts_min,
    ts_rank,
    ts_std,
    vwap,
)

__all__ = [
    "Alpha",
    "AlphaCompute",
    "Market",
    "decay_linear",
    "delta",
    "rank",
    "safe_div",
    "scale",
    "signed_power",
    "ts_argmax",
    "ts_argmin",
    "ts_corr",
    "ts_cov",
    "ts_max",
    "ts_mean",
    "ts_min",
    "ts_rank",
    "ts_std",
    "vwap",
]
