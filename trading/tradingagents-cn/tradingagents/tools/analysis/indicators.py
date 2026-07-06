from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class IndicatorSpec:
    name: str
    params: Optional[Dict[str, Any]] = None


SUPPORTED = {"ma", "ema", "macd", "rsi", "boll", "atr", "kdj"}


def _require_cols(df: pd.DataFrame, cols: Iterable[str]):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame缺少必要列: {missing}, 现有列: {list(df.columns)[:10]}...")


def ma(close: pd.Series, n: int, min_periods: int = None) -> pd.Series:
    """
    计算移动平均线（Moving Average）

    Args:
        close: 收盘价序列
        n: 周期
        min_periods: 最小周期数，默认为1（允许前期数据不足时也计算）

    Returns:
        移动平均线序列
    """
    if min_periods is None:
        min_periods = 1  # 默认为1，与现有代码保持一致
    return close.rolling(window=int(n), min_periods=min_periods).mean()


def ema(close: pd.Series, n: int) -> pd.Series:
    """
    计算指数移动平均线（Exponential Moving Average）

    Args:
        close: 收盘价序列
        n: 周期

    Returns:
        指数移动平均线序列
    """
    return close.ewm(span=int(n), adjust=False).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    计算MACD指标（Moving Average Convergence Divergence）

    Args:
        close: 收盘价序列
        fast: 快线周期，默认12
        slow: 慢线周期，默认26
        signal: 信号线周期，默认9

    Returns:
        包含 dif, dea, macd_hist 的 DataFrame
        - dif: 快线与慢线的差值（DIF）
        - dea: DIF的信号线（DEA）
        - macd_hist: MACD柱状图（DIF - DEA）
    """
    dif = ema(close, fast) - ema(close, slow)
    dea = dif.ewm(span=int(signal), adjust=False).mean()
    hist = dif - dea
    return pd.DataFrame({"dif": dif, "dea": dea, "macd_hist": hist})


def rsi(close: pd.Series, n: int = 14, method: str = 'ema') -> pd.Series:
    """
    计算RSI指标（Relative Strength Index）

    Args:
        close: 收盘价序列
        n: 周期，默认14
        method: 计算方法
            - 'ema': 指数移动平均（国际标准，Wilder's方法）
            - 'sma': 简单移动平均
            - 'china': 中国式SMA（同花顺/通达信风格）

    Returns:
        RSI序列（0-100）

    说明：
        - 'ema': 使用 ewm(alpha=1/n, adjust=False)，适用于国际市场
        - 'sma': 使用 rolling(window=n).mean()，简单移动平均
        - 'china': 使用 ewm(com=n-1, adjust=True)，与同花顺/通达信一致
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    if method == 'ema':
        # 国际标准：Wilder's指数移动平均
        avg_gain = gain.ewm(alpha=1 / float(n), adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / float(n), adjust=False).mean()
    elif method == 'sma':
        # 简单移动平均
        avg_gain = gain.rolling(window=int(n), min_periods=1).mean()
        avg_loss = loss.rolling(window=int(n), min_periods=1).mean()
    elif method == 'china':
        # 中国式SMA：同花顺/通达信风格
        # SMA(X, N, 1) = ewm(com=N-1, adjust=True).mean()
        # 参考：https://blog.csdn.net/u011218867/article/details/117427927
        avg_gain = gain.ewm(com=int(n) - 1, adjust=True).mean()
        avg_loss = loss.ewm(com=int(n) - 1, adjust=True).mean()
    else:
        raise ValueError(f"不支持的RSI计算方法: {method}，支持的方法: 'ema', 'sma', 'china'")

    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val


