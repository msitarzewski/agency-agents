
# ============================================================
# 中文名称: GTJA #42 - 量价相关性
# 简要说明: (-1*RANK(STD(HIGH,10)))*CORR(HIGH,VOLUME,10)，10日最高价标准差排名与量价相关的组合。
# 典型用途: 高波动环境下的量价关系评估。
# ============================================================
"""GTJA Alpha #42.

Formula: ((-1*RANK(STD(HIGH,10)))*CORR(HIGH,VOLUME,10))
Source: 国泰君安 191 alpha 研报 (2014), alpha 42."""

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
    "id": "gtja191_042",
    "theme": ['volume', 'volatility'],
    "formula_latex": '((-1*RANK(STD(HIGH,10)))*CORR(HIGH,VOLUME,10))',
    "columns_required": ['high', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 10,
    "min_warmup_bars": 11,
    "notes": 'Negative rank of 10d std(high) times 10d corr(high, volume).',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    v = panel["volume"]
    return (-1.0 * rank(ts_std(h, 10))) * ts_corr(h, v, 10)
