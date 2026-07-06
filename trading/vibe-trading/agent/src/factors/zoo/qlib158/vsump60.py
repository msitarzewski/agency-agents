# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量上涨强度 60日
# 简要说明: sum(max(delta_v, 0)) / sum(|delta_v|)，60日内正成交量变化占比。
# 典型用途: 衡量60日内成交量放大日的比例，反映买盘活跃程度。
# ============================================================
"""qlib158 VSUMP60: formula = \\sum \\max(\\Delta v, 0) / \\sum |\\Delta v|."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_vsump60',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\sum \\\\max(\\\\Delta v, 0) / \\\\sum |\\\\Delta v|',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VSUMP60 on the supplied OHLCV panel."""
    v = panel['volume']
    diff = v - v.shift(1)
    pos = diff.where(diff > 0, 0.0)
    absd = diff.abs()
    num = pos.rolling(window=60, min_periods=60).sum()
    den = absd.rolling(window=60, min_periods=60).sum()
    return safe_div(num, den)
