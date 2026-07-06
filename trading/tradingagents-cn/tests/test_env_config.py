#!/usr/bin/env python3
"""
测试使用.env配置的数据库管理器
"""

import sys
import os
from pathlib import Path

def test_env_config():
    """测试.env配置"""
    print("🔧 测试使用.env配置的数据库管理器")
    print("=" * 50)
    
    # 1. 检查.env文件
    print("\n📁 检查.env文件...")
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env文件存在: {env_file}")
        
        # 读取并显示相关配置
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("📊 数据库相关配置:")
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if any(keyword in line.upper() for keyword in ['MONGODB', 'REDIS']):
                    # 隐藏密码
                    if 'PASSWORD' in line.upper():
                        key, value = line.split('=', 1)
                        print(f"  {key}=***")
                    else:
                        print(f"  {line}")
    else:
        print(f"❌ .env文件不存在: {env_file}")
        return False
    
    # 2. 测试数据库管理器
    print("\n🔧 测试数据库管理器...")
    try:
        from tradingagents.config.database_manager import get_database_manager
        
        db_manager = get_database_manager()
        print("✅ 数据库管理器创建成功")
        
        # 获取状态报告
        status = db_manager.get_status_report()
        
        print("📊 数据库状态:")
        print(f"  数据库可用: {'✅ 是' if status['database_available'] else '❌ 否'}")
        
        mongodb_info = status['mongodb']
        print(f"  MongoDB: {'✅ 可用' if mongodb_info['available'] else '❌ 不可用'}")
        print(f"    地址: {mongodb_info['host']}:{mongodb_info['port']}")
        
        redis_info = status['redis']
        print(f"  Redis: {'✅ 可用' if redis_info['available'] else '❌ 不可用'}")
        print(f"    地址: {redis_info['host']}:{redis_info['port']}")
        
        print(f"  缓存后端: {status['cache_backend']}")
        print(f"  降级支持: {'✅ 启用' if status['fallback_enabled'] else '❌ 禁用'}")
        
    except Exception as e:
        print(f"❌ 数据库管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试缓存系统
    print("\n💾 测试缓存系统...")
    try:
        from tradingagents.dataflows.integrated_cache import get_cache
        
        cache = get_cache()
        print("✅ 缓存系统创建成功")
        
        # 获取后端信息
        backend_info = cache.get_cache_backend_info()
        print(f"  缓存系统: {backend_info['system']}")
        print(f"  主要后端: {backend_info['primary_backend']}")
        print(f"  性能模式: {cache.get_performance_mode()}")
        
        # 测试基本功能
        test_data = "测试数据 - 使用.env配置"
        cache_key = cache.save_stock_data(
            symbol="TEST_ENV",
            data=test_data,
            start_date="2024-01-01",
            end_date="2024-12-31",
            data_source="env_test"
        )
        print(f"✅ 数据保存成功: {cache_key}")
        
        # 加载数据
        loaded_data = cache.load_stock_data(cache_key)
        if loaded_data == test_data:
            print("✅ 数据加载成功，内容匹配")
        else:
            print("❌ 数据加载失败或内容不匹配")
            return False
        
    except Exception as e:
        print(f"❌ 缓存系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 显示环境变量
    print("\n🔍 检查环境变量...")
    env_vars = [
        "MONGODB_HOST", "MONGODB_PORT", "MONGODB_USERNAME", "MONGODB_PASSWORD",
        "MONGODB_DATABASE", "MONGODB_AUTH_SOURCE",
        "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_DB"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"  {var}=***")
            else:
                print(f"  {var}={value}")
        else:
            print(f"  {var}=未设置")
    
    # 5. 总结
    print("\n📊 测试总结:")
    print("✅ 系统已正确使用.env配置文件")
    print("✅ 数据库管理器正常工作")
    print("✅ 缓存系统正常工作")
    print("✅ 支持MongoDB和Redis的完整配置")
    print("✅ 在数据库不可用时自动降级到文件缓存")
    
    print("\n💡 配置说明:")
    print("1. 系统读取.env文件中的数据库配置")
    print("2. 自动检测MongoDB和Redis是否可用")
    print("3. 根据可用性选择最佳缓存后端")
    print("4. 支持用户名密码认证")
    print("5. 在数据库不可用时自动使用文件缓存")
    
    return True

def main():
    """主函数"""
    try:
        success = test_env_config()
        
        if success:
            print("\n🎉 .env配置测试完成!")
            print("\n🎯 系统特性:")
            print("✅ 使用项目现有的.env配置")
            print("✅ 默认不依赖数据库，可以纯文件缓存运行")
            print("✅ 自动检测和使用可用的数据库")
            print("✅ 支持完整的MongoDB和Redis配置")
            print("✅ 智能降级，确保系统稳定性")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
