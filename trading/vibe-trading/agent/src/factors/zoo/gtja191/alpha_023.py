
# ============================================================
# 中文名称: GTJA #23 - 条件相关系数
# 简要说明: ((SUM(MEAN(VOLUME,20),5) * SUM(MEAN(CLOSE,20),5)) * (-1*RANK(CORR(HIGH,MEAN(VOLUME,60),5))))，量价相关性与均值的组合。
# 典型用途: 长期量价均值与短期相关性的综合信号。
# ============================================================
"""GTJA Alpha #23.

Formula: SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)/(SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1) + SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)) * 100
Source: 国泰君安 191 alpha 研报 (2014), alpha 23."""

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
    "id": "gtja191_023",
    "theme": ['volatility'],
    "formula_latex": 'SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)/(SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1) + SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)) * 100',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 22,
    "notes": 'Up-volatility share. SMA(20, m=1) of STD(20) over up/down days.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    pc = c.shift(1)
    s20 = ts_std(c, 20)
    up = (c > pc)
    up_part = s20.where(up, 0.0)
    dn_part = s20.where(~up, 0.0)
    u_sma = up_part.ewm(alpha=1.0 / 20.0, adjust=False).mean()
    d_sma = dn_part.ewm(alpha=1.0 / 20.0, adjust=False).mean()
    return safe_div(u_sma, u_sma + d_sma) * 100.0
