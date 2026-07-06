
# ============================================================
# 中文名称: GTJA #56 - 开盘位序
# 简要说明: (RANK(OPEN-TSMIN(OPEN,12)) < RANK((RANK(CORR(SUM(((HIGH+LOW)/2),19),SUM(MEAN(VOLUME,40),19),13))^5)))，开盘位置排名与量价相关排名的比较。
# 典型用途: 比较开盘相对位置与量价关系强度，生成二元信号。
# ============================================================
"""GTJA Alpha #56.

Formula: (RANK(OPEN-TSMIN(OPEN,12)) < RANK((RANK(CORR(SUM(((HIGH+LOW)/2),19),SUM(MEAN(VOLUME,40),19),13))^5)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 56."""

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
    "id": "gtja191_056",
    "theme": ['volume'],
    "formula_latex": '(RANK(OPEN-TSMIN(OPEN,12)) < RANK((RANK(CORR(SUM(((HIGH+LOW)/2),19),SUM(MEAN(VOLUME,40),19),13))^5)))',
    "columns_required": ['open', 'high', 'low', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 19,
    "min_warmup_bars": 60,
    "notes": 'Boolean comparator returns 1/0; 40d mean truncated.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    lhs = rank(o - ts_min(o, 12))
    mid = (h + l) / 2.0
    sumA = mid.rolling(19, min_periods=19).sum()
    sumB = ts_mean(v, 30).rolling(19, min_periods=19).sum()
    rhs = rank(rank(ts_corr(sumA, sumB, 13)) ** 5)
    return (lhs < rhs).astype(float)
