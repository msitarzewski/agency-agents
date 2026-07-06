"""
示例SDK适配器实现 (tradingagents层)
展示如何基于BaseStockDataProvider创建新的数据源适配器

架构说明:
- tradingagents层: 纯数据获取和标准化，不涉及数据库操作
- app层: 数据同步服务，负责调用此适配器并写入数据库
- 职责分离: 适配器只负责数据获取，同步服务负责数据存储
"""
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
import pandas as pd

import os
from ..base_provider import BaseStockDataProvider


class ExampleSDKProvider(BaseStockDataProvider):
    """
    示例SDK数据提供器 (tradingagents层)

    职责:
    - 连接外部SDK API
    - 获取原始数据
    - 数据标准化处理
    - 返回标准格式数据

    注意:
    - 不涉及数据库操作
    - 不包含业务逻辑
    - 专注于数据获取和格式转换
    - 由app层的同步服务调用
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, **kwargs):
        super().__init__("ExampleSDK")
        
        # 配置参数
        self.api_key = api_key or os.getenv("EXAMPLE_SDK_API_KEY")
        self.base_url = base_url or os.getenv("EXAMPLE_SDK_BASE_URL", "https://api.example-sdk.com")
        self.timeout = int(os.getenv("EXAMPLE_SDK_TIMEOUT", "30"))
        self.enabled = os.getenv("EXAMPLE_SDK_ENABLED", "false").lower() == "true"
        
        # HTTP会话
        self.session = None
        
        # 请求头
        self.headers = {
            "User-Agent": "TradingAgents/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def connect(self) -> bool:
        """连接到数据源"""
        if not self.enabled:
            self.logger.warning("ExampleSDK未启用")
            return False
        
        if not self.api_key:
            self.logger.error("ExampleSDK API密钥未配置")
            return False
        
        try:
            # 创建HTTP会话
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
            
            # 测试连接
            test_url = f"{self.base_url}/ping"
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    self.connected = True
                    self.logger.info("ExampleSDK连接成功")
                    return True
                else:
                    self.logger.error(f"ExampleSDK连接失败: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self._handle_error(e, "ExampleSDK连接失败")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.connected = False
        self.logger.info("ExampleSDK连接已断开")
    
    async def get_stock_basic_info(self, symbol: str = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """获取股票基础信息"""
        if not self.connected:
            await self.connect()
        
        try:
            if symbol:
                # 获取单个股票信息
                url = f"{self.base_url}/stocks/{symbol}/info"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.standardize_basic_info(data)
                    else:
                        self.logger.warning(f"获取{symbol}基础信息失败: HTTP {response.status}")
                        return None
            else:
                # 获取所有股票信息
                url = f"{self.base_url}/stocks/list"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [self.standardize_basic_info(item) for item in data.get("stocks", [])]
                    else:
                        self.logger.warning(f"获取股票列表失败: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            self._handle_error(e, f"获取股票基础信息失败 symbol={symbol}")
            return None
    
    async def get_stock_list(self, market: str = None) -> Optional[List[Dict[str, Any]]]:
        """获取股票列表"""
        if not self.connected:
            await self.connect()
        
        try:
            url = f"{self.base_url}/stocks/list"
            params = {}
            if market:
                params["market"] = market
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self.standardize_basic_info(item) for item in data.get("stocks", [])]
                else:
                    self.logger.warning(f"获取股票列表失败: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self._handle_error(e, f"获取股票列表失败 market={market}")
            return None
    
    async def get_stock_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        if not self.connected:
            await self.connect()
        
        try:
            url = f"{self.base_url}/stocks/{symbol}/quote"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.standardize_quotes(data)
                else:
                    self.logger.warning(f"获取{symbol}实时行情失败: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self._handle_error(e, f"获取实时行情失败 symbol={symbol}")
            return None
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: Union[str, date], 
        end_date: Union[str, date] = None,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """获取历史数据"""
        if not self.connected:
            await self.connect()
        
        try:
            url = f"{self.base_url}/stocks/{symbol}/history"
            params = {
                "start_date": str(start_date),
                "period": period
            }
            
            if end_date:
                params["end_date"] = str(end_date)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._convert_to_dataframe(data.get("history", []))
                else:
                    self.logger.warning(f"获取{symbol}历史数据失败: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self._handle_error(e, f"获取历史数据失败 symbol={symbol}")
            return None
    
    async def get_financial_data(self, symbol: str, report_type: str = "annual") -> Optional[Dict[str, Any]]:
        """获取财务数据"""
        if not self.connected:
            await self.connect()
        
        try:
            url = f"{self.base_url}/stocks/{symbol}/financials"
            params = {"type": report_type}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._standardize_financial_data(data)
                else:
                    self.logger.warning(f"获取{symbol}财务数据失败: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self._handle_error(e, f"获取财务数据失败 symbol={symbol}")
            return None
    
    async def get_stock_news(self, symbol: str = None, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """获取股票新闻"""
        if not self.connected:
            await self.connect()
        
        try:
            if symbol:
                url = f"{self.base_url}/stocks/{symbol}/news"
            else:
                url = f"{self.base_url}/news/market"
            
            params = {"limit": limit}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._standardize_news(item) for item in data.get("news", [])]
                else:
                    self.logger.warning(f"获取新闻失败: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            self._handle_error(e, f"获取新闻失败 symbol={symbol}")
            return None
    
    # ==================== 数据转换方法 ====================
    
    def standardize_basic_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化股票基础信息 - 重写以适配ExampleSDK格式"""
        # 字段映射 (根据实际SDK的字段名称调整)
        mapped_data = {
            "symbol": raw_data.get("ticker", raw_data.get("symbol")),
            "name": raw_data.get("company_name", raw_data.get("name")),
            "industry": raw_data.get("sector", raw_data.get("industry")),
            "area": raw_data.get("region", raw_data.get("area")),
            "market_cap": raw_data.get("market_capitalization"),
            "list_date": raw_data.get("listing_date"),
            "pe": raw_data.get("pe_ratio"),
            "pb": raw_data.get("pb_ratio"),
            "roe": raw_data.get("return_on_equity")
        }
        
        # 调用父类的标准化方法
        return super().standardize_basic_info(mapped_data)
    
    def standardize_quotes(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化实时行情数据 - 重写以适配ExampleSDK格式"""
        # 字段映射
        mapped_data = {
            "symbol": raw_data.get("ticker", raw_data.get("symbol")),
            "price": raw_data.get("last_price", raw_data.get("current_price")),
            "open": raw_data.get("open_price"),
            "high": raw_data.get("high_price"),
            "low": raw_data.get("low_price"),
            "prev_close": raw_data.get("previous_close"),
            "change_percent": raw_data.get("percent_change"),
            "volume": raw_data.get("trading_volume"),
            "turnover": raw_data.get("trading_value"),
            "date": raw_data.get("trading_date"),
            "timestamp": raw_data.get("last_updated")
        }
        
        # 调用父类的标准化方法
        return super().standardize_quotes(mapped_data)
    
    def _convert_to_dataframe(self, history_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """将历史数据转换为DataFrame"""
        if not history_data:
            return pd.DataFrame()
        
        # 标准化每条记录
        standardized_data = []
        for item in history_data:
            standardized_item = {
                "date": item.get("date"),
                "open": self._convert_to_float(item.get("open")),
                "high": self._convert_to_float(item.get("high")),
                "low": self._convert_to_float(item.get("low")),
                "close": self._convert_to_float(item.get("close")),
                "volume": self._convert_to_float(item.get("volume")),
                "amount": self._convert_to_float(item.get("amount"))
            }
            standardized_data.append(standardized_item)
        
        df = pd.DataFrame(standardized_data)
        
        # 设置日期索引
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
        
        return df
    
    def _standardize_financial_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化财务数据"""
        return {
            "symbol": raw_data.get("ticker", raw_data.get("symbol")),
            "report_period": raw_data.get("period"),
            "report_type": raw_data.get("type", "annual"),
            "revenue": self._convert_to_float(raw_data.get("total_revenue")),
            "net_income": self._convert_to_float(raw_data.get("net_income")),
            "total_assets": self._convert_to_float(raw_data.get("total_assets")),
            "total_equity": self._convert_to_float(raw_data.get("shareholders_equity")),
            "cash_flow": self._convert_to_float(raw_data.get("operating_cash_flow")),
            "data_source": self.name.lower(),
            "updated_at": datetime.utcnow()
        }
    
    def _standardize_news(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化新闻数据"""
        return {
            "title": raw_data.get("headline", raw_data.get("title")),
            "content": raw_data.get("summary", raw_data.get("content")),
            "url": raw_data.get("url"),
            "source": raw_data.get("source"),
            "publish_time": self._parse_timestamp(raw_data.get("published_at")),
            "sentiment": raw_data.get("sentiment"),
            "symbols": raw_data.get("related_symbols", []),
            "data_source": self.name.lower(),
            "created_at": datetime.utcnow()
        }
    
    # ==================== 清理资源 ====================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    # 方式1: 直接使用
    provider = ExampleSDKProvider(api_key="your_api_key")
    
    try:
        # 连接
        if await provider.connect():
            # 获取股票基础信息
            basic_info = await provider.get_stock_basic_info("000001")
            print(f"基础信息: {basic_info}")
            
            # 获取实时行情
            quotes = await provider.get_stock_quotes("000001")
            print(f"实时行情: {quotes}")
            
            # 获取历史数据
            history = await provider.get_historical_data("000001", "2024-01-01", "2024-01-31")
            print(f"历史数据: {history.head() if history is not None else None}")
            
    finally:
        await provider.disconnect()
    
    # 方式2: 使用上下文管理器
    async with ExampleSDKProvider(api_key="your_api_key") as provider:
        basic_info = await provider.get_stock_basic_info("000001")
        print(f"基础信息: {basic_info}")


if __name__ == "__main__":
    asyncio.run(example_usage())
