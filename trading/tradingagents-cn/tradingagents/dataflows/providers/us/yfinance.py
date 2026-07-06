# gets data/stats

import yfinance as yf
from typing import Annotated, Callable, Any, Optional
from pandas import DataFrame
import pandas as pd
from functools import wraps
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

from tradingagents.utils.dataflow_utils import save_output, SavePathType, decorate_all_methods

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# 导入缓存管理器（延迟导入，避免循环依赖）
_cache_module = None
CACHE_AVAILABLE = True

def get_cache():
    """延迟导入缓存管理器"""
    global _cache_module, CACHE_AVAILABLE
    if _cache_module is None:
        try:
            from ...cache import get_cache as _get_cache
            _cache_module = _get_cache
            CACHE_AVAILABLE = True
        except ImportError as e:
            CACHE_AVAILABLE = False
            logger.debug(f"缓存管理器不可用（使用直接API调用）: {e}")
            return None
    return _cache_module() if _cache_module else None


def init_ticker(func: Callable) -> Callable:
    """Decorator to initialize yf.Ticker and pass it to the function."""

    @wraps(func)
    def wrapper(symbol: Annotated[str, "ticker symbol"], *args, **kwargs) -> Any:
        ticker = yf.Ticker(symbol)
        return func(ticker, *args, **kwargs)

    return wrapper


