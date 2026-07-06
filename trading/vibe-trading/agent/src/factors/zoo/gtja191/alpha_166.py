
# ============================================================
# 中文名称: GTJA Alpha #166
# 简要说明: 国泰君安191短周期交易型alpha因子第166号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 166 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    -20*(20-1)^1.5*SUM(CLOSE/DELAY(CLOSE,1)-1-MEAN(CLOSE/DELAY(CLOSE,1)-1,20),20)/((20-1)*(20-2)*(SUM((CLOSE/DELAY(CLOSE,1)-1)^2,20))^1.5)

Notes: Skewness-style; constants from report.
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

ALPHA_ID = "gtja191_166"

__alpha_meta__ = {
    'id': 'gtja191_166',
    'theme': ['volatility'],
    'formula_latex': 'see body',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 40,
    'notes': 'Skewness-style; constants from report.',
}


def compute(panel):
    """Compute gtja191_166.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    ret = safe_div(c, c.shift(1)) - 1.0
    m = ts_mean(ret, 20)
    num = (ret - m).rolling(20).sum() * -20.0 * (20.0 - 1.0) ** 1.5
    den = (20.0 - 1.0) * (20.0 - 2.0) * (ret ** 2).rolling(20).sum() ** 1.5
    out = safe_div(num, den)
    return out
