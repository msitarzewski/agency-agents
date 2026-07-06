
# ============================================================
# 中文名称: GTJA Alpha #127
# 简要说明: 国泰君安191短周期交易型alpha因子第127号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 127 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (MEAN((100*(CLOSE-MAX(CLOSE,12))/MAX(CLOSE,12))^2,12))^(1/2)

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

ALPHA_ID = "gtja191_127"

__alpha_meta__ = {
    'id': 'gtja191_127',
    'theme': ['volatility'],
    'formula_latex': 'sqrt(mean((100*(c-tsmax(c,12))/tsmax(c,12))^2,12))',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 12,
    'min_warmup_bars': 24,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_127.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    ratio = safe_div(c - ts_max(c, 12), ts_max(c, 12)) * 100.0
    out = ts_mean(ratio ** 2, 12) ** 0.5
    return out
