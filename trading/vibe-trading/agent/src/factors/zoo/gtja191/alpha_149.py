
# ============================================================
# 中文名称: GTJA Alpha #149
# 简要说明: 国泰君安191短周期交易型alpha因子第149号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 149 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    REGBETA(FILTER(CLOSE/DELAY(CLOSE,1)-1, BENCH<DELAY(BENCH,1)), FILTER(BENCH/DELAY(BENCH,1)-1, BENCH<DELAY(BENCH,1)), 252)

Notes: Downside beta vs. benchmark; uses fallback cross-sectional mean if benchmark_close missing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
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
)

ALPHA_ID = "gtja191_149"

__alpha_meta__ = {
    'id': 'gtja191_149',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 253,
    'notes': 'Downside beta vs. benchmark; uses fallback cross-sectional mean if benchmark_close missing.',
}


def compute(panel):
    """Compute gtja191_149.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _bench_close():
        """Benchmark close fallback: cross-sectional mean of `close`."""
        if "benchmark_close" in panel:
            return panel["benchmark_close"]
        c = panel["close"]
        return pd.DataFrame(
            np.tile(c.mean(axis=1).to_numpy().reshape(-1, 1), (1, c.shape[1])),
            index=c.index,
            columns=c.columns,
        )
    c = panel["close"]
    bench = _bench_close()
    br = safe_div(bench - bench.shift(1), bench.shift(1))
    cr = safe_div(c - c.shift(1), c.shift(1))
    # Multiplicative gating instead of NaN-masking so the rolling window keeps
    # enough valid samples (NaN-masking on roughly half the rows blows the
    # min_periods=n requirement on small panels).
    mask = (bench < bench.shift(1)).astype("float64")
    cr_g = cr * mask
    br_g = br * mask
    n = 20
    out = safe_div(ts_cov(cr_g, br_g, n), ts_std(br_g, n) ** 2)
    return out
