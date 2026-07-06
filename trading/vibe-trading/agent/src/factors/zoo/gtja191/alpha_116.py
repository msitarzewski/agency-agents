
# ============================================================
# 中文名称: GTJA Alpha #116
# 简要说明: 国泰君安191短周期交易型alpha因子第116号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 116 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    REGBETA(CLOSE, SEQUENCE, 20)

Notes: Rolling OLS slope vs. linear index; cov(c,t,20)/var(t,20).
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

ALPHA_ID = "gtja191_116"

__alpha_meta__ = {
    'id': 'gtja191_116',
    'theme': ['momentum'],
    'formula_latex': 'regbeta(close,sequence(20),20)',
    'columns_required': ['close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
    'notes': 'Rolling OLS slope vs. linear index; cov(c,t,20)/var(t,20).',
}


def compute(panel):
    """Compute gtja191_116.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    n = 20
    t = pd.DataFrame(
        np.tile(np.arange(c.shape[0], dtype=np.float64).reshape(-1, 1), (1, c.shape[1])),
        index=c.index, columns=c.columns,
    )
    beta = safe_div(ts_cov(c, t, n), ts_std(t, n) ** 2)
    return beta
