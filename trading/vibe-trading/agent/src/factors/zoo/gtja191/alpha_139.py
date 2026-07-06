
# ============================================================
# 中文名称: GTJA Alpha #139
# 简要说明: 国泰君安191短周期交易型alpha因子第139号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 139 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (-1 * CORR(OPEN, VOLUME, 10))

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

ALPHA_ID = "gtja191_139"

__alpha_meta__ = {
    'id': 'gtja191_139',
    'theme': ['volume'],
    'formula_latex': '-1*corr(open,volume,10)',
    'columns_required': ['open', 'volume', 'close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 10,
    'min_warmup_bars': 10,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_139.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    o = panel["open"]
    v = panel["volume"]
    out = -1.0 * ts_corr(o, v, 10)
    return out
