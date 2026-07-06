#!/usr/bin/env python3
"""
优化的美股数据获取工具
集成缓存策略，减少API调用，提高响应速度
"""

import os
import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from typing import Optional, Dict, Any
import yfinance as yf
import pandas as pd

# 导入缓存管理器（支持新旧路径）
try:
    from ...cache import StockDataCache
    def get_cache():
        return StockDataCache()
except ImportError:
    from ...cache_manager import get_cache

# 导入配置（支持新旧路径）
try:
    from ...config import get_config
except ImportError:
    def get_config():
        return {}

from tradingagents.config.runtime_settings import get_float, get_timezone_name
# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


class OptimizedUSDataProvider:
    """优化的美股数据提供器 - 集成缓存和API限制处理"""

    def __init__(self):
        self.cache = get_cache()
        self.config = get_config()
        self.last_api_call = 0
        self.min_api_interval = get_float("TA_US_MIN_API_INTERVAL_SECONDS", "ta_us_min_api_interval_seconds", 1.0)

        # 🔥 初始化数据源管理器（从数据库读取配置）
        try:
            from tradingagents.dataflows.data_source_manager import USDataSourceManager
            self.us_manager = USDataSourceManager()
            logger.info(f"✅ 美股数据源管理器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 美股数据源管理器初始化失败: {e}，将使用默认顺序")
            self.us_manager = None

        logger.info(f"📊 优化美股数据提供器初始化完成")

    def _wait_for_rate_limit(self):
        """等待API限制"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call

        if time_since_last_call < self.min_api_interval:
            wait_time = self.min_api_interval - time_since_last_call
            logger.info(f"⏳ API限制等待 {wait_time:.1f}s...")
            time.sleep(wait_time)

        self.last_api_call = time.time()

    def get_stock_data(self, symbol: str, start_date: str, end_date: str,
                      force_refresh: bool = False) -> str:
        """
        获取美股数据 - 优先使用缓存

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            force_refresh: 是否强制刷新缓存

        Returns:
            格式化的股票数据字符串
        """
        logger.info(f"📈 获取美股数据: {symbol} ({start_date} 到 {end_date})")

        # 检查缓存（除非强制刷新）
        if not force_refresh:
            # 🔥 按照数据源优先级顺序查找缓存
            from ...data_source_manager import get_us_data_source_manager, USDataSource
            us_manager = get_us_data_source_manager()

            # 获取数据源优先级顺序
            priority_order = us_manager._get_data_source_priority_order(symbol)

            # 数据源名称映射
            source_name_mapping = {
                USDataSource.ALPHA_VANTAGE: "alpha_vantage",
                USDataSource.YFINANCE: "yfinance",
                USDataSource.FINNHUB: "finnhub",
            }

            # 按优先级顺序查找缓存
            for source in priority_order:
                if source == USDataSource.MONGODB:
                    continue  # MongoDB 缓存单独处理

                source_name = source_name_mapping.get(source)
                if source_name:
                    cache_key = self.cache.find_cached_stock_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        data_source=source_name
                    )

                    if cache_key:
                        cached_data = self.cache.load_stock_data(cache_key)
                        if cached_data:
                            logger.info(f"⚡ [数据来源: 缓存-{source_name}] 从缓存加载美股数据: {symbol}")
                            return cached_data

        # 缓存未命中，从API获取 - 使用数据源管理器的优先级顺序
        formatted_data = None
        data_source = None

        # 🔥 从数据源管理器获取优先级顺序
        if self.us_manager:
            try:
                source_priority = self.us_manager._get_data_source_priority_order(symbol)
                logger.info(f"📊 [美股数据源优先级] 从数据库读取: {[s.value for s in source_priority]}")
            except Exception as e:
                logger.warning(f"⚠️ 获取数据源优先级失败: {e}，使用默认顺序")
                source_priority = None
        else:
            source_priority = None

        # 如果没有配置优先级，使用默认顺序
        if not source_priority:
            # 默认顺序：yfinance > alpha_vantage > finnhub
            from tradingagents.dataflows.data_source_manager import USDataSource
            source_priority = [USDataSource.YFINANCE, USDataSource.ALPHA_VANTAGE, USDataSource.FINNHUB]
            logger.info(f"📊 [美股数据源优先级] 使用默认顺序: {[s.value for s in source_priority]}")

        # 按优先级尝试各个数据源
        for source in source_priority:
            try:
                source_name = source.value
                logger.info(f"🌐 [数据来源: API调用-{source_name.upper()}] 尝试从 {source_name.upper()} 获取数据: {symbol}")
                self._wait_for_rate_limit()

                # 根据数据源类型调用不同的方法
                if source_name == 'finnhub':
                    formatted_data = self._get_data_from_finnhub(symbol, start_date, end_date)
                elif source_name == 'alpha_vantage':
                    formatted_data = self._get_data_from_alpha_vantage(symbol, start_date, end_date)
                elif source_name == 'yfinance':
                    formatted_data = self._get_data_from_yfinance(symbol, start_date, end_date)
                else:
                    logger.warning(f"⚠️ 未知的数据源类型: {source_name}")
                    continue

                if formatted_data and "❌" not in formatted_data:
                    data_source = source_name
                    logger.info(f"✅ [数据来源: API调用成功-{source_name.upper()}] {source_name.upper()} 数据获取成功: {symbol}")
                    break  # 成功获取数据，跳出循环
                else:
                    logger.warning(f"⚠️ [数据来源: API失败-{source_name.upper()}] {source_name.upper()} 数据获取失败，尝试下一个数据源")
                    formatted_data = None

            except Exception as e:
                logger.error(f"❌ [数据来源: API异常-{source.value.upper()}] {source.value.upper()} API调用失败: {e}")
                formatted_data = None
                continue  # 尝试下一个数据源

        # 如果所有配置的数据源都失败，尝试备用方案
        if not formatted_data:
            try:
                # 检测股票类型
                from tradingagents.utils.stock_utils import StockUtils
                market_info = StockUtils.get_market_info(symbol)

                if market_info['is_hk']:
                    # 港股优先使用AKShare数据源
                    logger.info(f"🇭🇰 [数据来源: API调用-AKShare] 尝试使用AKShare获取港股数据: {symbol}")
                    try:
                        from tradingagents.dataflows.interface import get_hk_stock_data_unified
                        hk_data_text = get_hk_stock_data_unified(symbol, start_date, end_date)

                        if hk_data_text and "❌" not in hk_data_text:
                            formatted_data = hk_data_text
                            data_source = "akshare_hk"
                            logger.info(f"✅ [数据来源: API调用成功-AKShare] AKShare港股数据获取成功: {symbol}")
                        else:
                            raise Exception("AKShare港股数据获取失败")

                    except Exception as e:
                        logger.error(f"⚠️ [数据来源: API失败-AKShare] AKShare港股数据获取失败: {e}")
                        # 备用方案：Yahoo Finance
                        logger.info(f"🔄 [数据来源: API调用-Yahoo Finance备用] 使用Yahoo Finance备用方案获取港股数据: {symbol}")

                        self._wait_for_rate_limit()
                        ticker = yf.Ticker(symbol)  # 港股代码保持原格式
                        data = ticker.history(start=start_date, end=end_date)

                        if not data.empty:
                            formatted_data = self._format_stock_data(symbol, data, start_date, end_date)
                            data_source = "yfinance_hk"
                            logger.info(f"✅ [数据来源: API调用成功-Yahoo Finance] Yahoo Finance港股数据获取成功: {symbol}")
                        else:
                            logger.error(f"❌ [数据来源: API失败-Yahoo Finance] Yahoo Finance港股数据为空: {symbol}")
                else:
                    # 美股使用Yahoo Finance
                    logger.info(f"🇺🇸 [数据来源: API调用-Yahoo Finance] 从Yahoo Finance API获取美股数据: {symbol}")
                    self._wait_for_rate_limit()

                    # 获取数据
                    ticker = yf.Ticker(symbol.upper())
                    data = ticker.history(start=start_date, end=end_date)

                    if data.empty:
                        error_msg = f"未找到股票 '{symbol}' 在 {start_date} 到 {end_date} 期间的数据"
                        logger.error(f"❌ [数据来源: API失败-Yahoo Finance] {error_msg}")
                    else:
                        # 格式化数据
                        formatted_data = self._format_stock_data(symbol, data, start_date, end_date)
                        data_source = "yfinance"
                        logger.info(f"✅ [数据来源: API调用成功-Yahoo Finance] Yahoo Finance美股数据获取成功: {symbol}")

            except Exception as e:
                logger.error(f"❌ [数据来源: API异常] 数据获取失败: {e}")
                formatted_data = None

        # 如果所有API都失败，生成备用数据
        if not formatted_data:
            error_msg = "所有美股数据源都不可用"
            logger.error(f"❌ [数据来源: 所有API失败] {error_msg}")
            logger.warning(f"⚠️ [数据来源: 备用数据] 生成备用数据: {symbol}")
            return self._generate_fallback_data(symbol, start_date, end_date, error_msg)

        # 保存到缓存
        self.cache.save_stock_data(
            symbol=symbol,
            data=formatted_data,
            start_date=start_date,
            end_date=end_date,
            data_source=data_source
        )

        logger.info(f"💾 [数据来源: {data_source}] 数据已缓存: {symbol}")
        return formatted_data

    def _format_stock_data(self, symbol: str, data: pd.DataFrame,
                          start_date: str, end_date: str) -> str:
        """格式化股票数据为字符串"""

        # 移除时区信息
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        # 四舍五入数值
        numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)

        # 获取最新价格和统计信息
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
        price_change_pct = (price_change / data['Close'].iloc[0]) * 100

        # 🔥 使用统一的技术指标计算函数
        # 注意：美股数据列名是大写的 Close, High, Low
        from tradingagents.tools.analysis.indicators import add_all_indicators
        data = add_all_indicators(data, close_col='Close', high_col='High', low_col='Low')

        # 获取最新技术指标
        latest = data.iloc[-1]

        # 格式化输出
        result = f"""# {symbol} 美股数据分析

