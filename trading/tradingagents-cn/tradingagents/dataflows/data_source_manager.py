#!/usr/bin/env python3
"""
数据源管理器
统一管理中国股票数据源的选择和切换，支持Tushare、AKShare、BaoStock等
"""

import os
import time
from typing import Dict, List, Optional, Any
from enum import Enum
import warnings
import pandas as pd
import numpy as np

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')

# 导入统一日志系统
from tradingagents.utils.logging_init import setup_dataflow_logging
logger = setup_dataflow_logging()

# 导入统一数据源编码
from tradingagents.constants import DataSourceCode


class ChinaDataSource(Enum):
    """
    中国股票数据源枚举

    注意：这个枚举与 tradingagents.constants.DataSourceCode 保持同步
    值使用统一的数据源编码
    """
    MONGODB = DataSourceCode.MONGODB  # MongoDB数据库缓存（最高优先级）
    TUSHARE = DataSourceCode.TUSHARE
    AKSHARE = DataSourceCode.AKSHARE
    BAOSTOCK = DataSourceCode.BAOSTOCK


class USDataSource(Enum):
    """
    美股数据源枚举

    注意：这个枚举与 tradingagents.constants.DataSourceCode 保持同步
    值使用统一的数据源编码
    """
    MONGODB = DataSourceCode.MONGODB  # MongoDB数据库缓存（最高优先级）
    YFINANCE = DataSourceCode.YFINANCE  # Yahoo Finance（免费，股票价格和技术指标）
    ALPHA_VANTAGE = DataSourceCode.ALPHA_VANTAGE  # Alpha Vantage（基本面和新闻）
    FINNHUB = DataSourceCode.FINNHUB  # Finnhub（备用数据源）





