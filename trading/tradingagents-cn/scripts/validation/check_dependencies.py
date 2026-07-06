#!/usr/bin/env python3
"""
检查和配置MongoDB等依赖项
确保系统可以在有或没有MongoDB的情况下正常运行
"""

import sys
import os
import traceback
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')

def check_mongodb_availability():
    """检查MongoDB是否可用"""
    logger.debug(f"🔍 检查MongoDB依赖...")
    
    # 检查pymongo是否安装
    try:
        import pymongo
        logger.info(f"✅ pymongo 已安装")
        pymongo_available = True
    except ImportError:
        logger.error(f"❌ pymongo 未安装")
        pymongo_available = False
    
    # 检查MongoDB服务是否运行
    mongodb_running = False
    if pymongo_available:
        try:
            from pymongo import MongoClient
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000)
            client.server_info()  # 触发连接
            logger.info(f"✅ MongoDB 服务正在运行")
            mongodb_running = True
            client.close()
        except Exception as e:
            logger.error(f"❌ MongoDB 服务未运行: {e}")
            mongodb_running = False
    
    return pymongo_available, mongodb_running

def check_redis_availability():
    """检查Redis是否可用"""
    logger.debug(f"\n🔍 检查Redis依赖...")
    
    # 检查redis是否安装
    try:
        import redis
        logger.info(f"✅ redis 已安装")
        redis_available = True
    except ImportError:
        logger.error(f"❌ redis 未安装")
        redis_available = False
    
    # 检查Redis服务是否运行
    redis_running = False
    if redis_available:
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
            r.ping()
            logger.info(f"✅ Redis 服务正在运行")
            redis_running = True
        except Exception as e:
            logger.error(f"❌ Redis 服务未运行: {e}")
            redis_running = False
    
    return redis_available, redis_running

