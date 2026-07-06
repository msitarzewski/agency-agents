
# ============================================================
# 中文名称: GTJA Alpha #108
# 简要说明: 国泰君安191短周期交易型alpha因子第108号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 108 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((RANK((HIGH - MIN(HIGH,2)))^RANK(CORR((VWAP), (MEAN(VOLUME,120)), 6))) * -1)

Notes: x^y interpreted as x ** y after rank; both terms in (0,1].
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
    vwap,
)

ALPHA_ID = "gtja191_108"

__alpha_meta__ = {
    'id': 'gtja191_108',
    'theme': ['reversal', 'volume'],
    'formula_latex': '(rank(high-min(high,2))^rank(corr(vwap,mean(volume,120),6)))*-1',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 6,
    'min_warmup_bars': 125,
    'notes': 'x^y interpreted as x ** y after rank; both terms in (0,1].',
}


def compute(panel):
    """Compute gtja191_108.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    h = panel["high"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    left = rank(h - ts_min(h, 2))
    right = rank(ts_corr(vw, ts_mean(v, 120), 6))
    out = signed_power(left, 1.0) * 0  # placeholder to load library
    # We compute left ** right with NaN safety.
    arr_l = left.to_numpy(dtype=np.float64, na_value=np.nan)
    arr_r = right.to_numpy(dtype=np.float64, na_value=np.nan)
    arr = np.power(arr_l, arr_r)
    out = pd.DataFrame(arr, index=left.index, columns=left.columns) * -1.0
    return out
