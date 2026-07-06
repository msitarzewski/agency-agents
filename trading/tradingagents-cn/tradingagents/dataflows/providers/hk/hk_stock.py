"""
港股数据获取工具
提供港股数据的获取、处理和缓存功能
"""

import pandas as pd
import numpy as np
import yfinance as yf
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from tradingagents.config.runtime_settings import get_timezone_name

import os

from tradingagents.config.runtime_settings import get_float, get_int
# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')



class HKStockProvider:
    """港股数据提供器"""

    def __init__(self):
        """初始化港股数据提供器"""
        self.last_request_time = 0
        self.min_request_interval = get_float("TA_HK_MIN_REQUEST_INTERVAL_SECONDS", "ta_hk_min_request_interval_seconds", 2.0)
        self.timeout = get_int("TA_HK_TIMEOUT_SECONDS", "ta_hk_timeout_seconds", 60)
        self.max_retries = get_int("TA_HK_MAX_RETRIES", "ta_hk_max_retries", 3)
        self.rate_limit_wait = get_int("TA_HK_RATE_LIMIT_WAIT_SECONDS", "ta_hk_rate_limit_wait_seconds", 60)

        logger.info(f"🇭🇰 港股数据提供器初始化完成")

    def _wait_for_rate_limit(self):
        """等待速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取港股历史数据

        Args:
            symbol: 港股代码 (如: 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame: 股票历史数据
        """
        try:
            # 标准化港股代码
            symbol = self._normalize_hk_symbol(symbol)

            # 设置默认日期
            if not end_date:
                end_date = datetime.now(ZoneInfo(get_timezone_name())).strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now(ZoneInfo(get_timezone_name())) - timedelta(days=365)).strftime('%Y-%m-%d')

            logger.info(f"🇭🇰 获取港股数据: {symbol} ({start_date} 到 {end_date})")

            # 多次重试获取数据
            for attempt in range(self.max_retries):
                try:
                    self._wait_for_rate_limit()

                    # 使用yfinance获取数据
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(
                        start=start_date,
                        end=end_date,
                        timeout=self.timeout
                    )

                    if not data.empty:
                        # 数据预处理
                        data = data.reset_index()
                        data['Symbol'] = symbol

                        logger.info(f"✅ 港股数据获取成功: {symbol}, {len(data)}条记录")
                        return data
                    else:
                        logger.warning(f"⚠️ 港股数据为空: {symbol} (尝试 {attempt + 1}/{self.max_retries})")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ 港股数据获取失败 (尝试 {attempt + 1}/{self.max_retries}): {error_msg}")

                    # 检查是否是频率限制错误
                    if "Rate limited" in error_msg or "Too Many Requests" in error_msg:
                        if attempt < self.max_retries - 1:
                            logger.info(f"⏳ 检测到频率限制，等待{self.rate_limit_wait}秒...")
                            time.sleep(self.rate_limit_wait)
                        else:
                            logger.error(f"❌ 频率限制，跳过重试")
                            break
                    else:
                        if attempt < self.max_retries - 1:
                            time.sleep(2 ** attempt)  # 指数退避

            logger.error(f"❌ 港股数据获取最终失败: {symbol}")
            return None

        except Exception as e:
            logger.error(f"❌ 港股数据获取异常: {e}")
            return None

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取港股基本信息

        Args:
            symbol: 港股代码

        Returns:
            Dict: 股票基本信息
        """
        try:
            symbol = self._normalize_hk_symbol(symbol)

            logger.info(f"🇭🇰 获取港股信息: {symbol}")

            self._wait_for_rate_limit()

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if info and 'symbol' in info:
                return {
                    'symbol': symbol,
                    'name': info.get('longName', info.get('shortName', f'港股{symbol}')),
                    'currency': info.get('currency', 'HKD'),
                    'exchange': info.get('exchange', 'HKG'),
                    'market_cap': info.get('marketCap'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'source': 'yfinance_hk'
                }
            else:
                return {
                    'symbol': symbol,
                    'name': f'港股{symbol}',
                    'currency': 'HKD',
                    'exchange': 'HKG',
                    'source': 'yfinance_hk'
                }

        except Exception as e:
            logger.error(f"❌ 获取港股信息失败: {e}")
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'unknown',
                'error': str(e)
            }

    def get_real_time_price(self, symbol: str) -> Optional[Dict]:
        """
        获取港股实时价格

        Args:
            symbol: 港股代码

        Returns:
            Dict: 实时价格信息
        """
        try:
            symbol = self._normalize_hk_symbol(symbol)

            self._wait_for_rate_limit()

            ticker = yf.Ticker(symbol)

            # 获取最新的历史数据（1天）
            data = ticker.history(period="1d", timeout=self.timeout)

            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'price': latest['Close'],
                    'open': latest['Open'],
                    'high': latest['High'],
                    'low': latest['Low'],
                    'volume': latest['Volume'],
                    'timestamp': data.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
                    'currency': 'HKD'
                }
            else:
                return None

        except Exception as e:
            logger.error(f"❌ 获取港股实时价格失败: {e}")
            return None

    def _normalize_hk_symbol(self, symbol: str) -> str:
        """
        标准化港股代码格式

        Yahoo Finance 期望的格式：0700.HK（4位数字）
        输入可能的格式：00700, 700, 0700, 0700.HK, 00700.HK

        Args:
            symbol: 原始港股代码

        Returns:
            str: 标准化后的港股代码（格式：0700.HK）
        """
        if not symbol:
            return symbol

        symbol = str(symbol).strip().upper()

        # 如果已经有.HK后缀，先移除
        if symbol.endswith('.HK'):
            symbol = symbol[:-3]

        # 如果是纯数字，标准化为4位数字
        if symbol.isdigit():
            # 移除前导0，然后补齐到4位
            clean_code = symbol.lstrip('0') or '0'  # 如果全是0，保留一个0
            normalized_code = clean_code.zfill(4)
            return f"{normalized_code}.HK"

        return symbol

    def format_stock_data(self, symbol: str, data: pd.DataFrame, start_date: str, end_date: str) -> str:
        """
        格式化港股数据为文本格式（包含技术指标）

        Args:
            symbol: 股票代码
            data: 股票数据DataFrame
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据文本（包含技术指标）
        """
        if data is None or data.empty:
            return f"❌ 无法获取港股 {symbol} 的数据"

        try:
            original_data_count = len(data)
            logger.info(f"📊 [港股技术指标] 开始计算技术指标，原始数据: {original_data_count}条")

            # 获取股票基本信息
            stock_info = self.get_stock_info(symbol)
            stock_name = stock_info.get('name', f'港股{symbol}')

            # 确保数据按日期排序
            if 'Date' in data.columns:
                data = data.sort_values('Date')
            else:
                data = data.sort_index()

            # 计算移动平均线
            data['ma5'] = data['Close'].rolling(window=5, min_periods=1).mean()
            data['ma10'] = data['Close'].rolling(window=10, min_periods=1).mean()
            data['ma20'] = data['Close'].rolling(window=20, min_periods=1).mean()
            data['ma60'] = data['Close'].rolling(window=60, min_periods=1).mean()

            # 计算RSI（相对强弱指标）
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / (loss.replace(0, np.nan))
            data['rsi'] = 100 - (100 / (1 + rs))

            # 计算MACD
            ema12 = data['Close'].ewm(span=12, adjust=False).mean()
            ema26 = data['Close'].ewm(span=26, adjust=False).mean()
            data['macd_dif'] = ema12 - ema26
            data['macd_dea'] = data['macd_dif'].ewm(span=9, adjust=False).mean()
            data['macd'] = (data['macd_dif'] - data['macd_dea']) * 2

            # 计算布林带
            data['boll_mid'] = data['Close'].rolling(window=20, min_periods=1).mean()
            std = data['Close'].rolling(window=20, min_periods=1).std()
            data['boll_upper'] = data['boll_mid'] + 2 * std
            data['boll_lower'] = data['boll_mid'] - 2 * std

            # 只保留最后3-5天的数据用于展示（减少token消耗）
            display_rows = min(5, len(data))
            display_data = data.tail(display_rows)
            latest_data = data.iloc[-1]

            # 🔍 [调试日志] 打印最近5天的原始数据和技术指标
            logger.info(f"🔍 [港股技术指标详情] ===== 最近{display_rows}个交易日数据 =====")
            for i, (idx, row) in enumerate(display_data.iterrows(), 1):
                date_str = row.get('Date', idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx))
                logger.info(f"🔍 [港股技术指标详情] 第{i}天 ({date_str}):")
                logger.info(f"   价格: 开={row.get('Open', 0):.2f}, 高={row.get('High', 0):.2f}, 低={row.get('Low', 0):.2f}, 收={row.get('Close', 0):.2f}")
                logger.info(f"   MA: MA5={row.get('ma5', 0):.2f}, MA10={row.get('ma10', 0):.2f}, MA20={row.get('ma20', 0):.2f}, MA60={row.get('ma60', 0):.2f}")
                logger.info(f"   MACD: DIF={row.get('macd_dif', 0):.4f}, DEA={row.get('macd_dea', 0):.4f}, MACD={row.get('macd', 0):.4f}")
                logger.info(f"   RSI: {row.get('rsi', 0):.2f}")
                logger.info(f"   BOLL: 上={row.get('boll_upper', 0):.2f}, 中={row.get('boll_mid', 0):.2f}, 下={row.get('boll_lower', 0):.2f}")

            logger.info(f"🔍 [港股技术指标详情] ===== 数据详情结束 =====")

            # 格式化输出包含所有技术指标和解读
            result = f"📊 {stock_name}({symbol}) - 港股技术分析数据\n"
            result += "=" * 60 + "\n\n"

            # 基本信息
            result += "📈 基本信息\n"
            result += f"   代码: {symbol}\n"
            result += f"   名称: {stock_name}\n"
            result += f"   货币: 港币 (HKD)\n"
            result += f"   交易所: 香港交易所 (HKG)\n"
            result += f"   数据期间: {start_date} 至 {end_date}\n"
            result += f"   交易天数: {len(data)}天\n\n"

            # 最新价格
            latest_price = latest_data['Close']
            result += "💰 最新价格\n"
            result += f"   收盘价: HK${latest_price:.2f}\n"
            result += f"   开盘价: HK${latest_data['Open']:.2f}\n"
            result += f"   最高价: HK${latest_data['High']:.2f}\n"
            result += f"   最低价: HK${latest_data['Low']:.2f}\n"
            result += f"   成交量: {latest_data['Volume']:,.0f}股\n\n"

            # 移动平均线
            result += "📊 移动平均线 (MA)\n"
            ma5 = latest_data['ma5']
            ma10 = latest_data['ma10']
            ma20 = latest_data['ma20']
            ma60 = latest_data['ma60']

            if not pd.isna(ma5):
                ma5_diff = ((latest_price - ma5) / ma5) * 100
                ma5_pos = "上方" if latest_price > ma5 else "下方"
                result += f"   MA5: HK${ma5:.2f} (价格在MA5{ma5_pos} {abs(ma5_diff):.2f}%)\n"

            if not pd.isna(ma10):
                ma10_diff = ((latest_price - ma10) / ma10) * 100
                ma10_pos = "上方" if latest_price > ma10 else "下方"
                result += f"   MA10: HK${ma10:.2f} (价格在MA10{ma10_pos} {abs(ma10_diff):.2f}%)\n"

            if not pd.isna(ma20):
                ma20_diff = ((latest_price - ma20) / ma20) * 100
                ma20_pos = "上方" if latest_price > ma20 else "下方"
                result += f"   MA20: HK${ma20:.2f} (价格在MA20{ma20_pos} {abs(ma20_diff):.2f}%)\n"

            if not pd.isna(ma60):
                ma60_diff = ((latest_price - ma60) / ma60) * 100
                ma60_pos = "上方" if latest_price > ma60 else "下方"
                result += f"   MA60: HK${ma60:.2f} (价格在MA60{ma60_pos} {abs(ma60_diff):.2f}%)\n"

            # 判断均线排列
            if not pd.isna(ma5) and not pd.isna(ma10) and not pd.isna(ma20):
                if ma5 > ma10 > ma20:
                    result += "   ✅ 均线呈多头排列\n\n"
                elif ma5 < ma10 < ma20:
                    result += "   ⚠️ 均线呈空头排列\n\n"
                else:
                    result += "   ➡️ 均线排列混乱\n\n"
            else:
                result += "\n"

            # MACD指标
            result += "📉 MACD指标\n"
            macd_dif = latest_data['macd_dif']
            macd_dea = latest_data['macd_dea']
            macd = latest_data['macd']

            if not pd.isna(macd_dif) and not pd.isna(macd_dea):
                result += f"   DIF: {macd_dif:.4f}\n"
                result += f"   DEA: {macd_dea:.4f}\n"
                result += f"   MACD柱: {macd:.4f} ({'多头' if macd > 0 else '空头'})\n"

                # MACD金叉/死叉检测
                if len(data) > 1:
                    prev_dif = data.iloc[-2]['macd_dif']
                    prev_dea = data.iloc[-2]['macd_dea']
                    curr_dif = latest_data['macd_dif']
                    curr_dea = latest_data['macd_dea']

                    if not pd.isna(prev_dif) and not pd.isna(prev_dea):
                        if prev_dif <= prev_dea and curr_dif > curr_dea:
                            result += "   ⚠️ MACD金叉信号（DIF上穿DEA）\n\n"
                        elif prev_dif >= prev_dea and curr_dif < curr_dea:
                            result += "   ⚠️ MACD死叉信号（DIF下穿DEA）\n\n"
                        else:
                            result += "\n"
                    else:
                        result += "\n"
                else:
                    result += "\n"
            else:
                result += "   数据不足，无法计算MACD\n\n"

            # RSI指标
            result += "📊 RSI指标\n"
            rsi = latest_data['rsi']

            if not pd.isna(rsi):
                result += f"   RSI(14): {rsi:.2f}"
                if rsi >= 70:
                    result += " (超买区域)\n\n"
                elif rsi <= 30:
                    result += " (超卖区域)\n\n"
                elif rsi >= 60:
                    result += " (接近超买区域)\n\n"
                elif rsi <= 40:
                    result += " (接近超卖区域)\n\n"
                else:
                    result += " (中性区域)\n\n"
            else:
                result += "   数据不足，无法计算RSI\n\n"

            # 布林带
            result += "📐 布林带 (BOLL)\n"
            boll_upper = latest_data['boll_upper']
            boll_mid = latest_data['boll_mid']
            boll_lower = latest_data['boll_lower']

            if not pd.isna(boll_upper) and not pd.isna(boll_mid) and not pd.isna(boll_lower):
                result += f"   上轨: HK${boll_upper:.2f}\n"
                result += f"   中轨: HK${boll_mid:.2f}\n"
                result += f"   下轨: HK${boll_lower:.2f}\n"

                # 计算价格在布林带中的位置
                boll_width = boll_upper - boll_lower
                if boll_width > 0:
                    boll_position = ((latest_price - boll_lower) / boll_width) * 100
                    result += f"   价格位置: {boll_position:.1f}%"

                    if boll_position >= 90:
                        result += " (接近上轨)\n\n"
                    elif boll_position <= 10:
                        result += " (接近下轨)\n\n"
                    else:
                        result += "\n\n"
                else:
                    result += "\n"
            else:
                result += "   数据不足，无法计算布林带\n\n"

            # 最近交易日数据
            result += "📅 最近交易日数据\n"
            for _, row in display_data.iterrows():
                if 'Date' in row:
                    date_str = row['Date'].strftime('%Y-%m-%d')
                else:
                    date_str = row.name.strftime('%Y-%m-%d')

                result += f"   {date_str}: "
                result += f"开盘HK${row['Open']:.2f}, "
                result += f"收盘HK${row['Close']:.2f}, "
                result += f"最高HK${row['High']:.2f}, "
                result += f"最低HK${row['Low']:.2f}, "
                result += f"成交量{row['Volume']:,.0f}\n"

            result += "\n数据来源: Yahoo Finance (港股)\n"

            logger.info(f"✅ [港股技术指标] 技术指标计算完成，展示最后{display_rows}天数据")

            return result

        except Exception as e:
            logger.error(f"❌ 格式化港股数据失败: {e}", exc_info=True)
            return f"❌ 港股数据格式化失败: {symbol}"


# 全局提供器实例
_hk_provider = None

def get_hk_stock_provider() -> HKStockProvider:
    """获取全局港股提供器实例"""
    global _hk_provider
    if _hk_provider is None:
        _hk_provider = HKStockProvider()
    return _hk_provider


def get_hk_stock_data(symbol: str, start_date: str = None, end_date: str = None) -> str:
    """
    获取港股数据的便捷函数

    Args:
        symbol: 港股代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的港股数据
    """
    provider = get_hk_stock_provider()
    data = provider.get_stock_data(symbol, start_date, end_date)
    return provider.format_stock_data(symbol, data, start_date, end_date)


def get_hk_stock_info(symbol: str) -> Dict:
    """
    获取港股信息的便捷函数

    Args:
        symbol: 港股代码

    Returns:
        Dict: 港股信息
    """
    provider = get_hk_stock_provider()
    return provider.get_stock_info(symbol)