@decorate_all_methods(init_ticker)
class YFinanceUtils:

    def get_stock_data(
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[
            str, "start date for retrieving stock price data, YYYY-mm-dd"
        ],
        end_date: Annotated[
            str, "end date for retrieving stock price data, YYYY-mm-dd"
        ],
        save_path: SavePathType = None,
    ) -> DataFrame:
        """retrieve stock price data for designated ticker symbol"""
        ticker = symbol
        # add one day to the end_date so that the data range is inclusive
        end_date = pd.to_datetime(end_date) + pd.DateOffset(days=1)
        end_date = end_date.strftime("%Y-%m-%d")
        stock_data = ticker.history(start=start_date, end=end_date)
        # save_output(stock_data, f"Stock data for {ticker.ticker}", save_path)
        return stock_data

    def get_stock_info(
        symbol: Annotated[str, "ticker symbol"],
    ) -> dict:
        """Fetches and returns latest stock information."""
        ticker = symbol
        stock_info = ticker.info
        return stock_info

    def get_company_info(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """Fetches and returns company information as a DataFrame."""
        ticker = symbol
        info = ticker.info
        company_info = {
            "Company Name": info.get("shortName", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Country": info.get("country", "N/A"),
            "Website": info.get("website", "N/A"),
        }
        company_info_df = DataFrame([company_info])
        if save_path:
            company_info_df.to_csv(save_path)
            logger.info(f"Company info for {ticker.ticker} saved to {save_path}")
        return company_info_df

    def get_stock_dividends(
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """Fetches and returns the latest dividends data as a DataFrame."""
        ticker = symbol
        dividends = ticker.dividends
        if save_path:
            dividends.to_csv(save_path)
            logger.info(f"Dividends for {ticker.ticker} saved to {save_path}")
        return dividends

    def get_income_stmt(symbol: Annotated[str, "ticker symbol"]) -> DataFrame:
        """Fetches and returns the latest income statement of the company as a DataFrame."""
        ticker = symbol
        income_stmt = ticker.financials
        return income_stmt

    def get_balance_sheet(symbol: Annotated[str, "ticker symbol"]) -> DataFrame:
        """Fetches and returns the latest balance sheet of the company as a DataFrame."""
        ticker = symbol
        balance_sheet = ticker.balance_sheet
        return balance_sheet

    def get_cash_flow(symbol: Annotated[str, "ticker symbol"]) -> DataFrame:
        """Fetches and returns the latest cash flow statement of the company as a DataFrame."""
        ticker = symbol
        cash_flow = ticker.cashflow
        return cash_flow

    def get_analyst_recommendations(symbol: Annotated[str, "ticker symbol"]) -> tuple:
        """Fetches the latest analyst recommendations and returns the most common recommendation and its count."""
        ticker = symbol
        recommendations = ticker.recommendations
        if recommendations.empty:
            return None, 0  # No recommendations available

        # Assuming 'period' column exists and needs to be excluded
        row_0 = recommendations.iloc[0, 1:]  # Exclude 'period' column if necessary

        # Find the maximum voting result
        max_votes = row_0.max()
        majority_voting_result = row_0[row_0 == max_votes].index.tolist()

        return majority_voting_result[0], max_votes


# ==================== 技术指标相关函数 ====================

def get_stock_data_with_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    获取股票数据（OHLCV）并返回 CSV 格式字符串

    参考原版 TradingAgents 的 get_YFin_data_online 实现
    """
    try:
        # 验证日期格式
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        # 创建 ticker 对象
        ticker = yf.Ticker(symbol.upper())

        # 获取历史数据
        data = ticker.history(start=start_date, end=end_date)

        # 检查数据是否为空
        if data.empty:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

        # 移除时区信息
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        # 数值列保留2位小数
        numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)

        # 转换为 CSV 字符串
        csv_string = data.to_csv()

        # 添加头部信息
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        logger.error(f"❌ [yfinance] 获取股票数据失败 {symbol}: {e}")
        return f"Error retrieving stock data for {symbol}: {str(e)}"


def get_technical_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to calculate"],
    curr_date: Annotated[str, "The current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 60,
) -> str:
    """
    获取技术指标数据（使用 stockstats 库计算）

    参考原版 TradingAgents 的 get_stock_stats_indicators_window 实现

    支持的指标：
    - close_50_sma: 50日简单移动平均
    - close_200_sma: 200日简单移动平均
    - close_10_ema: 10日指数移动平均
    - macd: MACD指标
    - macds: MACD信号线
    - macdh: MACD柱状图
    - rsi: 相对强弱指标
    - boll: 布林带中轨
    - boll_ub: 布林带上轨
    - boll_lb: 布林带下轨
    - atr: 平均真实波幅
    - vwma: 成交量加权移动平均
    - mfi: 资金流量指标
    """
    try:
        from stockstats import wrap

        # 指标说明
        indicator_descriptions = {
            "close_50_sma": (
                "50 SMA: 中期趋势指标。"
                "用途：识别趋势方向，作为动态支撑/阻力位。"
                "提示：滞后于价格，建议结合快速指标使用。"
            ),
            "close_200_sma": (
                "200 SMA: 长期趋势基准。"
                "用途：确认整体市场趋势，识别金叉/死叉。"
                "提示：反应缓慢，适合战略性趋势确认。"
            ),
            "close_10_ema": (
                "10 EMA: 短期响应平均线。"
                "用途：捕捉快速动量变化和潜在入场点。"
                "提示：在震荡市场中容易产生噪音。"
            ),
            "macd": (
                "MACD: 通过EMA差值计算动量。"
                "用途：寻找交叉和背离作为趋势变化信号。"
                "提示：在低波动或横盘市场中需要其他指标确认。"
            ),
            "macds": (
                "MACD信号线: MACD线的EMA平滑。"
                "用途：与MACD线交叉触发交易信号。"
                "提示：应作为更广泛策略的一部分。"
            ),
            "macdh": (
                "MACD柱状图: MACD线与信号线的差值。"
                "用途：可视化动量强度，早期发现背离。"
                "提示：可能波动较大，在快速市场中需要额外过滤。"
            ),
            "rsi": (
                "RSI: 测量动量以标记超买/超卖状态。"
                "用途：应用70/30阈值，观察背离以信号反转。"
                "提示：在强趋势中RSI可能保持极端值，需结合趋势分析。"
            ),
            "boll": (
                "布林带中轨: 20日SMA作为布林带基准。"
                "用途：作为价格运动的动态基准。"
                "提示：结合上下轨有效发现突破或反转。"
            ),
            "boll_ub": (
                "布林带上轨: 通常为中轨上方2个标准差。"
                "用途：信号潜在超买状态和突破区域。"
                "提示：需其他工具确认，强趋势中价格可能沿轨道运行。"
            ),
            "boll_lb": (
                "布林带下轨: 通常为中轨下方2个标准差。"
                "用途：指示潜在超卖状态。"
                "提示：使用额外分析避免虚假反转信号。"
            ),
            "atr": (
                "ATR: 平均真实波幅测量波动性。"
                "用途：设置止损位，根据当前市场波动调整仓位大小。"
                "提示：这是反应性指标，应作为更广泛风险管理策略的一部分。"
            ),
            "vwma": (
                "VWMA: 成交量加权移动平均。"
                "用途：通过整合价格和成交量数据确认趋势。"
                "提示：注意成交量激增导致的偏差，结合其他成交量分析使用。"
            ),
            "mfi": (
                "MFI: 资金流量指标，使用价格和成交量测量买卖压力。"
                "用途：识别超买(>80)或超卖(<20)状态，确认趋势或反转强度。"
                "提示：与RSI或MACD结合使用确认信号，价格与MFI背离可能预示反转。"
            ),
        }

        if indicator not in indicator_descriptions:
            supported = ", ".join(indicator_descriptions.keys())
            return f"❌ 不支持的指标 '{indicator}'。支持的指标: {supported}"

        # 计算日期范围
        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date_dt = curr_date_dt - relativedelta(days=look_back_days + 365)  # 多获取一年数据用于计算
        start_date = start_date_dt.strftime("%Y-%m-%d")

        # 获取股票数据
        logger.info(f"📊 [yfinance] 获取 {symbol} 技术指标 {indicator}，日期范围: {start_date} 至 {curr_date}")
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(start=start_date, end=curr_date)

        if data.empty:
            return f"❌ 未找到 {symbol} 的数据"

        # 重置索引，将日期作为列
        data = data.reset_index()
        data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')

        # 使用 stockstats 计算指标
        df = wrap(data)
        df[indicator]  # 触发计算

        # 生成指定日期范围的结果
        result_lines = []
        check_date = curr_date_dt
        end_date = curr_date_dt - relativedelta(days=look_back_days)

        while check_date >= end_date:
            date_str = check_date.strftime('%Y-%m-%d')

            # 查找该日期的指标值
            matching_rows = df[df['Date'] == date_str]

            if not matching_rows.empty:
                value = matching_rows.iloc[0][indicator]
                if pd.isna(value):
                    result_lines.append(f"{date_str}: N/A")
                else:
                    result_lines.append(f"{date_str}: {value:.4f}")
            else:
                result_lines.append(f"{date_str}: N/A: Not a trading day (weekend or holiday)")

            check_date = check_date - relativedelta(days=1)

        # 构建结果字符串
        result = f"## {indicator} values from {end_date.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        result += "\n".join(result_lines)
        result += "\n\n" + indicator_descriptions[indicator]

        return result

    except ImportError:
        return "❌ 需要安装 stockstats 库: pip install stockstats"
    except Exception as e:
        logger.error(f"❌ [yfinance] 计算技术指标失败 {symbol}/{indicator}: {e}")
        return f"Error calculating indicator {indicator} for {symbol}: {str(e)}"
