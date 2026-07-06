
# ============================================================
# 中文名称: GTJA Alpha #103
# 简要说明: 国泰君安191短周期交易型alpha因子第103号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 103 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((20-LOWDAY(low,20))/20)*100

Notes: LOWDAY -> ts_argmin (0-based); (20 - argmin)/20 * 100.
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

ALPHA_ID = "gtja191_103"

__alpha_meta__ = {
    'id': 'gtja191_103',
    'theme': ['reversal'],
    'formula_latex': '((20-lowday(low,20))/20)*100',
    'columns_required': ['close', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
    'notes': 'LOWDAY -> ts_argmin (0-based); (20 - argmin)/20 * 100.',
}


def compute(panel):
    """Compute gtja191_103.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    l = panel["low"]
    am = ts_argmin(l, 20)
    out = (20.0 - am) / 20.0 * 100.0
    return out
