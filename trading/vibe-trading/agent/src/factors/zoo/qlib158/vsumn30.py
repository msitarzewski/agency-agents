# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量下跌强度 30日
# 简要说明: sum(max(-delta_v, 0)) / sum(|delta_v|)，30日内负成交量变化占比。
# 典型用途: 衡量30日内成交量缩小日的比例，反映卖盘衰竭程度。
# ============================================================
"""qlib158 VSUMN30: formula = \\sum \\max(-\\Delta v, 0) / \\sum |\\Delta v|."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_vsumn30',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\sum \\\\max(-\\\\Delta v, 0) / \\\\sum |\\\\Delta v|',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 VSUMN30 on the supplied OHLCV panel."""
    v = panel['volume']
    diff = v - v.shift(1)
    neg = (-diff).where(diff < 0, 0.0)
    absd = diff.abs()
    num = neg.rolling(window=30, min_periods=30).sum()
    den = absd.rolling(window=30, min_periods=30).sum()
    return safe_div(num, den)
