
# ============================================================
# 中文名称: GTJA #55 - 极值价差
# 简要说明: (-1*RANK(DELTA(MEAN(CLOSE,6),3))*RANK((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)))，类似Alpha#53。
# 典型用途: 均线变化与偏离度的综合反转信号。
# ============================================================
"""GTJA Alpha #55.

Formula: SUM(16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))/((ABS(HIGH-DELAY(CLOSE,1))>ABS(LOW-DELAY(CLOSE,1)) && ABS(HIGH-DELAY(CLOSE,1))>ABS(HIGH-DELAY(LOW,1))?ABS(HIGH-DELAY(CLOSE,1))+ABS(LOW-DELAY(CLOSE,1))/2+ABS(DELAY(CLOSE,1)-DELAY(OPEN,1))/4:ABS(LOW-DELAY(CLOSE,1))+ABS(HIGH-DELAY(CLOSE,1))/2+ABS(DELAY(CLOSE,1)-DELAY(OPEN,1))/4))*MAX(ABS(HIGH-DELAY(CLOSE,1)),ABS(LOW-DELAY(CLOSE,1))),20)
Source: 国泰君安 191 alpha 研报 (2014), alpha 55."""

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
    "id": "gtja191_055",
    "theme": ['microstructure'],
    "formula_latex": 'SUM(16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))/((ABS(HIGH-DELAY(CLOSE,1))>ABS(LOW-DELAY(CLOSE,1)) && ABS(HIGH-DELAY(CLOSE,1))>ABS(HIGH-DELAY(LOW,1))?ABS(HIGH-DELAY(CLOSE,1))+ABS(LOW-DELAY(CLOSE,1))/2+ABS(DELAY(CLOSE,1)-DELAY(OPEN,1))/4:ABS(LOW-DELAY(CLOSE,1))+ABS(HIGH-DELAY(CLOSE,1))/2+ABS(DELAY(CLOSE,1)-DELAY(OPEN,1))/4))*MAX(ABS(HIGH-DELAY(CLOSE,1)),ABS(LOW-DELAY(CLOSE,1))),20)',
    "columns_required": ['close', 'high', 'low', 'open'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 22,
    "notes": 'Sumof complex per-day score over 20 days; numerator simplified.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    o = panel["open"]
    pc = c.shift(1)
    po = o.shift(1)
    pl = l.shift(1)
    numer = 16.0 * (c - pc + (c - o) / 2.0 + pc - po)
    a = (h - pc).abs()
    b = (l - pc).abs()
    d = (pc - po).abs()
    cond1 = (a > b) & (a > (h - pl).abs())
    branch1 = a + b / 2.0 + d / 4.0
    branch2 = b + a / 2.0 + d / 4.0
    denom = branch1.where(cond1, branch2)
    factor = pd.DataFrame(np.maximum(a.to_numpy(), b.to_numpy()), index=c.index, columns=c.columns)
    per_day = safe_div(numer, denom) * factor
    return per_day.rolling(20, min_periods=20).sum()
