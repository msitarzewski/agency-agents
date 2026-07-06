
# ============================================================
# 中文名称: GTJA Alpha #145
# 简要说明: 国泰君安191短周期交易型alpha因子第145号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 145 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100

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

ALPHA_ID = "gtja191_145"

__alpha_meta__ = {
    'id': 'gtja191_145',
    'theme': ['volume'],
    'formula_latex': '(mean(v,9)-mean(v,26))/mean(v,12)*100',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 26,
    'min_warmup_bars': 26,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_145.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    v = panel["volume"]
    out = safe_div(ts_mean(v, 9) - ts_mean(v, 26), ts_mean(v, 12)) * 100.0
    return out
