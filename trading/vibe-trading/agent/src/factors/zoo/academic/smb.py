
# ============================================================
# 中文名称: 市值规模因子 (SMB)
# 简要说明: Fama-French三因子模型中的规模因子(Small Minus Big)，做多小市值做空大市值的投资组合收益。
# 典型用途: 捕获小市值公司相对于大市值公司的超额收益，用于规模效应分析。
# ============================================================
"""academic SMB: size factor as inverse log of 60-day average dollar volume.

Reference:
    Fama, E. F., & French, K. R. (1993). "Common risk factors in the returns on
    stocks and bonds." Journal of Financial Economics, 33(1), 3-56.

This is a price-based proxy: the original SMB (Small Minus Big) sorts on market
capitalization, which we do not carry in the OHLCV panel. We use average daily
dollar volume (close * volume) as a liquidity-weighted size proxy — small caps
typically have low dollar volume. Higher z-scores = smaller (illiquid) names.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import ts_mean

__alpha_meta__ = {
    'id': 'academic_smb',
    'nickname': '[PRICE PROXY] FF1993 SMB — small-minus-big via inverse dollar-volume',
    'theme': ['quality'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(-\log(\mathrm{ts\_mean}(\mathrm{volume} \cdot \mathrm{close},\,60) + 1)\bigr)',
    'columns_required': ['close', 'volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
    'notes': (
        '[PRICE PROXY] for the Fama-French (1993) SMB (Small Minus Big) size factor. '
        'The original definition uses market capitalization from book equity data; here '
        'we use the negative log of 60-day average dollar volume (close * volume) as a '
        'liquidity-weighted size proxy, then cross-sectional z-score per date for '
        'long-short ranking. Top z-scores = smaller / less liquid names.'
    ),
}


def _cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Per-row z-score: (x - row_mean) / row_std; zero/NaN std rows -> NaN."""
    mean = df.mean(axis=1, skipna=True)
    std = df.std(axis=1, ddof=1, skipna=True)
    centered = df.sub(mean, axis=0)
    result = centered.div(std.where(std > 0), axis=0)
    return result.replace([np.inf, -np.inf], np.nan)


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return inverse log 60-day dollar-volume z-score per stock."""
    close = panel['close']
    volume = panel['volume']
    dollar_volume = volume * close
    avg = ts_mean(dollar_volume, 60)
    log_size = np.log(avg + 1.0)
    return _cross_sectional_zscore(-log_size)
