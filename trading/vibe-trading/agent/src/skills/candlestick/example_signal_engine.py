"""K线形态识别信号引擎。

纯 pandas 向量化实现 15 种经典蜡烛图形态识别：
- 单根形态 (5): 锤子线、倒锤子、射击之星、十字星、纺锤线
- 双根形态 (6): 看涨/看跌吞没、看涨/看跌孕线、刺穿线、乌云盖顶
- 三根形态 (4): 晨星、暮星、三白兵、三乌鸦

信号约定: 1=做多, -1=做空, 0=观望
"""

from typing import Dict

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 向量化辅助函数
# ---------------------------------------------------------------------------


def _body(o: pd.Series, c: pd.Series) -> pd.Series:
    """实体长度（绝对值）。

    Args:
        o: 开盘价序列。
        c: 收盘价序列。

    Returns:
        每根K线的实体长度。
    """
    return (c - o).abs()


def _range(h: pd.Series, l: pd.Series) -> pd.Series:
    """K线振幅（最高 - 最低）。

    Args:
        h: 最高价序列。
        l: 最低价序列。

    Returns:
        每根K线的振幅。
    """
    return h - l


def _upper_shadow(o: pd.Series, c: pd.Series, h: pd.Series) -> pd.Series:
    """上影线长度。

    Args:
        o: 开盘价序列。
        c: 收盘价序列。
        h: 最高价序列。

    Returns:
        每根K线的上影线长度。
    """
    return h - pd.concat([o, c], axis=1).max(axis=1)


def _lower_shadow(o: pd.Series, c: pd.Series, l: pd.Series) -> pd.Series:
    """下影线长度。

    Args:
        o: 开盘价序列。
        c: 收盘价序列。
        l: 最低价序列。

    Returns:
        每根K线的下影线长度。
    """
    return pd.concat([o, c], axis=1).min(axis=1) - l


# ---------------------------------------------------------------------------
# 信号引擎
# ---------------------------------------------------------------------------


