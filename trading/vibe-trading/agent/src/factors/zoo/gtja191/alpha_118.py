
# ============================================================
# 中文名称: GTJA Alpha #118
# 简要说明: 国泰君安191短周期交易型alpha因子第118号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 118 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100

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

ALPHA_ID = "gtja191_118"

__alpha_meta__ = {
    'id': 'gtja191_118',
    'theme': ['reversal'],
    'formula_latex': 'sum(h-o,20)/sum(o-l,20)*100',
    'columns_required': ['open', 'high', 'low', 'close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_118.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    out = safe_div((h - o).rolling(20).sum(), (o - l).rolling(20).sum()) * 100.0
    return out
