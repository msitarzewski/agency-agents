
# ============================================================
# 中文名称: GTJA #26 - 条件SMA差值
# 简要说明: (-1*TSMAX(CORR(TSRANK(VOLUME,5), TSRANK(HIGH,5),5),3))，成交量与最高价5日秩相关的3日最大值取负。
# 典型用途: 量价同步性达到极值后的反转信号。
# ============================================================
"""GTJA Alpha #26.

Formula: ((((SUM(CLOSE,7)/7)-CLOSE))+((CORR(VWAP,DELAY(CLOSE,5),230))))
Source: 国泰君安 191 alpha 研报 (2014), alpha 26."""

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
    "id": "gtja191_026",
    "theme": ['momentum', 'microstructure'],
    "formula_latex": '((((SUM(CLOSE,7)/7)-CLOSE))+((CORR(VWAP,DELAY(CLOSE,5),230))))',
    "columns_required": ['close', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 7,
    "min_warmup_bars": 35,
    "notes": '230d corr approximated with 30d window; see notes.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    term1 = ts_mean(c, 7) - c
    term2 = ts_corr(vw, c.shift(5), 30)
    return term1 + term2
