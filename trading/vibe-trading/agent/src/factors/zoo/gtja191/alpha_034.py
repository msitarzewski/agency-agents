
# ============================================================
# 中文名称: GTJA #34 - 量价波动偏度
# 简要说明: RANK(CORR(HIGH,MEAN(VOLUME,60),5)) * (-1)，最高价与60日均量的5日相关性取负排名。
# 典型用途: 量价同步性的反转信号。
# ============================================================
"""GTJA Alpha #34.

Formula: MEAN(CLOSE,12)/CLOSE
Source: 国泰君安 191 alpha 研报 (2014), alpha 34."""

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
    "id": "gtja191_034",
    "theme": ['reversal'],
    "formula_latex": 'MEAN(CLOSE,12)/CLOSE',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 12,
    "min_warmup_bars": 13,
    "notes": 'MA12 over close.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    return safe_div(ts_mean(c, 12), c)
