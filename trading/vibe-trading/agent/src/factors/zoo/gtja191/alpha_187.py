
# ============================================================
# 中文名称: GTJA Alpha #187
# 简要说明: 国泰君安191短周期交易型alpha因子第187号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 187 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SUM((OPEN<=DELAY(OPEN,1) ? 0 : MAX(HIGH-OPEN, OPEN-DELAY(OPEN,1))), 20)

Notes: 
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

ALPHA_ID = "gtja191_187"

__alpha_meta__ = {
    'id': 'gtja191_187',
    'theme': ['reversal'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 21,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_187.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    o = panel["open"]
    h = panel["high"]
    prev = o.shift(1)
    cond = (o <= prev).astype("float64")
    arr_a = (h - o).to_numpy(dtype=np.float64, na_value=np.nan)
    arr_b = (o - prev).to_numpy(dtype=np.float64, na_value=np.nan)
    mx = pd.DataFrame(np.maximum(arr_a, arr_b), index=o.index, columns=o.columns)
    val = mx * (1.0 - cond)
    out = val.rolling(20).sum()
    return out
