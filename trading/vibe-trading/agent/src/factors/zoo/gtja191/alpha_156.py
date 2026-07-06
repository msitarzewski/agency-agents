
# ============================================================
# 中文名称: GTJA Alpha #156
# 简要说明: 国泰君安191短周期交易型alpha因子第156号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 156 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MAX(RANK(DECAYLINEAR(DELTA(VWAP,5),3)), RANK(DECAYLINEAR((-1*((OPEN*0.15)+(LOW*0.85)) * DELTA(...,2)/((OPEN*0.15)+(LOW*0.85))),3)))*-1

Notes: MAX elementwise -> np.maximum.
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

ALPHA_ID = "gtja191_156"

__alpha_meta__ = {
    'id': 'gtja191_156',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 10,
    'notes': 'MAX elementwise -> np.maximum.',
}


def compute(panel):
    """Compute gtja191_156.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    o = panel["open"]
    l = panel["low"]
    vw = vwap(panel, "equity_cn")

    a = rank(decay_linear(delta(vw, 5), 3))
    mix = o * 0.15 + l * 0.85
    b_inner = -1.0 * safe_div(delta(mix, 2), mix)
    b = rank(decay_linear(b_inner, 3))
    arr = np.maximum(a.to_numpy(dtype=np.float64, na_value=np.nan),
                     b.to_numpy(dtype=np.float64, na_value=np.nan))
    out = pd.DataFrame(arr, index=a.index, columns=a.columns) * -1.0
    return out
