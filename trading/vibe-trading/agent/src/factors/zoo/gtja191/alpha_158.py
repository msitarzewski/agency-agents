
# ============================================================
# 中文名称: GTJA Alpha #158
# 简要说明: 国泰君安191短周期交易型alpha因子第158号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 158 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    ((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE

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

ALPHA_ID = "gtja191_158"

__alpha_meta__ = {
    'id': 'gtja191_158',
    'theme': ['volatility'],
    'formula_latex': '((h-sma(c,15,2))-(l-sma(c,15,2)))/c',
    'columns_required': ['close', 'high', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 15,
    'min_warmup_bars': 16,
    'notes': '',
}


def compute(panel):
    """Compute gtja191_158.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    s = _sma(c, 15, 2)
    out = safe_div((h - s) - (l - s), c)
    return out
