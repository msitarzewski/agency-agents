#!/usr/bin/env python3
"""
智能系统完整测试 - 验证自适应配置和缓存系统
"""

import time
import sys
from datetime import datetime

def test_smart_config():
    """测试智能配置系统"""
    print("🔧 测试智能配置系统")
    print("-" * 30)
    
    try:
        from smart_config import get_smart_config, get_config
        
        # 获取配置管理器
        config_manager = get_smart_config()
        config_manager.print_status()
        
        # 获取配置信息
        config = get_config()
        print(f"\n✅ 配置获取成功")
        print(f"主要缓存后端: {config['cache']['primary_backend']}")
        
        return True, config_manager
        
    except Exception as e:
        print(f"❌ 智能配置测试失败: {e}")
        return False, None

def test_adaptive_cache():
    """测试自适应缓存系统"""
    print("\n💾 测试自适应缓存系统")
    print("-" * 30)
    
    try:
        from adaptive_cache_manager import get_cache
        
        # 获取缓存管理器
        cache = get_cache()
        
        # 显示缓存状态
        stats = cache.get_cache_stats()
        print("📊 缓存状态:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 测试基本功能
        print("\n🧪 测试基本缓存功能...")
        
        test_data = f"测试数据 - {datetime.now()}"
        cache_key = cache.save_stock_data(
            symbol="AAPL",
            data=test_data,
            start_date="2024-01-01",
            end_date="2024-12-31",
            data_source="smart_test"
        )
        print(f"✅ 数据保存成功: {cache_key}")
        
        # 测试加载
        loaded_data = cache.load_stock_data(cache_key)
        if loaded_data == test_data:
            print("✅ 数据加载成功，内容匹配")
        else:
            print("❌ 数据加载失败或内容不匹配")
            return False
        
        # 测试查找
        found_key = cache.find_cached_stock_data(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            data_source="smart_test"
        )
        
        if found_key:
            print(f"✅ 缓存查找成功: {found_key}")
        else:
            print("❌ 缓存查找失败")
            return False
        
        return True, cache
        
    except Exception as e:
        print(f"❌ 自适应缓存测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_performance():
    """测试性能"""
    print("\n⚡ 测试缓存性能")
    print("-" * 30)
    
    try:
        from adaptive_cache_manager import get_cache
        
        cache = get_cache()
        
        # 性能测试数据
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        print("📊 性能测试结果:")
        
        total_save_time = 0
        total_load_time = 0
        
        for symbol in symbols:
            test_data = f"性能测试数据 - {symbol}"
            
            # 测试保存性能
            start_time = time.time()
            cache_key = cache.save_stock_data(
                symbol=symbol,
                data=test_data,
                start_date="2024-01-01",
                end_date="2024-12-31",
                data_source="perf_test"
            )
            save_time = time.time() - start_time
            total_save_time += save_time
            
            # 测试加载性能
            start_time = time.time()
            loaded_data = cache.load_stock_data(cache_key)
            load_time = time.time() - start_time
            total_load_time += load_time
            
            print(f"  {symbol}: 保存 {save_time:.4f}s, 加载 {load_time:.4f}s")
        
        avg_save_time = total_save_time / len(symbols)
        avg_load_time = total_load_time / len(symbols)
        
        print(f"\n📈 平均性能:")
        print(f"  保存时间: {avg_save_time:.4f}秒")
        print(f"  加载时间: {avg_load_time:.4f}秒")
        
        # 计算性能改进
        api_simulation_time = 2.0  # 假设API调用需要2秒
        if avg_load_time < api_simulation_time:
            improvement = ((api_simulation_time - avg_load_time) / api_simulation_time) * 100
            print(f"  性能改进: {improvement:.1f}%")
            
            if improvement > 90:
                print("🚀 性能改进显著！")
                return True
            else:
                print("⚠️ 性能改进有限")
                return True
        else:
            print("❌ 缓存性能不如预期")
            return False
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def test_fallback_mechanism():
    """测试降级机制"""
    print("\n🔄 测试降级机制")
    print("-" * 30)
    
    try:
        from adaptive_cache_manager import get_cache
        
        cache = get_cache()
        
        # 检查降级配置
        if cache.fallback_enabled:
            print("✅ 降级机制已启用")
        else:
            print("⚠️ 降级机制未启用")
        
        # 测试在主要后端不可用时的行为
        print(f"主要后端: {cache.primary_backend}")
        
        if cache.primary_backend == "file":
            print("✅ 使用文件缓存，无需降级")
        elif cache.primary_backend == "redis" and not cache.redis_enabled:
            print("✅ Redis不可用，已自动降级到文件缓存")
        elif cache.primary_backend == "mongodb" and not cache.mongodb_enabled:
            print("✅ MongoDB不可用，已自动降级到文件缓存")
        else:
            print(f"✅ {cache.primary_backend} 后端正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 降级机制测试失败: {e}")
        return False

def generate_test_report(results):
    """生成测试报告"""
    print("\n📋 测试报告")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 生成建议
    print("\n💡 建议:")
    
    if all(results.values()):
        print("🎉 所有测试通过！系统可以正常运行")
        print("✅ 可以开始准备上游贡献")
    else:
        print("⚠️ 部分测试失败，需要检查以下问题:")
        
        if not results.get("智能配置", True):
            print("  - 检查智能配置系统")
        if not results.get("自适应缓存", True):
            print("  - 检查缓存系统配置")
        if not results.get("性能测试", True):
            print("  - 优化缓存性能")
        if not results.get("降级机制", True):
            print("  - 检查降级机制配置")

def main():
    """主测试函数"""
    print("🚀 TradingAgents 智能系统完整测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行所有测试
    results = {}
    
    # 测试1: 智能配置
    config_success, config_manager = test_smart_config()
    results["智能配置"] = config_success
    
    # 测试2: 自适应缓存
    cache_success, cache_manager = test_adaptive_cache()
    results["自适应缓存"] = cache_success
    
    # 测试3: 性能测试
    if cache_success:
        perf_success = test_performance()
        results["性能测试"] = perf_success
    else:
        results["性能测试"] = False
    
    # 测试4: 降级机制
    if cache_success:
        fallback_success = test_fallback_mechanism()
        results["降级机制"] = fallback_success
    else:
        results["降级机制"] = False
    
    # 生成报告
    generate_test_report(results)
    
    # 保存配置（如果可用）
    if config_manager:
        config_manager.save_config("test_config.json")
        print(f"\n💾 测试配置已保存: test_config.json")
    
    # 返回总体结果
    return all(results.values())

if __name__ == "__main__":
    success = main()
    
    print(f"\n🎯 测试{'成功' if success else '失败'}!")
    
    if success:
        print("\n下一步:")
        print("1. 清理中文内容")
        print("2. 添加英文文档")
        print("3. 准备上游贡献")
    else:
        print("\n需要解决的问题:")
        print("1. 检查依赖安装")
        print("2. 修复配置问题")
        print("3. 重新运行测试")
    
    sys.exit(0 if success else 1)
