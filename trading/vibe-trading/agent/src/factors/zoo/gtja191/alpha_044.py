
# ============================================================
# 中文名称: GTJA #44 - 条件量价积
# 简要说明: (-1*RANK(CORR(HIGH,MEAN(VOLUME,20),5)) + RANK(CORR(RANK(LOW),RANK(MEAN(VOLUME,20)),6)))，两种量价关系的差值排名。
# 典型用途: 不同维度量价关系的综合比较。
# ============================================================
"""GTJA Alpha #44.

Formula: (TSRANK(DECAYLINEAR(CORR(LOW,MEAN(VOLUME,10),7),6),4)+TSRANK(DECAYLINEAR(DELTA(VWAP,3),10),15))
Source: 国泰君安 191 alpha 研报 (2014), alpha 44."""

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
    "id": "gtja191_044",
    "theme": ['volume'],
    "formula_latex": '(TSRANK(DECAYLINEAR(CORR(LOW,MEAN(VOLUME,10),7),6),4)+TSRANK(DECAYLINEAR(DELTA(VWAP,3),10),15))',
    "columns_required": ['low', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 10,
    "min_warmup_bars": 27,
    "notes": 'Sum of two TSRANK terms.',
}

def compute(panel: dict) -> pd.DataFrame:
    l = panel["low"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    t1 = ts_rank(decay_linear(ts_corr(l, ts_mean(v, 10), 7), 6), 4)
    t2 = ts_rank(decay_linear(delta(vw, 3), 10), 15)
    return t1 + t2
