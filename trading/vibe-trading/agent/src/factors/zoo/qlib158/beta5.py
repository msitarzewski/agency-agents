# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: Beta系数 5日
# 简要说明: ts_cov(close, ts_mean(close, 5), 5) / ts_var(close, 5)，个股相对于自身的5日Beta。
# 典型用途: 衡量个股在5日窗口内的弹性/风险，高Beta意味着高波动和高弹性。
# ============================================================
"""qlib158 BETA5: formula = (\\mathrm{close}_t - \\mathrm{close}_{{t-5}}) / (5\\,\\mathrm{close})."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, delta

__alpha_meta__ = {
    'id': 'qlib158_beta5',
    'theme': ['momentum'],
    'formula_latex': '(\\\\mathrm{close}_t - \\\\mathrm{close}_{{t-5}}) / (5\\\\,\\\\mathrm{close})',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 5,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 BETA5 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(delta(c, 5), c) / float(5)
