#!/usr/bin/env python3
"""
MongoDB 缓存适配器
根据 TA_USE_APP_CACHE 配置，优先使用 MongoDB 中的同步数据
"""

import pandas as pd
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta, timezone

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# 导入配置
from tradingagents.config.runtime_settings import use_app_cache_enabled

class MongoDBCacheAdapter:
    """MongoDB 缓存适配器（从 app 的 MongoDB 读取同步数据）"""
    
    def __init__(self):
        self.use_app_cache = use_app_cache_enabled(False)
        self.mongodb_client = None
        self.db = None
        
        if self.use_app_cache:
            self._init_mongodb_connection()
            logger.info("🔄 MongoDB缓存适配器已启用 - 优先使用MongoDB数据")
        else:
            logger.info("📁 MongoDB缓存适配器使用传统缓存模式")
    
    def _init_mongodb_connection(self):
        """初始化MongoDB连接"""
        try:
            from tradingagents.config.database_manager import get_mongodb_client
            self.mongodb_client = get_mongodb_client()
            if self.mongodb_client:
                self.db = self.mongodb_client.get_database('tradingagents')
                logger.debug("✅ MongoDB连接初始化成功")
            else:
                logger.warning("⚠️ MongoDB客户端不可用，回退到传统模式")
                self.use_app_cache = False
        except Exception as e:
            logger.warning(f"⚠️ MongoDB连接初始化失败: {e}")
            self.use_app_cache = False
    
    def get_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基础信息（按数据源优先级查询）"""
        if not self.use_app_cache or self.db is None:
            return None

        try:
            code6 = str(symbol).zfill(6)
            collection = self.db.stock_basic_info

            # 🔥 获取数据源优先级
            source_priority = self._get_data_source_priority(symbol)

            # 🔥 按优先级查询
            doc = None
            for src in source_priority:
                doc = collection.find_one({"code": code6, "source": src}, {"_id": 0})
                if doc:
                    logger.debug(f"✅ 从MongoDB获取基础信息: {symbol}, 数据源: {src}")
                    return doc

            # 如果所有数据源都没有，尝试不带 source 条件查询（兼容旧数据）
            if not doc:
                doc = collection.find_one({"code": code6}, {"_id": 0})
                if doc:
                    logger.debug(f"✅ 从MongoDB获取基础信息（旧数据）: {symbol}")
                    return doc
                else:
                    logger.debug(f"📊 MongoDB中未找到基础信息: {symbol}")
                    return None

        except Exception as e:
            logger.warning(f"⚠️ 获取基础信息失败: {e}")
            return None
    
    def _get_data_source_priority(self, symbol: str) -> list:
        """
        获取数据源优先级顺序

        Args:
            symbol: 股票代码

        Returns:
            按优先级排序的数据源列表，例如: ["tushare", "akshare", "baostock"]
        """
        try:
            # 1. 识别市场分类
            from tradingagents.utils.stock_utils import StockUtils, StockMarket
            market = StockUtils.identify_stock_market(symbol)

            market_mapping = {
                StockMarket.CHINA_A: 'a_shares',
                StockMarket.US: 'us_stocks',
                StockMarket.HONG_KONG: 'hk_stocks',
            }
            market_category = market_mapping.get(market)
            logger.info(f"📊 [数据源优先级] 股票代码: {symbol}, 市场分类: {market_category}")

            # 2. 从数据库读取配置
            if self.db is not None:
                config_collection = self.db.system_configs
                config_data = config_collection.find_one(
                    {"is_active": True},
                    sort=[("version", -1)]
                )

                if config_data and config_data.get('data_source_configs'):
                    configs = config_data['data_source_configs']
                    logger.info(f"📊 [数据源优先级] 从数据库读取到 {len(configs)} 个数据源配置")

                    # 3. 过滤启用的数据源
                    enabled = []
                    for ds in configs:
                        ds_type = ds.get('type', '')
                        ds_enabled = ds.get('enabled', True)
                        ds_priority = ds.get('priority', 0)
                        ds_categories = ds.get('market_categories', [])

                        logger.info(f"📊 [数据源配置] 类型: {ds_type}, 启用: {ds_enabled}, 优先级: {ds_priority}, 市场: {ds_categories}")

                        if not ds_enabled:
                            logger.info(f"⚠️ [数据源优先级] {ds_type} 未启用，跳过")
                            continue

                        # 检查市场分类
                        if ds_categories and market_category:
                            if market_category not in ds_categories:
                                logger.info(f"⚠️ [数据源优先级] {ds_type} 不支持市场 {market_category}，跳过")
                                continue

                        enabled.append(ds)

                    logger.info(f"📊 [数据源优先级] 过滤后启用的数据源: {len(enabled)} 个")

                    # 4. 按优先级排序（数字越大优先级越高）
                    enabled.sort(key=lambda x: x.get('priority', 0), reverse=True)

                    # 5. 返回数据源类型列表
                    result = [ds.get('type', '').lower() for ds in enabled if ds.get('type')]
                    if result:
                        logger.info(f"✅ [数据源优先级] {symbol} ({market_category}): {result}")
                        return result
                    else:
                        logger.warning(f"⚠️ [数据源优先级] 没有可用的数据源配置，使用默认顺序")
                else:
                    logger.warning(f"⚠️ [数据源优先级] 数据库中没有找到数据源配置")

        except Exception as e:
            logger.error(f"❌ 获取数据源优先级失败: {e}", exc_info=True)

        # 默认顺序：Tushare > AKShare > BaoStock
        logger.info(f"📊 [数据源优先级] 使用默认顺序: ['tushare', 'akshare', 'baostock']")
        return ['tushare', 'akshare', 'baostock']

    def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None,
                          period: str = "daily") -> Optional[pd.DataFrame]:
        """
        获取历史数据，支持多周期，按数据源优先级查询

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期（daily/weekly/monthly），默认为daily

        Returns:
            DataFrame: 历史数据
        """
        if not self.use_app_cache or self.db is None:
            return None

        try:
            code6 = str(symbol).zfill(6)
            collection = self.db.stock_daily_quotes

            # 获取数据源优先级
            priority_order = self._get_data_source_priority(symbol)

            # 按优先级查询
            for data_source in priority_order:
                # 构建查询条件
                query = {
                    "symbol": code6,
                    "period": period,
                    "data_source": data_source  # 指定数据源
                }

                if start_date:
                    query["trade_date"] = {"$gte": start_date}
                if end_date:
                    if "trade_date" in query:
                        query["trade_date"]["$lte"] = end_date
                    else:
                        query["trade_date"] = {"$lte": end_date}

                # 查询数据
                logger.debug(f"🔍 [MongoDB查询] 尝试数据源: {data_source}, symbol={code6}, period={period}")
                cursor = collection.find(query, {"_id": 0}).sort("trade_date", 1)
                data = list(cursor)

                if data:
                    df = pd.DataFrame(data)
                    logger.info(f"✅ [数据来源: MongoDB-{data_source}] {symbol}, {len(df)}条记录 (period={period})")
                    return df
                else:
                    logger.debug(f"⚠️ [MongoDB-{data_source}] 未找到{period}数据: {symbol}")

            # 所有数据源都没有数据
            logger.warning(f"⚠️ [数据来源: MongoDB] 所有数据源({', '.join(priority_order)})都没有{period}数据: {symbol}，降级到其他数据源")
            return None

        except Exception as e:
            logger.warning(f"⚠️ 获取历史数据失败: {e}")
            return None
    
    def get_financial_data(self, symbol: str, report_period: str = None) -> Optional[Dict[str, Any]]:
        """获取财务数据，按数据源优先级查询"""
        if not self.use_app_cache or self.db is None:
            return None

        try:
            code6 = str(symbol).zfill(6)
            collection = self.db.stock_financial_data

            # 获取数据源优先级
            priority_order = self._get_data_source_priority(symbol)

            # 按优先级查询
            for data_source in priority_order:
                # 构建查询条件
                query = {
                    "code": code6,
                    "data_source": data_source  # 指定数据源
                }
                if report_period:
                    query["report_period"] = report_period

                # 获取最新的财务数据
                doc = collection.find_one(query, {"_id": 0}, sort=[("report_period", -1)])

                if doc:
                    logger.info(f"✅ [数据来源: MongoDB-{data_source}] {symbol}财务数据")
                    logger.debug(f"📊 [财务数据] 成功提取{symbol}的财务数据，包含字段: {list(doc.keys())}")
                    return doc

            # 所有数据源都没有数据
            logger.debug(f"📊 [数据来源: MongoDB] 所有数据源都没有财务数据: {symbol}")
            return None

        except Exception as e:
            logger.warning(f"⚠️ [数据来源: MongoDB-财务数据] 获取财务数据失败: {e}")
            return None
    
    def get_news_data(self, symbol: str = None, hours_back: int = 24, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """获取新闻数据"""
        if not self.use_app_cache or self.db is None:
            return None

        try:
            collection = self.db.stock_news  # 修正集合名称
            
            # 构建查询条件
            query = {}
            if symbol:
                code6 = str(symbol).zfill(6)
                query["symbol"] = code6
            
            # 时间范围
            if hours_back:
                start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                query["publish_time"] = {"$gte": start_time}
            
            # 查询数据
            cursor = collection.find(query, {"_id": 0}).sort("publish_time", -1).limit(limit)
            data = list(cursor)
            
            if data:
                logger.debug(f"✅ [数据来源: MongoDB-新闻数据] 从MongoDB获取新闻数据: {len(data)}条")
                return data
            else:
                logger.debug(f"📊 [数据来源: MongoDB-新闻数据] MongoDB中未找到新闻数据")
                return None

        except Exception as e:
            logger.warning(f"⚠️ [数据来源: MongoDB-新闻数据] 获取新闻数据失败: {e}")
            return None
    
    def get_social_media_data(self, symbol: str = None, hours_back: int = 24, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """获取社媒数据"""
        if not self.use_app_cache or self.db is None:
            return None
            
        try:
            collection = self.db.social_media_messages
            
            # 构建查询条件
            query = {}
            if symbol:
                code6 = str(symbol).zfill(6)
                query["symbol"] = code6
            
            # 时间范围
            if hours_back:
                start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                query["publish_time"] = {"$gte": start_time}
            
            # 查询数据
            cursor = collection.find(query, {"_id": 0}).sort("publish_time", -1).limit(limit)
            data = list(cursor)
            
            if data:
                logger.debug(f"✅ 从MongoDB获取社媒数据: {len(data)}条")
                return data
            else:
                logger.debug(f"📊 MongoDB中未找到社媒数据")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ 获取社媒数据失败: {e}")
            return None
    
    def get_market_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情数据"""
        if not self.use_app_cache or self.db is None:
            return None
            
        try:
            code6 = str(symbol).zfill(6)
            collection = self.db.market_quotes
            
            # 获取最新行情
            doc = collection.find_one({"code": code6}, {"_id": 0}, sort=[("timestamp", -1)])
            
            if doc:
                logger.debug(f"✅ 从MongoDB获取行情数据: {symbol}")
                return doc
            else:
                logger.debug(f"📊 MongoDB中未找到行情数据: {symbol}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ 获取行情数据失败: {e}")
            return None


