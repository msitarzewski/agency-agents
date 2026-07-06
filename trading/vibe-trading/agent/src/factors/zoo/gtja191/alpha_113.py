
# ============================================================
# 中文名称: GTJA Alpha #113
# 简要说明: 国泰君安191短周期交易型alpha因子第113号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 113 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (-1 * ((RANK((SUM(DELAY(CLOSE, 5), 20) / 20)) * CORR(CLOSE, VOLUME, 2)) * RANK(CORR(SUM(CLOSE, 5), SUM(CLOSE, 20), 2))))

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

ALPHA_ID = "gtja191_113"

__alpha_meta__ = {
    'id': 'gtja191_113',
    'theme': ['volume'],
    'formula_latex': '-1*(rank(mean(delay(c,5),20))*corr(c,v,2))*rank(corr(sum(c,5),sum(c,20),2))',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 27,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_113.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    v = panel["volume"]
    m1 = rank(c.shift(5).rolling(20).sum() / 20.0)
    m2 = ts_corr(c, v, 2)
    m3 = rank(ts_corr(c.rolling(5).sum(), c.rolling(20).sum(), 2))
    out = -1.0 * (m1 * m2) * m3
    return out
