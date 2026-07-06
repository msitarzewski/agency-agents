
# ============================================================
# 中文名称: GTJA #5 - 量价秩相关极值
# 简要说明: (-1 * TSMAX(CORR(TSRANK(VOLUME,5), TSRANK(HIGH,5), 5), 3))，成交量与最高价的5日秩相关在3日内的最大值取负。
# 典型用途: 成交量与价格同步性达到极值后的反转信号。
# ============================================================
"""GTJA Alpha #5.

Formula: (-1 * TSMAX(CORR(TSRANK(VOLUME,5), TSRANK(HIGH,5), 5), 3))
Source: 国泰君安 191 alpha 研报 (2014), alpha 5."""

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
    "id": "gtja191_005",
    "theme": ['volume'],
    "formula_latex": '(-1 * TSMAX(CORR(TSRANK(VOLUME,5), TSRANK(HIGH,5), 5), 3))',
    "columns_required": ['volume', 'high'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 13,
    "notes": 'Max over 3 days of 5d corr of TSRANK(volume,5) and TSRANK(high,5).',
}

def compute(panel: dict) -> pd.DataFrame:
    v = panel["volume"]
    h = panel["high"]
    return -1.0 * ts_max(ts_corr(ts_rank(v, 5), ts_rank(h, 5), 5), 3)
