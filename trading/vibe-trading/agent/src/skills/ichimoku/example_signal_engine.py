"""一目均衡表（Ichimoku Kinko Hyo）信号引擎。

五线系统：转换线/基准线交叉触发，云带位置+方向三重过滤。
纯 pandas 实现，无外部技术分析库依赖。
"""

from typing import Dict, Optional

import pandas as pd


class SignalEngine:
    """一目均衡表信号引擎。

    通过 TK 交叉事件触发，三重过滤生成高质量交易信号：
    1. 转换线/基准线金叉或死叉（触发条件）
    2. 价格相对云带的位置（方向确认）
    3. 云带自身方向（趋势确认）

    Attributes:
        tenkan_period: 转换线周期。
        kijun_period: 基准线周期。
        senkou_b_period: 先行带B周期。
        displacement: 前移/后移周期。

    Example:
        >>> engine = SignalEngine()
        >>> signals = engine.generate({"BTC-USDT": df})
        >>> signals["BTC-USDT"].value_counts()
    """

    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26,
    ):
        """初始化一目均衡表信号引擎。

        Args:
            tenkan_period: 转换线周期，默认9。
            kijun_period: 基准线周期，默认26。
            senkou_b_period: 先行带B周期，默认52。
            displacement: 前移/后移周期，默认26。
        """
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.displacement = displacement

    def _donchian_mid(
        self, high: pd.Series, low: pd.Series, period: int
    ) -> pd.Series:
        """计算 Donchian 通道中线。

        公式: (highest_high(period) + lowest_low(period)) / 2

        Args:
            high: 最高价序列。
            low: 最低价序列。
            period: 回看周期。

        Returns:
            Donchian 通道中线序列。
        """
        return (high.rolling(period).max() + low.rolling(period).min()) / 2

    def generate(
        self, data_map: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.Series]:
        """根据一目均衡表五线系统生成交易信号。

        Args:
            data_map: 标的代码到 OHLCV DataFrame 的映射。
                DataFrame 需包含 open/high/low/close 列，index 为 datetime。

        Returns:
            标的代码到信号 Series 的映射（1=做多, -1=做空, 0=观望）。
        """
        result = {}
        warmup = self.senkou_b_period + self.displacement

        for symbol, df in data_map.items():
            signal = pd.Series(0, index=df.index, dtype=int)

            if len(df) < warmup:
                result[symbol] = signal
                continue

            high = df["high"]
            low = df["low"]
            close = df["close"]

            # --- 五线计算 ---
            tenkan = self._donchian_mid(high, low, self.tenkan_period)
            kijun = self._donchian_mid(high, low, self.kijun_period)
            span_a = ((tenkan + kijun) / 2).shift(self.displacement)
            span_b = self._donchian_mid(
                high, low, self.senkou_b_period
            ).shift(self.displacement)
            # chikou = close.shift(-self.displacement)  # 不参与信号计算

            # --- TK 交叉检测 ---
            tk_cross_up = (tenkan > kijun) & (
                tenkan.shift(1) <= kijun.shift(1)
            )
            tk_cross_down = (tenkan < kijun) & (
                tenkan.shift(1) >= kijun.shift(1)
            )

            # --- 云带位置 ---
            cloud_top = pd.concat([span_a, span_b], axis=1).max(axis=1)
            cloud_bottom = pd.concat([span_a, span_b], axis=1).min(axis=1)
            above_cloud = close > cloud_top
            below_cloud = close < cloud_bottom

            # --- 云带方向 ---
            bullish_cloud = span_a > span_b
            bearish_cloud = span_a < span_b

            # --- 三重过滤信号 ---
            buy = tk_cross_up & above_cloud & bullish_cloud
            sell = tk_cross_down & below_cloud & bearish_cloud
            signal = buy.astype(int) - sell.astype(int)

            result[symbol] = signal

        return result


def _fetch_okx(
    inst_id: str, bar: str = "1D", limit: int = 300
) -> pd.DataFrame:
    """从 OKX API 获取K线数据。

    Args:
        inst_id: 交易对标识，如 "BTC-USDT"。
        bar: K线周期，默认 "1D"。
        limit: 获取数量，默认 300。

    Returns:
        OHLCV DataFrame，index 为 datetime。

    Raises:
        KeyError: API 返回格式异常时。
    """
    import requests

    resp = requests.get(
        "https://www.okx.com/api/v5/market/candles",
        params={"instId": inst_id, "bar": bar, "limit": str(limit)},
    )
    candles = resp.json()["data"]
    columns = [
        "ts", "open", "high", "low", "close",
        "vol", "volCcy", "volCcyQuote", "confirm",
    ]
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

    print("=== 一目均衡表信号引擎 ===\n")

    for sym in symbols:
        print(f"获取 {sym} 数据...")
        data_map[sym] = _fetch_okx(sym, bar="1D", limit=300)
        print(f"  {len(data_map[sym])} 根K线, "
              f"{data_map[sym].index[0]:%Y-%m-%d} ~ "
              f"{data_map[sym].index[-1]:%Y-%m-%d}")

    engine = SignalEngine()
    signals = engine.generate(data_map)

    print("\n--- 信号统计 ---")
    for sym in symbols:
        sig = signals[sym]
        buys = sig[sig == 1]
        sells = sig[sig == -1]
        print(f"\n{sym} ({len(data_map[sym])} 根K线):")
        print(f"  做多信号: {len(buys)} 个")
        print(f"  做空信号: {len(sells)} 个")
        if len(buys) > 0:
            print(f"  最近做多: {buys.index[-1]:%Y-%m-%d}")
        if len(sells) > 0:
            print(f"  最近做空: {sells.index[-1]:%Y-%m-%d}")
