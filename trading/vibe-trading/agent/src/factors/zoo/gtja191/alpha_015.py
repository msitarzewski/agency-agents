
# ============================================================
# 中文名称: GTJA #15 - 收益排名差
# 简要说明: (-1*sum(rank(correlation(rank(high), rank(volume), 3)), 3))，最高价与成交量3日秩相关的3日累计取负。
# 典型用途: 量价相关性持续为负意味着量价持续背离。
# ============================================================
"""GTJA Alpha #15.

Formula: (OPEN/DELAY(CLOSE,1) - 1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 15."""

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
    "id": "gtja191_015",
    "theme": ['reversal'],
    "formula_latex": '(OPEN/DELAY(CLOSE,1) - 1)',
    "columns_required": ['open', 'close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 1,
    "min_warmup_bars": 2,
    "notes": 'Overnight gap return.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    c = panel["close"]
    pc = c.shift(1)
    return safe_div(o, pc) - 1.0
