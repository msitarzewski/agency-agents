# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 下跌强度 5日
# 简要说明: sum(max(-delta_close, 0)) / sum(|delta_close|)，5日内负收益占比。
# 典型用途: 衡量5日下跌日的比例强度，值接近1表示连续下跌。
# ============================================================
"""qlib158 SUMN5: formula = \\sum \\max(-\\Delta\\mathrm{close}, 0) / \\sum |\\Delta\\mathrm{close}|."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_sumn5',
    'theme': ['reversal'],
    'formula_latex': '\\\\sum \\\\max(-\\\\Delta\\\\mathrm{close}, 0) / \\\\sum |\\\\Delta\\\\mathrm{close}|',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 5,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 SUMN5 on the supplied OHLCV panel."""
    c = panel['close']
    diff = c - c.shift(1)
    neg = (-diff).where(diff < 0, 0.0)
    absd = diff.abs()
    num = neg.rolling(window=5, min_periods=5).sum()
    den = absd.rolling(window=5, min_periods=5).sum()
    return safe_div(num, den)
