
# ============================================================
# 中文名称: GTJA Alpha #178
# 简要说明: 国泰君安191短周期交易型alpha因子第178号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 178 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME

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

ALPHA_ID = "gtja191_178"

__alpha_meta__ = {
    'id': 'gtja191_178',
    'theme': ['momentum', 'volume'],
    'formula_latex': '(c-delay(c,1))/delay(c,1)*v',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 2,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_178.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    v = panel["volume"]
    out = safe_div(c - c.shift(1), c.shift(1)) * v
    return out
