
# ============================================================
# 中文名称: GTJA #12 - 开盘动量排名
# 简要说明: (SIGN(DELTA(VOLUME,1)) * (-1 * DELTA(CLOSE,1)))，成交量方向与价格变化方向的乘积取负。
# 典型用途: 量价背离的瞬时信号，放量下跌或缩量上涨。
# ============================================================
"""GTJA Alpha #12.

Formula: (RANK((OPEN - (SUM(VWAP,10)/10))) * (-1 * RANK(ABS((CLOSE - VWAP)))))
Source: 国泰君安 191 alpha 研报 (2014), alpha 12."""

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
    "id": "gtja191_012",
    "theme": ['reversal', 'microstructure'],
    "formula_latex": '(RANK((OPEN - (SUM(VWAP,10)/10))) * (-1 * RANK(ABS((CLOSE - VWAP)))))',
    "columns_required": ['open', 'close', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 10,
    "min_warmup_bars": 11,
    "notes": 'Open-minus-10d-vwap rank times negative rank of |close-vwap|.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    c = panel["close"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    return rank(o - ts_mean(vw, 10)) * (-1.0 * rank((c - vw).abs()))