def boll(close: pd.Series, n: int = 20, k: float = 2.0, min_periods: int = None) -> pd.DataFrame:
    """
    计算布林带指标（Bollinger Bands）

    Args:
        close: 收盘价序列
        n: 周期，默认20
        k: 标准差倍数，默认2.0
        min_periods: 最小周期数，默认为1（允许前期数据不足时也计算）

    Returns:
        包含 boll_mid, boll_upper, boll_lower 的 DataFrame
        - boll_mid: 中轨（n日移动平均）
        - boll_upper: 上轨（中轨 + k倍标准差）
        - boll_lower: 下轨（中轨 - k倍标准差）
    """
    if min_periods is None:
        min_periods = 1  # 默认为1，与现有代码保持一致
    mid = close.rolling(window=int(n), min_periods=min_periods).mean()
    std = close.rolling(window=int(n), min_periods=min_periods).std()
    upper = mid + k * std
    lower = mid - k * std
    return pd.DataFrame({"boll_mid": mid, "boll_upper": upper, "boll_lower": lower})


def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=int(n), min_periods=int(n)).mean()


def kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    lowest_low = low.rolling(window=int(n), min_periods=int(n)).min()
    highest_high = high.rolling(window=int(n), min_periods=int(n)).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    # 处理除零与起始NaN
    rsv = rsv.replace([np.inf, -np.inf], np.nan)

    # 按经典公式递推（初始化 50）
    k = pd.Series(np.nan, index=close.index)
    d = pd.Series(np.nan, index=close.index)
    alpha_k = 1 / float(m1)
    alpha_d = 1 / float(m2)
    last_k = 50.0
    last_d = 50.0
    for i in range(len(close)):
        rv = rsv.iloc[i]
        if np.isnan(rv):
            k.iloc[i] = np.nan
            d.iloc[i] = np.nan
            continue
        curr_k = (1 - alpha_k) * last_k + alpha_k * rv
        curr_d = (1 - alpha_d) * last_d + alpha_d * curr_k
        k.iloc[i] = curr_k
        d.iloc[i] = curr_d
        last_k, last_d = curr_k, curr_d
    j = 3 * k - 2 * d
    return pd.DataFrame({"kdj_k": k, "kdj_d": d, "kdj_j": j})


def compute_indicator(df: pd.DataFrame, spec: IndicatorSpec) -> pd.DataFrame:
    name = spec.name.lower()
    params = spec.params or {}
    out = df.copy()

    if name == "ma":
        _require_cols(df, ["close"])
        n = int(params.get("n", params.get("period", 20)))
        out[f"ma{n}"] = ma(df["close"], n)
        return out

    if name == "ema":
        _require_cols(df, ["close"])
        n = int(params.get("n", params.get("period", 20)))
        out[f"ema{n}"] = ema(df["close"], n)
        return out

    if name == "macd":
        _require_cols(df, ["close"])
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))
        macd_df = macd(df["close"], fast=fast, slow=slow, signal=signal)
        for c in macd_df.columns:
            out[c] = macd_df[c]
        return out

    if name == "rsi":
        _require_cols(df, ["close"])
        n = int(params.get("n", params.get("period", 14)))
        out[f"rsi{n}"] = rsi(df["close"], n)
        return out

    if name == "boll":
        _require_cols(df, ["close"])
        n = int(params.get("n", 20))
        k = float(params.get("k", 2.0))
        boll_df = boll(df["close"], n=n, k=k)
        for c in boll_df.columns:
            out[c] = boll_df[c]
        return out

    if name == "atr":
        _require_cols(df, ["high", "low", "close"])
        n = int(params.get("n", 14))
        out[f"atr{n}"] = atr(df["high"], df["low"], df["close"], n=n)
        return out

    if name == "kdj":
        _require_cols(df, ["high", "low", "close"])
        n = int(params.get("n", 9))
        m1 = int(params.get("m1", 3))
        m2 = int(params.get("m2", 3))
        kdj_df = kdj(df["high"], df["low"], df["close"], n=n, m1=m1, m2=m2)
        for c in kdj_df.columns:
            out[c] = kdj_df[c]
        return out

    raise ValueError(f"不支持的指标: {name}")


def compute_many(df: pd.DataFrame, specs: List[IndicatorSpec]) -> pd.DataFrame:
    if not specs:
        return df.copy()
    # 粗略去重（按 name+sorted(params)）
    def key(s: IndicatorSpec):
        p = s.params or {}
        items = tuple(sorted(p.items()))
        return (s.name.lower(), items)

    unique_specs: List[IndicatorSpec] = []
    seen = set()
    for s in specs:
        k = key(s)
        if k not in seen:
            seen.add(k)
            unique_specs.append(s)

    out = df.copy()
    for s in unique_specs:
        out = compute_indicator(out, s)
    return out


