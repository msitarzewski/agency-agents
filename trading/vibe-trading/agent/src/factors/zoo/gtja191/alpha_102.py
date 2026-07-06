
# ============================================================
# 中文名称: GTJA Alpha #102
# 简要说明: 国泰君安191短周期交易型alpha因子第102号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 102 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SMA(MAX(volume-DELAY(volume,1),0),6,1)/SMA(ABS(volume-DELAY(volume,1)),6,1)*100

Notes: SMA(x,n,m) -> x.ewm(alpha=m/n, adjust=False).mean().
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

ALPHA_ID = "gtja191_102"

__alpha_meta__ = {
    'id': 'gtja191_102',
    'theme': ['volume'],
    'formula_latex': 'sma(max(volume-delay(volume,1),0),6,1)/sma(abs(volume-delay(volume,1)),6,1)*100',
    'columns_required': ['close', 'volume'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 6,
    'min_warmup_bars': 7,
    'notes': 'SMA(x,n,m) -> x.ewm(alpha=m/n, adjust=False).mean().',
}


def compute(panel):
    """Compute gtja191_102.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    v = panel["volume"]
    dv = v - v.shift(1)
    num = _sma(dv.clip(lower=0.0), 6, 1)
    den = _sma(dv.abs(), 6, 1)
    out = safe_div(num, den) * 100.0
    return out
