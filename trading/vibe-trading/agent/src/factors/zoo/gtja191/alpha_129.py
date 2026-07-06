
# ============================================================
# 中文名称: GTJA Alpha #129
# 简要说明: 国泰君安191短周期交易型alpha因子第129号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 129 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SUM((CLOSE-DELAY(CLOSE,1)<0?ABS(CLOSE-DELAY(CLOSE,1)):0),12)

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

ALPHA_ID = "gtja191_129"

__alpha_meta__ = {
    'id': 'gtja191_129',
    'theme': ['momentum'],
    'formula_latex': 'sum(abs(c-delay(c,1)) if dc<0 else 0,12)',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 12,
    'min_warmup_bars': 13,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_129.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    dc = c - c.shift(1)
    out = (-dc).where(dc < 0, 0.0).rolling(12).sum()
    return out
