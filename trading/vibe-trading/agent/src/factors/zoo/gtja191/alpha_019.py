
# ============================================================
# 中文名称: GTJA #19 - 波动条件信号
# 简要说明: (-1*SIGN(DELTA(CLOSE,7)) + SIGN(DELTA(CLOSE,7)) * RANK(TSMIN(LOW,12)))，7日价格方向与12日最低排名的组合。
# 典型用途: 趋势方向与支撑位置的组合交易信号。
# ============================================================
"""GTJA Alpha #19.

Formula: (CLOSE<DELAY(CLOSE,5)?(CLOSE-DELAY(CLOSE,5))/DELAY(CLOSE,5):(CLOSE=DELAY(CLOSE,5)?0:(CLOSE-DELAY(CLOSE,5))/CLOSE))
Source: 国泰君安 191 alpha 研报 (2014), alpha 19."""

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
    "id": "gtja191_019",
    "theme": ['reversal'],
    "formula_latex": '(CLOSE<DELAY(CLOSE,5)?(CLOSE-DELAY(CLOSE,5))/DELAY(CLOSE,5):(CLOSE=DELAY(CLOSE,5)?0:(CLOSE-DELAY(CLOSE,5))/CLOSE))',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 6,
    "notes": 'Piecewise 5d momentum normalized differently in up/down regimes.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    pc = c.shift(5)
    diff = c - pc
    up = c > pc
    dn = c < pc
    out = pd.DataFrame(np.where(dn, safe_div(diff, pc).to_numpy(),
                                np.where(up, safe_div(diff, c).to_numpy(), 0.0)),
                       index=c.index, columns=c.columns)
    return out