class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        """初始化数据源管理器"""
        # 检查是否启用MongoDB缓存
        self.use_mongodb_cache = self._check_mongodb_enabled()

        self.default_source = self._get_default_source()
        self.available_sources = self._check_available_sources()
        self.current_source = self.default_source

        # 初始化统一缓存管理器
        self.cache_manager = None
        self.cache_enabled = False
        try:
            from .cache import get_cache
            self.cache_manager = get_cache()
            self.cache_enabled = True
            logger.info(f"✅ 统一缓存管理器已启用")
        except Exception as e:
            logger.warning(f"⚠️ 统一缓存管理器初始化失败: {e}")

        logger.info(f"📊 数据源管理器初始化完成")
        logger.info(f"   MongoDB缓存: {'✅ 已启用' if self.use_mongodb_cache else '❌ 未启用'}")
        logger.info(f"   统一缓存: {'✅ 已启用' if self.cache_enabled else '❌ 未启用'}")
        logger.info(f"   默认数据源: {self.default_source.value}")
        logger.info(f"   可用数据源: {[s.value for s in self.available_sources]}")

    def _check_mongodb_enabled(self) -> bool:
        """检查是否启用MongoDB缓存"""
        from tradingagents.config.runtime_settings import use_app_cache_enabled
        return use_app_cache_enabled()

    def _get_data_source_priority_order(self, symbol: Optional[str] = None) -> List[ChinaDataSource]:
        """
        从数据库获取数据源优先级顺序（用于降级）

        Args:
            symbol: 股票代码，用于识别市场类型（A股/美股/港股）

        Returns:
            按优先级排序的数据源列表（不包含MongoDB，因为MongoDB是最高优先级）
        """
        # 🔥 识别市场类型
        market_category = self._identify_market_category(symbol)

        try:
            # 🔥 从数据库读取数据源配置（使用同步客户端）
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()
            config_collection = db.system_configs

            # 获取最新的激活配置
            config_data = config_collection.find_one(
                {"is_active": True},
                sort=[("version", -1)]
            )

            if config_data and config_data.get('data_source_configs'):
                data_source_configs = config_data.get('data_source_configs', [])

                # 🔥 过滤出启用的数据源，并按市场分类过滤
                enabled_sources = []
                for ds in data_source_configs:
                    if not ds.get('enabled', True):
                        continue

                    # 检查数据源是否属于当前市场分类
                    market_categories = ds.get('market_categories', [])
                    if market_categories and market_category:
                        # 如果数据源配置了市场分类，只选择匹配的数据源
                        if market_category not in market_categories:
                            continue

                    enabled_sources.append(ds)

                # 按优先级排序（数字越大优先级越高）
                enabled_sources.sort(key=lambda x: x.get('priority', 0), reverse=True)

                # 转换为 ChinaDataSource 枚举（使用统一编码）
                source_mapping = {
                    DataSourceCode.TUSHARE: ChinaDataSource.TUSHARE,
                    DataSourceCode.AKSHARE: ChinaDataSource.AKSHARE,
                    DataSourceCode.BAOSTOCK: ChinaDataSource.BAOSTOCK,
                }

                result = []
                for ds in enabled_sources:
                    ds_type = ds.get('type', '').lower()
                    if ds_type in source_mapping:
                        source = source_mapping[ds_type]
                        # 排除 MongoDB（MongoDB 是最高优先级，不参与降级）
                        if source != ChinaDataSource.MONGODB and source in self.available_sources:
                            result.append(source)

                if result:
                    logger.info(f"✅ [数据源优先级] 市场={market_category or '全部'}, 从数据库读取: {[s.value for s in result]}")
                    return result
                else:
                    logger.warning(f"⚠️ [数据源优先级] 市场={market_category or '全部'}, 数据库配置中没有可用的数据源，使用默认顺序")
            else:
                logger.warning("⚠️ [数据源优先级] 数据库中没有数据源配置，使用默认顺序")
        except Exception as e:
            logger.warning(f"⚠️ [数据源优先级] 从数据库读取失败: {e}，使用默认顺序")

        # 🔥 回退到默认顺序（兼容性）
        # 默认顺序：AKShare > Tushare > BaoStock
        default_order = [
            ChinaDataSource.AKSHARE,
            ChinaDataSource.TUSHARE,
            ChinaDataSource.BAOSTOCK,
        ]
        # 只返回可用的数据源
        return [s for s in default_order if s in self.available_sources]

    def _identify_market_category(self, symbol: Optional[str]) -> Optional[str]:
        """
        识别股票代码所属的市场分类

        Args:
            symbol: 股票代码

        Returns:
            市场分类ID（a_shares/us_stocks/hk_stocks），如果无法识别则返回None
        """
        if not symbol:
            return None

        try:
            from tradingagents.utils.stock_utils import StockUtils, StockMarket

            market = StockUtils.identify_stock_market(symbol)

            # 映射到市场分类ID
            market_mapping = {
                StockMarket.CHINA_A: 'a_shares',
                StockMarket.US: 'us_stocks',
                StockMarket.HONG_KONG: 'hk_stocks',
            }

            category = market_mapping.get(market)
            if category:
                logger.debug(f"🔍 [市场识别] {symbol} → {category}")
            return category
        except Exception as e:
            logger.warning(f"⚠️ [市场识别] 识别失败: {e}")
            return None

    def _get_default_source(self) -> ChinaDataSource:
        """获取默认数据源"""
        # 如果启用MongoDB缓存，MongoDB作为最高优先级数据源
        if self.use_mongodb_cache:
            return ChinaDataSource.MONGODB

        # 从环境变量获取，默认使用AKShare作为第一优先级数据源
        env_source = os.getenv('DEFAULT_CHINA_DATA_SOURCE', DataSourceCode.AKSHARE).lower()

        # 映射到枚举（使用统一编码）
        source_mapping = {
            DataSourceCode.TUSHARE: ChinaDataSource.TUSHARE,
            DataSourceCode.AKSHARE: ChinaDataSource.AKSHARE,
            DataSourceCode.BAOSTOCK: ChinaDataSource.BAOSTOCK,
        }

        return source_mapping.get(env_source, ChinaDataSource.AKSHARE)

    # ==================== Tushare数据接口 ====================

    def get_china_stock_data_tushare(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        使用Tushare获取中国A股历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据报告
        """
        # 临时切换到Tushare数据源
        original_source = self.current_source
        self.current_source = ChinaDataSource.TUSHARE

        try:
            result = self._get_tushare_data(symbol, start_date, end_date)
            return result
        finally:
            # 恢复原始数据源
            self.current_source = original_source

    def get_fundamentals_data(self, symbol: str) -> str:
        """
        获取基本面数据，支持多数据源和自动降级
        优先级：MongoDB → Tushare → AKShare → 生成分析

        Args:
            symbol: 股票代码

        Returns:
            str: 基本面分析报告
        """
        logger.info(f"📊 [数据来源: {self.current_source.value}] 开始获取基本面数据: {symbol}",
                   extra={
                       'symbol': symbol,
                       'data_source': self.current_source.value,
                       'event_type': 'fundamentals_fetch_start'
                   })

        start_time = time.time()

        try:
            # 根据数据源调用相应的获取方法
            if self.current_source == ChinaDataSource.MONGODB:
                result = self._get_mongodb_fundamentals(symbol)
            elif self.current_source == ChinaDataSource.TUSHARE:
                result = self._get_tushare_fundamentals(symbol)
            elif self.current_source == ChinaDataSource.AKSHARE:
                result = self._get_akshare_fundamentals(symbol)
            else:
                # 其他数据源暂不支持基本面数据，生成基本分析
                result = self._generate_fundamentals_analysis(symbol)

            # 检查结果
            duration = time.time() - start_time
            result_length = len(result) if result else 0

            if result and "❌" not in result:
                logger.info(f"✅ [数据来源: {self.current_source.value}] 成功获取基本面数据: {symbol} ({result_length}字符, 耗时{duration:.2f}秒)",
                           extra={
                               'symbol': symbol,
                               'data_source': self.current_source.value,
                               'duration': duration,
                               'result_length': result_length,
                               'event_type': 'fundamentals_fetch_success'
                           })
                return result
            else:
                logger.warning(f"⚠️ [数据来源: {self.current_source.value}失败] 基本面数据质量异常，尝试降级: {symbol}",
                              extra={
                                  'symbol': symbol,
                                  'data_source': self.current_source.value,
                                  'event_type': 'fundamentals_fetch_fallback'
                              })
                return self._try_fallback_fundamentals(symbol)

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [数据来源: {self.current_source.value}异常] 获取基本面数据失败: {symbol} - {e}",
                        extra={
                            'symbol': symbol,
                            'data_source': self.current_source.value,
                            'duration': duration,
                            'error': str(e),
                            'event_type': 'fundamentals_fetch_exception'
                        }, exc_info=True)
            return self._try_fallback_fundamentals(symbol)

    def get_china_stock_fundamentals_tushare(self, symbol: str) -> str:
        """
        使用Tushare获取中国股票基本面数据（兼容旧接口）

        Args:
            symbol: 股票代码

        Returns:
            str: 基本面分析报告
        """
        # 重定向到统一接口
        return self._get_tushare_fundamentals(symbol)

    def get_news_data(self, symbol: str = None, hours_back: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取新闻数据的统一接口，支持多数据源和自动降级
        优先级：MongoDB → Tushare → AKShare

        Args:
            symbol: 股票代码，为空则获取市场新闻
            hours_back: 回溯小时数
            limit: 返回数量限制

        Returns:
            List[Dict]: 新闻数据列表
        """
        logger.info(f"📰 [数据来源: {self.current_source.value}] 开始获取新闻数据: {symbol or '市场新闻'}, 回溯{hours_back}小时",
                   extra={
                       'symbol': symbol,
                       'hours_back': hours_back,
                       'limit': limit,
                       'data_source': self.current_source.value,
                       'event_type': 'news_fetch_start'
                   })

        start_time = time.time()

        try:
            # 根据数据源调用相应的获取方法
            if self.current_source == ChinaDataSource.MONGODB:
                result = self._get_mongodb_news(symbol, hours_back, limit)
            elif self.current_source == ChinaDataSource.TUSHARE:
                result = self._get_tushare_news(symbol, hours_back, limit)
            elif self.current_source == ChinaDataSource.AKSHARE:
                result = self._get_akshare_news(symbol, hours_back, limit)
            else:
                # 其他数据源暂不支持新闻数据
                logger.warning(f"⚠️ 数据源 {self.current_source.value} 不支持新闻数据")
                result = []

            # 检查结果
            duration = time.time() - start_time
            result_count = len(result) if result else 0

            if result and result_count > 0:
                logger.info(f"✅ [数据来源: {self.current_source.value}] 成功获取新闻数据: {symbol or '市场新闻'} ({result_count}条, 耗时{duration:.2f}秒)",
                           extra={
                               'symbol': symbol,
                               'data_source': self.current_source.value,
                               'news_count': result_count,
                               'duration': duration,
                               'event_type': 'news_fetch_success'
                           })
                return result
            else:
                logger.warning(f"⚠️ [数据来源: {self.current_source.value}] 未获取到新闻数据: {symbol or '市场新闻'}，尝试降级",
                              extra={
                                  'symbol': symbol,
                                  'data_source': self.current_source.value,
                                  'duration': duration,
                                  'event_type': 'news_fetch_fallback'
                              })
                return self._try_fallback_news(symbol, hours_back, limit)

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [数据来源: {self.current_source.value}异常] 获取新闻数据失败: {symbol or '市场新闻'} - {e}",
                        extra={
                            'symbol': symbol,
                            'data_source': self.current_source.value,
                            'duration': duration,
                            'error': str(e),
                            'event_type': 'news_fetch_exception'
                        }, exc_info=True)
            return self._try_fallback_news(symbol, hours_back, limit)

    def _check_available_sources(self) -> List[ChinaDataSource]:
        """
        检查可用的数据源

        检查逻辑：
        1. 检查依赖包是否安装（技术可用性）
        2. 检查数据库配置中是否启用（业务可用性）

        Returns:
            可用且已启用的数据源列表
        """
        available = []

        # 🔥 从数据库读取数据源配置，获取启用状态
        enabled_sources_in_db = set()
        try:
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()
            config_collection = db.system_configs

            # 获取最新的激活配置
            config_data = config_collection.find_one(
                {"is_active": True},
                sort=[("version", -1)]
            )

            if config_data and config_data.get('data_source_configs'):
                data_source_configs = config_data.get('data_source_configs', [])

                # 提取已启用的数据源类型
                for ds in data_source_configs:
                    if ds.get('enabled', True):
                        ds_type = ds.get('type', '').lower()
                        enabled_sources_in_db.add(ds_type)

                logger.info(f"✅ [数据源配置] 从数据库读取到已启用的数据源: {enabled_sources_in_db}")
            else:
                logger.warning("⚠️ [数据源配置] 数据库中没有数据源配置，将检查所有已安装的数据源")
                # 如果数据库中没有配置，默认所有数据源都启用
                enabled_sources_in_db = {'mongodb', 'tushare', 'akshare', 'baostock'}
        except Exception as e:
            logger.warning(f"⚠️ [数据源配置] 从数据库读取失败: {e}，将检查所有已安装的数据源")
            # 如果读取失败，默认所有数据源都启用
            enabled_sources_in_db = {'mongodb', 'tushare', 'akshare', 'baostock'}

        # 检查MongoDB（最高优先级）
        if self.use_mongodb_cache and 'mongodb' in enabled_sources_in_db:
            try:
                from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
                adapter = get_mongodb_cache_adapter()
                if adapter.use_app_cache and adapter.db is not None:
                    available.append(ChinaDataSource.MONGODB)
                    logger.info("✅ MongoDB数据源可用且已启用（最高优先级）")
                else:
                    logger.warning("⚠️ MongoDB数据源不可用: 数据库未连接")
            except Exception as e:
                logger.warning(f"⚠️ MongoDB数据源不可用: {e}")
        elif self.use_mongodb_cache and 'mongodb' not in enabled_sources_in_db:
            logger.info("ℹ️ MongoDB数据源已在数据库中禁用")

        # 从数据库读取数据源配置
        datasource_configs = self._get_datasource_configs_from_db()

        # 检查Tushare
        if 'tushare' in enabled_sources_in_db:
            try:
                import tushare as ts
                # 优先从数据库配置读取 API Key，其次从环境变量读取
                token = datasource_configs.get('tushare', {}).get('api_key') or os.getenv('TUSHARE_TOKEN')
                if token:
                    available.append(ChinaDataSource.TUSHARE)
                    source = "数据库配置" if datasource_configs.get('tushare', {}).get('api_key') else "环境变量"
                    logger.info(f"✅ Tushare数据源可用且已启用 (API Key来源: {source})")
                else:
                    logger.warning("⚠️ Tushare数据源不可用: API Key未配置（数据库和环境变量均未找到）")
            except ImportError:
                logger.warning("⚠️ Tushare数据源不可用: 库未安装")
        else:
            logger.info("ℹ️ Tushare数据源已在数据库中禁用")

        # 检查AKShare
        if 'akshare' in enabled_sources_in_db:
            try:
                import akshare as ak
                available.append(ChinaDataSource.AKSHARE)
                logger.info("✅ AKShare数据源可用且已启用")
            except ImportError:
                logger.warning("⚠️ AKShare数据源不可用: 库未安装")
        else:
            logger.info("ℹ️ AKShare数据源已在数据库中禁用")

        # 检查BaoStock
        if 'baostock' in enabled_sources_in_db:
            try:
                import baostock as bs
                available.append(ChinaDataSource.BAOSTOCK)
                logger.info(f"✅ BaoStock数据源可用且已启用")
            except ImportError:
                logger.warning(f"⚠️ BaoStock数据源不可用: 库未安装")
        else:
            logger.info("ℹ️ BaoStock数据源已在数据库中禁用")

        # TDX (通达信) 已移除
        # 不再检查和支持 TDX 数据源

        return available

    def _get_datasource_configs_from_db(self) -> dict:
        """从数据库读取数据源配置（包括 API Key）"""
        try:
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()

            # 从 system_configs 集合读取激活的配置
            config = db.system_configs.find_one({"is_active": True})
            if not config:
                return {}

            # 提取数据源配置
            datasource_configs = config.get('data_source_configs', [])

            # 构建配置字典 {数据源名称: {api_key, api_secret, ...}}
            result = {}
            for ds_config in datasource_configs:
                name = ds_config.get('name', '').lower()
                result[name] = {
                    'api_key': ds_config.get('api_key', ''),
                    'api_secret': ds_config.get('api_secret', ''),
                    'config_params': ds_config.get('config_params', {})
                }

            return result
        except Exception as e:
            logger.warning(f"⚠️ 从数据库读取数据源配置失败: {e}")
            return {}

    def get_current_source(self) -> ChinaDataSource:
        """获取当前数据源"""
        return self.current_source

    def set_current_source(self, source: ChinaDataSource) -> bool:
        """设置当前数据源"""
        if source in self.available_sources:
            self.current_source = source
            logger.info(f"✅ 数据源已切换到: {source.value}")
            return True
        else:
            logger.error(f"❌ 数据源不可用: {source.value}")
            return False

    def get_data_adapter(self):
        """获取当前数据源的适配器"""
        if self.current_source == ChinaDataSource.MONGODB:
            return self._get_mongodb_adapter()
        elif self.current_source == ChinaDataSource.TUSHARE:
            return self._get_tushare_adapter()
        elif self.current_source == ChinaDataSource.AKSHARE:
            return self._get_akshare_adapter()
        elif self.current_source == ChinaDataSource.BAOSTOCK:
            return self._get_baostock_adapter()
        # TDX 已移除
        else:
            raise ValueError(f"不支持的数据源: {self.current_source}")

    def _get_mongodb_adapter(self):
        """获取MongoDB适配器"""
        try:
            from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
            return get_mongodb_cache_adapter()
        except ImportError as e:
            logger.error(f"❌ MongoDB适配器导入失败: {e}")
            return None

    def _get_tushare_adapter(self):
        """获取Tushare提供器（原adapter已废弃，现在直接使用provider）"""
        try:
            from .providers.china.tushare import get_tushare_provider
            return get_tushare_provider()
        except ImportError as e:
            logger.error(f"❌ Tushare提供器导入失败: {e}")
            return None

    def _get_akshare_adapter(self):
        """获取AKShare适配器"""
        try:
            from .providers.china.akshare import get_akshare_provider
            return get_akshare_provider()
        except ImportError as e:
            logger.error(f"❌ AKShare适配器导入失败: {e}")
            return None

    def _get_baostock_adapter(self):
        """获取BaoStock适配器"""
        try:
            from .providers.china.baostock import get_baostock_provider
            return get_baostock_provider()
        except ImportError as e:
            logger.error(f"❌ BaoStock适配器导入失败: {e}")
            return None

    # TDX 适配器已移除
    # def _get_tdx_adapter(self):
    #     """获取TDX适配器 (已移除)"""
    #     logger.error(f"❌ TDX数据源已不再支持")
    #     return None

    def _get_cached_data(self, symbol: str, start_date: str = None, end_date: str = None, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
        """
        从缓存获取数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            max_age_hours: 最大缓存时间（小时）

        Returns:
            DataFrame: 缓存的数据，如果没有则返回None
        """
        if not self.cache_enabled or not self.cache_manager:
            return None

        try:
            cache_key = self.cache_manager.find_cached_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                max_age_hours=max_age_hours
            )

            if cache_key:
                cached_data = self.cache_manager.load_stock_data(cache_key)
                if cached_data is not None and hasattr(cached_data, 'empty') and not cached_data.empty:
                    logger.debug(f"📦 从缓存获取{symbol}数据: {len(cached_data)}条")
                    return cached_data
        except Exception as e:
            logger.warning(f"⚠️ 从缓存读取数据失败: {e}")

        return None

    def _save_to_cache(self, symbol: str, data: pd.DataFrame, start_date: str = None, end_date: str = None):
        """
        保存数据到缓存

        Args:
            symbol: 股票代码
            data: 数据
            start_date: 开始日期
            end_date: 结束日期
        """
        if not self.cache_enabled or not self.cache_manager:
            return

        try:
            if data is not None and hasattr(data, 'empty') and not data.empty:
                self.cache_manager.save_stock_data(symbol, data, start_date, end_date)
                logger.debug(f"💾 保存{symbol}数据到缓存: {len(data)}条")
        except Exception as e:
            logger.warning(f"⚠️ 保存数据到缓存失败: {e}")

    def _get_volume_safely(self, data: pd.DataFrame) -> float:
        """
        安全获取成交量数据

        Args:
            data: 股票数据DataFrame

        Returns:
            float: 成交量，如果获取失败返回0
        """
        try:
            if 'volume' in data.columns:
                return data['volume'].iloc[-1]
            elif 'vol' in data.columns:
                return data['vol'].iloc[-1]
            else:
                return 0
        except Exception:
            return 0

    def _format_stock_data_response(self, data: pd.DataFrame, symbol: str, stock_name: str,
                                    start_date: str, end_date: str) -> str:
        """
        格式化股票数据响应（包含技术指标）

        Args:
            data: 股票数据DataFrame
            symbol: 股票代码
            stock_name: 股票名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的数据报告（包含技术指标）
        """
        try:
            original_data_count = len(data)
            logger.info(f"📊 [技术指标] 开始计算技术指标，原始数据: {original_data_count}条")

            # 🔧 计算技术指标（使用完整数据）
            # 确保数据按日期排序
            if 'date' in data.columns:
                data = data.sort_values('date')

            # 计算移动平均线
            data['ma5'] = data['close'].rolling(window=5, min_periods=1).mean()
            data['ma10'] = data['close'].rolling(window=10, min_periods=1).mean()
            data['ma20'] = data['close'].rolling(window=20, min_periods=1).mean()
            data['ma60'] = data['close'].rolling(window=60, min_periods=1).mean()

            # 计算RSI（相对强弱指标）- 同花顺风格：使用中国式SMA（EMA with adjust=True）
            # 参考：https://blog.csdn.net/u011218867/article/details/117427927
            # 同花顺/通达信的RSI使用SMA函数，等价于pandas的ewm(com=N-1, adjust=True)
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # RSI6 - 使用中国式SMA
            avg_gain6 = gain.ewm(com=5, adjust=True).mean()  # com = N - 1
            avg_loss6 = loss.ewm(com=5, adjust=True).mean()
            rs6 = avg_gain6 / avg_loss6.replace(0, np.nan)
            data['rsi6'] = 100 - (100 / (1 + rs6))

            # RSI12 - 使用中国式SMA
            avg_gain12 = gain.ewm(com=11, adjust=True).mean()
            avg_loss12 = loss.ewm(com=11, adjust=True).mean()
            rs12 = avg_gain12 / avg_loss12.replace(0, np.nan)
            data['rsi12'] = 100 - (100 / (1 + rs12))

            # RSI24 - 使用中国式SMA
            avg_gain24 = gain.ewm(com=23, adjust=True).mean()
            avg_loss24 = loss.ewm(com=23, adjust=True).mean()
            rs24 = avg_gain24 / avg_loss24.replace(0, np.nan)
            data['rsi24'] = 100 - (100 / (1 + rs24))

            # 保留RSI14作为国际标准参考（使用简单移动平均）
            gain14 = gain.rolling(window=14, min_periods=1).mean()
            loss14 = loss.rolling(window=14, min_periods=1).mean()
            rs14 = gain14 / loss14.replace(0, np.nan)
            data['rsi14'] = 100 - (100 / (1 + rs14))

            # 计算MACD
            ema12 = data['close'].ewm(span=12, adjust=False).mean()
            ema26 = data['close'].ewm(span=26, adjust=False).mean()
            data['macd_dif'] = ema12 - ema26
            data['macd_dea'] = data['macd_dif'].ewm(span=9, adjust=False).mean()
            data['macd'] = (data['macd_dif'] - data['macd_dea']) * 2

            # 计算布林带
            data['boll_mid'] = data['close'].rolling(window=20, min_periods=1).mean()
            std = data['close'].rolling(window=20, min_periods=1).std()
            data['boll_upper'] = data['boll_mid'] + 2 * std
            data['boll_lower'] = data['boll_mid'] - 2 * std

            logger.info(f"✅ [技术指标] 技术指标计算完成")

            # 🔧 只保留最后3-5天的数据用于展示（减少token消耗）
            display_rows = min(5, len(data))
            display_data = data.tail(display_rows)
            latest_data = data.iloc[-1]

            # 🔍 [调试日志] 打印最近5天的原始数据和技术指标
            logger.info(f"🔍 [技术指标详情] ===== 最近{display_rows}个交易日数据 =====")
            for i, (idx, row) in enumerate(display_data.iterrows(), 1):
                logger.info(f"🔍 [技术指标详情] 第{i}天 ({row.get('date', 'N/A')}):")
                logger.info(f"   价格: 开={row.get('open', 0):.2f}, 高={row.get('high', 0):.2f}, 低={row.get('low', 0):.2f}, 收={row.get('close', 0):.2f}")
                logger.info(f"   MA: MA5={row.get('ma5', 0):.2f}, MA10={row.get('ma10', 0):.2f}, MA20={row.get('ma20', 0):.2f}, MA60={row.get('ma60', 0):.2f}")
                logger.info(f"   MACD: DIF={row.get('macd_dif', 0):.4f}, DEA={row.get('macd_dea', 0):.4f}, MACD={row.get('macd', 0):.4f}")
                logger.info(f"   RSI: RSI6={row.get('rsi6', 0):.2f}, RSI12={row.get('rsi12', 0):.2f}, RSI24={row.get('rsi24', 0):.2f} (同花顺风格)")
                logger.info(f"   RSI14: {row.get('rsi14', 0):.2f} (国际标准)")
                logger.info(f"   BOLL: 上={row.get('boll_upper', 0):.2f}, 中={row.get('boll_mid', 0):.2f}, 下={row.get('boll_lower', 0):.2f}")

            logger.info(f"🔍 [技术指标详情] ===== 数据详情结束 =====")

            # 计算最新价格和涨跌幅
            latest_price = latest_data.get('close', 0)
            prev_close = data.iloc[-2].get('close', latest_price) if len(data) > 1 else latest_price
            change = latest_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0

            # 格式化数据报告
            result = f"📊 {stock_name}({symbol}) - 技术分析数据\n"
            result += f"数据期间: {start_date} 至 {end_date}\n"
            result += f"数据条数: {original_data_count}条 (展示最近{display_rows}个交易日)\n\n"

            result += f"💰 最新价格: ¥{latest_price:.2f}\n"
            result += f"📈 涨跌额: {change:+.2f} ({change_pct:+.2f}%)\n\n"

            # 添加技术指标
            result += f"📊 移动平均线 (MA):\n"
            result += f"   MA5:  ¥{latest_data['ma5']:.2f}"
            if latest_price > latest_data['ma5']:
                result += " (价格在MA5上方 ↑)\n"
            else:
                result += " (价格在MA5下方 ↓)\n"

            result += f"   MA10: ¥{latest_data['ma10']:.2f}"
            if latest_price > latest_data['ma10']:
                result += " (价格在MA10上方 ↑)\n"
            else:
                result += " (价格在MA10下方 ↓)\n"

            result += f"   MA20: ¥{latest_data['ma20']:.2f}"
            if latest_price > latest_data['ma20']:
                result += " (价格在MA20上方 ↑)\n"
            else:
                result += " (价格在MA20下方 ↓)\n"

            result += f"   MA60: ¥{latest_data['ma60']:.2f}"
            if latest_price > latest_data['ma60']:
                result += " (价格在MA60上方 ↑)\n\n"
            else:
                result += " (价格在MA60下方 ↓)\n\n"

            # MACD指标
            result += f"📈 MACD指标:\n"
            result += f"   DIF:  {latest_data['macd_dif']:.3f}\n"
            result += f"   DEA:  {latest_data['macd_dea']:.3f}\n"
            result += f"   MACD: {latest_data['macd']:.3f}"
            if latest_data['macd'] > 0:
                result += " (多头 ↑)\n"
            else:
                result += " (空头 ↓)\n"

            # 判断金叉/死叉
            if len(data) > 1:
                prev_dif = data.iloc[-2]['macd_dif']
                prev_dea = data.iloc[-2]['macd_dea']
                curr_dif = latest_data['macd_dif']
                curr_dea = latest_data['macd_dea']

                if prev_dif <= prev_dea and curr_dif > curr_dea:
                    result += "   ⚠️ MACD金叉信号（DIF上穿DEA）\n\n"
                elif prev_dif >= prev_dea and curr_dif < curr_dea:
                    result += "   ⚠️ MACD死叉信号（DIF下穿DEA）\n\n"
                else:
                    result += "\n"
            else:
                result += "\n"

            # RSI指标 - 同花顺风格 (6, 12, 24)
            rsi6 = latest_data['rsi6']
            rsi12 = latest_data['rsi12']
            rsi24 = latest_data['rsi24']
            result += f"📉 RSI指标 (同花顺风格):\n"
            result += f"   RSI6:  {rsi6:.2f}"
            if rsi6 >= 80:
                result += " (超买 ⚠️)\n"
            elif rsi6 <= 20:
                result += " (超卖 ⚠️)\n"
            else:
                result += "\n"

            result += f"   RSI12: {rsi12:.2f}"
            if rsi12 >= 80:
                result += " (超买 ⚠️)\n"
            elif rsi12 <= 20:
                result += " (超卖 ⚠️)\n"
            else:
                result += "\n"

            result += f"   RSI24: {rsi24:.2f}"
            if rsi24 >= 80:
                result += " (超买 ⚠️)\n"
            elif rsi24 <= 20:
                result += " (超卖 ⚠️)\n"
            else:
                result += "\n"

            # 判断RSI趋势
            if rsi6 > rsi12 > rsi24:
                result += "   趋势: 多头排列 ↑\n\n"
            elif rsi6 < rsi12 < rsi24:
                result += "   趋势: 空头排列 ↓\n\n"
            else:
                result += "   趋势: 震荡整理 ↔\n\n"

            # 布林带
            result += f"📊 布林带 (BOLL):\n"
            result += f"   上轨: ¥{latest_data['boll_upper']:.2f}\n"
            result += f"   中轨: ¥{latest_data['boll_mid']:.2f}\n"
            result += f"   下轨: ¥{latest_data['boll_lower']:.2f}\n"

            # 判断价格在布林带的位置
            boll_position = (latest_price - latest_data['boll_lower']) / (latest_data['boll_upper'] - latest_data['boll_lower']) * 100
            result += f"   价格位置: {boll_position:.1f}%"
            if boll_position >= 80:
                result += " (接近上轨，可能超买 ⚠️)\n\n"
            elif boll_position <= 20:
                result += " (接近下轨，可能超卖 ⚠️)\n\n"
            else:
                result += " (中性区域)\n\n"

            # 价格统计
            result += f"📊 价格统计 (最近{display_rows}个交易日):\n"
            result += f"   最高价: ¥{display_data['high'].max():.2f}\n"
            result += f"   最低价: ¥{display_data['low'].min():.2f}\n"
            result += f"   平均价: ¥{display_data['close'].mean():.2f}\n"

            # 防御性获取成交量数据
            volume_value = self._get_volume_safely(display_data)
            result += f"   平均成交量: {volume_value:,.0f}股\n"

            return result

        except Exception as e:
            logger.error(f"❌ 格式化数据响应失败: {e}", exc_info=True)
            return f"❌ 格式化{symbol}数据失败: {e}"

    def get_stock_dataframe(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """
        获取股票数据的 DataFrame 接口，支持多数据源和自动降级

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期（daily/weekly/monthly），默认为daily

        Returns:
            pd.DataFrame: 股票数据 DataFrame，列标准：open, high, low, close, vol, amount, date
        """
        logger.info(f"📊 [DataFrame接口] 获取股票数据: {symbol} ({start_date} 到 {end_date})")

        try:
            # 尝试当前数据源
            df = None
            if self.current_source == ChinaDataSource.MONGODB:
                from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
                adapter = get_mongodb_cache_adapter()
                df = adapter.get_historical_data(symbol, start_date, end_date, period=period)
            elif self.current_source == ChinaDataSource.TUSHARE:
                from .providers.china.tushare import get_tushare_provider
                provider = get_tushare_provider()
                df = provider.get_daily_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.AKSHARE:
                from .providers.china.akshare import get_akshare_provider
                provider = get_akshare_provider()
                df = provider.get_stock_data(symbol, start_date, end_date)
            elif self.current_source == ChinaDataSource.BAOSTOCK:
                from .providers.china.baostock import get_baostock_provider
                provider = get_baostock_provider()
                df = provider.get_stock_data(symbol, start_date, end_date)

            if df is not None and not df.empty:
                logger.info(f"✅ [DataFrame接口] 从 {self.current_source.value} 获取成功: {len(df)}条")
                return self._standardize_dataframe(df)

            # 降级到其他数据源
            logger.warning(f"⚠️ [DataFrame接口] {self.current_source.value} 失败，尝试降级")
            for source in self.available_sources:
                if source == self.current_source:
                    continue
                try:
                    if source == ChinaDataSource.MONGODB:
                        from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
                        adapter = get_mongodb_cache_adapter()
                        df = adapter.get_historical_data(symbol, start_date, end_date, period=period)
                    elif source == ChinaDataSource.TUSHARE:
                        from .providers.china.tushare import get_tushare_provider
                        provider = get_tushare_provider()
                        df = provider.get_daily_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.AKSHARE:
                        from .providers.china.akshare import get_akshare_provider
                        provider = get_akshare_provider()
                        df = provider.get_stock_data(symbol, start_date, end_date)
                    elif source == ChinaDataSource.BAOSTOCK:
                        from .providers.china.baostock import get_baostock_provider
                        provider = get_baostock_provider()
                        df = provider.get_stock_data(symbol, start_date, end_date)

                    if df is not None and not df.empty:
                        logger.info(f"✅ [DataFrame接口] 降级到 {source.value} 成功: {len(df)}条")
                        return self._standardize_dataframe(df)
                except Exception as e:
                    logger.warning(f"⚠️ [DataFrame接口] {source.value} 失败: {e}")
                    continue

            logger.error(f"❌ [DataFrame接口] 所有数据源都失败: {symbol}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ [DataFrame接口] 获取失败: {e}", exc_info=True)
            return pd.DataFrame()

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化 DataFrame 列名和格式

        Args:
            df: 原始 DataFrame

        Returns:
            pd.DataFrame: 标准化后的 DataFrame
        """
        if df is None or df.empty:
            return pd.DataFrame()

        out = df.copy()

        # 列名映射
        colmap = {
            # English
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
            'Volume': 'vol', 'Amount': 'amount', 'symbol': 'code', 'Symbol': 'code',
            # Already lower
            'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close',
            'vol': 'vol', 'volume': 'vol', 'amount': 'amount', 'code': 'code',
            'date': 'date', 'trade_date': 'date',
            # Chinese (AKShare common)
            '日期': 'date', '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close',
            '成交量': 'vol', '成交额': 'amount', '涨跌幅': 'pct_change', '涨跌额': 'change',
        }
        out = out.rename(columns={c: colmap.get(c, c) for c in out.columns})

        # 确保日期排序
        if 'date' in out.columns:
            try:
                out['date'] = pd.to_datetime(out['date'])
                out = out.sort_values('date')
            except Exception:
                pass

        # 计算涨跌幅（如果缺失）
        if 'pct_change' not in out.columns and 'close' in out.columns:
            out['pct_change'] = out['close'].pct_change() * 100.0

        return out

    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "daily") -> str:
        """
        获取股票数据的统一接口，支持多周期数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期（daily/weekly/monthly），默认为daily

        Returns:
            str: 格式化的股票数据
        """
        # 记录详细的输入参数
        logger.info(f"📊 [数据来源: {self.current_source.value}] 开始获取{period}数据: {symbol}",
                   extra={
                       'symbol': symbol,
                       'start_date': start_date,
                       'end_date': end_date,
                       'period': period,
                       'data_source': self.current_source.value,
                       'event_type': 'data_fetch_start'
                   })

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] DataSourceManager.get_stock_data 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 当前数据源: {self.current_source.value}")

        start_time = time.time()

        try:
            # 根据数据源调用相应的获取方法
            actual_source = None  # 实际使用的数据源

            if self.current_source == ChinaDataSource.MONGODB:
                result, actual_source = self._get_mongodb_data(symbol, start_date, end_date, period)
            elif self.current_source == ChinaDataSource.TUSHARE:
                logger.info(f"🔍 [股票代码追踪] 调用 Tushare 数据源，传入参数: symbol='{symbol}', period='{period}'")
                result = self._get_tushare_data(symbol, start_date, end_date, period)
                actual_source = "tushare"
            elif self.current_source == ChinaDataSource.AKSHARE:
                result = self._get_akshare_data(symbol, start_date, end_date, period)
                actual_source = "akshare"
            elif self.current_source == ChinaDataSource.BAOSTOCK:
                result = self._get_baostock_data(symbol, start_date, end_date, period)
                actual_source = "baostock"
            # TDX 已移除
            else:
                result = f"❌ 不支持的数据源: {self.current_source.value}"
                actual_source = None

            # 记录详细的输出结果
            duration = time.time() - start_time
            result_length = len(result) if result else 0
            is_success = result and "❌" not in result and "错误" not in result

            # 使用实际数据源名称，如果没有则使用 current_source
            display_source = actual_source or self.current_source.value

            if is_success:
                logger.info(f"✅ [数据来源: {display_source}] 成功获取股票数据: {symbol} ({result_length}字符, 耗时{duration:.2f}秒)",
                           extra={
                               'symbol': symbol,
                               'start_date': start_date,
                               'end_date': end_date,
                               'data_source': display_source,
                               'actual_source': actual_source,
                               'requested_source': self.current_source.value,
                               'duration': duration,
                               'result_length': result_length,
                               'result_preview': result[:200] + '...' if result_length > 200 else result,
                               'event_type': 'data_fetch_success'
                           })
                return result
            else:
                logger.warning(f"⚠️ [数据来源: {self.current_source.value}失败] 数据质量异常，尝试降级到其他数据源: {symbol}",
                              extra={
                                  'symbol': symbol,
                                  'start_date': start_date,
                                  'end_date': end_date,
                                  'data_source': self.current_source.value,
                                  'duration': duration,
                                  'result_length': result_length,
                                  'result_preview': result[:200] + '...' if result_length > 200 else result,
                                  'event_type': 'data_fetch_warning'
                              })

                # 数据质量异常时也尝试降级到其他数据源
                fallback_result = self._try_fallback_sources(symbol, start_date, end_date)
                if fallback_result and "❌" not in fallback_result and "错误" not in fallback_result:
                    logger.info(f"✅ [数据来源: 备用数据源] 降级成功获取数据: {symbol}")
                    return fallback_result
                else:
                    logger.error(f"❌ [数据来源: 所有数据源失败] 所有数据源都无法获取有效数据: {symbol}")
                    return result  # 返回原始结果（包含错误信息）

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [数据获取] 异常失败: {e}",
                        extra={
                            'symbol': symbol,
                            'start_date': start_date,
                            'end_date': end_date,
                            'data_source': self.current_source.value,
                            'duration': duration,
                            'error': str(e),
                            'event_type': 'data_fetch_exception'
                        }, exc_info=True)
            return self._try_fallback_sources(symbol, start_date, end_date)

    def _get_mongodb_data(self, symbol: str, start_date: str, end_date: str, period: str = "daily") -> tuple[str, str | None]:
        """
        从MongoDB获取多周期数据 - 包含技术指标计算

        Returns:
            tuple[str, str | None]: (结果字符串, 实际使用的数据源名称)
        """
        logger.debug(f"📊 [MongoDB] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}, period={period}")

        try:
            from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
            adapter = get_mongodb_cache_adapter()

            # 从MongoDB获取指定周期的历史数据
            df = adapter.get_historical_data(symbol, start_date, end_date, period=period)

            if df is not None and not df.empty:
                logger.info(f"✅ [数据来源: MongoDB缓存] 成功获取{period}数据: {symbol} ({len(df)}条记录)")

                # 🔧 修复：使用统一的格式化方法，包含技术指标计算
                # 获取股票名称（从DataFrame中提取或使用默认值）
                stock_name = f'股票{symbol}'
                if 'name' in df.columns and not df['name'].empty:
                    stock_name = df['name'].iloc[0]

                # 调用统一的格式化方法（包含技术指标计算）
                result = self._format_stock_data_response(df, symbol, stock_name, start_date, end_date)

                logger.info(f"✅ [MongoDB] 已计算技术指标: MA5/10/20/60, MACD, RSI, BOLL")
                return result, "mongodb"
            else:
                # MongoDB没有数据（adapter内部已记录详细的数据源信息），降级到其他数据源
                logger.info(f"🔄 [MongoDB] 未找到{period}数据: {symbol}，开始尝试备用数据源")
                return self._try_fallback_sources(symbol, start_date, end_date, period)

        except Exception as e:
            logger.error(f"❌ [数据来源: MongoDB异常] 获取{period}数据失败: {symbol}, 错误: {e}")
            # MongoDB异常，降级到其他数据源
            return self._try_fallback_sources(symbol, start_date, end_date, period)

    def _get_tushare_data(self, symbol: str, start_date: str, end_date: str, period: str = "daily") -> str:
        """使用Tushare获取多周期数据 - 使用provider + 统一缓存"""
        logger.debug(f"📊 [Tushare] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}, period={period}")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] _get_tushare_data 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")
        logger.info(f"🔍 [DataSourceManager详细日志] _get_tushare_data 开始执行")
        logger.info(f"🔍 [DataSourceManager详细日志] 当前数据源: {self.current_source.value}")

        start_time = time.time()
        try:
            # 1. 先尝试从缓存获取
            cached_data = self._get_cached_data(symbol, start_date, end_date, max_age_hours=24)
            if cached_data is not None and not cached_data.empty:
                logger.info(f"✅ [缓存命中] 从缓存获取{symbol}数据")
                # 获取股票基本信息
                provider = self._get_tushare_adapter()
                if provider:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                    except RuntimeError:
                        # 在线程池中没有事件循环，创建新的
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    stock_info = loop.run_until_complete(provider.get_stock_basic_info(symbol))
                    stock_name = stock_info.get('name', f'股票{symbol}') if stock_info else f'股票{symbol}'
                else:
                    stock_name = f'股票{symbol}'

                # 格式化返回
                return self._format_stock_data_response(cached_data, symbol, stock_name, start_date, end_date)

            # 2. 缓存未命中，从provider获取
            logger.info(f"🔍 [股票代码追踪] 调用 tushare_provider，传入参数: symbol='{symbol}'")
            logger.info(f"🔍 [DataSourceManager详细日志] 开始调用tushare_provider...")

            provider = self._get_tushare_adapter()
            if not provider:
                return f"❌ Tushare提供器不可用"

            # 使用异步方法获取历史数据
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                # 在线程池中没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            data = loop.run_until_complete(provider.get_historical_data(symbol, start_date, end_date))

            if data is not None and not data.empty:
                # 保存到缓存
                self._save_to_cache(symbol, data, start_date, end_date)

                # 获取股票基本信息（异步）
                stock_info = loop.run_until_complete(provider.get_stock_basic_info(symbol))
                stock_name = stock_info.get('name', f'股票{symbol}') if stock_info else f'股票{symbol}'

                # 格式化返回
                result = self._format_stock_data_response(data, symbol, stock_name, start_date, end_date)

                duration = time.time() - start_time
                logger.info(f"🔍 [DataSourceManager详细日志] 调用完成，耗时: {duration:.3f}秒")
                logger.info(f"🔍 [股票代码追踪] 返回结果前200字符: {result[:200] if result else 'None'}")
                logger.debug(f"📊 [Tushare] 调用完成: 耗时={duration:.2f}s, 结果长度={len(result) if result else 0}")

                return result
            else:
                result = f"❌ 未获取到{symbol}的有效数据"
                duration = time.time() - start_time
                logger.warning(f"⚠️ [Tushare] 未获取到数据，耗时={duration:.2f}s")
                return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [Tushare] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            logger.error(f"❌ [DataSourceManager详细日志] 异常类型: {type(e).__name__}")
            logger.error(f"❌ [DataSourceManager详细日志] 异常信息: {str(e)}")
            import traceback
            logger.error(f"❌ [DataSourceManager详细日志] 异常堆栈: {traceback.format_exc()}")
            raise

    def _get_akshare_data(self, symbol: str, start_date: str, end_date: str, period: str = "daily") -> str:
        """使用AKShare获取多周期数据 - 包含技术指标计算"""
        logger.debug(f"📊 [AKShare] 调用参数: symbol={symbol}, start_date={start_date}, end_date={end_date}, period={period}")

        start_time = time.time()
        try:
            # 使用AKShare的统一接口
            from .providers.china.akshare import get_akshare_provider
            provider = get_akshare_provider()

            # 使用异步方法获取历史数据
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                # 在线程池中没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            data = loop.run_until_complete(provider.get_historical_data(symbol, start_date, end_date, period))

            duration = time.time() - start_time

            if data is not None and not data.empty:
                # 🔧 修复：使用统一的格式化方法，包含技术指标计算
                # 获取股票基本信息
                stock_info = loop.run_until_complete(provider.get_stock_basic_info(symbol))
                stock_name = stock_info.get('name', f'股票{symbol}') if stock_info else f'股票{symbol}'

                # 调用统一的格式化方法（包含技术指标计算）
                result = self._format_stock_data_response(data, symbol, stock_name, start_date, end_date)

                logger.debug(f"📊 [AKShare] 调用成功: 耗时={duration:.2f}s, 数据条数={len(data)}, 结果长度={len(result)}")
                logger.info(f"✅ [AKShare] 已计算技术指标: MA5/10/20/60, MACD, RSI, BOLL")
                return result
            else:
                result = f"❌ 未能获取{symbol}的股票数据"
                logger.warning(f"⚠️ [AKShare] 数据为空: 耗时={duration:.2f}s")
                return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ [AKShare] 调用失败: {e}, 耗时={duration:.2f}s", exc_info=True)
            return f"❌ AKShare获取{symbol}数据失败: {e}"

    def _get_baostock_data(self, symbol: str, start_date: str, end_date: str, period: str = "daily") -> str:
        """使用BaoStock获取多周期数据 - 包含技术指标计算"""
        # 使用BaoStock的统一接口
        from .providers.china.baostock import get_baostock_provider
        provider = get_baostock_provider()

        # 使用异步方法获取历史数据
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # 在线程池中没有事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        data = loop.run_until_complete(provider.get_historical_data(symbol, start_date, end_date, period))

        if data is not None and not data.empty:
            # 🔧 修复：使用统一的格式化方法，包含技术指标计算
            # 获取股票基本信息
            stock_info = loop.run_until_complete(provider.get_stock_basic_info(symbol))
            stock_name = stock_info.get('name', f'股票{symbol}') if stock_info else f'股票{symbol}'

            # 调用统一的格式化方法（包含技术指标计算）
            result = self._format_stock_data_response(data, symbol, stock_name, start_date, end_date)

            logger.info(f"✅ [BaoStock] 已计算技术指标: MA5/10/20/60, MACD, RSI, BOLL")
            return result
        else:
            return f"❌ 未能获取{symbol}的股票数据"

    # TDX 数据获取方法已移除
    # def _get_tdx_data(self, symbol: str, start_date: str, end_date: str, period: str = "daily") -> str:
    #     """使用TDX获取多周期数据 (已移除)"""
    #     logger.error(f"❌ TDX数据源已不再支持")
    #     return f"❌ TDX数据源已不再支持"

    def _get_volume_safely(self, data) -> float:
        """安全地获取成交量数据，支持多种列名"""
        try:
            # 支持多种可能的成交量列名
            volume_columns = ['volume', 'vol', 'turnover', 'trade_volume']

            for col in volume_columns:
                if col in data.columns:
                    logger.info(f"✅ 找到成交量列: {col}")
                    return data[col].sum()

            # 如果都没找到，记录警告并返回0
            logger.warning(f"⚠️ 未找到成交量列，可用列: {list(data.columns)}")
            return 0

        except Exception as e:
            logger.error(f"❌ 获取成交量失败: {e}")
            return 0

    def _try_fallback_sources(self, symbol: str, start_date: str, end_date: str, period: str = "daily") -> tuple[str, str | None]:
        """
        尝试备用数据源 - 避免递归调用

        Returns:
            tuple[str, str | None]: (结果字符串, 实际使用的数据源名称)
        """
        logger.info(f"🔄 [{self.current_source.value}] 失败，尝试备用数据源获取{period}数据: {symbol}")

        # 🔥 从数据库获取数据源优先级顺序（根据股票代码识别市场）
        # 注意：不包含MongoDB，因为MongoDB是最高优先级，如果失败了就不再尝试
        fallback_order = self._get_data_source_priority_order(symbol)

        for source in fallback_order:
            if source != self.current_source and source in self.available_sources:
                try:
                    logger.info(f"🔄 [备用数据源] 尝试 {source.value} 获取{period}数据: {symbol}")

                    # 直接调用具体的数据源方法，避免递归
                    if source == ChinaDataSource.TUSHARE:
                        result = self._get_tushare_data(symbol, start_date, end_date, period)
                    elif source == ChinaDataSource.AKSHARE:
                        result = self._get_akshare_data(symbol, start_date, end_date, period)
                    elif source == ChinaDataSource.BAOSTOCK:
                        result = self._get_baostock_data(symbol, start_date, end_date, period)
                    # TDX 已移除
                    else:
                        logger.warning(f"⚠️ 未知数据源: {source.value}")
                        continue

                    if "❌" not in result:
                        logger.info(f"✅ [备用数据源-{source.value}] 成功获取{period}数据: {symbol}")
                        return result, source.value  # 返回结果和实际使用的数据源
                    else:
                        logger.warning(f"⚠️ [备用数据源-{source.value}] 返回错误结果: {symbol}")

                except Exception as e:
                    logger.error(f"❌ [备用数据源-{source.value}] 获取失败: {symbol}, 错误: {e}")
                    continue

        logger.error(f"❌ [所有数据源失败] 无法获取{period}数据: {symbol}")
        return f"❌ 所有数据源都无法获取{symbol}的{period}数据", None

    def get_stock_info(self, symbol: str) -> Dict:
        """
        获取股票基本信息，支持多数据源和自动降级
        优先级：MongoDB → Tushare → AKShare → BaoStock
        """
        logger.info(f"📊 [数据来源: {self.current_source.value}] 开始获取股票信息: {symbol}")

        # 优先使用 App Mongo 缓存（当 ta_use_app_cache=True）
        try:
            from tradingagents.config.runtime_settings import use_app_cache_enabled  # type: ignore
            use_cache = use_app_cache_enabled(False)
            logger.info(f"🔧 [配置检查] use_app_cache_enabled() 返回值: {use_cache}")
        except Exception as e:
            logger.error(f"❌ [配置检查] use_app_cache_enabled() 调用失败: {e}", exc_info=True)
            use_cache = False

        logger.info(f"🔧 [配置] ta_use_app_cache={use_cache}, current_source={self.current_source.value}")

        if use_cache:

            try:
                from .cache.app_adapter import get_basics_from_cache, get_market_quote_dataframe
                doc = get_basics_from_cache(symbol)
                if doc:
                    name = doc.get('name') or doc.get('stock_name') or ''
                    # 规范化行业与板块（避免把“中小板/创业板”等板块值误作行业）
                    board_labels = {'主板', '中小板', '创业板', '科创板'}
                    raw_industry = (doc.get('industry') or doc.get('industry_name') or '').strip()
                    sec_or_cat = (doc.get('sec') or doc.get('category') or '').strip()
                    market_val = (doc.get('market') or '').strip()
                    industry_val = raw_industry or sec_or_cat or '未知'
                    changed = False
                    if raw_industry in board_labels:
                        # 若industry是板块名，则将其用于market；industry改用更细分类（sec/category）
                        if not market_val:
                            market_val = raw_industry
                            changed = True
                        if sec_or_cat:
                            industry_val = sec_or_cat
                            changed = True
                    if changed:
                        try:
                            logger.debug(f"🔧 [字段归一化] industry原值='{raw_industry}' → 行业='{industry_val}', 市场/板块='{market_val or doc.get('market', '未知')}'")
                        except Exception:
                            pass

                    result = {
                        'symbol': symbol,
                        'name': name or f'股票{symbol}',
                        'area': doc.get('area', '未知'),
                        'industry': industry_val or '未知',
                        'market': market_val or doc.get('market', '未知'),
                        'list_date': doc.get('list_date', '未知'),
                        'source': 'app_cache'
                    }
                    # 追加快照行情（若存在）
                    try:
                        df = get_market_quote_dataframe(symbol)
                        if df is not None and not df.empty:
                            row = df.iloc[-1]
                            result['current_price'] = row.get('close')
                            result['change_pct'] = row.get('pct_chg')
                            result['volume'] = row.get('volume')
                            result['quote_date'] = row.get('date')
                            result['quote_source'] = 'market_quotes'
                            logger.info(f"✅ [股票信息] 附加行情 | price={result['current_price']} pct={result['change_pct']} vol={result['volume']} code={symbol}")
                    except Exception as _e:
                        logger.debug(f"附加行情失败（忽略）：{_e}")

                    if name:
                        logger.info(f"✅ [数据来源: MongoDB-stock_basic_info] 成功获取: {symbol}")
                        return result
                    else:
                        logger.warning(f"⚠️ [数据来源: MongoDB] 未找到有效名称: {symbol}，降级到其他数据源")
            except Exception as e:
                logger.error(f"❌ [数据来源: MongoDB异常] 获取股票信息失败: {e}", exc_info=True)


        # 首先尝试当前数据源
        try:
            if self.current_source == ChinaDataSource.TUSHARE:
                from .interface import get_china_stock_info_tushare
                info_str = get_china_stock_info_tushare(symbol)
                result = self._parse_stock_info_string(info_str, symbol)

                # 检查是否获取到有效信息
                if result.get('name') and result['name'] != f'股票{symbol}':
                    logger.info(f"✅ [数据来源: Tushare-股票信息] 成功获取: {symbol}")
                    return result
                else:
                    logger.warning(f"⚠️ [数据来源: Tushare失败] 返回无效信息，尝试降级: {symbol}")
                    return self._try_fallback_stock_info(symbol)
            else:
                adapter = self.get_data_adapter()
                if adapter and hasattr(adapter, 'get_stock_info'):
                    result = adapter.get_stock_info(symbol)
                    if result.get('name') and result['name'] != f'股票{symbol}':
                        logger.info(f"✅ [数据来源: {self.current_source.value}-股票信息] 成功获取: {symbol}")
                        return result
                    else:
                        logger.warning(f"⚠️ [数据来源: {self.current_source.value}失败] 返回无效信息，尝试降级: {symbol}")
                        return self._try_fallback_stock_info(symbol)
                else:
                    logger.warning(f"⚠️ [数据来源: {self.current_source.value}] 不支持股票信息获取，尝试降级: {symbol}")
                    return self._try_fallback_stock_info(symbol)

        except Exception as e:
            logger.error(f"❌ [数据来源: {self.current_source.value}异常] 获取股票信息失败: {e}", exc_info=True)
            return self._try_fallback_stock_info(symbol)

    def get_stock_basic_info(self, stock_code: str = None) -> Optional[Dict[str, Any]]:
        """
        获取股票基础信息（兼容 stock_data_service 接口）

        Args:
            stock_code: 股票代码，如果为 None 则返回所有股票列表

        Returns:
            Dict: 股票信息字典，或包含 error 字段的错误字典
        """
        if stock_code is None:
            # 返回所有股票列表
            logger.info("📊 获取所有股票列表")
            try:
                # 尝试从 MongoDB 获取
                from tradingagents.config.database_manager import get_database_manager
                db_manager = get_database_manager()
                if db_manager and db_manager.is_mongodb_available():
                    collection = db_manager.mongodb_db['stock_basic_info']
                    stocks = list(collection.find({}, {'_id': 0}))
                    if stocks:
                        logger.info(f"✅ 从MongoDB获取所有股票: {len(stocks)}条")
                        return stocks
            except Exception as e:
                logger.warning(f"⚠️ 从MongoDB获取所有股票失败: {e}")

            # 降级：返回空列表
            return []

        # 获取单个股票信息
        try:
            result = self.get_stock_info(stock_code)
            if result and result.get('name'):
                return result
            else:
                return {'error': f'未找到股票 {stock_code} 的信息'}
        except Exception as e:
            logger.error(f"❌ 获取股票信息失败: {e}")
            return {'error': str(e)}

    def get_stock_data_with_fallback(self, stock_code: str, start_date: str, end_date: str) -> str:
        """
        获取股票数据（兼容 stock_data_service 接口）

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 格式化的股票数据报告
        """
        logger.info(f"📊 获取股票数据: {stock_code} ({start_date} 到 {end_date})")

        try:
            # 使用统一的数据获取接口
            return self.get_stock_data(stock_code, start_date, end_date)
        except Exception as e:
            logger.error(f"❌ 获取股票数据失败: {e}")
            return f"❌ 获取股票数据失败: {str(e)}\n\n💡 建议：\n1. 检查网络连接\n2. 确认股票代码格式正确\n3. 检查数据源配置"

    def _try_fallback_stock_info(self, symbol: str) -> Dict:
        """尝试使用备用数据源获取股票基本信息"""
        logger.error(f"🔄 {self.current_source.value}失败，尝试备用数据源获取股票信息...")

        # 获取所有可用数据源
        available_sources = self.available_sources.copy()

        # 移除当前数据源
        if self.current_source.value in available_sources:
            available_sources.remove(self.current_source.value)

        # 尝试所有备用数据源
        for source_name in available_sources:
            try:
                source = ChinaDataSource(source_name)
                logger.info(f"🔄 尝试备用数据源获取股票信息: {source_name}")

                # 根据数据源类型获取股票信息
                if source == ChinaDataSource.TUSHARE:
                    # 🔥 直接调用 Tushare 适配器，避免循环调用
                    result = self._get_tushare_stock_info(symbol)
                elif source == ChinaDataSource.AKSHARE:
                    result = self._get_akshare_stock_info(symbol)
                elif source == ChinaDataSource.BAOSTOCK:
                    result = self._get_baostock_stock_info(symbol)
                else:
                    # 尝试通用适配器
                    original_source = self.current_source
                    self.current_source = source
                    adapter = self.get_data_adapter()
                    self.current_source = original_source

                    if adapter and hasattr(adapter, 'get_stock_info'):
                        result = adapter.get_stock_info(symbol)
                    else:
                        logger.warning(f"⚠️ [股票信息] {source_name}不支持股票信息获取")
                        continue

                # 检查是否获取到有效信息
                if result.get('name') and result['name'] != f'股票{symbol}':
                    logger.info(f"✅ [数据来源: 备用数据源] 降级成功获取股票信息: {source_name}")
                    return result
                else:
                    logger.warning(f"⚠️ [数据来源: {source_name}] 返回无效信息")

            except Exception as e:
                logger.error(f"❌ 备用数据源{source_name}失败: {e}")
                continue

        # 所有数据源都失败，返回默认值
        logger.error(f"❌ 所有数据源都无法获取{symbol}的股票信息")
        return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

    def _get_akshare_stock_info(self, symbol: str) -> Dict:
        """使用AKShare获取股票基本信息

        🔥 重要：AKShare 需要区分股票和指数
        - 对于 000001，如果不加后缀，会被识别为"深圳成指"（指数）
        - 对于股票，需要使用完整代码（如 sz000001 或 sh600000）
        """
        try:
            import akshare as ak

            # 🔥 转换为 AKShare 格式的股票代码
            # AKShare 的 stock_individual_info_em 需要使用 "sz000001" 或 "sh600000" 格式
            if symbol.startswith('6'):
                # 上海股票：600000 -> sh600000
                akshare_symbol = f"sh{symbol}"
            elif symbol.startswith(('0', '3', '2')):
                # 深圳股票：000001 -> sz000001
                akshare_symbol = f"sz{symbol}"
            elif symbol.startswith(('8', '4')):
                # 北京股票：830000 -> bj830000
                akshare_symbol = f"bj{symbol}"
            else:
                # 其他情况，直接使用原始代码
                akshare_symbol = symbol

            logger.debug(f"📊 [AKShare股票信息] 原始代码: {symbol}, AKShare格式: {akshare_symbol}")

            # 尝试获取个股信息
            stock_info = ak.stock_individual_info_em(symbol=akshare_symbol)

            if stock_info is not None and not stock_info.empty:
                # 转换为字典格式
                info = {'symbol': symbol, 'source': 'akshare'}

                # 提取股票名称
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    stock_name = name_row['value'].iloc[0]
                    info['name'] = stock_name
                    logger.info(f"✅ [AKShare股票信息] {symbol} -> {stock_name}")
                else:
                    info['name'] = f'股票{symbol}'
                    logger.warning(f"⚠️ [AKShare股票信息] 未找到股票简称: {symbol}")

                # 提取其他信息
                info['area'] = '未知'  # AKShare没有地区信息
                info['industry'] = '未知'  # 可以通过其他API获取
                info['market'] = '未知'  # 可以根据股票代码推断
                info['list_date'] = '未知'  # 可以通过其他API获取

                return info
            else:
                logger.warning(f"⚠️ [AKShare股票信息] 返回空数据: {symbol}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

        except Exception as e:
            logger.error(f"❌ [股票信息] AKShare获取失败: {symbol}, 错误: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare', 'error': str(e)}

    def _get_baostock_stock_info(self, symbol: str) -> Dict:
        """使用BaoStock获取股票基本信息"""
        try:
            import baostock as bs

            # 转换股票代码格式
            if symbol.startswith('6'):
                bs_code = f"sh.{symbol}"
            else:
                bs_code = f"sz.{symbol}"

            # 登录BaoStock
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"❌ [股票信息] BaoStock登录失败: {lg.error_msg}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

            # 查询股票基本信息
            rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != '0':
                bs.logout()
                logger.error(f"❌ [股票信息] BaoStock查询失败: {rs.error_msg}")
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

            # 解析结果
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            # 登出
            bs.logout()

            if data_list:
                # BaoStock返回格式: [code, code_name, ipoDate, outDate, type, status]
                info = {'symbol': symbol, 'source': 'baostock'}
                info['name'] = data_list[0][1]  # code_name
                info['area'] = '未知'  # BaoStock没有地区信息
                info['industry'] = '未知'  # BaoStock没有行业信息
                info['market'] = '未知'  # 可以根据股票代码推断
                info['list_date'] = data_list[0][2]  # ipoDate

                return info
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock'}

        except Exception as e:
            logger.error(f"❌ [股票信息] BaoStock获取失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'baostock', 'error': str(e)}

    def _parse_stock_info_string(self, info_str: str, symbol: str) -> Dict:
        """解析股票信息字符串为字典"""
        try:
            info = {'symbol': symbol, 'source': self.current_source.value}
            lines = info_str.split('\n')

            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if '股票名称' in key:
                        info['name'] = value
                    elif '所属行业' in key:
                        info['industry'] = value
                    elif '所属地区' in key:
                        info['area'] = value
                    elif '上市市场' in key:
                        info['market'] = value
                    elif '上市日期' in key:
                        info['list_date'] = value

            return info

        except Exception as e:
            logger.error(f"⚠️ 解析股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': self.current_source.value}

    # ==================== 基本面数据获取方法 ====================

    def _get_mongodb_fundamentals(self, symbol: str) -> str:
        """从 MongoDB 获取财务数据"""
        logger.debug(f"📊 [MongoDB] 调用参数: symbol={symbol}")

        try:
            from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
            import pandas as pd
            adapter = get_mongodb_cache_adapter()

            # 从 MongoDB 获取财务数据
            financial_data = adapter.get_financial_data(symbol)

            # 检查数据类型和内容
            if financial_data is not None:
                # 如果是 DataFrame，转换为字典列表
                if isinstance(financial_data, pd.DataFrame):
                    if not financial_data.empty:
                        logger.info(f"✅ [数据来源: MongoDB-财务数据] 成功获取: {symbol} ({len(financial_data)}条记录)")
                        # 转换为字典列表
                        financial_dict_list = financial_data.to_dict('records')
                        # 格式化财务数据为报告
                        return self._format_financial_data(symbol, financial_dict_list)
                    else:
                        logger.warning(f"⚠️ [数据来源: MongoDB] 财务数据为空: {symbol}，降级到其他数据源")
                        return self._try_fallback_fundamentals(symbol)
                # 如果是列表
                elif isinstance(financial_data, list) and len(financial_data) > 0:
                    logger.info(f"✅ [数据来源: MongoDB-财务数据] 成功获取: {symbol} ({len(financial_data)}条记录)")
                    return self._format_financial_data(symbol, financial_data)
                # 如果是单个字典（这是MongoDB实际返回的格式）
                elif isinstance(financial_data, dict):
                    logger.info(f"✅ [数据来源: MongoDB-财务数据] 成功获取: {symbol} (单条记录)")
                    # 将单个字典包装成列表
                    financial_dict_list = [financial_data]
                    return self._format_financial_data(symbol, financial_dict_list)
                else:
                    logger.warning(f"⚠️ [数据来源: MongoDB] 未找到财务数据: {symbol}，降级到其他数据源")
                    return self._try_fallback_fundamentals(symbol)
            else:
                logger.warning(f"⚠️ [数据来源: MongoDB] 未找到财务数据: {symbol}，降级到其他数据源")
                # MongoDB 没有数据，降级到其他数据源
                return self._try_fallback_fundamentals(symbol)

        except Exception as e:
            logger.error(f"❌ [数据来源: MongoDB异常] 获取财务数据失败: {e}", exc_info=True)
            # MongoDB 异常，降级到其他数据源
            return self._try_fallback_fundamentals(symbol)

    def _get_tushare_fundamentals(self, symbol: str) -> str:
        """从 Tushare 获取基本面数据 - 暂时不可用，需要实现"""
        logger.warning(f"⚠️ Tushare基本面数据功能暂时不可用")
        return f"⚠️ Tushare基本面数据功能暂时不可用，请使用其他数据源"

    def _get_akshare_fundamentals(self, symbol: str) -> str:
        """从 AKShare 生成基本面分析"""
        logger.debug(f"📊 [AKShare] 调用参数: symbol={symbol}")

        try:
            # AKShare 没有直接的基本面数据接口，使用生成分析
            logger.info(f"📊 [数据来源: AKShare-生成分析] 生成基本面分析: {symbol}")
            return self._generate_fundamentals_analysis(symbol)

        except Exception as e:
            logger.error(f"❌ [数据来源: AKShare异常] 生成基本面分析失败: {e}")
            return f"❌ 生成{symbol}基本面分析失败: {e}"

    def _get_valuation_indicators(self, symbol: str) -> Dict:
        """从stock_basic_info集合获取估值指标"""
        try:
            db_manager = get_database_manager()
            if not db_manager.is_mongodb_available():
                return {}
                
            client = db_manager.get_mongodb_client()
            db = client[db_manager.config.mongodb_config.database_name]
            
            # 从stock_basic_info集合获取估值指标
            collection = db['stock_basic_info']
            result = collection.find_one({'ts_code': symbol})
            
            if result:
                return {
                    'pe': result.get('pe'),
                    'pb': result.get('pb'),
                    'pe_ttm': result.get('pe_ttm'),
                    'total_mv': result.get('total_mv'),
                    'circ_mv': result.get('circ_mv')
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取{symbol}估值指标失败: {e}")
            return {}

    def _format_financial_data(self, symbol: str, financial_data: List[Dict]) -> str:
        """格式化财务数据为报告"""
        try:
            if not financial_data or len(financial_data) == 0:
                return f"❌ 未找到{symbol}的财务数据"

            # 获取最新的财务数据
            latest = financial_data[0]

            # 构建报告
            report = f"📊 {symbol} 基本面数据（来自MongoDB）\n\n"

            # 基本信息
            report += f"📅 报告期: {latest.get('report_period', latest.get('end_date', '未知'))}\n"
            report += f"📈 数据来源: MongoDB财务数据库\n\n"

            # 财务指标
            report += "💰 财务指标:\n"
            revenue = latest.get('revenue') or latest.get('total_revenue')
            if revenue is not None:
                report += f"   营业总收入: {revenue:,.2f}\n"
            
            net_profit = latest.get('net_profit') or latest.get('net_income')
            if net_profit is not None:
                report += f"   净利润: {net_profit:,.2f}\n"
                
            total_assets = latest.get('total_assets')
            if total_assets is not None:
                report += f"   总资产: {total_assets:,.2f}\n"
                
            total_liab = latest.get('total_liab')
            if total_liab is not None:
                report += f"   总负债: {total_liab:,.2f}\n"
                
            total_equity = latest.get('total_equity')
            if total_equity is not None:
                report += f"   股东权益: {total_equity:,.2f}\n"

            # 估值指标 - 从stock_basic_info集合获取
            report += "\n📊 估值指标:\n"
            valuation_data = self._get_valuation_indicators(symbol)
            if valuation_data:
                pe = valuation_data.get('pe')
                if pe is not None:
                    report += f"   市盈率(PE): {pe:.2f}\n"
                    
                pb = valuation_data.get('pb')
                if pb is not None:
                    report += f"   市净率(PB): {pb:.2f}\n"
                    
                pe_ttm = valuation_data.get('pe_ttm')
                if pe_ttm is not None:
                    report += f"   市盈率TTM(PE_TTM): {pe_ttm:.2f}\n"
                    
                total_mv = valuation_data.get('total_mv')
                if total_mv is not None:
                    report += f"   总市值: {total_mv:.2f}亿元\n"
                    
                circ_mv = valuation_data.get('circ_mv')
                if circ_mv is not None:
                    report += f"   流通市值: {circ_mv:.2f}亿元\n"
            else:
                # 如果无法从stock_basic_info获取，尝试从财务数据计算
                pe = latest.get('pe')
                if pe is not None:
                    report += f"   市盈率(PE): {pe:.2f}\n"
                    
                pb = latest.get('pb')
                if pb is not None:
                    report += f"   市净率(PB): {pb:.2f}\n"
                    
                ps = latest.get('ps')
                if ps is not None:
                    report += f"   市销率(PS): {ps:.2f}\n"

            # 盈利能力
            report += "\n💹 盈利能力:\n"
            roe = latest.get('roe')
            if roe is not None:
                report += f"   净资产收益率(ROE): {roe:.2f}%\n"
                
            roa = latest.get('roa')
            if roa is not None:
                report += f"   总资产收益率(ROA): {roa:.2f}%\n"
                
            gross_margin = latest.get('gross_margin')
            if gross_margin is not None:
                report += f"   毛利率: {gross_margin:.2f}%\n"
                
            netprofit_margin = latest.get('netprofit_margin') or latest.get('net_margin')
            if netprofit_margin is not None:
                report += f"   净利率: {netprofit_margin:.2f}%\n"

            # 现金流
            n_cashflow_act = latest.get('n_cashflow_act')
            if n_cashflow_act is not None:
                report += "\n💰 现金流:\n"
                report += f"   经营活动现金流: {n_cashflow_act:,.2f}\n"
                
                n_cashflow_inv_act = latest.get('n_cashflow_inv_act')
                if n_cashflow_inv_act is not None:
                    report += f"   投资活动现金流: {n_cashflow_inv_act:,.2f}\n"
                    
                c_cash_equ_end_period = latest.get('c_cash_equ_end_period')
                if c_cash_equ_end_period is not None:
                    report += f"   期末现金及等价物: {c_cash_equ_end_period:,.2f}\n"

            report += f"\n📝 共有 {len(financial_data)} 期财务数据\n"

            return report

        except Exception as e:
            logger.error(f"❌ 格式化财务数据失败: {e}")
            return f"❌ 格式化{symbol}财务数据失败: {e}"

    def _generate_fundamentals_analysis(self, symbol: str) -> str:
        """生成基本的基本面分析"""
        try:
            # 获取股票基本信息
            stock_info = self.get_stock_info(symbol)

            report = f"📊 {symbol} 基本面分析（生成）\n\n"
            report += f"📈 股票名称: {stock_info.get('name', '未知')}\n"
            report += f"🏢 所属行业: {stock_info.get('industry', '未知')}\n"
            report += f"📍 所属地区: {stock_info.get('area', '未知')}\n"
            report += f"📅 上市日期: {stock_info.get('list_date', '未知')}\n"
            report += f"🏛️ 交易所: {stock_info.get('exchange', '未知')}\n\n"

            report += "⚠️ 注意: 详细财务数据需要从数据源获取\n"
            report += "💡 建议: 启用MongoDB缓存以获取完整的财务数据\n"

            return report

        except Exception as e:
            logger.error(f"❌ 生成基本面分析失败: {e}")
            return f"❌ 生成{symbol}基本面分析失败: {e}"

    def _try_fallback_fundamentals(self, symbol: str) -> str:
        """基本面数据降级处理"""
        logger.error(f"🔄 {self.current_source.value}失败，尝试备用数据源获取基本面...")

        # 🔥 从数据库获取数据源优先级顺序（根据股票代码识别市场）
        fallback_order = self._get_data_source_priority_order(symbol)

        for source in fallback_order:
            if source != self.current_source and source in self.available_sources:
                try:
                    logger.info(f"🔄 尝试备用数据源获取基本面: {source.value}")

                    # 直接调用具体的数据源方法，避免递归
                    if source == ChinaDataSource.TUSHARE:
                        result = self._get_tushare_fundamentals(symbol)
                    elif source == ChinaDataSource.AKSHARE:
                        result = self._get_akshare_fundamentals(symbol)
                    else:
                        continue

                    if result and "❌" not in result:
                        logger.info(f"✅ [数据来源: 备用数据源] 降级成功获取基本面: {source.value}")
                        return result
                    else:
                        logger.warning(f"⚠️ 备用数据源{source.value}返回错误结果")

                except Exception as e:
                    logger.error(f"❌ 备用数据源{source.value}异常: {e}")
                    continue

        # 所有数据源都失败，生成基本分析
        logger.warning(f"⚠️ [数据来源: 生成分析] 所有数据源失败，生成基本分析: {symbol}")
        return self._generate_fundamentals_analysis(symbol)

    def _get_mongodb_news(self, symbol: str, hours_back: int, limit: int) -> List[Dict[str, Any]]:
        """从MongoDB获取新闻数据"""
        try:
            from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter
            adapter = get_mongodb_cache_adapter()

            # 从MongoDB获取新闻数据
            news_data = adapter.get_news_data(symbol, hours_back=hours_back, limit=limit)

            if news_data and len(news_data) > 0:
                logger.info(f"✅ [数据来源: MongoDB-新闻] 成功获取: {symbol or '市场新闻'} ({len(news_data)}条)")
                return news_data
            else:
                logger.warning(f"⚠️ [数据来源: MongoDB] 未找到新闻: {symbol or '市场新闻'}，降级到其他数据源")
                return self._try_fallback_news(symbol, hours_back, limit)

        except Exception as e:
            logger.error(f"❌ [数据来源: MongoDB] 获取新闻失败: {e}")
            return self._try_fallback_news(symbol, hours_back, limit)

    def _get_tushare_news(self, symbol: str, hours_back: int, limit: int) -> List[Dict[str, Any]]:
        """从Tushare获取新闻数据"""
        try:
            # Tushare新闻功能暂时不可用，返回空列表
            logger.warning(f"⚠️ [数据来源: Tushare] Tushare新闻功能暂时不可用")
            return []

        except Exception as e:
            logger.error(f"❌ [数据来源: Tushare] 获取新闻失败: {e}")
            return []

    def _get_akshare_news(self, symbol: str, hours_back: int, limit: int) -> List[Dict[str, Any]]:
        """从AKShare获取新闻数据"""
        try:
            # AKShare新闻功能暂时不可用，返回空列表
            logger.warning(f"⚠️ [数据来源: AKShare] AKShare新闻功能暂时不可用")
            return []

        except Exception as e:
            logger.error(f"❌ [数据来源: AKShare] 获取新闻失败: {e}")
            return []

    def _try_fallback_news(self, symbol: str, hours_back: int, limit: int) -> List[Dict[str, Any]]:
        """新闻数据降级处理"""
        logger.error(f"🔄 {self.current_source.value}失败，尝试备用数据源获取新闻...")

        # 🔥 从数据库获取数据源优先级顺序（根据股票代码识别市场）
        fallback_order = self._get_data_source_priority_order(symbol)

        for source in fallback_order:
            if source != self.current_source and source in self.available_sources:
                try:
                    logger.info(f"🔄 尝试备用数据源获取新闻: {source.value}")

                    # 直接调用具体的数据源方法，避免递归
                    if source == ChinaDataSource.TUSHARE:
                        result = self._get_tushare_news(symbol, hours_back, limit)
                    elif source == ChinaDataSource.AKSHARE:
                        result = self._get_akshare_news(symbol, hours_back, limit)
                    else:
                        continue

                    if result and len(result) > 0:
                        logger.info(f"✅ [数据来源: 备用数据源] 降级成功获取新闻: {source.value}")
                        return result
                    else:
                        logger.warning(f"⚠️ 备用数据源{source.value}未返回新闻")

                except Exception as e:
                    logger.error(f"❌ 备用数据源{source.value}异常: {e}")
                    continue

        # 所有数据源都失败
        logger.warning(f"⚠️ [数据来源: 所有数据源失败] 无法获取新闻: {symbol or '市场新闻'}")
        return []


# 全局数据源管理器实例
_data_source_manager = None

def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager


def get_china_stock_data_unified(symbol: str, start_date: str, end_date: str) -> str:
    """
    统一的中国股票数据获取接口
    自动使用配置的数据源，支持备用数据源

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的股票数据
    """
    from tradingagents.utils.logging_init import get_logger


    # 添加详细的股票代码追踪日志
    logger.info(f"🔍 [股票代码追踪] data_source_manager.get_china_stock_data_unified 接收到的股票代码: '{symbol}' (类型: {type(symbol)})")
    logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(symbol))}")
    logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(symbol))}")

    manager = get_data_source_manager()
    logger.info(f"🔍 [股票代码追踪] 调用 manager.get_stock_data，传入参数: symbol='{symbol}', start_date='{start_date}', end_date='{end_date}'")
    result = manager.get_stock_data(symbol, start_date, end_date)
    # 分析返回结果的详细信息
    if result:
        lines = result.split('\n')
        data_lines = [line for line in lines if '2025-' in line and symbol in line]
        logger.info(f"🔍 [股票代码追踪] 返回结果统计: 总行数={len(lines)}, 数据行数={len(data_lines)}, 结果长度={len(result)}字符")
        logger.info(f"🔍 [股票代码追踪] 返回结果前500字符: {result[:500]}")
        if len(data_lines) > 0:
            logger.info(f"🔍 [股票代码追踪] 数据行示例: 第1行='{data_lines[0][:100]}', 最后1行='{data_lines[-1][:100]}'")
    else:
        logger.info(f"🔍 [股票代码追踪] 返回结果: None")
    return result


def get_china_stock_info_unified(symbol: str) -> Dict:
    """
    统一的中国股票信息获取接口

    Args:
        symbol: 股票代码

    Returns:
        Dict: 股票基本信息
    """
    manager = get_data_source_manager()
    return manager.get_stock_info(symbol)


# 全局数据源管理器实例
_data_source_manager = None

def get_data_source_manager() -> DataSourceManager:
    """获取全局数据源管理器实例"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager

# ==================== 兼容性接口 ====================
# 为了兼容 stock_data_service，提供相同的接口

def get_stock_data_service() -> DataSourceManager:
    """
    获取股票数据服务实例（兼容 stock_data_service 接口）

    ⚠️ 此函数为兼容性接口，实际返回 DataSourceManager 实例
    推荐直接使用 get_data_source_manager()
    """
    return get_data_source_manager()


# ==================== 美股数据源管理器 ====================

class USDataSourceManager:
    """
    美股数据源管理器

    支持的数据源：
    - yfinance: 股票价格和技术指标（免费）
    - alpha_vantage: 基本面和新闻数据（需要API Key）
    - finnhub: 备用数据源（需要API Key）
    - mongodb: 缓存数据源（最高优先级）
    """

    def __init__(self):
        """初始化美股数据源管理器"""
        # 检查是否启用 MongoDB 缓存
        self.use_mongodb_cache = self._check_mongodb_enabled()

        # 检查可用的数据源
        self.available_sources = self._check_available_sources()

        # 设置默认数据源
        self.default_source = self._get_default_source()
        self.current_source = self.default_source

        logger.info(f"📊 美股数据源管理器初始化完成")
        logger.info(f"   MongoDB缓存: {'✅ 已启用' if self.use_mongodb_cache else '❌ 未启用'}")
        logger.info(f"   默认数据源: {self.default_source.value}")
        logger.info(f"   可用数据源: {[s.value for s in self.available_sources]}")

    def _check_mongodb_enabled(self) -> bool:
        """检查是否启用MongoDB缓存"""
        from tradingagents.config.runtime_settings import use_app_cache_enabled
        return use_app_cache_enabled()

    def _get_data_source_priority_order(self, symbol: Optional[str] = None) -> List[USDataSource]:
        """
        从数据库获取美股数据源优先级顺序（用于降级）

        Args:
            symbol: 股票代码

        Returns:
            按优先级排序的数据源列表（不包含MongoDB）
        """
        try:
            # 从数据库读取数据源配置
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()

            # 方法1: 从 datasource_groupings 集合读取（推荐）
            groupings_collection = db.datasource_groupings
            groupings = list(groupings_collection.find({
                "market_category_id": "us_stocks",
                "enabled": True
            }).sort("priority", -1))  # 降序排序，优先级高的在前

            if groupings:
                # 转换为 USDataSource 枚举
                # 🔥 数据源名称映射（数据库名称 → USDataSource 枚举）
                source_mapping = {
                    'yfinance': USDataSource.YFINANCE,
                    'yahoo_finance': USDataSource.YFINANCE,  # 别名
                    'alpha_vantage': USDataSource.ALPHA_VANTAGE,
                    'finnhub': USDataSource.FINNHUB,
                }

                result = []
                for grouping in groupings:
                    ds_name = grouping.get('data_source_name', '').lower()
                    if ds_name in source_mapping:
                        source = source_mapping[ds_name]
                        # 排除 MongoDB（MongoDB 是最高优先级，不参与降级）
                        if source != USDataSource.MONGODB and source in self.available_sources:
                            result.append(source)

                if result:
                    logger.info(f"✅ [美股数据源优先级] 从数据库读取: {[s.value for s in result]}")
                    return result

            logger.warning("⚠️ [美股数据源优先级] 数据库中没有配置，使用默认顺序")
        except Exception as e:
            logger.warning(f"⚠️ [美股数据源优先级] 从数据库读取失败: {e}，使用默认顺序")

        # 回退到默认顺序
        # 默认顺序：yfinance > Alpha Vantage > Finnhub
        default_order = [
            USDataSource.YFINANCE,
            USDataSource.ALPHA_VANTAGE,
            USDataSource.FINNHUB,
        ]
        # 只返回可用的数据源
        return [s for s in default_order if s in self.available_sources]

    def _get_default_source(self) -> USDataSource:
        """获取默认数据源"""
        # 如果启用MongoDB缓存，MongoDB作为最高优先级数据源
        if self.use_mongodb_cache:
            return USDataSource.MONGODB

        # 从环境变量获取，默认使用 yfinance
        env_source = os.getenv('DEFAULT_US_DATA_SOURCE', DataSourceCode.YFINANCE).lower()

        # 映射到枚举
        source_mapping = {
            DataSourceCode.YFINANCE: USDataSource.YFINANCE,
            DataSourceCode.ALPHA_VANTAGE: USDataSource.ALPHA_VANTAGE,
            DataSourceCode.FINNHUB: USDataSource.FINNHUB,
        }

        return source_mapping.get(env_source, USDataSource.YFINANCE)

    def _check_available_sources(self) -> List[USDataSource]:
        """
        检查可用的数据源

        从数据库读取启用状态，并检查依赖是否满足
        """
        available = []

        # MongoDB 缓存
        if self.use_mongodb_cache:
            available.append(USDataSource.MONGODB)
            logger.info("✅ MongoDB缓存数据源可用")

        # 从数据库读取启用的数据源列表和配置
        enabled_sources_in_db = self._get_enabled_sources_from_db()
        datasource_configs = self._get_datasource_configs_from_db()

        # 检查 yfinance
        if 'yfinance' in enabled_sources_in_db:
            try:
                import yfinance
                available.append(USDataSource.YFINANCE)
                logger.info("✅ yfinance数据源可用且已启用")
            except ImportError:
                logger.warning("⚠️ yfinance数据源不可用: 未安装 yfinance 库")
        else:
            logger.info("ℹ️ yfinance数据源已在数据库中禁用")

        # 检查 Alpha Vantage
        if 'alpha_vantage' in enabled_sources_in_db:
            try:
                # 优先从数据库配置读取 API Key，其次从环境变量读取
                api_key = datasource_configs.get('alpha_vantage', {}).get('api_key') or os.getenv("ALPHA_VANTAGE_API_KEY")
                if api_key:
                    available.append(USDataSource.ALPHA_VANTAGE)
                    source = "数据库配置" if datasource_configs.get('alpha_vantage', {}).get('api_key') else "环境变量"
                    logger.info(f"✅ Alpha Vantage数据源可用且已启用 (API Key来源: {source})")
                else:
                    logger.warning("⚠️ Alpha Vantage数据源不可用: API Key未配置（数据库和环境变量均未找到）")
            except Exception as e:
                logger.warning(f"⚠️ Alpha Vantage数据源检查失败: {e}")
        else:
            logger.info("ℹ️ Alpha Vantage数据源已在数据库中禁用")

        # 检查 Finnhub
        if 'finnhub' in enabled_sources_in_db:
            try:
                # 优先从数据库配置读取 API Key，其次从环境变量读取
                api_key = datasource_configs.get('finnhub', {}).get('api_key') or os.getenv("FINNHUB_API_KEY")
                if api_key:
                    available.append(USDataSource.FINNHUB)
                    source = "数据库配置" if datasource_configs.get('finnhub', {}).get('api_key') else "环境变量"
                    logger.info(f"✅ Finnhub数据源可用且已启用 (API Key来源: {source})")
                else:
                    logger.warning("⚠️ Finnhub数据源不可用: API Key未配置（数据库和环境变量均未找到）")
            except Exception as e:
                logger.warning(f"⚠️ Finnhub数据源检查失败: {e}")
        else:
            logger.info("ℹ️ Finnhub数据源已在数据库中禁用")

        return available

    def _get_enabled_sources_from_db(self) -> List[str]:
        """从数据库读取启用的数据源列表"""
        try:
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()

            # 从 datasource_groupings 集合读取
            groupings = list(db.datasource_groupings.find({
                "market_category_id": "us_stocks",
                "enabled": True
            }))

            # 🔥 数据源名称映射（数据库名称 → 代码中使用的名称）
            name_mapping = {
                'alpha vantage': 'alpha_vantage',
                'yahoo finance': 'yfinance',
                'finnhub': 'finnhub',
            }

            result = []
            for g in groupings:
                db_name = g.get('data_source_name', '').lower()
                # 使用映射表转换名称
                code_name = name_mapping.get(db_name, db_name)
                result.append(code_name)
                logger.debug(f"🔄 数据源名称映射: '{db_name}' → '{code_name}'")

            return result
        except Exception as e:
            logger.warning(f"⚠️ 从数据库读取启用的数据源失败: {e}")
            # 默认全部启用
            return ['yfinance', 'alpha_vantage', 'finnhub']

    def _get_datasource_configs_from_db(self) -> dict:
        """从数据库读取数据源配置（包括 API Key）"""
        try:
            from app.core.database import get_mongo_db_sync
            db = get_mongo_db_sync()

            # 从 system_configs 集合读取激活的配置
            config = db.system_configs.find_one({"is_active": True})
            if not config:
                return {}

            # 提取数据源配置
            datasource_configs = config.get('data_source_configs', [])

            # 构建配置字典 {数据源名称: {api_key, api_secret, ...}}
            result = {}
            for ds_config in datasource_configs:
                name = ds_config.get('name', '').lower()
                result[name] = {
                    'api_key': ds_config.get('api_key', ''),
                    'api_secret': ds_config.get('api_secret', ''),
                    'config_params': ds_config.get('config_params', {})
                }

            return result
        except Exception as e:
            logger.warning(f"⚠️ 从数据库读取数据源配置失败: {e}")
            return {}

    def get_current_source(self) -> USDataSource:
        """获取当前数据源"""
        return self.current_source

    def set_current_source(self, source: USDataSource) -> bool:
        """设置当前数据源"""
        if source in self.available_sources:
            self.current_source = source
            logger.info(f"✅ 美股数据源已切换到: {source.value}")
            return True
        else:
            logger.error(f"❌ 美股数据源不可用: {source.value}")
            return False


# 全局美股数据源管理器实例
_us_data_source_manager = None

def get_us_data_source_manager() -> USDataSourceManager:
    """获取全局美股数据源管理器实例"""
    global _us_data_source_manager
    if _us_data_source_manager is None:
        _us_data_source_manager = USDataSourceManager()
    return _us_data_source_manager
