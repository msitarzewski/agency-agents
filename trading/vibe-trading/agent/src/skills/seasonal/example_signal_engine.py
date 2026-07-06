"""季节性/日历效应策略信号引擎。

基于月份效应、周内效应等时间规律生成交易信号。
纯 pandas 实现，适用于任何 OHLCV 数据。
"""

from typing import Dict, List

import numpy as np
import pandas as pd


class SignalEngine:
    """季节性日历效应信号引擎。

    根据月份和周内效应生成做多/做空信号。

    Attributes:
        bullish_months: 看多月份列表。
        bearish_months: 看空月份列表。
        use_weekday: 是否启用周内效应。
        bullish_weekdays: 看多星期列表。
        bearish_weekdays: 看空星期列表。

    Example:
        >>> engine = SignalEngine(bullish_months=[1, 2, 3], bearish_months=[5, 6, 7, 8, 9])
        >>> signals = engine.generate({"000001.SZ": df})
    """

    def __init__(
        self,
        bullish_months: List[int] = None,
        bearish_months: List[int] = None,
        use_weekday: bool = False,
        bullish_weekdays: List[int] = None,
        bearish_weekdays: List[int] = None,
    ):
        """初始化季节性引擎。

        Args:
            bullish_months: 看多月份（1-12），默认 [1,2,3,11,12]。
            bearish_months: 看空月份（1-12），默认 [5,6,7,8,9]。
            use_weekday: 是否启用周内效应。
            bullish_weekdays: 看多星期（0=周一, 4=周五），默认 [4]。
            bearish_weekdays: 看空星期，默认 [0]。
        """
        self.bullish_months = bullish_months or [1, 2, 3, 11, 12]
        self.bearish_months = bearish_months or [5, 6, 7, 8, 9]
        self.use_weekday = use_weekday
        self.bullish_weekdays = bullish_weekdays or [4]
        self.bearish_weekdays = bearish_weekdays or [0]

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """根据日历效应生成交易信号。

        Args:
            data_map: 标的代码到 OHLCV DataFrame 的映射。

        Returns:
            标的代码到信号 Series 的映射（1=做多, -1=做空, 0=观望）。
        """
        result = {}
        for code, df in data_map.items():
            result[code] = self._generate_one(df)
        return result

    def _generate_one(self, df: pd.DataFrame) -> pd.Series:
        """对单个标的生成日历信号。

        Args:
            df: OHLCV DataFrame，index 为 DatetimeIndex。

        Returns:
            信号 Series。
        """
        idx = df.index
        month = idx.month
        signal = pd.Series(0, index=idx)

        # 月份效应
        signal[month.isin(self.bullish_months)] = 1
        signal[month.isin(self.bearish_months)] = -1

        # 周内效应（叠加模式：双重确认）
        if self.use_weekday:
            weekday = idx.weekday
            weekday_signal = pd.Series(0, index=idx)
            weekday_signal[weekday.isin(self.bullish_weekdays)] = 1
            weekday_signal[weekday.isin(self.bearish_weekdays)] = -1

            # 双重确认：月份和周内方向一致时才有信号
            combined = signal + weekday_signal
            signal = pd.Series(0, index=idx)
            signal[combined >= 2] = 1    # 月份看多 + 周内看多
            signal[combined <= -2] = -1  # 月份看空 + 周内看空

        return signal.fillna(0).astype(int)


if __name__ == "__main__":
    import requests

    def _fetch_okx(inst_id: str, bar: str = "1D", limit: int = 300) -> pd.DataFrame:
        """从 OKX API 获取 K 线数据。

        Args:
            inst_id: 交易对标识，如 "BTC-USDT"。
            bar: K 线周期。
            limit: 获取根数。

        Returns:
            OHLCV DataFrame。
        """
        resp = requests.get(
            "https://www.okx.com/api/v5/market/candles",
            params={"instId": inst_id, "bar": bar, "limit": str(limit)},
        )
        candles = resp.json()["data"]
        columns = ["ts", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm"]
        df = pd.DataFrame(reversed(candles), columns=columns)
        df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms")
        df = df.set_index("ts")
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)
        df["volume"] = df["vol"].astype(float)
        return df

    symbols = ["BTC-USDT", "ETH-USDT"]
    data_map = {}
    for sym in symbols:
        print(f"Fetching {sym} ...")
        data_map[sym] = _fetch_okx(sym, bar="1D", limit=300)

    engine = SignalEngine(
        bullish_months=[1, 2, 3, 10, 11, 12],
        bearish_months=[5, 6, 7, 8, 9],
    )
    signals = engine.generate(data_map)

    for sym in symbols:
        sig = signals[sym]
        print(f"\n{sym} ({len(sig)} bars)")
        print(f"  Bullish days: {(sig == 1).sum()}")
        print(f"  Bearish days: {(sig == -1).sum()}")
        print(f"  Neutral days: {(sig == 0).sum()}")