## 📊 基本信息
- 股票代码: {symbol}
- 数据期间: {start_date} 至 {end_date}
- 数据条数: {len(data)}条
- 最新价格: ${latest_price:.2f}
- 期间涨跌: ${price_change:+.2f} ({price_change_pct:+.2f}%)

## 📈 价格统计
- 期间最高: ${data['High'].max():.2f}
- 期间最低: ${data['Low'].min():.2f}
- 平均成交量: {data['Volume'].mean():,.0f}

## 🔍 技术指标（最新值）
**移动平均线**:
- MA5: ${latest['ma5']:.2f}
- MA10: ${latest['ma10']:.2f}
- MA20: ${latest['ma20']:.2f}
- MA60: ${latest['ma60']:.2f}

**MACD指标**:
- DIF: {latest['macd_dif']:.2f}
- DEA: {latest['macd_dea']:.2f}
- MACD: {latest['macd']:.2f}

**RSI指标**:
- RSI(14): {latest['rsi']:.2f}

**布林带**:
- 上轨: ${latest['boll_upper']:.2f}
- 中轨: ${latest['boll_mid']:.2f}
- 下轨: ${latest['boll_lower']:.2f}

## 📋 最近5日数据
{data[['Open', 'High', 'Low', 'Close', 'Volume']].tail().to_string()}

