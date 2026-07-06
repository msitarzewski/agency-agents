
# ============================================================
# 中文名称: GTJA Alpha #107
# 简要说明: 国泰君安191短周期交易型alpha因子第107号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 107 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (((-1 * RANK((OPEN - DELAY(HIGH, 1)))) * RANK((OPEN - DELAY(CLOSE, 1)))) * RANK((OPEN - DELAY(LOW, 1))))

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

ALPHA_ID = "gtja191_107"

__alpha_meta__ = {
    'id': 'gtja191_107',
    'theme': ['reversal'],
    'formula_latex': '-1*rank(open-delay(high,1))*rank(open-delay(close,1))*rank(open-delay(low,1))',
    'columns_required': ['open', 'high', 'low', 'close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 2,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_107.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    out = (-1.0 * rank(o - h.shift(1))) * rank(o - c.shift(1)) * rank(o - l.shift(1))
    return out
