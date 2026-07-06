
# ============================================================
# 中文名称: GTJA #1 - 量价秩相关
# 简要说明: (-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))，成交量变化排名与日内收益排名的6日负相关。
# 典型用途: 量价背离识别：放量不涨或缩量不跌预示短期反转。
# ============================================================
"""GTJA Alpha #1.

Formula: (-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))
Source: 国泰君安 191 alpha 研报 (2014), alpha 1."""

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
    "id": "gtja191_001",
    "theme": ['volume', 'reversal'],
    "formula_latex": '(-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 6))',
    "columns_required": ['volume', 'close', 'open'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 7,
    "notes": 'Standard GTJA #1: lag-1 log-volume change rank vs intraday return rank, 6d corr.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    c = panel["close"]
    o = panel["open"]
    x = rank(delta(np.log(v.where(v > 0)), 1))
    y = rank(safe_div(c - o, o))
    return -1.0 * ts_corr(x, y, 6)
