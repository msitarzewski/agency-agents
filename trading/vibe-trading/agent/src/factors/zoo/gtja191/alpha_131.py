
# ============================================================
# 中文名称: GTJA Alpha #131
# 简要说明: 国泰君安191短周期交易型alpha因子第131号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 131 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    (RANK(DELAT(VWAP,1))^TSRANK(CORR(CLOSE,MEAN(VOLUME,50),18),18))

Notes: DELAT in report typo = DELTA.
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
    vwap,
)

ALPHA_ID = "gtja191_131"

__alpha_meta__ = {
    'id': 'gtja191_131',
    'theme': ['volume'],
    'formula_latex': 'rank(delta(vwap,1))^tsrank(corr(close,mean(v,50),18),18)',
    'columns_required': ['open', 'high', 'low', 'close', 'volume', 'amount'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 50,
    'min_warmup_bars': 84,
    'notes': 'DELAT in report typo = DELTA.',
}


def compute(panel):
    """Compute gtja191_131.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    v = panel["volume"]
    vw = vwap(panel, "equity_cn")

    left = rank(delta(vw, 1))
    right = ts_rank(ts_corr(c, ts_mean(v, 50), 18), 18)
    arr = np.power(left.to_numpy(dtype=np.float64, na_value=np.nan),
                   right.to_numpy(dtype=np.float64, na_value=np.nan))
    out = pd.DataFrame(arr, index=left.index, columns=left.columns)
    return out