数据来源: Yahoo Finance API
更新时间: {datetime.now(ZoneInfo(get_timezone_name())).strftime('%Y-%m-%d %H:%M:%S')}
"""

        return result

    def _try_get_old_cache(self, symbol: str, start_date: str, end_date: str) -> Optional[str]:
        """尝试获取过期的缓存数据作为备用"""
        try:
            # 查找任何相关的缓存，不考虑TTL
            for metadata_file in self.cache.metadata_dir.glob(f"*_meta.json"):
                try:
                    import json
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    if (metadata.get('symbol') == symbol and
                        metadata.get('data_type') == 'stock_data' and
                        metadata.get('market_type') == 'us'):

                        cache_key = metadata_file.stem.replace('_meta', '')
                        cached_data = self.cache.load_stock_data(cache_key)
                        if cached_data:
                            return cached_data + "\n\n⚠️ 注意: 使用的是过期缓存数据"
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def _get_data_from_finnhub(self, symbol: str, start_date: str, end_date: str) -> str:
        """从FINNHUB API获取股票数据"""
        try:
            import finnhub
            import os
            from datetime import datetime, timedelta


            # 获取API密钥
            api_key = os.getenv('FINNHUB_API_KEY')
            if not api_key:
                return None

            client = finnhub.Client(api_key=api_key)

            # 获取实时报价
            quote = client.quote(symbol.upper())
            if not quote or 'c' not in quote:
                return None

            # 获取公司信息
            profile = client.company_profile2(symbol=symbol.upper())
            company_name = profile.get('name', symbol.upper()) if profile else symbol.upper()

            # 格式化数据
            current_price = quote.get('c', 0)
            change = quote.get('d', 0)
            change_percent = quote.get('dp', 0)

            formatted_data = f"""# {symbol.upper()} 美股数据分析

