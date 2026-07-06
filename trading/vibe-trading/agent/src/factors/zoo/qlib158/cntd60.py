# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 涨跌天数差 60日
# 简要说明: CNTP_60 - CNTN_60，60日内上涨天数与下跌天数之差。
# 典型用途: 综合衡量60日内的涨跌方向，正值表示多头天数占优。
# ============================================================
"""qlib158 CNTD60: formula = \\mathrm{CNTP}_60 - \\mathrm{CNTN}_60."""
from __future__ import annotations

import pandas as pd

__alpha_meta__ = {
    'id': 'qlib158_cntd60',
    'theme': ['reversal'],
    'formula_latex': '\\\\mathrm{CNTP}_60 - \\\\mathrm{CNTN}_60',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 CNTD60 on the supplied OHLCV panel."""
    c = panel['close']
    up = (c > c.shift(1)).astype('float64')
    dn = (c < c.shift(1)).astype('float64')
    up_w = up.rolling(window=60, min_periods=60).mean()
    dn_w = dn.rolling(window=60, min_periods=60).mean()
    return up_w - dn_w
