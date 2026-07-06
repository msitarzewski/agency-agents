#!/usr/bin/env python3
"""
MongoDB + Redis 数据库缓存管理器
提供高性能的股票数据缓存和持久化存储
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from tradingagents.config.runtime_settings import get_timezone_name

from typing import Optional, Dict, Any, List, Union
import pandas as pd

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# MongoDB
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning(f"⚠️ pymongo 未安装，MongoDB功能不可用")

# Redis
try:
    import redis
    from redis.exceptions import ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning(f"⚠️ redis 未安装，Redis功能不可用")


class DatabaseCacheManager:
    """MongoDB + Redis 数据库缓存管理器"""

    def __init__(self,
                 mongodb_url: Optional[str] = None,
                 redis_url: Optional[str] = None,
                 mongodb_db: str = "tradingagents",
                 redis_db: int = 0):
        """
        初始化数据库缓存管理器

        Args:
            mongodb_url: MongoDB连接URL，默认使用配置文件端口
            redis_url: Redis连接URL，默认使用配置文件端口
            mongodb_db: MongoDB数据库名
            redis_db: Redis数据库编号
        """
        # 从配置文件获取正确的端口
        mongodb_port = os.getenv("MONGODB_PORT", "27018")
        redis_port = os.getenv("REDIS_PORT", "6380")
        mongodb_password = os.getenv("MONGODB_PASSWORD", "tradingagents123")
        redis_password = os.getenv("REDIS_PASSWORD", "tradingagents123")

        self.mongodb_url = mongodb_url or os.getenv("MONGODB_URL", f"mongodb://admin:{mongodb_password}@localhost:{mongodb_port}")
        self.redis_url = redis_url or os.getenv("REDIS_URL", f"redis://:{redis_password}@localhost:{redis_port}")
        self.mongodb_db_name = mongodb_db
        self.redis_db = redis_db

        # 初始化连接
        self.mongodb_client = None
        self.mongodb_db = None
        self.redis_client = None

        self._init_mongodb()
        self._init_redis()

        logger.info(f"🗄️ 数据库缓存管理器初始化完成")
        logger.error(f"   MongoDB: {'✅ 已连接' if self.mongodb_client else '❌ 未连接'}")
        logger.error(f"   Redis: {'✅ 已连接' if self.redis_client else '❌ 未连接'}")

    def _init_mongodb(self):
        """初始化MongoDB连接"""
        if not MONGODB_AVAILABLE:
            return

        try:
            # 从环境变量读取超时配置，使用合理的默认值
            import os
            connect_timeout = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "30000"))
            socket_timeout = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "60000"))
            server_selection_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))

            self.mongodb_client = MongoClient(
                self.mongodb_url,
                serverSelectionTimeoutMS=server_selection_timeout,
                connectTimeoutMS=connect_timeout,
                socketTimeoutMS=socket_timeout
            )
            # 测试连接
            self.mongodb_client.admin.command('ping')
            self.mongodb_db = self.mongodb_client[self.mongodb_db_name]

            # 创建索引
            self._create_mongodb_indexes()

            logger.info(f"✅ MongoDB连接成功: {self.mongodb_url}")
            logger.info(f"⏱️  超时配置: connectTimeout={connect_timeout}ms, socketTimeout={socket_timeout}ms")

        except Exception as e:
            logger.error(f"❌ MongoDB连接失败: {e}")
            self.mongodb_client = None
            self.mongodb_db = None

    def _init_redis(self):
        """初始化Redis连接"""
        if not REDIS_AVAILABLE:
            return

        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                db=self.redis_db,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()

            logger.info(f"✅ Redis连接成功: {self.redis_url}")

        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            self.redis_client = None

    def _create_mongodb_indexes(self):
        """创建MongoDB索引"""
        if self.mongodb_db is None:
            return

        try:
            # 股票数据集合索引
            stock_collection = self.mongodb_db.stock_data
            stock_collection.create_index([
                ("symbol", 1),
                ("data_source", 1),
                ("start_date", 1),
                ("end_date", 1)
            ])
            stock_collection.create_index([("created_at", 1)])

            # 新闻数据集合索引
            news_collection = self.mongodb_db.news_data
            news_collection.create_index([
                ("symbol", 1),
                ("data_source", 1),
                ("date_range", 1)
            ])
            news_collection.create_index([("created_at", 1)])

            # 基本面数据集合索引
            fundamentals_collection = self.mongodb_db.fundamentals_data
            fundamentals_collection.create_index([
                ("symbol", 1),
                ("data_source", 1),
                ("analysis_date", 1)
            ])
            fundamentals_collection.create_index([("created_at", 1)])

            logger.info(f"✅ MongoDB索引创建完成")

        except Exception as e:
            logger.error(f"⚠️ MongoDB索引创建失败: {e}")

    def _generate_cache_key(self, data_type: str, symbol: str, **kwargs) -> str:
        """生成缓存键"""
        params_str = f"{data_type}_{symbol}"
        for key, value in sorted(kwargs.items()):
            params_str += f"_{key}_{value}"

        cache_key = hashlib.md5(params_str.encode()).hexdigest()[:16]
        return f"{data_type}:{symbol}:{cache_key}"

    def save_stock_data(self, symbol: str, data: Union[pd.DataFrame, str],
                       start_date: str = None, end_date: str = None,
                       data_source: str = "unknown", market_type: str = None) -> str:
        """
        保存股票数据到MongoDB和Redis

        Args:
            symbol: 股票代码
            data: 股票数据
            start_date: 开始日期
            end_date: 结束日期
            data_source: 数据源
            market_type: 市场类型 (us/china)

        Returns:
            cache_key: 缓存键
        """
        cache_key = self._generate_cache_key("stock", symbol,
                                           start_date=start_date,
                                           end_date=end_date,
                                           source=data_source)

        # 自动推断市场类型
        if market_type is None:
            # 根据股票代码格式推断市场类型
            import re

            if re.match(r'^\d{6}$', symbol):  # 6位数字为A股
                market_type = "china"
            else:  # 其他格式为美股
                market_type = "us"

        # 准备文档数据
        doc = {
            "_id": cache_key,
            "symbol": symbol,
            "market_type": market_type,
            "data_type": "stock_data",
            "start_date": start_date,
            "end_date": end_date,
            "data_source": data_source,
            "created_at": datetime.now(ZoneInfo(get_timezone_name())),
            "updated_at": datetime.now(ZoneInfo(get_timezone_name()))
        }

        # 处理数据格式
        if isinstance(data, pd.DataFrame):
            doc["data"] = data.to_json(orient='records', date_format='iso')
            doc["data_format"] = "dataframe_json"
        else:
            doc["data"] = str(data)
            doc["data_format"] = "text"

        # 保存到MongoDB（持久化）
        if self.mongodb_db is not None:
            try:
                collection = self.mongodb_db.stock_data
                collection.replace_one({"_id": cache_key}, doc, upsert=True)
                logger.info(f"💾 股票数据已保存到MongoDB: {symbol} -> {cache_key}")
            except Exception as e:
                logger.error(f"⚠️ MongoDB保存失败: {e}")

        # 保存到Redis（快速缓存，6小时过期）
        if self.redis_client:
            try:
                redis_data = {
                    "data": doc["data"],
                    "data_format": doc["data_format"],
                    "symbol": symbol,
                    "data_source": data_source,
                    "created_at": doc["created_at"].isoformat()
                }
                self.redis_client.setex(
                    cache_key,
                    6 * 3600,  # 6小时过期
                    json.dumps(redis_data, ensure_ascii=False)
                )
                logger.info(f"⚡ 股票数据已缓存到Redis: {symbol} -> {cache_key}")
            except Exception as e:
                logger.error(f"⚠️ Redis缓存失败: {e}")

        return cache_key

    def load_stock_data(self, cache_key: str) -> Optional[Union[pd.DataFrame, str]]:
        """从Redis或MongoDB加载股票数据"""

        # 首先尝试从Redis加载（更快）
        if self.redis_client:
            try:
                redis_data = self.redis_client.get(cache_key)
                if redis_data:
                    data_dict = json.loads(redis_data)
                    logger.info(f"⚡ 从Redis加载数据: {cache_key}")

                    if data_dict["data_format"] == "dataframe_json":
                        return pd.read_json(data_dict["data"], orient='records')
                    else:
                        return data_dict["data"]
            except Exception as e:
                logger.error(f"⚠️ Redis加载失败: {e}")

        # 如果Redis没有，从MongoDB加载
        if self.mongodb_db is not None:
            try:
                collection = self.mongodb_db.stock_data
                doc = collection.find_one({"_id": cache_key})

                if doc:
                    logger.info(f"💾 从MongoDB加载数据: {cache_key}")

                    # 同时更新到Redis缓存
                    if self.redis_client:
                        try:
                            redis_data = {
                                "data": doc["data"],
                                "data_format": doc["data_format"],
                                "symbol": doc["symbol"],
                                "data_source": doc["data_source"],
                                "created_at": doc["created_at"].isoformat()
                            }
                            self.redis_client.setex(
                                cache_key,
                                6 * 3600,
                                json.dumps(redis_data, ensure_ascii=False)
                            )
                            logger.info(f"⚡ 数据已同步到Redis缓存")
                        except Exception as e:
                            logger.error(f"⚠️ Redis同步失败: {e}")

                    if doc["data_format"] == "dataframe_json":
                        return pd.read_json(doc["data"], orient='records')
                    else:
                        return doc["data"]

            except Exception as e:
                logger.error(f"⚠️ MongoDB加载失败: {e}")

        return None

    def find_cached_stock_data(self, symbol: str, start_date: str = None,
                              end_date: str = None, data_source: str = None,
                              max_age_hours: int = 6) -> Optional[str]:
        """查找匹配的缓存数据"""

        # 生成精确匹配的缓存键
        exact_key = self._generate_cache_key("stock", symbol,
                                           start_date=start_date,
                                           end_date=end_date,
                                           source=data_source)

        # 检查Redis中是否有精确匹配
        if self.redis_client and self.redis_client.exists(exact_key):
            logger.info(f"⚡ Redis中找到精确匹配: {symbol} -> {exact_key}")
            return exact_key

        # 检查MongoDB中的匹配项
        if self.mongodb_db is not None:
            try:
                collection = self.mongodb_db.stock_data
                cutoff_time = datetime.now(ZoneInfo(get_timezone_name())) - timedelta(hours=max_age_hours)

                query = {
                    "symbol": symbol,
                    "created_at": {"$gte": cutoff_time}
                }

                if data_source:
                    query["data_source"] = data_source
                if start_date:
                    query["start_date"] = start_date
                if end_date:
                    query["end_date"] = end_date

                doc = collection.find_one(query, sort=[("created_at", -1)])

                if doc:
                    cache_key = doc["_id"]
                    logger.info(f"💾 MongoDB中找到匹配: {symbol} -> {cache_key}")
                    return cache_key

            except Exception as e:
                logger.error(f"⚠️ MongoDB查询失败: {e}")

        logger.error(f"❌ 未找到有效缓存: {symbol}")
        return None

    def save_news_data(self, symbol: str, news_data: str,
                      start_date: str = None, end_date: str = None,
                      data_source: str = "unknown") -> str:
        """保存新闻数据到MongoDB和Redis"""
        cache_key = self._generate_cache_key("news", symbol,
                                           start_date=start_date,
                                           end_date=end_date,
                                           source=data_source)

        doc = {
            "_id": cache_key,
            "symbol": symbol,
            "data_type": "news_data",
            "date_range": f"{start_date}_{end_date}",
            "start_date": start_date,
            "end_date": end_date,
            "data_source": data_source,
            "data": news_data,
            "created_at": datetime.now(ZoneInfo(get_timezone_name())),
            "updated_at": datetime.now(ZoneInfo(get_timezone_name()))
        }

        # 保存到MongoDB
        if self.mongodb_db is not None:
            try:
                collection = self.mongodb_db.news_data
                collection.replace_one({"_id": cache_key}, doc, upsert=True)
                logger.info(f"📰 新闻数据已保存到MongoDB: {symbol} -> {cache_key}")
            except Exception as e:
                logger.error(f"⚠️ MongoDB保存失败: {e}")

        # 保存到Redis（24小时过期）
        if self.redis_client:
            try:
                redis_data = {
                    "data": news_data,
                    "symbol": symbol,
                    "data_source": data_source,
                    "created_at": doc["created_at"].isoformat()
                }
                self.redis_client.setex(
                    cache_key,
                    24 * 3600,  # 24小时过期
                    json.dumps(redis_data, ensure_ascii=False)
                )
                logger.info(f"⚡ 新闻数据已缓存到Redis: {symbol} -> {cache_key}")
            except Exception as e:
                logger.error(f"⚠️ Redis缓存失败: {e}")

        return cache_key

    def save_fundamentals_data(self, symbol: str, fundamentals_data: str,
                              analysis_date: str = None,
                              data_source: str = "unknown") -> str:
        """保存基本面数据到MongoDB和Redis"""
        if not analysis_date:
            analysis_date = datetime.now(ZoneInfo(get_timezone_name())).strftime("%Y-%m-%d")

        cache_key = self._generate_cache_key("fundamentals", symbol,
                                           date=analysis_date,
                                           source=data_source)

        doc = {
            "_id": cache_key,
            "symbol": symbol,
            "data_type": "fundamentals_data",
            "analysis_date": analysis_date,
            "data_source": data_source,
            "data": fundamentals_data,
            "created_at": datetime.now(ZoneInfo(get_timezone_name())),
            "updated_at": datetime.now(ZoneInfo(get_timezone_name()))
        }

        # 保存到MongoDB
        if self.mongodb_db is not None:
            try:
                collection = self.mongodb_db.fundamentals_data
                collection.replace_one({"_id": cache_key}, doc, upsert=True)
                logger.info(f"💼 基本面数据已保存到MongoDB: {symbol} -> {cache_key}")
            except Exception as e:
                logger.error(f"⚠️ MongoDB保存失败: {e}")

        # 保存到Redis（24小时过期）
        if self.redis_client:
            try:
                redis_data = {
                    "data": fundamentals_data,
                    "symbol": symbol,
                    "data_source": data_source,
                    "analysis_date": analysis_date,
                    "created_at": doc["created_at"].isoformat()
                }
                self.redis_client.setex(
                    cache_key,
                    24 * 3600,  # 24小时过期
                    json.dumps(redis_data, ensure_ascii=False)
                )
                logger.info(f"⚡ 基本面数据已缓存到Redis: {symbol} -> {cache_key}")
            except Exception as e:
                logger.error(f"⚠️ Redis缓存失败: {e}")

        return cache_key

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        # 标准统计格式（与 file_cache 保持一致）
        stats = {
            'total_files': 0,
            'stock_data_count': 0,
            'news_count': 0,
            'fundamentals_count': 0,
            'total_size': 0,  # 字节
            'total_size_mb': 0,  # MB
            'skipped_count': 0
        }

        # 详细的后端信息
        backend_info = {
            "mongodb": {"available": self.mongodb_db is not None, "collections": {}},
            "redis": {"available": self.redis_client is not None, "keys": 0, "memory_usage": "N/A"}
        }

        # MongoDB统计
        total_size_bytes = 0
        if self.mongodb_db is not None:
            try:
                for collection_name in ["stock_data", "news_data", "fundamentals_data"]:
                    collection = self.mongodb_db[collection_name]
                    count = collection.count_documents({})
                    size = self.mongodb_db.command("collStats", collection_name).get("size", 0)
                    backend_info["mongodb"]["collections"][collection_name] = {
                        "count": count,
                        "size_mb": round(size / (1024 * 1024), 2)
                    }

                    # 累加到标准统计
                    total_size_bytes += size
                    stats['total_files'] += count

                    # 按类型分类
                    if collection_name == "stock_data":
                        stats['stock_data_count'] += count
                    elif collection_name == "news_data":
                        stats['news_count'] += count
                    elif collection_name == "fundamentals_data":
                        stats['fundamentals_count'] += count

            except Exception as e:
                logger.error(f"⚠️ MongoDB统计获取失败: {e}")

        # Redis统计
        if self.redis_client:
            try:
                info = self.redis_client.info()
                backend_info["redis"]["keys"] = info.get("db0", {}).get("keys", 0)
                backend_info["redis"]["memory_usage"] = f"{info.get('used_memory_human', 'N/A')}"
            except Exception as e:
                logger.error(f"⚠️ Redis统计获取失败: {e}")

        # 设置总大小
        stats['total_size'] = total_size_bytes
        stats['total_size_mb'] = round(total_size_bytes / (1024 * 1024), 2)

        # 添加后端详细信息
        stats['backend_info'] = backend_info

        return stats

    def clear_old_cache(self, max_age_days: int = 7):
        """清理过期缓存"""
        cutoff_time = datetime.now(ZoneInfo(get_timezone_name())) - timedelta(days=max_age_days)
        cleared_count = 0

        # 清理MongoDB
        if self.mongodb_db is not None:
            try:
                for collection_name in ["stock_data", "news_data", "fundamentals_data"]:
                    collection = self.mongodb_db[collection_name]
                    result = collection.delete_many({"created_at": {"$lt": cutoff_time}})
                    cleared_count += result.deleted_count
                    logger.info(f"🧹 MongoDB {collection_name} 清理了 {result.deleted_count} 条记录")
            except Exception as e:
                logger.error(f"⚠️ MongoDB清理失败: {e}")

        # Redis会自动过期，不需要手动清理
        logger.info(f"🧹 总共清理了 {cleared_count} 条过期记录")
        return cleared_count

    def close(self):
        """关闭数据库连接"""
        if self.mongodb_client:
            self.mongodb_client.close()
            logger.info(f"🔒 MongoDB连接已关闭")

        if self.redis_client:
            self.redis_client.close()
            logger.info(f"🔒 Redis连接已关闭")


# 全局数据库缓存实例
_db_cache_instance = None

def get_db_cache() -> DatabaseCacheManager:
    """获取全局数据库缓存实例"""
    global _db_cache_instance
    if _db_cache_instance is None:
        _db_cache_instance = DatabaseCacheManager()
    return _db_cache_instance
