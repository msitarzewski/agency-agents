
# ============================================================
# 中文名称: GTJA Alpha #143
# 简要说明: 国泰君安191短周期交易型alpha因子第143号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 143 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    CLOSE>DELAY(CLOSE,1)?(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*SELF:SELF

Notes: Recursive SELF unrolled to cumulative product of (1 + up_return) since series start.
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

ALPHA_ID = "gtja191_143"

__alpha_meta__ = {
    'id': 'gtja191_143',
    'theme': ['momentum'],
    'formula_latex': 'cumprod(1 + (c/delay(c,1)-1) if c>delay(c,1) else 0)',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 2,
    'notes': 'Recursive SELF unrolled to cumulative product of (1 + up_return) since series start.',
}


def compute(panel):
    """Compute gtja191_143.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    dc = c - c.shift(1)
    inc = safe_div(dc, c.shift(1)).where(dc > 0, 0.0)
    out = (1.0 + inc).cumprod()
    return out
