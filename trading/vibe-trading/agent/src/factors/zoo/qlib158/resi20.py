# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 残差 20日
# 简要说明: (close - ts_mean(close, 20)) / close，价格相对20日均线的偏离度。
# 典型用途: 衡量价格偏离均线的程度，用于均值回复策略。
# ============================================================
"""qlib158 RESI20: formula = (\\mathrm{close} - \\mathrm{ts\\_mean}(\\mathrm{close}, 20)) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_mean

__alpha_meta__ = {
    'id': 'qlib158_resi20',
    'theme': ['momentum'],
    'formula_latex': '(\\\\mathrm{close} - \\\\mathrm{ts\\\\_mean}(\\\\mathrm{close}, 20)) / \\\\mathrm{close}',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 RESI20 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(c - ts_mean(c, 20), c)
