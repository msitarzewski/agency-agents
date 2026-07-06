
# ============================================================
# 中文名称: GTJA #2 - 高低价差动量
# 简要说明: (-1 * CORR(RANK(DELTA(LOG(VOLUME), 1)), RANK(((CLOSE - OPEN) / OPEN)), 4))，类似Alpha#1但窗口缩短为4日。
# 典型用途: 更短周期的量价背离检测，适合高频反转策略。
# ============================================================
"""GTJA Alpha #2.

Formula: (-1 * DELTA(((CLOSE - LOW) - (HIGH - CLOSE)) / (HIGH - LOW), 1))
Source: 国泰君安 191 alpha 研报 (2014), alpha 2."""

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
    "id": "gtja191_002",
    "theme": ['reversal', 'microstructure'],
    "formula_latex": '(-1 * DELTA(((CLOSE - LOW) - (HIGH - CLOSE)) / (HIGH - LOW), 1))',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 1,
    "min_warmup_bars": 2,
    "notes": 'Daily change in close-position-within-range.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    raw = safe_div((c - l) - (h - c), h - l)
    return -1.0 * delta(raw, 1)
