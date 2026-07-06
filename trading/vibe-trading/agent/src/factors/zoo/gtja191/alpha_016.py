
# ============================================================
# 中文名称: GTJA #16 - VWAP位置
# 简要说明: (-1*rank(covariance(rank(high), rank(volume), 5)))，最高价与成交量5日协方差排名取负。
# 典型用途: 评估成交量推动价格的能力，高协方差意味着量价配合。
# ============================================================
"""GTJA Alpha #16.

Formula: (-1 * TSMAX(RANK(CORR(RANK(VOLUME), RANK(VWAP), 5)), 5))
Source: 国泰君安 191 alpha 研报 (2014), alpha 16."""

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
    "id": "gtja191_016",
    "theme": ['volume', 'microstructure'],
    "formula_latex": '(-1 * TSMAX(RANK(CORR(RANK(VOLUME), RANK(VWAP), 5)), 5))',
    "columns_required": ['volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 11,
    "notes": 'Max over 5d of rank of rolling rank-volume vs rank-vwap correlation.',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    return -1.0 * ts_max(rank(ts_corr(rank(v), rank(vw), 5)), 5)
