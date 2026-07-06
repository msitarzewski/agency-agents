
# ============================================================
# 中文名称: GTJA Alpha #146
# 简要说明: 国泰君安191短周期交易型alpha因子第146号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 146 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MEAN((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)-SMA(...,61,2),20)*((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)-SMA(...,61,2))/SMA(((...)-SMA(...))^2,60,2)

Notes: Standardised return deviation; SMA(.,61,2)=ewm(alpha=2/61).
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

ALPHA_ID = "gtja191_146"

__alpha_meta__ = {
    'id': 'gtja191_146',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 81,
    'notes': 'Standardised return deviation; SMA(.,61,2)=ewm(alpha=2/61).',
}


def compute(panel):
    """Compute gtja191_146.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    def _sma(x, n, m):
        """SMA(x, n, m) per GTJA convention -> ewm with alpha = m/n."""
        return x.ewm(alpha=m / n, adjust=False).mean()
    c = panel["close"]
    ret = safe_div(c - c.shift(1), c.shift(1))
    ewm_ret = _sma(ret, 61, 2)
    dev = ret - ewm_ret
    left = ts_mean(dev, 20)
    right = dev
    den = _sma(dev ** 2, 60, 2)
    out = safe_div(left * right, den)
    return out
