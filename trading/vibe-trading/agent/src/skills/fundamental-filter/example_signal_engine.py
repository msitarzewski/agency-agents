"""基本面因子过滤选股信号引擎。

基于 PE/PB/ROE 等财务指标对 A 股进行价值筛选，
满足全部条件的股票等权做多。支持 tushare `extra_fields`
以及 `fundamental_fields` 注入的财务报表字段。
"""

from typing import Dict, List

import numpy as np
import pandas as pd


class SignalEngine:
    """基本面因子过滤信号引擎。

    通过 PE/PB/ROE 三重过滤筛选价值股，满足条件的股票等权分配。

    Attributes:
        pe_min: PE 下限（排除亏损股）。
        pe_max: PE 上限（排除高估值）。
        pb_max: PB 上限。
        roe_min: ROE 下限（%）。

    Example:
        >>> engine = SignalEngine(pe_max=15, pb_max=2, roe_min=10)
        >>> signals = engine.generate({"000001.SZ": df1, "600036.SH": df2})
    """

    def __init__(
        self,
        pe_min: float = 0.0,
        pe_max: float = 20.0,
        pb_max: float = 3.0,
        roe_min: float = 8.0,
        revenue_min: float = 0.0,
        net_assets_min: float = 0.0,
    ):
        """初始化基本面过滤引擎。

        Args:
            pe_min: PE 下限（排除亏损股，默认 0）。
            pe_max: PE 上限（排除高估值）。
            pb_max: PB 上限。
            roe_min: ROE 下限（%）。
            revenue_min: 营收下限，单位沿用 Tushare income 表。
            net_assets_min: 净资产下限，单位沿用 Tushare balancesheet 表。
        """
        self.pe_min = pe_min
        self.pe_max = pe_max
        self.pb_max = pb_max
        self.roe_min = roe_min
        self.revenue_min = revenue_min
        self.net_assets_min = net_assets_min

    def _passes_statement_filter(self, row: pd.Series) -> bool | None:
        """Return statement-filter decision, or None when statement data is absent."""
        revenue = _first_number(row, ["income_total_revenue", "income_revenue"])
        profit = _first_number(row, ["income_n_income"])
        net_assets = _first_number(row, ["balancesheet_total_hldr_eqy_exc_min_int"])
        roe = _first_number(row, ["fina_indicator_roe", "roe"])

        statement_values = [revenue, profit, net_assets, roe]
        if all(pd.isna(value) for value in statement_values):
            return None
        if any(pd.isna(value) for value in statement_values):
            return False
        return (
            revenue >= self.revenue_min
            and profit > 0
            and net_assets > self.net_assets_min
            and roe >= self.roe_min
        )

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """基于基本面条件过滤，对满足条件的股票等权做多。

        Args:
            data_map: 标的代码到 DataFrame 的映射。
                DataFrame 需包含 open/high/low/close/volume 列及 pe/pb/roe 等 extra_fields。

        Returns:
            标的代码到信号 Series 的映射。
        """
        codes = list(data_map.keys())
        if not codes:
            return {}

        # 获取所有日期的并集
        all_dates = sorted(set().union(*(df.index for df in data_map.values())))
        date_index = pd.DatetimeIndex(all_dates)

        # 逐日判断每只股票是否满足条件
        signals: Dict[str, pd.Series] = {code: pd.Series(0.0, index=date_index) for code in codes}

        for dt in date_index:
            qualified: List[str] = []
            for code, df in data_map.items():
                if dt not in df.index:
                    continue
                row = df.loc[dt]
                statement_pass = self._passes_statement_filter(row)
                if statement_pass is not None:
                    if statement_pass:
                        qualified.append(code)
                    continue

                pe = row.get("pe", np.nan)
                pb = row.get("pb", np.nan)
                roe = row.get("roe", np.nan)

                if pd.isna(pe) or pd.isna(pb) or pd.isna(roe):
                    continue
                if self.pe_min < pe <= self.pe_max and pb <= self.pb_max and roe >= self.roe_min:
                    qualified.append(code)

            if qualified:
                weight = 1.0 / len(qualified)
                for code in qualified:
                    signals[code].at[dt] = weight

        # 对齐到各自原始索引
        result = {}
        for code, df in data_map.items():
            result[code] = signals[code].reindex(df.index).fillna(0.0)
        return result


def _first_number(row: pd.Series, columns: List[str]) -> float:
    """Return the first numeric value found in row, otherwise NaN."""
    for column in columns:
        value = row.get(column, np.nan)
        if pd.notna(value):
            return float(value)
    return np.nan


if __name__ == "__main__":
    # 演示：用随机数据模拟基本面过滤
    np.random.seed(42)
    dates = pd.bdate_range("2024-01-01", "2024-12-31")

    def _mock_stock(pe_range, pb_range, roe_range):
        n = len(dates)
        return pd.DataFrame({
            "open": np.random.uniform(10, 50, n),
            "high": np.random.uniform(10, 50, n),
            "low": np.random.uniform(10, 50, n),
            "close": np.random.uniform(10, 50, n),
            "volume": np.random.uniform(1e6, 1e7, n),
            "pe": np.random.uniform(*pe_range, n),
            "pb": np.random.uniform(*pb_range, n),
            "roe": np.random.uniform(*roe_range, n),
        }, index=dates)

    data_map = {
        "000001.SZ": _mock_stock((5, 15), (0.5, 2.0), (8, 20)),    # 大概率入选
        "600036.SH": _mock_stock((3, 10), (0.3, 1.5), (12, 25)),   # 高概率入选
        "000858.SZ": _mock_stock((30, 80), (5, 15), (5, 10)),       # 大概率不入选
    }

    engine = SignalEngine(pe_max=20, pb_max=3, roe_min=8)
    signals = engine.generate(data_map)

    for code in data_map:
        sig = signals[code]
        active_days = (sig > 0).sum()
        print(f"{code}: {active_days}/{len(sig)} days in portfolio")
