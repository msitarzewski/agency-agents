
# ============================================================
# 中文名称: GTJA Alpha #148
# 简要说明: 国泰君安191短周期交易型alpha因子第148号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 148 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((RANK(CORR((OPEN), SUM(MEAN(VOLUME,60), 9), 6)) < RANK((OPEN - MIN(OPEN, 14)))) * -1)

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

ALPHA_ID = "gtja191_148"

__alpha_meta__ = {
    'id': 'gtja191_148',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 75,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_148.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    o = panel["open"]
    v = panel["volume"]
    left = rank(ts_corr(o, ts_mean(v, 60).rolling(9).sum(), 6))
    right = rank(o - ts_min(o, 14))
    out = (left < right).astype("float64") * -1.0
    return out
