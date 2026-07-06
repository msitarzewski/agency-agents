
# ============================================================
# 中文名称: GTJA #40 - 成交量比率
# 简要说明: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:0),26)/SUM((CLOSE<=DELAY(CLOSE,1)?VOLUME:0),26)*100，上涨日成交量与下跌日成交量比率。
# 典型用途: 经典的量价强度指标，类似成交量OBV的变种。
# ============================================================
"""GTJA Alpha #40.

Formula: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:0),26)/SUM((CLOSE<=DELAY(CLOSE,1)?VOLUME:0),26)*100
Source: 国泰君安 191 alpha 研报 (2014), alpha 40."""

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
    "id": "gtja191_040",
    "theme": ['volume'],
    "formula_latex": 'SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:0),26)/SUM((CLOSE<=DELAY(CLOSE,1)?VOLUME:0),26)*100',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 26,
    "min_warmup_bars": 27,
    "notes": 'Up-volume vs down-volume ratio over 26 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    pc = c.shift(1)
    up = c > pc
    up_v = v.where(up, 0.0).rolling(26, min_periods=26).sum()
    dn_v = v.where(~up, 0.0).rolling(26, min_periods=26).sum()
    return safe_div(up_v, dn_v) * 100.0
