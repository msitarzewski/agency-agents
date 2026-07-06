
# ============================================================
# 中文名称: GTJA #29 - 日内价差比
# 简要说明: (CLOSE-DELAY(CLOSE,1)) * RANK(CORR(HIGH,MEAN(VOLUME,60),5)) * (-1)，当日收益与量价相关的乘积取反。
# 典型用途: 收益与量价关系的交叉信号。
# ============================================================
"""GTJA Alpha #29.

Formula: (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*VOLUME
Source: 国泰君安 191 alpha 研报 (2014), alpha 29."""

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
    "id": "gtja191_029",
    "theme": ['momentum', 'volume'],
    "formula_latex": '(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*VOLUME',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 7,
    "notes": '6d return times current volume.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    return safe_div(c - c.shift(6), c.shift(6)) * v
