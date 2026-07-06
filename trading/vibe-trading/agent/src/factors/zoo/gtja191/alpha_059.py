
# ============================================================
# 中文名称: GTJA #59 - 价格极值差
# 简要说明: (-1*RANK(DELTA(MEAN(CLOSE,6),3))*RANK((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)))，同Alpha#53/#55/#58。
# 典型用途: 均线趋势与偏离度的综合判断。
# ============================================================
"""GTJA Alpha #59.

Formula: SUM((CLOSE=DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),20)
Source: 国泰君安 191 alpha 研报 (2014), alpha 59."""

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
    "id": "gtja191_059",
    "theme": ['momentum'],
    "formula_latex": 'SUM((CLOSE=DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),20)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 22,
    "notes": 'Like alpha #3 but with 20d window.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    pc = c.shift(1)
    up = c > pc
    dn = c < pc
    ref = pd.DataFrame(np.where(up, np.minimum(l, pc), np.where(dn, np.maximum(h, pc), c)),
                       index=c.index, columns=c.columns)
    move = (c - ref).where(up | dn, 0.0)
    return move.rolling(20, min_periods=20).sum()
