
# ============================================================
# 中文名称: GTJA #46 - 条件量价排名
# 简要说明: (MEAN(CLOSE,20)-LOW+MEAN(CLOSE,20)-HIGH)/MEAN(CLOSE,20)*VOLUME，价格偏离均值的量加权指标。
# 典型用途: 成交量加权的价格偏离度，值大表示当前价格明显偏离均线且有成交确认。
# ============================================================
"""GTJA Alpha #46.

Formula: (MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/(4*CLOSE)
Source: 国泰君安 191 alpha 研报 (2014), alpha 46."""

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
    "id": "gtja191_046",
    "theme": ['reversal'],
    "formula_latex": '(MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/(4*CLOSE)',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 24,
    "min_warmup_bars": 25,
    "notes": 'Mean of four MA windows over price.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    s = ts_mean(c, 3) + ts_mean(c, 6) + ts_mean(c, 12) + ts_mean(c, 24)
    return safe_div(s, 4.0 * c)