## 📊 实时行情
- 股票名称: {company_name}
- 当前价格: ${current_price:.2f}
- 涨跌额: ${change:+.2f}
- 涨跌幅: {change_percent:+.2f}%
- 开盘价: ${quote.get('o', 0):.2f}
- 最高价: ${quote.get('h', 0):.2f}
- 最低价: ${quote.get('l', 0):.2f}
- 前收盘: ${quote.get('pc', 0):.2f}
- 更新时间: {datetime.now(ZoneInfo(get_timezone_name())).strftime('%Y-%m-%d %H:%M:%S')}

## 📈 数据概览
- 数据期间: {start_date} 至 {end_date}
- 数据来源: FINNHUB API (实时数据)
- 当前价位相对位置: {((current_price - quote.get('l', current_price)) / max(quote.get('h', current_price) - quote.get('l', current_price), 0.01) * 100):.1f}%
- 日内振幅: {((quote.get('h', 0) - quote.get('l', 0)) / max(quote.get('pc', 1), 0.01) * 100):.2f}%

生成时间: {datetime.now(ZoneInfo(get_timezone_name())).strftime('%Y-%m-%d %H:%M:%S')}
"""

            return formatted_data

        except Exception as e:
            logger.error(f"❌ FINNHUB数据获取失败: {e}")
            return None

    def _get_data_from_yfinance(self, symbol: str, start_date: str, end_date: str) -> str:
        """从 Yahoo Finance API 获取股票数据"""
        try:
            # 获取数据
            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                error_msg = f"未找到股票 '{symbol}' 在 {start_date} 到 {end_date} 期间的数据"
                logger.error(f"❌ Yahoo Finance数据为空: {error_msg}")
                return None

            # 格式化数据
            formatted_data = self._format_stock_data(symbol, data, start_date, end_date)
            return formatted_data

        except Exception as e:
            logger.error(f"❌ Yahoo Finance数据获取失败: {e}")
            return None

    def _get_data_from_alpha_vantage(self, symbol: str, start_date: str, end_date: str) -> str:
        """从 Alpha Vantage API 获取股票数据"""
        try:
            from tradingagents.dataflows.providers.us.alpha_vantage_common import get_api_key
            import requests
            from datetime import datetime

            # 获取 API Key
            api_key = get_api_key()
            if not api_key:
                logger.warning("⚠️ Alpha Vantage API Key 未配置")
                return None

            # 调用 Alpha Vantage API (TIME_SERIES_DAILY)
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol.upper(),
                "apikey": api_key,
                "outputsize": "full"  # 获取完整历史数据
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data_json = response.json()

            # 检查错误
            if "Error Message" in data_json:
                logger.error(f"❌ Alpha Vantage API 错误: {data_json['Error Message']}")
                return None

            if "Note" in data_json:
                logger.warning(f"⚠️ Alpha Vantage API 限制: {data_json['Note']}")
                return None

            # 解析时间序列数据
            time_series = data_json.get("Time Series (Daily)", {})
            if not time_series:
                logger.error("❌ Alpha Vantage 返回数据为空")
                return None

            # 转换为 DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # 重命名列
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float)

            # 过滤日期范围
            df = df[(df.index >= start_date) & (df.index <= end_date)]

            if df.empty:
                logger.error(f"❌ Alpha Vantage 数据在指定日期范围内为空")
                return None

            # 格式化数据
            formatted_data = self._format_stock_data(symbol, df, start_date, end_date)
            return formatted_data

        except Exception as e:
            logger.error(f"❌ Alpha Vantage数据获取失败: {e}")
            return None

    def _generate_fallback_data(self, symbol: str, start_date: str, end_date: str, error_msg: str) -> str:
        """生成备用数据"""
        return f"""# {symbol} 美股数据获取失败

