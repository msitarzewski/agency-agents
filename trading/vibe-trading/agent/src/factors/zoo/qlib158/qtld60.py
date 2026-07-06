# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 下分位数 60日
# 简要说明: quantile_0.2(close, 60) / close，60日20%分位价格与当前收盘价的比率。
# 典型用途: 衡量当前价格相对于60日低分位的位置，值大表示价格在近期低位以上。
# ============================================================
"""qlib158 QTLD60: formula = \\mathrm{quantile}_{{0.2}}(\\mathrm{close}, 60) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_qtld60',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{quantile}_{{0.2}}(\\\\mathrm{close}, 60) / \\\\mathrm{close}',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 QTLD60 on the supplied OHLCV panel."""
    c = panel['close']
    q = c.rolling(window=60, min_periods=60).quantile(0.2)
    return safe_div(q, c)
