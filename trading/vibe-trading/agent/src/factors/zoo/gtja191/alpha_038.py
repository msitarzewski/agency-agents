
# ============================================================
# 中文名称: GTJA #38 - 夏普比信号
# 简要说明: ((-1*RANK(TSRANK(CLOSE,10)))*RANK(CLOSE/OPEN))，10日排名与日内涨跌幅的组合。
# 典型用途: 中期排名与短期表现的交叉验证信号。
# ============================================================
"""GTJA Alpha #38.

Formula: (((SUM(HIGH,20)/20)<HIGH)?(-1*DELTA(HIGH,2)):0)
Source: 国泰君安 191 alpha 研报 (2014), alpha 38."""

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
    "id": "gtja191_038",
    "theme": ['reversal'],
    "formula_latex": '(((SUM(HIGH,20)/20)<HIGH)?(-1*DELTA(HIGH,2)):0)',
    "columns_required": ['high'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 21,
    "notes": 'When current high > MA20(high), output -delta(high,2); else 0.',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    m20 = ts_mean(h, 20)
    cond = m20 < h
    return (-1.0 * delta(h, 2)).where(cond, 0.0)
