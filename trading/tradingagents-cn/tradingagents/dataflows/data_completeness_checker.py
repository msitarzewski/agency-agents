#!/usr/bin/env python3
"""
数据完整性检查器
用于检查历史数据是否完整、是否包含最新交易日，并在需要时自动重新拉取
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import pandas as pd

logger = logging.getLogger(__name__)


class DataCompletenessChecker:
    """数据完整性检查器"""
    
    def __init__(self):
        self.logger = logger
    
    def check_data_completeness(
        self,
        symbol: str,
        data: str,
        start_date: str,
        end_date: str,
        market: str = "CN"
    ) -> Tuple[bool, str, dict]:
        """
        检查数据完整性
        
        Args:
            symbol: 股票代码
            data: 数据字符串
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            market: 市场类型 (CN/HK/US)
        
        Returns:
            (is_complete, message, details)
            - is_complete: 数据是否完整
            - message: 检查结果消息
            - details: 详细信息字典
        """
        details = {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "market": market,
            "data_rows": 0,
            "expected_rows": 0,
            "missing_days": 0,
            "has_latest_trade_date": False,
            "latest_date_in_data": None,
            "latest_trade_date": None,
            "completeness_ratio": 0.0
        }
        
        # 1. 检查数据是否为空或错误
        if not data or "❌" in data or "错误" in data or "获取失败" in data:
            return False, "数据为空或包含错误", details
        
        # 2. 尝试解析数据
        try:
            df = self._parse_data_to_dataframe(data)
            if df is None or df.empty:
                return False, "无法解析数据或数据为空", details
            
            details["data_rows"] = len(df)
            
            # 3. 获取数据中的日期范围
            if 'date' in df.columns:
                date_col = 'date'
            elif 'trade_date' in df.columns:
                date_col = 'trade_date'
            else:
                # 尝试查找日期列
                date_col = None
                for col in df.columns:
                    if 'date' in col.lower() or '日期' in col:
                        date_col = col
                        break
                
                if not date_col:
                    self.logger.warning(f"⚠️ 无法找到日期列: {symbol}")
                    return False, "无法找到日期列", details
            
            # 转换日期列为 datetime
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            
            data_start_date = df[date_col].min()
            data_end_date = df[date_col].max()
            details["latest_date_in_data"] = data_end_date.strftime('%Y-%m-%d')
            
            # 4. 获取最新交易日
            latest_trade_date = self._get_latest_trade_date(market)
            details["latest_trade_date"] = latest_trade_date
            
            # 5. 检查是否包含最新交易日
            if latest_trade_date:
                latest_trade_dt = datetime.strptime(latest_trade_date, '%Y-%m-%d')
                details["has_latest_trade_date"] = data_end_date.date() >= latest_trade_dt.date()
            
            # 6. 计算预期交易日数量（粗略估算）
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            total_days = (end_dt - start_dt).days + 1
            
            # 假设交易日约占总天数的 70%（考虑周末和节假日）
            expected_trade_days = int(total_days * 0.7)
            details["expected_rows"] = expected_trade_days
            
            # 7. 计算完整性比率
            if expected_trade_days > 0:
                completeness_ratio = len(df) / expected_trade_days
                details["completeness_ratio"] = completeness_ratio
            
            # 8. 检查数据缺口
            missing_days = self._check_data_gaps(df, date_col)
            details["missing_days"] = len(missing_days)
            
            # 9. 综合判断
            is_complete = True
            messages = []
            
            # 检查1：数据量是否足够
            if len(df) < expected_trade_days * 0.5:  # 少于预期的50%
                is_complete = False
                messages.append(f"数据量不足（{len(df)}条，预期约{expected_trade_days}条）")
            
            # 检查2：是否包含最新交易日
            if not details["has_latest_trade_date"]:
                is_complete = False
                messages.append(f"缺少最新交易日数据（最新: {details['latest_date_in_data']}, 应为: {latest_trade_date}）")
            
            # 检查3：是否有较多缺口
            if len(missing_days) > expected_trade_days * 0.1:  # 缺口超过10%
                is_complete = False
                messages.append(f"数据缺口较多（{len(missing_days)}个缺口）")
            
            if is_complete:
                message = f"✅ 数据完整（{len(df)}条记录，完整性{completeness_ratio:.1%}）"
            else:
                message = "⚠️ 数据不完整: " + "; ".join(messages)
            
            return is_complete, message, details
            
        except Exception as e:
            self.logger.error(f"❌ 检查数据完整性失败: {e}")
            return False, f"检查失败: {str(e)}", details
    
    def _parse_data_to_dataframe(self, data: str) -> Optional[pd.DataFrame]:
        """将数据字符串解析为 DataFrame"""
        try:
            # 尝试多种解析方式
            
            # 方式1：假设是 CSV 格式
            from io import StringIO
            try:
                df = pd.read_csv(StringIO(data))
                if not df.empty:
                    return df
            except Exception:
                pass
            
            # 方式2：假设是 TSV 格式
            try:
                df = pd.read_csv(StringIO(data), sep='\t')
                if not df.empty:
                    return df
            except Exception:
                pass
            
            # 方式3：假设是空格分隔
            try:
                df = pd.read_csv(StringIO(data), sep=r'\s+')
                if not df.empty:
                    return df
            except Exception:
                pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 解析数据失败: {e}")
            return None
    
    def _get_latest_trade_date(self, market: str = "CN") -> Optional[str]:
        """获取最新交易日"""
        try:
            if market == "CN":
                # A股：使用 Tushare 查找最新交易日
                from tradingagents.dataflows.providers.china.tushare import TushareProvider
                import asyncio
                
                provider = TushareProvider()
                if provider.is_available():
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    latest_date = loop.run_until_complete(provider.find_latest_trade_date())
                    if latest_date:
                        return latest_date
            
            # 备用方案：假设最新交易日是今天或昨天（如果今天是周末则往前推）
            today = datetime.now()
            for delta in range(0, 5):  # 最多回溯5天
                check_date = today - timedelta(days=delta)
                # 跳过周末
                if check_date.weekday() < 5:  # 0-4 是周一到周五
                    return check_date.strftime('%Y-%m-%d')
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 获取最新交易日失败: {e}")
            return None
    
    def _check_data_gaps(self, df: pd.DataFrame, date_col: str) -> List[str]:
        """检查数据缺口"""
        try:
            df = df.sort_values(date_col)
            dates = df[date_col].tolist()
            
            missing_dates = []
            for i in range(len(dates) - 1):
                current_date = dates[i]
                next_date = dates[i + 1]
                
                # 计算日期差
                delta = (next_date - current_date).days
                
                # 如果差距大于3天（考虑周末），可能有缺口
                if delta > 3:
                    missing_dates.append(f"{current_date.strftime('%Y-%m-%d')} 到 {next_date.strftime('%Y-%m-%d')}")
            
            return missing_dates
            
        except Exception as e:
            self.logger.error(f"❌ 检查数据缺口失败: {e}")
            return []


# 全局实例
_checker = None

def get_data_completeness_checker() -> DataCompletenessChecker:
    """获取数据完整性检查器实例"""
    global _checker
    if _checker is None:
        _checker = DataCompletenessChecker()
    return _checker

