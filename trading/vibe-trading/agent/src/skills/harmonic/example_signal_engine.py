"""谐波形态（Harmonic Patterns）信号引擎。

基于 Fibonacci 几何学派，识别 Gartley/Bat/Butterfly/Crab 等 XABCD 五点形态，
在 PRZ（潜在反转区）生成交易信号。

优先使用 pyharmonics 库，若不可用则回退到内置检测器。
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Harmonic pattern definitions: (b_ratio_range, d_ratio_range, name)
#   b_ratio = AB / XA
#   d_ratio = AD / XA  (对于看涨形态，AD = X price - D price 的绝对距离)
# ---------------------------------------------------------------------------
PATTERNS = {
    "Gartley": {
        "b_retrace": (0.55, 0.68),   # AB / XA ≈ 0.618
        "d_retrace": (0.72, 0.84),   # AD / XA ≈ 0.786
        "bc_ratio": (0.382, 0.886),  # BC / AB
        "cd_ratio": (1.27, 1.618),   # CD / BC
    },
    "Bat": {
        "b_retrace": (0.33, 0.55),   # AB / XA ≈ 0.382-0.5
        "d_retrace": (0.82, 0.94),   # AD / XA ≈ 0.886
        "bc_ratio": (0.382, 0.886),
        "cd_ratio": (1.618, 2.618),
    },
    "Butterfly": {
        "b_retrace": (0.72, 0.84),   # AB / XA ≈ 0.786
        "d_retrace": (1.20, 1.38),   # AD / XA ≈ 1.27 (超出X)
        "bc_ratio": (0.382, 0.886),
        "cd_ratio": (1.618, 2.618),
    },
    "Crab": {
        "b_retrace": (0.33, 0.68),   # AB / XA ≈ 0.382-0.618
        "d_retrace": (1.52, 1.72),   # AD / XA ≈ 1.618 (最远延伸)
        "bc_ratio": (0.382, 0.886),
        "cd_ratio": (2.24, 3.618),
    },
}


def _in_range(value: float, lo: float, hi: float, tol: float = 0.0) -> bool:
    """检查 value 是否在 [lo - tol, hi + tol] 范围内。

    Args:
        value: 待检查数值。
        lo: 区间下界。
        hi: 区间上界。
        tol: 容差。

    Returns:
        是否在范围内。
    """
    return (lo - tol) <= value <= (hi + tol)


# ========================== 内置谐波检测器 ==================================


def _find_swings(
    high: pd.Series,
    low: pd.Series,
    window: int = 10,
) -> Tuple[pd.Series, pd.Series]:
    """检测摆动高低点。

    使用滚动窗口方法：当某根K线的高点等于前后 window 根K线的最大值时，
    判定为摆动高点；低点同理。

    Args:
        high: 最高价序列。
        low: 最低价序列。
        window: 半窗口大小，实际窗口为 2*window+1。

    Returns:
        (swing_highs, swing_lows) 两个 Series，NaN 位置表示非摆动点。
    """
    full_window = window * 2 + 1
    rolling_max = high.rolling(full_window, center=True).max()
    rolling_min = low.rolling(full_window, center=True).min()

    swing_high = high.where(high == rolling_max)
    swing_low = low.where(low == rolling_min)

    return swing_high.dropna(), swing_low.dropna()


def _merge_swings(
    swing_highs: pd.Series,
    swing_lows: pd.Series,
) -> List[Tuple]:
    """合并摆动高低点为时间排序的序列。

    Args:
        swing_highs: 摆动高点序列。
        swing_lows: 摆动低点序列。

    Returns:
        排序列表，每个元素为 (timestamp, price, type)，type 为 "H" 或 "L"。
    """
    points = []
    for ts, price in swing_highs.items():
        points.append((ts, price, "H"))
    for ts, price in swing_lows.items():
        points.append((ts, price, "L"))
    points.sort(key=lambda x: x[0])

    # 去除连续同类型点（保留极值）
    merged = []
    for pt in points:
        if not merged or merged[-1][2] != pt[2]:
            merged.append(pt)
        else:
            # 同类型取极值
            if pt[2] == "H" and pt[1] > merged[-1][1]:
                merged[-1] = pt
            elif pt[2] == "L" and pt[1] < merged[-1][1]:
                merged[-1] = pt
    return merged


def _classify_pattern(
    x_price: float,
    a_price: float,
    b_price: float,
    c_price: float,
    d_price: float,
    tol: float = 0.08,
) -> Optional[str]:
    """根据 Fibonacci 比率判断 XABCD 属于哪种谐波形态。

    Args:
        x_price: X 点价格。
        a_price: A 点价格。
        b_price: B 点价格。
        c_price: C 点价格。
        d_price: D 点价格。
        tol: 比率容差。

    Returns:
        形态名称（如 "Gartley"），若不匹配任何形态则返回 None。
    """
    xa = abs(a_price - x_price)
    ab = abs(b_price - a_price)
    bc = abs(c_price - b_price)
    cd = abs(d_price - c_price)

    if xa == 0 or ab == 0 or bc == 0:
        return None

    b_retrace = ab / xa
    d_retrace = (ab - cd + bc) / xa  # 近似 AD/XA，需根据方向调整

    # 更精确的 D 点回撤计算
    ad = abs(d_price - a_price)
    d_retrace = ad / xa

    bc_ratio = bc / ab
    cd_ratio = cd / bc if bc != 0 else 0.0

    for name, rules in PATTERNS.items():
        # Primary validation: B retrace and D retrace (most important)
        if (
            _in_range(b_retrace, *rules["b_retrace"], tol=tol)
            and _in_range(d_retrace, *rules["d_retrace"], tol=tol)
        ):
            return name
    return None


def _detect_patterns_fallback(
    df: pd.DataFrame,
    swing_window: int = 10,
    tol: float = 0.08,
) -> List[Dict]:
    """内置谐波形态检测（回退方案）。

    流程：找摆动点 → 枚举5点组合 → 验证 Fibonacci 比率 → 输出形态。

    Args:
        df: OHLCV DataFrame，需含 high/low/close 列。
        swing_window: 摆动点检测窗口。
        tol: Fibonacci 比率容差。

    Returns:
        检测到的形态列表，每项含 pattern/direction/d_index/d_price 等字段。
    """
    swing_highs, swing_lows = _find_swings(df["high"], df["low"], swing_window)
    merged = _merge_swings(swing_highs, swing_lows)

    if len(merged) < 5:
        return []

    found = []
    # 滑动窗口，每次取5个连续摆动点作为 X-A-B-C-D 候选
    for i in range(len(merged) - 4):
        pts = merged[i : i + 5]
        x_ts, x_price, x_type = pts[0]
        a_ts, a_price, a_type = pts[1]
        b_ts, b_price, b_type = pts[2]
        c_ts, c_price, c_type = pts[3]
        d_ts, d_price, d_type = pts[4]

        # XABCD 必须交替高低
        types = [p[2] for p in pts]
        alternating = all(types[j] != types[j + 1] for j in range(4))
        if not alternating:
            continue

        pattern_name = _classify_pattern(
            x_price, a_price, b_price, c_price, d_price, tol=tol
        )
        if pattern_name is None:
            continue

        # 判断看涨/看跌：看涨形态 X 为低点（D 在底部反转区）
        if x_type == "L":
            direction = "bullish"
        else:
            direction = "bearish"

        found.append(
            {
                "pattern": pattern_name,
                "direction": direction,
                "x": (x_ts, x_price),
                "a": (a_ts, a_price),
                "b": (b_ts, b_price),
                "c": (c_ts, c_price),
                "d": (d_ts, d_price),
                "d_index": d_ts,
                "d_price": d_price,
            }
        )
    return found


# ========================== pyharmonics 适配层 ==============================


def _detect_patterns_pyharmonics(
    df: pd.DataFrame,
    is_stock: bool = False,
) -> List[Dict]:
    """使用 pyharmonics 库检测谐波形态。

    Args:
        df: OHLCV DataFrame，需含 open/high/low/close/volume 列。
        is_stock: 是否为股票标的。

    Returns:
        检测到的形态列表，格式与 _detect_patterns_fallback 一致。

    Raises:
        ImportError: pyharmonics 未安装时。
        Exception: pyharmonics 内部错误时。
    """
    from pyharmonics.technicals import OHLCTechnicals

    tech = OHLCTechnicals(df, is_stock=is_stock)
    tech.fit()

    found = []

    # pyharmonics 将形态存储在 tech.matrix 中（bearish/bullish 分类）
    for direction_attr, direction_label in [
        ("bullish", "bullish"),
        ("bearish", "bearish"),
    ]:
        matrix = getattr(tech, direction_attr, None)
        if matrix is None:
            continue
        for pattern_type, patterns in matrix.items():
            if not isinstance(patterns, list):
                continue
            for p in patterns:
                try:
                    # pyharmonics Pattern 对象有 name/x/a/b/c/d 属性
                    d_idx = p.d.idx if hasattr(p.d, "idx") else None
                    d_price = p.d.price if hasattr(p.d, "price") else None

                    if d_idx is not None and d_price is not None:
                        # 将整数索引映射回 DataFrame 时间戳
                        if isinstance(d_idx, int) and d_idx < len(df):
                            d_ts = df.index[d_idx]
                        else:
                            d_ts = d_idx

                        found.append(
                            {
                                "pattern": str(
                                    getattr(p, "name", pattern_type)
                                ),
                                "direction": direction_label,
                                "d_index": d_ts,
                                "d_price": float(d_price),
                            }
                        )
                except (AttributeError, TypeError, IndexError):
                    continue
    return found


# ========================== 信号引擎 ========================================


class SignalEngine:
    """谐波形态信号引擎。

    识别 Gartley/Bat/Butterfly/Crab 等 XABCD 五点形态，
    在 D 点（PRZ 潜在反转区）生成交易信号。

    优先使用 pyharmonics 库，若不可用则回退到内置检测器。

    Attributes:
        is_stock: 是否为股票标的。
        swing_window: 摆动点检测窗口（仅内置检测器使用）。
        tol: Fibonacci 比率容差（仅内置检测器使用）。
        use_pyharmonics: 运行时确定是否使用 pyharmonics。

    Example:
        >>> engine = SignalEngine()
        >>> signals = engine.generate({"BTC-USDT": df})
        >>> signals["BTC-USDT"].value_counts()
    """

    def __init__(
        self,
        is_stock: bool = False,
        swing_window: int = 10,
        tol: float = 0.12,
    ):
        """初始化谐波形态信号引擎。

        Args:
            is_stock: 是否为股票（影响 pyharmonics 参数）。
            swing_window: 摆动点检测半窗口大小。
            tol: Fibonacci 比率匹配容差。
        """
        self.is_stock = is_stock
        self.swing_window = swing_window
        self.tol = tol
        self.use_pyharmonics = self._check_pyharmonics()

    @staticmethod
    def _check_pyharmonics() -> bool:
        """检测 pyharmonics 是否可用。

        Returns:
            True 如果 pyharmonics 可正常导入。
        """
        try:
            from pyharmonics.technicals import OHLCTechnicals  # noqa: F401
            return True
        except ImportError:
            return False

    def _detect(self, df: pd.DataFrame) -> List[Dict]:
        """检测单个标的的谐波形态。

        优先 pyharmonics，失败则回退内置检测器。

        Args:
            df: OHLCV DataFrame。

        Returns:
            检测到的形态列表。
        """
        if self.use_pyharmonics:
            try:
                return _detect_patterns_pyharmonics(
                    df, is_stock=self.is_stock
                )
            except Exception:
                pass
        return _detect_patterns_fallback(
            df, swing_window=self.swing_window, tol=self.tol
        )

    def generate(
        self, data_map: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.Series]:
        """根据谐波形态在 D 点生成交易信号。

        Args:
            data_map: 标的代码到 OHLCV DataFrame 的映射。
                DataFrame 需包含 open/high/low/close 列，index 为 datetime。

        Returns:
            标的代码到信号 Series 的映射（1=做多, -1=做空, 0=观望）。
        """
        result = {}
        for symbol, df in data_map.items():
            signal = pd.Series(0, index=df.index, dtype=int)

            if len(df) < self.swing_window * 4:
                result[symbol] = signal
                continue

            patterns = self._detect(df)
            for p in patterns:
                d_idx = p.get("d_index")
                direction = p.get("direction", "")
                if d_idx is None:
                    continue
                # 确保 d_idx 在 signal index 中
                if d_idx in signal.index:
                    if direction == "bullish":
                        signal.at[d_idx] = 1
                    elif direction == "bearish":
                        signal.at[d_idx] = -1

            result[symbol] = signal
        return result


# ========================== OKX 数据获取 ====================================


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


# ========================== 主入口 ==========================================

if __name__ == "__main__":
    symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    data_map = {}

    print("=== 谐波形态信号引擎 ===\n")

    for sym in symbols:
        print(f"获取 {sym} 数据...")
        data_map[sym] = _fetch_okx(sym, bar="1D", limit=300)
        print(
            f"  {len(data_map[sym])} 根K线, "
            f"{data_map[sym].index[0]:%Y-%m-%d} ~ "
            f"{data_map[sym].index[-1]:%Y-%m-%d}"
        )

    engine = SignalEngine(is_stock=False)
    backend = "pyharmonics" if engine.use_pyharmonics else "内置检测器"
    print(f"\n检测后端: {backend}")

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

    # 打印检测到的形态详情
    print("\n--- 形态详情 ---")
    for sym in symbols:
        patterns = engine._detect(data_map[sym])
        if patterns:
            print(f"\n{sym}: 共 {len(patterns)} 个形态")
            for p in patterns[-5:]:  # 最近5个
                print(
                    f"  {p['pattern']} ({p['direction']}) "
                    f"D点: {p['d_index']}"
                )
        else:
            print(f"\n{sym}: 无检测到形态")
