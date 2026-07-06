
# ============================================================
# 中文名称: GTJA #25 - 条件成交量压力
# 简要说明: RANK(((((-1*RANK(DELTA(CLOSE,7)))*SIGN(DELTA(CLOSE,7)))*VOLUME)+1))，价格方向与成交量的组合排名。
# 典型用途: 下跌时放量信号的强度排名，用于恐慌性抛售识别。
# ============================================================
"""GTJA Alpha #25.

Formula: ((-1*RANK((DELTA(CLOSE,7)*(1-RANK(DECAYLINEAR((VOLUME/MEAN(VOLUME,20)),9))))))*(1+RANK(SUM(RET,250))))
Source: 国泰君安 191 alpha 研报 (2014), alpha 25."""

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
    "id": "gtja191_025",
    "theme": ['momentum', 'volume'],
    "formula_latex": '((-1*RANK((DELTA(CLOSE,7)*(1-RANK(DECAYLINEAR((VOLUME/MEAN(VOLUME,20)),9))))))*(1+RANK(SUM(RET,250))))',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 9,
    "min_warmup_bars": 61,
    "notes": 'Long-window RET sum approximated with 60d cap (warmup feasibility); see notes.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    pc = c.shift(1)
    ret = safe_div(c - pc, pc)
    vmean20 = ts_mean(v, 20)
    decayed = decay_linear(safe_div(v, vmean20), 9)
    term1 = -1.0 * rank(delta(c, 7) * (1.0 - rank(decayed)))
    # Approximate SUM(RET, 250) with min(60, available) window — see notes.
    long_sum = ret.rolling(60, min_periods=20).sum()
    return term1 * (1.0 + rank(long_sum))
