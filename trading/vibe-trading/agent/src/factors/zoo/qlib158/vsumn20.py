# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量下跌强度 20日
# 简要说明: sum(max(-delta_v, 0)) / sum(|delta_v|)，20日内负成交量变化占比。
# 典型用途: 衡量20日内成交量缩小日的比例，反映卖盘衰竭程度。
# ============================================================
"""qlib158 VSUMN20: formula = \\sum \\max(-\\Delta v, 0) / \\sum |\\Delta v|."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_vsumn20',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\sum \\\\max(-\\\\Delta v, 0) / \\\\sum |\\\\Delta v|',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VSUMN20 on the supplied OHLCV panel."""
    v = panel['volume']
    diff = v - v.shift(1)
    neg = (-diff).where(diff < 0, 0.0)
    absd = diff.abs()
    num = neg.rolling(window=20, min_periods=20).sum()
    den = absd.rolling(window=20, min_periods=20).sum()
    return safe_div(num, den)
