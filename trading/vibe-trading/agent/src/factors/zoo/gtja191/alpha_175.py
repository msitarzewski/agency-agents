
# ============================================================
# 中文名称: GTJA Alpha #175
# 简要说明: 国泰君安191短周期交易型alpha因子第175号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 175 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MEAN(MAX(MAX(HIGH-LOW,ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),6)

Notes: ATR(6).
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

ALPHA_ID = "gtja191_175"

__alpha_meta__ = {
    'id': 'gtja191_175',
    'theme': ['volatility'],
    'formula_latex': 'mean(true_range,6)',
    'columns_required': ['close', 'high', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 6,
    'min_warmup_bars': 7,
    'notes': 'ATR(6).',
}


def compute(panel):
    """Compute gtja191_175.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    prev = c.shift(1)
    a = (h - l).to_numpy(dtype=np.float64, na_value=np.nan)
    b = (prev - h).abs().to_numpy(dtype=np.float64, na_value=np.nan)
    d = (prev - l).abs().to_numpy(dtype=np.float64, na_value=np.nan)
    tr = np.maximum(np.maximum(a, b), d)
    tr_df = pd.DataFrame(tr, index=c.index, columns=c.columns)
    out = ts_mean(tr_df, 6)
    return out
