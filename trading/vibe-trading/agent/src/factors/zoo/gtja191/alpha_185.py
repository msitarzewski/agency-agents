
# ============================================================
# 中文名称: GTJA Alpha #185
# 简要说明: 国泰君安191短周期交易型alpha因子第185号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 185 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    RANK((-1*((1-(OPEN/CLOSE))^2)))

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

ALPHA_ID = "gtja191_185"

__alpha_meta__ = {
    'id': 'gtja191_185',
    'theme': ['reversal'],
    'formula_latex': 'rank(-1*(1-open/close)^2)',
    'columns_required': ['open', 'close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 1,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_185.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    o = panel["open"]
    out = rank(-1.0 * (1.0 - safe_div(o, c)) ** 2)
    return out