class SignalEngine:
    """K线形态识别信号引擎。

    纯向量化实现，通过看涨/看跌形态评分生成综合交易信号。

    Attributes:
        body_pct: 十字星判定阈值，实体占振幅比例。
        shadow_ratio: 影线与实体的长度比阈值。
    """

    def __init__(self, body_pct: float = 0.1, shadow_ratio: float = 2.0):
        """初始化K线形态信号引擎。

        Args:
            body_pct: 十字星实体/振幅比阈值，默认 0.1。
            shadow_ratio: 影线与实体长度比，默认 2.0。
        """
        self.body_pct = body_pct
        self.shadow_ratio = shadow_ratio

    # -----------------------------------------------------------------------
    # 单根形态
    # -----------------------------------------------------------------------

    def _detect_hammer(self, o: pd.Series, h: pd.Series,
                       l: pd.Series, c: pd.Series) -> pd.Series:
        """检测锤子线（Hammer）—— 看涨。

        条件：下影线 >= shadow_ratio * 实体，上影线 < 实体，实体 > 0，振幅 > 0。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=检测到锤子线，0=未检测到。
        """
        bd = _body(o, c)
        rng = _range(h, l)
        ls = _lower_shadow(o, c, l)
        us = _upper_shadow(o, c, h)
        cond = (ls >= self.shadow_ratio * bd) & (us < bd) & (bd > 0) & (rng > 0)
        return cond.astype(int)

    def _detect_inverted_hammer(self, o: pd.Series, h: pd.Series,
                                l: pd.Series, c: pd.Series) -> pd.Series:
        """检测倒锤子（Inverted Hammer）—— 看涨。

        条件：上影线 >= shadow_ratio * 实体，下影线 < 实体。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=检测到倒锤子，0=未检测到。
        """
        bd = _body(o, c)
        us = _upper_shadow(o, c, h)
        ls = _lower_shadow(o, c, l)
        cond = (us >= self.shadow_ratio * bd) & (ls < bd) & (bd > 0)
        return cond.astype(int)

    def _detect_shooting_star(self, o: pd.Series, h: pd.Series,
                              l: pd.Series, c: pd.Series) -> pd.Series:
        """检测射击之星（Shooting Star）—— 看跌。

        形态与倒锤子相同，但需出现在上涨趋势之后（前一根收盘 > 前两根收盘）。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：-1=检测到射击之星，0=未检测到。
        """
        bd = _body(o, c)
        us = _upper_shadow(o, c, h)
        ls = _lower_shadow(o, c, l)
        uptrend = c.shift(1) > c.shift(2)
        cond = (us >= self.shadow_ratio * bd) & (ls < bd) & (bd > 0) & uptrend
        return -(cond.astype(int))

    def _detect_doji(self, o: pd.Series, h: pd.Series,
                     l: pd.Series, c: pd.Series) -> pd.Series:
        """检测十字星（Doji）—— 中性（信号为0）。

        条件：实体/振幅 < body_pct 且振幅 > 0。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：始终为0（中性形态，不产生方向信号）。
        """
        bd = _body(o, c)
        rng = _range(h, l)
        safe_rng = rng.replace(0, np.nan)
        cond = (bd / safe_rng < self.body_pct) & (rng > 0)
        # 十字星为中性，不贡献方向分数
        return pd.Series(0, index=o.index)

    def _detect_spinning_top(self, o: pd.Series, h: pd.Series,
                             l: pd.Series, c: pd.Series) -> pd.Series:
        """检测纺锤线（Spinning Top）—— 中性（信号为0）。

        条件：实体/振幅 < 0.3，上影线 > 实体，下影线 > 实体，且不是十字星。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：始终为0（中性形态，不产生方向信号）。
        """
        bd = _body(o, c)
        rng = _range(h, l)
        safe_rng = rng.replace(0, np.nan)
        us = _upper_shadow(o, c, h)
        ls = _lower_shadow(o, c, l)
        is_doji = (bd / safe_rng < self.body_pct) & (rng > 0)
        cond = ((bd / safe_rng < 0.3) & (us > bd) & (ls > bd)
                & (rng > 0) & ~is_doji)
        # 纺锤线为中性，不贡献方向分数
        return pd.Series(0, index=o.index)

    # -----------------------------------------------------------------------
    # 双根形态
    # -----------------------------------------------------------------------

    def _detect_engulfing(self, o: pd.Series, h: pd.Series,
                          l: pd.Series, c: pd.Series) -> pd.Series:
        """检测吞没形态（Engulfing）。

        看涨吞没：前一根看跌，当前看涨，当前实体包含前一根实体。+1
        看跌吞没：前一根看涨，当前看跌，当前实体包含前一根实体。-1

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=看涨吞没，-1=看跌吞没，0=无。
        """
        o1, c1 = o.shift(1), c.shift(1)
        prev_bear = c1 < o1
        prev_bull = c1 > o1
        curr_bull = c > o
        curr_bear = c < o

        bullish = prev_bear & curr_bull & (c >= o1) & (o <= c1)
        bearish = prev_bull & curr_bear & (c <= o1) & (o >= c1)

        sig = pd.Series(0, index=o.index)
        sig[bullish] = 1
        sig[bearish] = -1
        return sig

    def _detect_harami(self, o: pd.Series, h: pd.Series,
                       l: pd.Series, c: pd.Series) -> pd.Series:
        """检测孕线形态（Harami）。

        看涨孕线：前一根看跌大实体，当前小实体被包含在前一根实体内。+1
        看跌孕线：前一根看涨大实体，当前小实体被包含在前一根实体内。-1

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=看涨孕线，-1=看跌孕线，0=无。
        """
        bd = _body(o, c)
        o1, c1 = o.shift(1), c.shift(1)
        bd1 = _body(o1, c1)

        prev_bear = c1 < o1
        prev_bull = c1 > o1
        large_prev = bd1 > bd

        # 当前实体完全在前一根实体内
        prev_top = pd.concat([o1, c1], axis=1).max(axis=1)
        prev_bot = pd.concat([o1, c1], axis=1).min(axis=1)
        curr_top = pd.concat([o, c], axis=1).max(axis=1)
        curr_bot = pd.concat([o, c], axis=1).min(axis=1)
        contained = (curr_top <= prev_top) & (curr_bot >= prev_bot)

        bullish = prev_bear & large_prev & contained
        bearish = prev_bull & large_prev & contained

        sig = pd.Series(0, index=o.index)
        sig[bullish] = 1
        sig[bearish] = -1
        return sig

    def _detect_piercing_line(self, o: pd.Series, h: pd.Series,
                              l: pd.Series, c: pd.Series) -> pd.Series:
        """检测刺穿线（Piercing Line）—— 看涨。

        条件：前一根看跌，当前开盘低于前一根最低价，当前收盘高于前一根实体中点。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=检测到刺穿线，0=无。
        """
        o1, c1, l1 = o.shift(1), c.shift(1), l.shift(1)
        prev_bear = c1 < o1
        curr_bull = c > o
        opens_below = o < l1
        mid1 = (o1 + c1) / 2
        closes_above_mid = c > mid1

        cond = prev_bear & curr_bull & opens_below & closes_above_mid
        return cond.astype(int)

    def _detect_dark_cloud(self, o: pd.Series, h: pd.Series,
                           l: pd.Series, c: pd.Series) -> pd.Series:
        """检测乌云盖顶（Dark Cloud Cover）—— 看跌。

        条件：前一根看涨，当前开盘高于前一根最高价，当前收盘低于前一根实体中点。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：-1=检测到乌云盖顶，0=无。
        """
        o1, c1, h1 = o.shift(1), c.shift(1), h.shift(1)
        prev_bull = c1 > o1
        curr_bear = c < o
        opens_above = o > h1
        mid1 = (o1 + c1) / 2
        closes_below_mid = c < mid1

        cond = prev_bull & curr_bear & opens_above & closes_below_mid
        return -(cond.astype(int))

    # -----------------------------------------------------------------------
    # 三根形态
    # -----------------------------------------------------------------------

    def _detect_morning_star(self, o: pd.Series, h: pd.Series,
                             l: pd.Series, c: pd.Series) -> pd.Series:
        """检测晨星（Morning Star）—— 看涨。

        条件：
        - Day1 看跌
        - Day2 小实体且向下跳空（Day2最高 < Day1最低）
        - Day3 看涨且收盘高于 Day1 实体中点

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=检测到晨星，0=无。
        """
        o1, c1 = o.shift(2), c.shift(2)  # Day1
        o2, c2, h2 = o.shift(1), c.shift(1), h.shift(1)  # Day2
        bd2 = _body(o2, c2)
        rng2 = _range(h.shift(1), l.shift(1))
        safe_rng2 = rng2.replace(0, np.nan)

        day1_bear = c1 < o1
        day2_small = bd2 / safe_rng2 < 0.3
        day2_gap = h2 < l.shift(2)  # Day2 high < Day1 low (gap down)
        day3_bull = c > o
        mid1 = (o1 + c1) / 2
        day3_above_mid = c > mid1

        cond = day1_bear & day2_small & day2_gap & day3_bull & day3_above_mid
        return cond.astype(int).fillna(0).astype(int)

    def _detect_evening_star(self, o: pd.Series, h: pd.Series,
                             l: pd.Series, c: pd.Series) -> pd.Series:
        """检测暮星（Evening Star）—— 看跌。

        条件：
        - Day1 看涨
        - Day2 小实体且向上跳空（Day2最低 > Day1最高）
        - Day3 看跌且收盘低于 Day1 实体中点

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：-1=检测到暮星，0=无。
        """
        o1, c1 = o.shift(2), c.shift(2)  # Day1
        o2, c2, l2 = o.shift(1), c.shift(1), l.shift(1)  # Day2
        bd2 = _body(o2, c2)
        rng2 = _range(h.shift(1), l.shift(1))
        safe_rng2 = rng2.replace(0, np.nan)

        day1_bull = c1 > o1
        day2_small = bd2 / safe_rng2 < 0.3
        day2_gap = l2 > h.shift(2)  # Day2 low > Day1 high (gap up)
        day3_bear = c < o
        mid1 = (o1 + c1) / 2
        day3_below_mid = c < mid1

        cond = day1_bull & day2_small & day2_gap & day3_bear & day3_below_mid
        return -(cond.astype(int).fillna(0).astype(int))

    def _detect_three_white_soldiers(self, o: pd.Series, h: pd.Series,
                                     l: pd.Series, c: pd.Series) -> pd.Series:
        """检测三白兵（Three White Soldiers）—— 看涨。

        条件：连续3根阳线，每根收盘递增，每根开盘在前一根实体内。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：1=检测到三白兵，0=无。
        """
        o1, c1 = o.shift(2), c.shift(2)  # Day1
        o2, c2 = o.shift(1), c.shift(1)  # Day2

        bull1 = c1 > o1
        bull2 = c2 > o2
        bull3 = c > o

        close_up = (c2 > c1) & (c > c2)

        # 每根开盘在前一根实体内
        open2_in = (o2 >= o1) & (o2 <= c1)
        open3_in = (o >= o2) & (o <= c2)

        cond = bull1 & bull2 & bull3 & close_up & open2_in & open3_in
        return cond.astype(int).fillna(0).astype(int)

    def _detect_three_black_crows(self, o: pd.Series, h: pd.Series,
                                  l: pd.Series, c: pd.Series) -> pd.Series:
        """检测三乌鸦（Three Black Crows）—— 看跌。

        条件：连续3根阴线，每根收盘递减，每根开盘在前一根实体内。

        Args:
            o: 开盘价。
            h: 最高价。
            l: 最低价。
            c: 收盘价。

        Returns:
            信号序列：-1=检测到三乌鸦，0=无。
        """
        o1, c1 = o.shift(2), c.shift(2)  # Day1
        o2, c2 = o.shift(1), c.shift(1)  # Day2

        bear1 = c1 < o1
        bear2 = c2 < o2
        bear3 = c < o

        close_dn = (c2 < c1) & (c < c2)

        # 每根开盘在前一根实体内（阴线实体：open在上，close在下）
        open2_in = (o2 <= o1) & (o2 >= c1)
        open3_in = (o <= o2) & (o >= c2)

        cond = bear1 & bear2 & bear3 & close_dn & open2_in & open3_in
        return -(cond.astype(int).fillna(0).astype(int))

    # -----------------------------------------------------------------------
    # 主入口
    # -----------------------------------------------------------------------

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """对每个标的运行全部形态检测，汇总评分生成信号。

        Args:
            data_map: 标的代码到 OHLCV DataFrame 的映射。
                DataFrame 需包含 open/high/low/close 列，index 为 datetime。

        Returns:
            标的代码到信号 Series 的映射（1=做多, -1=做空, 0=观望）。

        Example:
            >>> engine = SignalEngine()
            >>> signals = engine.generate({"BTC-USDT": df})
            >>> signals["BTC-USDT"].value_counts()
        """
        result = {}
        for code, df in data_map.items():
            o = df["open"]
            h = df["high"]
            l = df["low"]
            c = df["close"]

            # 收集所有形态的信号分数
            scores = pd.DataFrame(index=df.index)

            # 单根形态
            scores["hammer"] = self._detect_hammer(o, h, l, c)
            scores["inv_hammer"] = self._detect_inverted_hammer(o, h, l, c)
            scores["shooting_star"] = self._detect_shooting_star(o, h, l, c)
            scores["doji"] = self._detect_doji(o, h, l, c)
            scores["spinning_top"] = self._detect_spinning_top(o, h, l, c)

            # 双根形态
            scores["engulfing"] = self._detect_engulfing(o, h, l, c)
            scores["harami"] = self._detect_harami(o, h, l, c)
            scores["piercing"] = self._detect_piercing_line(o, h, l, c)
            scores["dark_cloud"] = self._detect_dark_cloud(o, h, l, c)

            # 三根形态
            scores["morning_star"] = self._detect_morning_star(o, h, l, c)
            scores["evening_star"] = self._detect_evening_star(o, h, l, c)
            scores["three_white"] = self._detect_three_white_soldiers(o, h, l, c)
            scores["three_black"] = self._detect_three_black_crows(o, h, l, c)

            total = scores.sum(axis=1)
            result[code] = pd.Series(
                np.sign(total).astype(int), index=df.index, name="signal"
            )
        return result


