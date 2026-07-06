
# ============================================================
# 中文名称: GTJA Alpha #165
# 简要说明: 国泰君安191短周期交易型alpha因子第165号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 165 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MAX(SUMAC(CLOSE-MEAN(CLOSE,48))) - MIN(SUMAC(CLOSE-MEAN(CLOSE,48))) / STD(CLOSE,48)

Notes: SUMAC = expanding cumulative sum approximated by rolling 48-day cumulative sum.
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

ALPHA_ID = "gtja191_165"

__alpha_meta__ = {
    'id': 'gtja191_165',
    'theme': ['volatility'],
    'formula_latex': 'see body',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 48,
    'min_warmup_bars': 142,
    'notes': 'SUMAC = expanding cumulative sum approximated by rolling 48-day cumulative sum.',
}


def compute(panel):
    """Compute gtja191_165.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    dev = c - ts_mean(c, 48)
    csum = dev.rolling(48).sum()
    out = safe_div(ts_max(csum, 48) - ts_min(csum, 48), ts_std(c, 48))
    return out