def last_values(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
    if df.empty:
        return {c: None for c in columns}
    last = df.iloc[-1]
    return {c: (None if c not in df.columns else (None if pd.isna(last.get(c)) else last.get(c))) for c in columns}


def add_all_indicators(df: pd.DataFrame, close_col: str = 'close',
                       high_col: str = 'high', low_col: str = 'low',
                       rsi_style: str = 'international') -> pd.DataFrame:
    """
    为DataFrame添加所有常用技术指标

    这是一个统一的技术指标计算函数，用于替代各个数据源模块中重复的计算代码。

    Args:
        df: 包含价格数据的DataFrame
        close_col: 收盘价列名，默认'close'
        high_col: 最高价列名，默认'high'（预留，暂未使用）
        low_col: 最低价列名，默认'low'（预留，暂未使用）
        rsi_style: RSI计算风格
            - 'international': 国际标准（RSI14，使用EMA）
            - 'china': 中国风格（RSI6/12/24 + RSI14，使用中国式SMA）

    Returns:
        添加了技术指标列的DataFrame（原地修改）

    添加的指标列：
        - ma5, ma10, ma20, ma60: 移动平均线
        - rsi: RSI指标（14日，国际标准）
        - rsi6, rsi12, rsi24: RSI指标（中国风格，仅当 rsi_style='china' 时）
        - rsi14: RSI指标（14日，简单移动平均，仅当 rsi_style='china' 时）
        - macd_dif, macd_dea, macd: MACD指标
        - boll_mid, boll_upper, boll_lower: 布林带

    示例：
        >>> df = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
        >>> df = add_all_indicators(df)
        >>> print(df[['close', 'ma5', 'rsi']].tail())
        >>>
        >>> # 中国风格
        >>> df = add_all_indicators(df, rsi_style='china')
        >>> print(df[['close', 'rsi6', 'rsi12', 'rsi24']].tail())
    """
    # 检查必要的列
    if close_col not in df.columns:
        raise ValueError(f"DataFrame缺少收盘价列: {close_col}")

    # 计算移动平均线（MA5, MA10, MA20, MA60）
    df['ma5'] = ma(df[close_col], 5, min_periods=1)
    df['ma10'] = ma(df[close_col], 10, min_periods=1)
    df['ma20'] = ma(df[close_col], 20, min_periods=1)
    df['ma60'] = ma(df[close_col], 60, min_periods=1)

    # 计算RSI指标
    if rsi_style == 'china':
        # 中国风格：RSI6, RSI12, RSI24（使用中国式SMA）
        df['rsi6'] = rsi(df[close_col], 6, method='china')
        df['rsi12'] = rsi(df[close_col], 12, method='china')
        df['rsi24'] = rsi(df[close_col], 24, method='china')
        # 保留RSI14作为国际标准参考（使用简单移动平均）
        df['rsi14'] = rsi(df[close_col], 14, method='sma')
        # 为了兼容性，也添加 'rsi' 列（指向 rsi12）
        df['rsi'] = df['rsi12']
    else:
        # 国际标准：RSI14（使用EMA）
        df['rsi'] = rsi(df[close_col], 14, method='ema')

    # 计算MACD
    macd_df = macd(df[close_col], fast=12, slow=26, signal=9)
    df['macd_dif'] = macd_df['dif']
    df['macd_dea'] = macd_df['dea']
    df['macd'] = macd_df['macd_hist'] * 2  # 注意：这里乘以2是为了与通达信/同花顺保持一致

    # 计算布林带（20日，2倍标准差）
    boll_df = boll(df[close_col], n=20, k=2.0, min_periods=1)
    df['boll_mid'] = boll_df['boll_mid']
    df['boll_upper'] = boll_df['boll_upper']
    df['boll_lower'] = boll_df['boll_lower']

    return df

