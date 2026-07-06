
# ============================================================
# 中文名称: GTJA #24 - SMA价格差
# 简要说明: SMA(CLOSE-DELAY(CLOSE,5),5,1)，收盘价5日变化的5日简单移动平均。
# 典型用途: 价格变化速度的平滑指标，用于识别趋势加速或减速。
# ============================================================
"""GTJA Alpha #24.

Formula: SMA(CLOSE-DELAY(CLOSE,5),5,1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 24."""

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
    "id": "gtja191_024",
    "theme": ['momentum'],
    "formula_latex": 'SMA(CLOSE-DELAY(CLOSE,5),5,1)',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 6,
    "notes": 'SMA(5, m=1) of 5d delta(close).',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    return delta(c, 5).ewm(alpha=1.0 / 5.0, adjust=False).mean()