def check_basic_dependencies():
    """检查基本依赖"""
    logger.debug(f"\n🔍 检查基本依赖...")
    
    required_packages = [
        'pandas',
        'yfinance', 
        'requests',
        'pathlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} 已安装")
        except ImportError:
            logger.error(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    return missing_packages

def create_fallback_config():
    """创建无数据库的备用配置"""
    logger.info(f"\n⚙️ 创建备用配置...")
    
    fallback_config = {
        "cache": {
            "enabled": True,
            "backend": "file",  # 使用文件缓存而不是数据库
            "file_cache_dir": "./tradingagents/dataflows/data_cache",
            "ttl_settings": {
                "us_stock_data": 7200,      # 2小时
                "china_stock_data": 3600,   # 1小时
                "us_news": 21600,           # 6小时
                "china_news": 14400,        # 4小时
                "us_fundamentals": 86400,   # 24小时
                "china_fundamentals": 43200, # 12小时
            }
        },
        "database": {
            "enabled": False,  # 禁用数据库
            "mongodb": {
                "enabled": False
            },
            "redis": {
                "enabled": False
            }
        }
    }
    
    return fallback_config

def test_cache_without_database():
    """测试不使用数据库的缓存功能"""
    logger.info(f"\n💾 测试文件缓存功能...")
    
    try:
        # 导入缓存管理器
        from tradingagents.dataflows.cache_manager import get_cache

        
        # 创建缓存实例
        cache = get_cache()
        logger.info(f"✅ 缓存实例创建成功: {type(cache).__name__}")
        
        # 测试基本功能
        test_data = "测试数据 - 无数据库模式"
        cache_key = cache.save_stock_data(
            symbol="TEST",
            data=test_data,
            start_date="2024-01-01",
            end_date="2024-12-31",
            data_source="no_db_test"
        )
        logger.info(f"✅ 数据保存成功: {cache_key}")
        
        # 加载数据
        loaded_data = cache.load_stock_data(cache_key)
        if loaded_data == test_data:
            logger.info(f"✅ 数据加载成功，文件缓存工作正常")
            return True
        else:
            logger.error(f"❌ 数据加载失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 缓存测试失败: {e}")
        traceback.print_exc()
        return False

def generate_installation_guide():
    """生成安装指南"""
    guide = """
# 依赖安装指南

## 基本运行（无数据库）
系统可以在没有MongoDB和Redis的情况下正常运行，使用文件缓存。

### 必需依赖
```bash
pip install pandas yfinance requests
```

## 完整功能（包含数据库）
如果需要企业级缓存和数据持久化功能：

### 1. 安装Python包
```bash
pip install pymongo redis
```

### 2. 安装MongoDB（可选）
#### Windows:
1. 下载MongoDB Community Server
2. 安装并启动服务
3. 默认端口：27017

#### 使用Docker:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:4.4
```

### 3. 安装Redis（可选）
#### Windows:
1. 下载Redis for Windows
2. 启动redis-server
3. 默认端口：6379

#### 使用Docker:
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

## 配置说明

### 文件缓存模式（默认）
- 缓存存储在本地文件系统
- 性能良好，适合单机使用
- 无需额外服务

### 数据库模式（可选）
- MongoDB：数据持久化
- Redis：高性能缓存
- 适合生产环境和多实例部署

## 运行模式检测
系统会自动检测可用的服务：
1. 如果MongoDB/Redis可用，自动使用数据库缓存
2. 如果不可用，自动降级到文件缓存
3. 功能完全兼容，性能略有差异
"""
    
    return guide

def main():
    """主函数"""
    logger.info(f"🔧 TradingAgents 依赖检查和配置")
    logger.info(f"=")
    
    # 检查基本依赖
    missing_packages = check_basic_dependencies()
    
    # 检查数据库依赖
    pymongo_available, mongodb_running = check_mongodb_availability()
    redis_available, redis_running = check_redis_availability()
    
    # 生成配置建议
    logger.info(f"\n📋 配置建议:")
    
    if missing_packages:
        logger.error(f"❌ 缺少必需依赖: {', '.join(missing_packages)}")
        logger.info(f"请运行: pip install ")
        return False
    
    if not pymongo_available and not redis_available:
        logger.info(f"ℹ️ 数据库依赖未安装，将使用文件缓存模式")
        logger.info(f"✅ 系统可以正常运行，性能良好")
        
    elif not mongodb_running and not redis_running:
        logger.info(f"ℹ️ 数据库服务未运行，将使用文件缓存模式")
        logger.info(f"✅ 系统可以正常运行")
        
    else:
        logger.info(f"🚀 数据库服务可用，将使用高性能缓存模式")
        if mongodb_running:
            logger.info(f"  ✅ MongoDB: 数据持久化")
        if redis_running:
            logger.info(f"  ✅ Redis: 高性能缓存")
    
    # 测试缓存功能
    cache_works = test_cache_without_database()
    
    # 生成安装指南
    guide = generate_installation_guide()
    with open("DEPENDENCY_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    logger.info(f"\n📝 已生成依赖安装指南: DEPENDENCY_GUIDE.md")
    
    # 总结
    logger.info(f"\n")
    logger.info(f"📊 检查结果总结:")
    logger.error(f"  基本依赖: {'✅ 完整' if not missing_packages else '❌ 缺失'}")
    logger.error(f"  MongoDB: {'✅ 可用' if mongodb_running else '❌ 不可用'}")
    logger.error(f"  Redis: {'✅ 可用' if redis_running else '❌ 不可用'}")
    logger.error(f"  缓存功能: {'✅ 正常' if cache_works else '❌ 异常'}")
    
    if not missing_packages and cache_works:
        logger.info(f"\n🎉 系统可以正常运行！")
        if not mongodb_running and not redis_running:
            logger.info(f"💡 提示: 安装MongoDB和Redis可以获得更好的性能")
        return True
    else:
        logger.warning(f"\n⚠️ 需要解决依赖问题才能正常运行")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
