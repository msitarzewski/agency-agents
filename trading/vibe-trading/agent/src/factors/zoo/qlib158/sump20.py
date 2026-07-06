# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 上涨强度 20日
# 简要说明: sum(max(delta_close, 0)) / sum(|delta_close|)，20日内正收益占比。
# 典型用途: 衡量20日上涨日的比例强度，值接近1表示连续上涨。
# ============================================================
"""qlib158 SUMP20: formula = \\sum \\max(\\Delta\\mathrm{close}, 0) / \\sum |\\Delta\\mathrm{close}|."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_sump20',
    'theme': ['reversal'],
    'formula_latex': '\\\\sum \\\\max(\\\\Delta\\\\mathrm{close}, 0) / \\\\sum |\\\\Delta\\\\mathrm{close}|',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 SUMP20 on the supplied OHLCV panel."""
    c = panel['close']
    diff = c - c.shift(1)
    pos = diff.where(diff > 0, 0.0)
    absd = diff.abs()
    num = pos.rolling(window=20, min_periods=20).sum()
    den = absd.rolling(window=20, min_periods=20).sum()
    return safe_div(num, den)
