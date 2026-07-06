"""缠论形态识别信号引擎。

基于 czsc 库实现缠中说禅理论的买卖点信号生成。
核心链路：K线 → 分型 → 笔 → 中枢 → 买卖点。
"""

from typing import Optional, Dict
from datetime import datetime

import pandas as pd
from czsc import CZSC, RawBar, Freq, ZS
from czsc.signals.cxt import (
    cxt_first_buy_V221126,
    cxt_first_sell_V221126,
    cxt_bi_base_V230228,
    cxt_three_bi_V230618,
    cxt_five_bi_V230619,
)


def _df_to_bars(df: pd.DataFrame, symbol: str, freq: Freq = Freq.D) -> list:
    """将 OHLCV DataFrame 转换为 czsc RawBar 列表。

    Args:
        df: 包含 open/high/low/close/volume 列的 DataFrame，index 为 datetime。
        symbol: 标的代码。
        freq: K线频率，默认日线。

    Returns:
        按时间正序排列的 RawBar 列表。
    """
    bars = []
    for i, (dt, row) in enumerate(df.iterrows()):
        if not isinstance(dt, datetime):
            dt = pd.Timestamp(dt).to_pydatetime()
        bars.append(RawBar(
            symbol=symbol,
            id=i,
            dt=dt,
            freq=freq,
            open=float(row["open"]),
            close=float(row["close"]),
            high=float(row["high"]),
            low=float(row["low"]),
            vol=float(row.get("volume", row.get("vol", 0))),
            amount=float(row.get("amount", 0)),
        ))
    return bars


def _get_signals(c: CZSC) -> dict:
    """计算缠论买卖点信号。

    Args:
        c: CZSC 分析器实例。

    Returns:
        信号字典。
    """
    s = {}
    s.update(cxt_first_buy_V221126(c, di=1))
    s.update(cxt_first_sell_V221126(c, di=1))
    s.update(cxt_bi_base_V230228(c, di=1))
    s.update(cxt_three_bi_V230618(c, di=1))
    s.update(cxt_five_bi_V230619(c, di=1))
    return s


def _check_zhongshu(bi_list: list) -> Optional[ZS]:
    """检测最近的有效中枢。

    Args:
        bi_list: 笔列表。

    Returns:
        最近的有效中枢，没有则返回 None。
    """
    if len(bi_list) < 3:
        return None
    for i in range(len(bi_list) - 3, max(len(bi_list) - 10, -1), -1):
        zs = ZS(bis=bi_list[i:i + 3])
        if zs.is_valid:
            return zs
    return None


class SignalEngine:
    """缠论形态识别信号引擎。

    基于分型→笔→中枢→买卖点链路，生成做多/做空/观望信号。

    Attributes:
        freq: K线分析频率。
    """

    def __init__(self, freq: Freq = Freq.D):
        """初始化缠论信号引擎。

        Args:
            freq: K线分析频率，默认日线。
        """
        self.freq = freq

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """根据缠论形态生成交易信号。

        Args:
            data_map: 标的代码到 OHLCV DataFrame 的映射。
                DataFrame 需包含 open/high/low/close/volume 列，index 为 datetime。

        Returns:
            标的代码到信号 Series 的映射（1=做多, -1=做空, 0=观望）。
        """
        result = {}
        for code, df in data_map.items():
            signal = pd.Series(0, index=df.index)
            bars = _df_to_bars(df, code, self.freq)

            if len(bars) < 30:
                result[code] = signal
                continue

            # 逐根K线分析，记录每根K线的信号
            c = CZSC(bars[:30], get_signals=_get_signals)
            for bar in bars[30:]:
                c.update(bar)
                sig = self._evaluate_signals(c)
                if sig != 0:
                    signal.iloc[bar.id] = sig

            result[code] = signal
        return result

    def _evaluate_signals(self, c: CZSC) -> int:
        """评估当前信号状态，返回交易方向。

        Args:
            c: CZSC 分析器实例。

        Returns:
            1=做多, -1=做空, 0=观望。
        """
        signals = c.signals
        if not signals:
            return 0

        # 一买信号
        buy1_key = [k for k in signals if "BUY1" in k]
        if buy1_key and "一买" in str(signals.get(buy1_key[0], "")):
            return 1

        # 一卖信号
        sell1_key = [k for k in signals if "SELL1" in k]
        if sell1_key and "一卖" in str(signals.get(sell1_key[0], "")):
            return -1

        # 三笔形态
        three_bi_key = [k for k in signals if "三笔" in k]
        if three_bi_key:
            val = str(signals.get(three_bi_key[0], ""))
            if "向上盘背" in val:
                return 1
            if "向下盘背" in val:
                return -1

        # 五笔形态
        five_bi_key = [k for k in signals if "五笔" in k]
        if five_bi_key:
            val = str(signals.get(five_bi_key[0], ""))
            if "类一买" in val:
                return 1
            if "类一卖" in val:
                return -1

        # 笔基础信号 + 中枢位置辅助
        bi_key = [k for k in signals if "V230228" in k]
        if bi_key and len(c.bi_list) >= 3:
            val = str(signals.get(bi_key[0], ""))
            zs = _check_zhongshu(c.bi_list)
            if zs and zs.is_valid:
                last_close = c.bars_raw[-1].close
                if "向下_转折" in val and last_close <= zs.zd:
                    return 1
                if "向上_转折" in val and last_close >= zs.zg:
                    return -1

        return 0


if __name__ == "__main__":
    import requests

    BASE_URL = "https://www.okx.com/api/v5"

    # 获取 BTC 日线数据
    resp = requests.get(f"{BASE_URL}/market/candles", params={
        "instId": "BTC-USDT", "bar": "1D", "limit": "300"
    })
    candles = resp.json()["data"]

    # 转为 DataFrame
    columns = ["ts", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm"]
    df = pd.DataFrame(reversed(candles), columns=columns)
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms")
    df = df.set_index("ts")
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df["vol"].astype(float)
    df["amount"] = df["volCcy"].astype(float)

    # 运行信号引擎
    engine = SignalEngine(freq=Freq.D)
    signals = engine.generate({"BTC-USDT": df})

    # 输出结果
    sig = signals["BTC-USDT"]
    buys = sig[sig == 1]
    sells = sig[sig == -1]
    print(f"BTC-USDT 缠论信号 ({len(df)} 根K线)")
    print(f"  做多信号: {len(buys)} 个")
    print(f"  做空信号: {len(sells)} 个")
    if len(buys) > 0:
        print(f"  最近做多: {buys.index[-1]:%Y-%m-%d}")
    if len(sells) > 0:
        print(f"  最近做空: {sells.index[-1]:%Y-%m-%d}")