## ❌ 错误信息
{error_msg}

## 📊 模拟数据（仅供演示）
- 股票代码: {symbol}
- 数据期间: {start_date} 至 {end_date}
- 最新价格: ${random.uniform(100, 300):.2f}
- 模拟涨跌: {random.uniform(-5, 5):+.2f}%

## ⚠️ 重要提示
由于API限制或网络问题，无法获取实时数据。
建议稍后重试或检查网络连接。

生成时间: {datetime.now(ZoneInfo(get_timezone_name())).strftime('%Y-%m-%d %H:%M:%S')}
"""


# 全局实例
_us_data_provider = None

def get_optimized_us_data_provider() -> OptimizedUSDataProvider:
    """获取全局美股数据提供器实例"""
    global _us_data_provider
    if _us_data_provider is None:
        _us_data_provider = OptimizedUSDataProvider()
    return _us_data_provider


def get_us_stock_data_cached(symbol: str, start_date: str, end_date: str,
                           force_refresh: bool = False) -> str:
    """
    获取美股数据的便捷函数

    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        force_refresh: 是否强制刷新缓存

    Returns:
        格式化的股票数据字符串
    """
    # 🔧 智能日期范围处理：自动扩展到配置的回溯天数，处理周末/节假日
    from tradingagents.utils.dataflow_utils import get_trading_date_range
    from app.core.config import get_settings
    from datetime import datetime

    original_start_date = start_date
    original_end_date = end_date

    # 从配置获取市场分析回溯天数（默认60天）
    try:
        settings = get_settings()
        lookback_days = settings.MARKET_ANALYST_LOOKBACK_DAYS
        logger.info(f"📅 [美股配置验证] MARKET_ANALYST_LOOKBACK_DAYS: {lookback_days}天")
    except Exception as e:
        lookback_days = 60  # 默认60天
        logger.warning(f"⚠️ [美股配置验证] 无法获取配置，使用默认值: {lookback_days}天")
        logger.warning(f"⚠️ [美股配置验证] 错误详情: {e}")

    # 使用 end_date 作为目标日期，向前回溯指定天数
    start_date, end_date = get_trading_date_range(end_date, lookback_days=lookback_days)

    logger.info(f"📅 [美股智能日期] 原始输入: {original_start_date} 至 {original_end_date}")
    logger.info(f"📅 [美股智能日期] 回溯天数: {lookback_days}天")
    logger.info(f"📅 [美股智能日期] 计算结果: {start_date} 至 {end_date}")
    logger.info(f"📅 [美股智能日期] 实际天数: {(datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days}天")

    provider = get_optimized_us_data_provider()
    return provider.get_stock_data(symbol, start_date, end_date, force_refresh)
