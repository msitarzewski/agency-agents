
# ============================================================
# 中文名称: GTJA #27 - 加权前日收盘
# 简要说明: (-1*RANK((DELTA(CORR(HIGH,MEAN(VOLUME,60),5),1))*RANK(CORR(CLOSE,MEAN(VOLUME,50),1))))，量价相关变化的组合排名。
# 典型用途: 量价关系的一阶变化信号，用于趋势转折点检测。
# ============================================================
"""GTJA Alpha #27.

Formula: WMA((CLOSE-DELAY(CLOSE,3))/DELAY(CLOSE,3)*100 + (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100, 12)
Source: 国泰君安 191 alpha 研报 (2014), alpha 27."""

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
    "id": "gtja191_027",
    "theme": ['momentum'],
    "formula_latex": 'WMA((CLOSE-DELAY(CLOSE,3))/DELAY(CLOSE,3)*100 + (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100, 12)',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 12,
    "min_warmup_bars": 18,
    "notes": 'WMA proxied by decay_linear.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    r3 = safe_div(c - c.shift(3), c.shift(3)) * 100.0
    r6 = safe_div(c - c.shift(6), c.shift(6)) * 100.0
    return decay_linear(r3 + r6, 12)
