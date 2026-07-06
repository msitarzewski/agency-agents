
# ============================================================
# 中文名称: GTJA Alpha #159
# 简要说明: 国泰君安191短周期交易型alpha因子第159号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 159 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),6))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),6))*12*24 + similar over 12 and 24 windows /(6*12+6*24+12*24)*100

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

ALPHA_ID = "gtja191_159"

__alpha_meta__ = {
    'id': 'gtja191_159',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 24,
    'min_warmup_bars': 25,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_159.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    prev = c.shift(1)
    lo = pd.DataFrame(
        np.minimum(l.to_numpy(dtype=np.float64, na_value=np.nan),
                   prev.to_numpy(dtype=np.float64, na_value=np.nan)),
        index=c.index, columns=c.columns,
    )
    hi = pd.DataFrame(
        np.maximum(h.to_numpy(dtype=np.float64, na_value=np.nan),
                   prev.to_numpy(dtype=np.float64, na_value=np.nan)),
        index=c.index, columns=c.columns,
    )
    def _term(n):
        return safe_div((c - lo.rolling(n).sum()), (hi - lo).rolling(n).sum())
    out = ((_term(6) * 12.0 * 24.0) + (_term(12) * 6.0 * 24.0) + (_term(24) * 6.0 * 12.0)) / (6.0 * 12.0 + 6.0 * 24.0 + 12.0 * 24.0) * 100.0
    return out
