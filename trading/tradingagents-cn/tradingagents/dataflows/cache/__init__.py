"""
缓存管理模块

支持多种缓存策略：
- 文件缓存（默认）- 简单稳定，不依赖外部服务
- 数据库缓存（可选）- MongoDB + Redis，性能更好
- 自适应缓存（推荐）- 自动选择最佳后端

使用方法：
    from tradingagents.dataflows.cache import get_cache
    cache = get_cache()  # 自动选择最佳缓存策略

配置缓存策略：
    export TA_CACHE_STRATEGY=integrated  # 启用集成缓存（MongoDB/Redis）
    export TA_CACHE_STRATEGY=file        # 使用文件缓存（默认）
"""

import os
from typing import Union

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# 导入文件缓存
try:
    from .file_cache import StockDataCache
    FILE_CACHE_AVAILABLE = True
except ImportError:
    StockDataCache = None
    FILE_CACHE_AVAILABLE = False

# 导入数据库缓存
try:
    from .db_cache import DatabaseCacheManager
    DB_CACHE_AVAILABLE = True
except ImportError:
    DatabaseCacheManager = None
    DB_CACHE_AVAILABLE = False

# 导入自适应缓存
try:
    from .adaptive import AdaptiveCacheSystem
    ADAPTIVE_CACHE_AVAILABLE = True
except ImportError:
    AdaptiveCacheSystem = None
    ADAPTIVE_CACHE_AVAILABLE = False

# 导入集成缓存
try:
    from .integrated import IntegratedCacheManager
    INTEGRATED_CACHE_AVAILABLE = True
except ImportError:
    IntegratedCacheManager = None
    INTEGRATED_CACHE_AVAILABLE = False

# 导入应用缓存适配器（函数，非类）
try:
    from .app_adapter import get_basics_from_cache, get_market_quote_dataframe
    APP_CACHE_AVAILABLE = True
except ImportError:
    get_basics_from_cache = None
    get_market_quote_dataframe = None
    APP_CACHE_AVAILABLE = False

# 导入 MongoDB 缓存适配器
try:
    from .mongodb_cache_adapter import MongoDBCacheAdapter
    MONGODB_CACHE_ADAPTER_AVAILABLE = True
except ImportError:
    MongoDBCacheAdapter = None
    MONGODB_CACHE_ADAPTER_AVAILABLE = False

# 全局缓存实例
_cache_instance = None

# 默认缓存策略（改为 integrated，优先使用 MongoDB/Redis 缓存）
DEFAULT_CACHE_STRATEGY = os.getenv("TA_CACHE_STRATEGY", "integrated")

def get_cache() -> Union[StockDataCache, IntegratedCacheManager]:
    """
    获取缓存实例（统一入口）

    根据环境变量 TA_CACHE_STRATEGY 选择缓存策略：
    - "file" (默认): 使用文件缓存
    - "integrated": 使用集成缓存（自动选择 MongoDB/Redis/File）
    - "adaptive": 使用自适应缓存（同 integrated）

    环境变量设置：
        export TA_CACHE_STRATEGY=integrated  # Linux/Mac
        set TA_CACHE_STRATEGY=integrated     # Windows

    返回：
        StockDataCache 或 IntegratedCacheManager 实例
    """
    global _cache_instance

    if _cache_instance is None:
        if DEFAULT_CACHE_STRATEGY in ["integrated", "adaptive"]:
            if INTEGRATED_CACHE_AVAILABLE:
                try:
                    _cache_instance = IntegratedCacheManager()
                    logger.info("✅ 使用集成缓存系统（支持 MongoDB/Redis/File 自动选择）")
                except Exception as e:
                    logger.warning(f"⚠️ 集成缓存初始化失败，降级到文件缓存: {e}")
                    _cache_instance = StockDataCache()
            else:
                logger.warning("⚠️ 集成缓存不可用，使用文件缓存")
                _cache_instance = StockDataCache()
        else:
            _cache_instance = StockDataCache()
            logger.info("✅ 使用文件缓存系统")

    return _cache_instance

__all__ = [
    # 统一入口（推荐使用）
    'get_cache',

    # 缓存类（供高级用户直接使用）
    'StockDataCache',
    'IntegratedCacheManager',
    'DatabaseCacheManager',
    'AdaptiveCacheSystem',

    # 可用性标志
    'FILE_CACHE_AVAILABLE',
    'DB_CACHE_AVAILABLE',
    'ADAPTIVE_CACHE_AVAILABLE',
    'INTEGRATED_CACHE_AVAILABLE',

    # 应用缓存适配器
    'get_basics_from_cache',
    'get_market_quote_dataframe',
    'APP_CACHE_AVAILABLE',

    # MongoDB 缓存适配器
    'MongoDBCacheAdapter',
    'MONGODB_CACHE_ADAPTER_AVAILABLE',
]

