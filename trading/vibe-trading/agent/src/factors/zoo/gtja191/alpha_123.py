
# ============================================================
# 中文名称: GTJA Alpha #123
# 简要说明: 国泰君安191短周期交易型alpha因子第123号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 123 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((RANK(CORR(SUM(((HIGH+LOW)/2),20),SUM(MEAN(VOLUME,60),20),9)) < RANK(CORR(LOW,VOLUME,6))) * -1)

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

ALPHA_ID = "gtja191_123"

__alpha_meta__ = {
    'id': 'gtja191_123',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 90,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_123.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    left = rank(ts_corr(((h + l) / 2.0).rolling(20).sum(), ts_mean(v, 60).rolling(20).sum(), 9))
    right = rank(ts_corr(l, v, 6))
    out = (left < right).astype("float64") * -1.0
    return out
