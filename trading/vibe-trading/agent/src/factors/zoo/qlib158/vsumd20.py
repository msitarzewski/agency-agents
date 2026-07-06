# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量涨跌差 20日
# 简要说明: VSUMP_20 - VSUMN_20，20日内成交量加权的上涨与下跌强度差。
# 典型用途: 结合成交量判断20日内的趋势可信度，量价配合时信号更强。
# ============================================================
"""qlib158 VSUMD20: formula = \\mathrm{VSUMP}_w - \\mathrm{VSUMN}_w."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_vsumd20',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\mathrm{VSUMP}_w - \\\\mathrm{VSUMN}_w',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VSUMD20 on the supplied OHLCV panel."""
    v = panel['volume']
    diff = v - v.shift(1)
    pos = diff.where(diff > 0, 0.0)
    neg = (-diff).where(diff < 0, 0.0)
    absd = diff.abs()
    num_p = pos.rolling(window=20, min_periods=20).sum()
    num_n = neg.rolling(window=20, min_periods=20).sum()
    den = absd.rolling(window=20, min_periods=20).sum()
    return safe_div(num_p - num_n, den)
