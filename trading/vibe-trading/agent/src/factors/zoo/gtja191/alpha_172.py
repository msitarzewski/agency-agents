
# ============================================================
# 中文名称: GTJA Alpha #172
# 简要说明: 国泰君安191短周期交易型alpha因子第172号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 172 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    MEAN(ABS(SUM((LD>0 & LD>HD)?LD:0,14)*100/SUM(TR,14) - SUM((HD>0 & HD>LD)?HD:0,14)*100/SUM(TR,14)) / (SUM(...same...)/SUM(...same...))*100, 6)

Notes: Wilder's ADX-style indicator; mean over last 6 bars.
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

ALPHA_ID = "gtja191_172"

__alpha_meta__ = {
    'id': 'gtja191_172',
    'theme': ['momentum'],
    'formula_latex': 'see body',
    'columns_required': ['close', 'high', 'low'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 14,
    'min_warmup_bars': 20,
    'notes': "Wilder's ADX-style indicator; mean over last 6 bars.",
}


def compute(panel):
    """Compute gtja191_172.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    HD = h - h.shift(1)
    LD = l.shift(1) - l
    prev = c.shift(1)
    a = (h - l).to_numpy(dtype=np.float64, na_value=np.nan)
    b = (prev - h).abs().to_numpy(dtype=np.float64, na_value=np.nan)
    d = (prev - l).abs().to_numpy(dtype=np.float64, na_value=np.nan)
    TR = pd.DataFrame(np.maximum(np.maximum(a, b), d), index=c.index, columns=c.columns)
    ld_cond = ((LD > 0) & (LD > HD)).astype("float64")
    hd_cond = ((HD > 0) & (HD > LD)).astype("float64")
    dm_plus = (LD * ld_cond).rolling(14).sum() * 100.0
    dm_minus = (HD * hd_cond).rolling(14).sum() * 100.0
    tr14 = TR.rolling(14).sum()
    di_p = safe_div(dm_plus, tr14)
    di_m = safe_div(dm_minus, tr14)
    dx = safe_div((di_p - di_m).abs(), di_p + di_m) * 100.0
    out = ts_mean(dx, 6)
    return out
