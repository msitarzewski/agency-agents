
# ============================================================
# 中文名称: GTJA Alpha #182
# 简要说明: 国泰君安191短周期交易型alpha因子第182号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 182 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    COUNT((CLOSE>OPEN & BENCH>DELAY(BENCH,1)) | (CLOSE<OPEN & BENCH<DELAY(BENCH,1)), 20) / 20

Notes: Benchmark falls back to cross-sectional mean of close.
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

ALPHA_ID = "gtja191_182"

__alpha_meta__ = {
    'id': 'gtja191_182',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 21,
    'notes': 'Benchmark falls back to cross-sectional mean of close.',
}


def compute(panel):
    """Compute gtja191_182.

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
    o = panel["open"]
    bench = _bench_close()
    up = ((c > o) & (bench > bench.shift(1)))
    dn = ((c < o) & (bench < bench.shift(1)))
    cond = (up | dn).astype("float64")
    out = cond.rolling(20).sum() / 20.0
    return out
