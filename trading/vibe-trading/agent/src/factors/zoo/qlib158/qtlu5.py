# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 上分位数 5日
# 简要说明: quantile_0.8(close, 5) / close，5日80%分位价格与当前收盘价的比率。
# 典型用途: 衡量当前价格相对于5日高分位的位置，值小表示价格在近期高位以下。
# ============================================================
"""qlib158 QTLU5: formula = \\mathrm{quantile}_{{0.8}}(\\mathrm{close}, 5) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_qtlu5',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{quantile}_{{0.8}}(\\\\mathrm{close}, 5) / \\\\mathrm{close}',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 5,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 QTLU5 on the supplied OHLCV panel."""
    c = panel['close']
    q = c.rolling(window=5, min_periods=5).quantile(0.8)
    return safe_div(q, c)
