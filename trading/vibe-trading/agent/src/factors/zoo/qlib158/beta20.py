# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: Beta系数 20日
# 简要说明: ts_cov(close, ts_mean(close, 20), 20) / ts_var(close, 20)，个股相对于自身的20日Beta。
# 典型用途: 衡量个股在20日窗口内的弹性/风险，高Beta意味着高波动和高弹性。
# ============================================================
"""qlib158 BETA20: formula = (\\mathrm{close}_t - \\mathrm{close}_{{t-20}}) / (20\\,\\mathrm{close})."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, delta

__alpha_meta__ = {
    'id': 'qlib158_beta20',
    'theme': ['momentum'],
    'formula_latex': '(\\\\mathrm{close}_t - \\\\mathrm{close}_{{t-20}}) / (20\\\\,\\\\mathrm{close})',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 BETA20 on the supplied OHLCV panel."""
    c = panel['close']
    return safe_div(delta(c, 20), c) / float(20)
