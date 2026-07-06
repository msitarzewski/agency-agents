# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 涨跌差 10日
# 简要说明: SUMP_10 - SUMN_10，10日内上涨强度与下跌强度的差值。
# 典型用途: 判断10日内的整体涨跌倾向，正值表示上涨动量占优。
# ============================================================
"""qlib158 SUMD10: formula = \\mathrm{SUMP}_w - \\mathrm{SUMN}_w."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_sumd10',
    'theme': ['reversal'],
    'formula_latex': '\\\\mathrm{SUMP}_w - \\\\mathrm{SUMN}_w',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 10,
    'min_warmup_bars': 10,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 SUMD10 on the supplied OHLCV panel."""
    c = panel['close']
    diff = c - c.shift(1)
    pos = diff.where(diff > 0, 0.0)
    neg = (-diff).where(diff < 0, 0.0)
    absd = diff.abs()
    num_p = pos.rolling(window=10, min_periods=10).sum()
    num_n = neg.rolling(window=10, min_periods=10).sum()
    den = absd.rolling(window=10, min_periods=10).sum()
    return safe_div(num_p - num_n, den)
