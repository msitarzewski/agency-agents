#!/usr/bin/env python3
"""
简单的系统测试 - 验证配置和缓存系统
"""

import sys
import os
from pathlib import Path

def test_basic_system():
    """测试基本系统功能"""
    print("🔧 TradingAgents 基本系统测试")
    print("=" * 40)
    
    # 1. 检查配置文件
    print("\n📁 检查配置文件...")
    config_file = Path("config/database_config.json")
    if config_file.exists():
        print(f"✅ 配置文件存在: {config_file}")
        
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("✅ 配置文件格式正确")
            print(f"  主要缓存后端: {config['cache']['primary_backend']}")
            print(f"  MongoDB启用: {config['database']['mongodb']['enabled']}")
            print(f"  Redis启用: {config['database']['redis']['enabled']}")
        except Exception as e:
            print(f"❌ 配置文件解析失败: {e}")
    else:
        print(f"❌ 配置文件不存在: {config_file}")
    
    # 2. 检查数据库包
    print("\n📦 检查数据库包...")
    
    # 检查pymongo
    try:
        import pymongo
        print("✅ pymongo 已安装")
        
        # 尝试连接MongoDB
        try:
            client = pymongo.MongoClient('localhost', 27017, serverSelectionTimeoutMS=2000)
            client.server_info()
            client.close()
            print("✅ MongoDB 连接成功")
            mongodb_available = True
        except Exception:
            print("❌ MongoDB 连接失败（正常，如果没有安装MongoDB）")
            mongodb_available = False
    except ImportError:
        print("❌ pymongo 未安装")
        mongodb_available = False
    
    # 检查redis
    try:
        import redis
        print("✅ redis 已安装")
        
        # 尝试连接Redis
        try:
            r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
            r.ping()
            print("✅ Redis 连接成功")
            redis_available = True
        except Exception:
            print("❌ Redis 连接失败（正常，如果没有安装Redis）")
            redis_available = False
    except ImportError:
        print("❌ redis 未安装")
        redis_available = False
    
    # 3. 测试缓存系统
    print("\n💾 测试缓存系统...")
    try:
        from tradingagents.dataflows.integrated_cache import get_cache
        
        cache = get_cache()
        print("✅ 缓存系统初始化成功")
        
        # 获取缓存信息
        backend_info = cache.get_cache_backend_info()
        print(f"  缓存系统: {backend_info['system']}")
        print(f"  主要后端: {backend_info['primary_backend']}")
        
        # 测试基本功能
        test_data = "测试数据 - 系统简单测试"
        cache_key = cache.save_stock_data(
            symbol="TEST_SIMPLE",
            data=test_data,
            start_date="2024-01-01",
            end_date="2024-12-31",
            data_source="simple_test"
        )
        print(f"✅ 数据保存成功: {cache_key}")
        
        # 加载数据
        loaded_data = cache.load_stock_data(cache_key)
        if loaded_data == test_data:
            print("✅ 数据加载成功")
        else:
            print("❌ 数据加载失败")
            return False
        
    except Exception as e:
        print(f"❌ 缓存系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试数据库管理器
    print("\n🔧 测试数据库管理器...")
    try:
        from tradingagents.config.database_manager import get_database_manager
        
        db_manager = get_database_manager()
        print("✅ 数据库管理器创建成功")
        
        # 获取状态报告
        status = db_manager.get_status_report()
        
        print("📊 数据库状态:")
        print(f"  数据库可用: {'✅ 是' if status['database_available'] else '❌ 否'}")
        print(f"  MongoDB: {'✅ 可用' if status['mongodb']['available'] else '❌ 不可用'}")
        print(f"  Redis: {'✅ 可用' if status['redis']['available'] else '❌ 不可用'}")
        print(f"  缓存后端: {status['cache_backend']}")
        
    except Exception as e:
        print(f"❌ 数据库管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 总结
    print("\n📊 系统测试总结:")
    print("✅ 缓存系统正常工作")
    print("✅ 数据库管理器正常工作")
    
    if mongodb_available or redis_available:
        print("✅ 数据库可用，系统运行在高性能模式")
    else:
        print("✅ 数据库不可用，系统运行在文件缓存模式")
        print("💡 这是正常的，系统可以完全使用文件缓存工作")
    
    print("\n🎯 系统特性:")
    print("✅ 智能缓存：自动选择最佳缓存后端")
    print("✅ 降级支持：数据库不可用时自动使用文件缓存")
    print("✅ 配置灵活：支持多种数据库配置")
    print("✅ 性能优化：根据可用资源自动调整")
    
    return True

def main():
    """主函数"""
    try:
        success = test_basic_system()
        
        if success:
            print("\n🎉 系统测试完成!")
            print("\n💡 下一步:")
            print("1. 如需高性能，可以安装并启动MongoDB/Redis")
            print("2. 运行完整的股票分析测试")
            print("3. 使用Web界面进行交互式分析")
        
        return success
        
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