# 全局实例
_mongodb_cache_adapter = None

def get_mongodb_cache_adapter() -> MongoDBCacheAdapter:
    """获取 MongoDB 缓存适配器实例"""
    global _mongodb_cache_adapter
    if _mongodb_cache_adapter is None:
        _mongodb_cache_adapter = MongoDBCacheAdapter()
    return _mongodb_cache_adapter

# 向后兼容的别名
def get_enhanced_data_adapter() -> MongoDBCacheAdapter:
    """获取增强数据适配器实例（向后兼容，推荐使用 get_mongodb_cache_adapter）"""
    return get_mongodb_cache_adapter()


def get_stock_data_with_fallback(symbol: str, start_date: str = None, end_date: str = None, 
                                fallback_func=None) -> Union[pd.DataFrame, str, None]:
    """
    带降级的股票数据获取
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        fallback_func: 降级函数
    
    Returns:
        优先返回MongoDB数据，失败时调用降级函数
    """
    adapter = get_enhanced_data_adapter()
    
    # 尝试从MongoDB获取
    if adapter.use_app_cache:
        df = adapter.get_historical_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            logger.info(f"📊 使用MongoDB历史数据: {symbol}")
            return df
    
    # 降级到传统方式
    if fallback_func:
        logger.info(f"🔄 降级到传统数据源: {symbol}")
        return fallback_func(symbol, start_date, end_date)
    
    return None


def get_financial_data_with_fallback(symbol: str, fallback_func=None) -> Union[Dict[str, Any], str, None]:
    """
    带降级的财务数据获取
    
    Args:
        symbol: 股票代码
        fallback_func: 降级函数
    
    Returns:
        优先返回MongoDB数据，失败时调用降级函数
    """
    adapter = get_enhanced_data_adapter()
    
    # 尝试从MongoDB获取
    if adapter.use_app_cache:
        data = adapter.get_financial_data(symbol)
        if data:
            logger.info(f"💰 使用MongoDB财务数据: {symbol}")
            return data
    
    # 降级到传统方式
    if fallback_func:
        logger.info(f"🔄 降级到传统数据源: {symbol}")
        return fallback_func(symbol)
    
    return None
