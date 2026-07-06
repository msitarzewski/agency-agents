
# ============================================================
# 中文名称: GTJA Alpha #137
# 简要说明: 国泰君安191短周期交易型alpha因子第137号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha 137 (国泰君安 191 短周期交易型 alpha 因子, 2014).

Formula (verbatim from the report):
    16*((c-dc1+(c-o)/2+dc1-do1)/MAX_term) * MAX(abs(h-dc1), abs(l-dc1))

Notes: Transcribed from the standard 137 implementation; piecewise denominator.
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

ALPHA_ID = "gtja191_137"

__alpha_meta__ = {
    'id': 'gtja191_137',
    'theme': ['volatility'],
    'formula_latex': 'see body',
    'columns_required': ['open', 'high', 'low', 'close'],
    'extras_required': [],
    'universe': ['equity_cn'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 2,
    'notes': 'Transcribed from the standard 137 implementation; piecewise denominator.',
}


def compute(panel):
    """Compute gtja191_137.

    Args:
        panel: dict[str, pd.DataFrame] with at least the required columns.

    Returns:
        pd.DataFrame with index = panel["close"].index, columns = panel["close"].columns.
    """
    c = panel["close"]
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    dc1 = c.shift(1)
    do1 = o.shift(1)
    dl1 = l.shift(1)
    dh1 = h.shift(1)
    abs_hdc = (h - dc1).abs()
    abs_ldc = (l - dc1).abs()
    abs_hdl1 = (h - dl1).abs()
    # Three candidate denominators per report
    cond1 = (abs_hdc > abs_ldc) & (abs_hdc > abs_hdl1)
    cond2 = (abs_ldc > abs_hdl1) & (abs_ldc > abs_hdc)
    den_a = abs_hdc + abs_ldc / 2.0 + (dc1 - do1).abs() / 4.0
    den_b = abs_ldc + abs_hdc / 2.0 + (dc1 - do1).abs() / 4.0
    den_c = abs_hdl1 + (dc1 - do1).abs() / 4.0
    den = den_c.where(~cond2, den_b).where(~cond1, den_a)
    num = c - dc1 + (c - o) / 2.0 + dc1 - do1
    mx = pd.DataFrame(
        np.maximum(abs_hdc.to_numpy(dtype=np.float64, na_value=np.nan),
                   abs_ldc.to_numpy(dtype=np.float64, na_value=np.nan)),
        index=c.index, columns=c.columns,
    )
    out = 16.0 * safe_div(num, den) * mx
    return out
