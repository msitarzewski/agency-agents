
# ============================================================
# 中文名称: GTJA Alpha #61
# 简要说明: 国泰君安191短周期交易型alpha因子第61号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #61.

Formula: (MAX(RANK(DECAYLINEAR(DELTA(VWAP,1),12)), RANK(DECAYLINEAR(RANK(CORR(LOW,MEAN(VOLUME,80),8)),17))) * -1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 61."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
    decay_linear,
    delta,
    rank,
    safe_div,
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

__alpha_meta__ = {
    "id": "gtja191_061",
    "theme": ['volume'],
    "formula_latex": '(MAX(RANK(DECAYLINEAR(DELTA(VWAP,1),12)), RANK(DECAYLINEAR(RANK(CORR(LOW,MEAN(VOLUME,80),8)),17))) * -1)',
    "columns_required": ['volume', 'amount', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 17,
    "min_warmup_bars": 53,
    "notes": '80d mean volume approximated with 30d.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    l = panel["low"]
    p1 = rank(decay_linear(delta(vw, 1), 12))
    p2 = rank(decay_linear(rank(ts_corr(l, ts_mean(v, 30), 8)), 17))
    return -1.0 * pd.DataFrame(np.maximum(p1.to_numpy(), p2.to_numpy()),
                               index=v.index, columns=v.columns)
