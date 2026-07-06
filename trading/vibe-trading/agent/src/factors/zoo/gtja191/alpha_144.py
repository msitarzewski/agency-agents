
# ============================================================
# 中文名称: GTJA Alpha #144
# 简要说明: 国泰君安191短周期交易型alpha因子第144号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 144 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    SUMIF(ABS(CLOSE/DELAY(CLOSE,1)-1)/AMOUNT, CLOSE<DELAY(CLOSE,1),20)/COUNT(CLOSE<DELAY(CLOSE,1),20)

Notes: SUMIF -> (x*cond).rolling(n).sum(); COUNT -> cond.rolling(n).sum().
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

ALPHA_ID = "gtja191_144"

__alpha_meta__ = {
    'id': 'gtja191_144',
    'theme': ['liquidity'],
    'formula_latex': 'see body',
    'columns_required': ['close', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 21,
    'notes': 'SUMIF -> (x*cond).rolling(n).sum(); COUNT -> cond.rolling(n).sum().',
}


def compute(panel):
    """Compute gtja191_144.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    amt = panel["amount"]
    dc = c - c.shift(1)
    cond = (dc < 0).astype("float64")
    x = safe_div((safe_div(c, c.shift(1)) - 1.0).abs(), amt)
    sumif = (x * cond).rolling(20).sum()
    cnt = cond.rolling(20).sum().where(lambda d: d > 0)
    out = safe_div(sumif, cnt)
    return out