# ---------------------------------------------------------------------------
# 数据获取
# ---------------------------------------------------------------------------


def _fetch_okx(inst_id: str, bar: str = "1D", limit: int = 300) -> pd.DataFrame:
    """从 OKX 获取K线数据。

    Args:
        inst_id: 交易对，如 "BTC-USDT"。
        bar: K线周期，默认 "1D"。
        limit: 获取数量，默认 300。

    Returns:
        包含 open/high/low/close/volume 列的 DataFrame，index 为 datetime。

    Raises:
        KeyError: 当 API 返回格式异常时。
    """
    import requests

    resp = requests.get("https://www.okx.com/api/v5/market/candles", params={
        "instId": inst_id, "bar": bar, "limit": str(limit)
    })
    candles = resp.json()["data"]
    columns = ["ts", "open", "high", "low", "close",
               "vol", "volCcy", "volCcyQuote", "confirm"]
    df = pd.DataFrame(reversed(candles), columns=columns)
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms")
    df = df.set_index("ts")
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df["vol"].astype(float)
    return df


if __name__ == "__main__":
    symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    data_map = {}
    for sym in symbols:
        print(f"Fetching {sym} ...")
        data_map[sym] = _fetch_okx(sym)

    engine = SignalEngine()
    signals = engine.generate(data_map)

    for sym in symbols:
        sig = signals[sym]
        buys = (sig == 1).sum()
        sells = (sig == -1).sum()
        holds = (sig == 0).sum()
        print(f"\n{sym} ({len(sig)} bars)")
        print(f"  Long:  {buys}")
        print(f"  Short: {sells}")
        print(f"  Hold:  {holds}")
        # 显示最近的非零信号
        nonzero = sig[sig != 0]
        if len(nonzero) > 0:
            last = nonzero.iloc[-1]
            label = "Long" if last == 1 else "Short"
            print(f"  Latest signal: {label} @ {nonzero.index[-1]:%Y-%m-%d}")
