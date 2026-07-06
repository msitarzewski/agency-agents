
# ============================================================
# 中文名称: GTJA #35 - 最高价位置
# 简要说明: (-1*RANK(DELTA(VWAP,1))^3 / RANK(CORR(LOW,MEAN(VOLUME,50),12)))，类似Alpha#32。
# 典型用途: VWAP一阶变化的趋势反转判断。
# ============================================================
"""GTJA Alpha #35.

Formula: (MIN(RANK(DECAYLINEAR(DELTA(OPEN,1),15)), RANK(DECAYLINEAR(CORR(VOLUME,((OPEN*0.65)+(OPEN*0.35)),17),7))) * -1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 35."""

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
    "id": "gtja191_035",
    "theme": ['volume'],
    "formula_latex": '(MIN(RANK(DECAYLINEAR(DELTA(OPEN,1),15)), RANK(DECAYLINEAR(CORR(VOLUME,((OPEN*0.65)+(OPEN*0.35)),17),7))) * -1)',
    "columns_required": ['open', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 15,
    "min_warmup_bars": 25,
    "notes": 'Element-wise min of two ranks, negated.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    v = panel["volume"]
    p1 = rank(decay_linear(delta(o, 1), 15))
    weighted = o * 0.65 + o * 0.35
    p2 = rank(decay_linear(ts_corr(v, weighted, 17), 7))
    return -1.0 * pd.DataFrame(np.minimum(p1.to_numpy(), p2.to_numpy()),
                               index=o.index, columns=o.columns)
