
# ============================================================
# 中文名称: GTJA Alpha #110
# 简要说明: 国泰君安191短周期交易型alpha因子第110号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 110 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20) / SUM(MAX(0,DELAY(CLOSE,1)-LOW),20) * 100

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

ALPHA_ID = "gtja191_110"

__alpha_meta__ = {
    'id': 'gtja191_110',
    'theme': ['momentum'],
    'formula_latex': 'sum(max(0,high-delay(close,1)),20)/sum(max(0,delay(close,1)-low),20)*100',
    'columns_required': ['close', 'high', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 21,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_110.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    prev_c = c.shift(1)
    num = (h - prev_c).clip(lower=0.0).rolling(20).sum()
    den = (prev_c - l).clip(lower=0.0).rolling(20).sum()
    out = safe_div(num, den) * 100.0
    return out
