
# ============================================================
# 中文名称: GTJA #52 - 均值回复信号
# 简要说明: ((-1*RANK(TSMIN(LOW,12)))*RANK(CORR(RANK(LOW),RANK(MEAN(VOLUME,60)),8)))，最低价位置与量价相关的组合。
# 典型用途: 价格处于低点且量价关系异常时的买入信号。
# ============================================================
"""GTJA Alpha #52.

Formula: SUM(MAX(0,HIGH-DELAY((HIGH+LOW+CLOSE)/3,1)),26) / SUM(MAX(0,DELAY((HIGH+LOW+CLOSE)/3,1)-LOW),26) * 100
Source: 国泰君安 191 alpha 研报 (2014), alpha 52."""

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
    "id": "gtja191_052",
    "theme": ['microstructure'],
    "formula_latex": 'SUM(MAX(0,HIGH-DELAY((HIGH+LOW+CLOSE)/3,1)),26) / SUM(MAX(0,DELAY((HIGH+LOW+CLOSE)/3,1)-LOW),26) * 100',
    "columns_required": ['high', 'low', 'close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 26,
    "min_warmup_bars": 27,
    "notes": 'Bull power / bear power ratio over 26 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    l = panel["low"]
    c = panel["close"]
    typ = (h + l + c) / 3.0
    p_typ = typ.shift(1)
    bull = (h - p_typ).clip(lower=0)
    bear = (p_typ - l).clip(lower=0)
    return safe_div(bull.rolling(26, min_periods=26).sum(),
                    bear.rolling(26, min_periods=26).sum()) * 100.0
