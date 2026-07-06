
# ============================================================
# 中文名称: GTJA Alpha #140
# 简要说明: 国泰君安191短周期交易型alpha因子第140号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 140 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MIN(RANK(DECAYLINEAR(((RANK(OPEN)+RANK(LOW))-(RANK(HIGH)+RANK(CLOSE))),8)),TSRANK(DECAYLINEAR(CORR(TSRANK(CLOSE,8),TSRANK(MEAN(VOLUME,60),20),8),7),3))

Notes: MIN(a,b) elementwise -> np.minimum.
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

ALPHA_ID = "gtja191_140"

__alpha_meta__ = {
    'id': 'gtja191_140',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 100,
    'notes': 'MIN(a,b) elementwise -> np.minimum.',
}


def compute(panel):
    """Compute gtja191_140.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    left = rank(decay_linear((rank(o) + rank(l)) - (rank(h) + rank(c)), 8))
    inner = ts_corr(ts_rank(c, 8), ts_rank(ts_mean(v, 60), 20), 8)
    right = ts_rank(decay_linear(ts_rank(inner, 7), 7), 3)
    arr = np.minimum(left.to_numpy(dtype=np.float64, na_value=np.nan),
                     right.to_numpy(dtype=np.float64, na_value=np.nan))
    out = pd.DataFrame(arr, index=left.index, columns=left.columns)
    return out
