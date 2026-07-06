
# ============================================================
# 中文名称: GTJA Alpha #167
# 简要说明: 国泰君安191短周期交易型alpha因子第167号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 167 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SUM((CLOSE-DELAY(CLOSE,1)>0?CLOSE-DELAY(CLOSE,1):0),12)

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

ALPHA_ID = "gtja191_167"

__alpha_meta__ = {
    'id': 'gtja191_167',
    'theme': ['momentum'],
    'formula_latex': 'sum(max(0,c-delay(c,1)),12)',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 12,
    'min_warmup_bars': 13,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_167.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    out = (c - c.shift(1)).clip(lower=0.0).rolling(12).sum()
    return out
