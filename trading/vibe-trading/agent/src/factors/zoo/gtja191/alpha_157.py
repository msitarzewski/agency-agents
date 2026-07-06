
# ============================================================
# 中文名称: GTJA Alpha #157
# 简要说明: 国泰君安191短周期交易型alpha因子第157号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 157 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (MIN(PROD(RANK(RANK(LOG(SUM(TSMIN(RANK(RANK((-1*RANK(DELTA((CLOSE-1),5))))),2),1)))),1),5) + TSRANK(DELAY((-1*RET),6),5))

Notes: PROD(.,1) is identity; we use it directly.
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

ALPHA_ID = "gtja191_157"

__alpha_meta__ = {
    'id': 'gtja191_157',
    'theme': ['volume'],
    'formula_latex': 'see body',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 12,
    'notes': 'PROD(.,1) is identity; we use it directly.',
}


def compute(panel):
    """Compute gtja191_157.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    ret = safe_div(c, c.shift(1)) - 1.0
    inner = -1.0 * rank(delta(c - 1.0, 5))
    inner2 = rank(rank(inner))
    inner3 = ts_min(inner2, 2).rolling(1).sum()
    inner4 = np.log(inner3.replace(0.0, np.nan))
    left = ts_min(rank(rank(inner4)), 5)
    right = ts_rank((-1.0 * ret).shift(6), 5)
    out = left + right
    return out
