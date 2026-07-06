#!/usr/bin/env python3
"""
简化版数据源测试程序
快速测试主要数据源的可用性
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_china_data_source():
    """测试中国股票数据源"""
    print("🇨🇳 测试中国股票数据源")
    print("-" * 40)
    
    try:
        # 测试数据源管理器
        from tradingagents.dataflows.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        print(f"✅ 数据源管理器初始化成功")
        print(f"   当前数据源: {manager.current_source.value}")
        print(f"   可用数据源: {[s.value for s in manager.available_sources]}")
        
        # 测试获取数据
        print(f"\n📊 测试获取平安银行(000001)数据...")
        start_time = time.time()
        result = manager.get_stock_data("000001", "2025-07-01", "2025-07-12")
        end_time = time.time()
        
        if result and "❌" not in result:
            print(f"✅ 数据获取成功 ({end_time - start_time:.2f}s)")
            print(f"   数据长度: {len(result)} 字符")
            print(f"   数据预览: {result[:100]}...")
            return True
        else:
            print(f"❌ 数据获取失败: {result[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ 中国股票数据源测试失败: {e}")
        return False

def test_us_data_source():
    """测试美股数据源"""
    print("\n🇺🇸 测试美股数据源")
    print("-" * 40)
    
    try:
        # 测试优化版本
        from tradingagents.dataflows.optimized_us_data import get_us_stock_data_cached
        
        print(f"📊 测试获取苹果(AAPL)数据...")
        start_time = time.time()
        result = get_us_stock_data_cached("AAPL", "2025-07-01", "2025-07-12", force_refresh=True)
        end_time = time.time()
        
        if result and "❌" not in result:
            print(f"✅ 数据获取成功 ({end_time - start_time:.2f}s)")
            print(f"   数据长度: {len(result)} 字符")
            
            # 检查数据源
            if "FINNHUB" in result.upper() or "finnhub" in result:
                print(f"   🎯 使用了FinnHub数据源")
            elif "Yahoo Finance" in result or "yfinance" in result:
                print(f"   ⚠️ 使用了Yahoo Finance备用数据源")
            
            print(f"   数据预览: {result[:100]}...")
            return True
        else:
            print(f"❌ 数据获取失败: {result[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ 美股数据源测试失败: {e}")
        return False

def test_cache_system():
    """测试缓存系统"""
    print("\n🗄️ 测试缓存系统")
    print("-" * 40)
    
    try:
        from tradingagents.dataflows.cache_manager import get_cache
        
        cache = get_cache()
        print(f"✅ 缓存管理器初始化成功")
        print(f"   缓存类型: {type(cache).__name__}")
        
        # 测试缓存操作
        test_data = f"测试数据_{datetime.now().strftime('%H%M%S')}"
        
        # 保存测试数据
        cache_key = cache.save_stock_data(
            symbol="TEST001",
            data=test_data,
            start_date="2025-07-01",
            end_date="2025-07-12",
            data_source="test"
        )
        
        # 加载测试数据
        loaded_data = cache.load_stock_data(cache_key)
        
        if loaded_data == test_data:
            print(f"✅ 缓存读写测试成功")
            print(f"   缓存键: {cache_key}")
            return True
        else:
            print(f"❌ 缓存数据不匹配")
            return False
            
    except Exception as e:
        print(f"❌ 缓存系统测试失败: {e}")
        return False

def test_api_keys():
    """测试API密钥配置"""
    print("\n🔑 测试API密钥配置")
    print("-" * 40)
    
    api_keys = {
        'TUSHARE_TOKEN': os.getenv('TUSHARE_TOKEN'),
        'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
        'DASHSCOPE_API_KEY': os.getenv('DASHSCOPE_API_KEY'),
        'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY'),
    }
    
    configured_count = 0
    total_count = len(api_keys)
    
    for key_name, key_value in api_keys.items():
        if key_value:
            print(f"✅ {key_name}: 已配置")
            configured_count += 1
        else:
            print(f"❌ {key_name}: 未配置")
    
    print(f"\n📊 API密钥配置率: {configured_count}/{total_count} ({configured_count/total_count*100:.1f}%)")
    
    return configured_count >= 2  # 至少需要2个API密钥

def main():
    """主测试函数"""
    print("🧪 数据源简化测试程序")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 测试API密钥配置
    api_result = test_api_keys()
    results.append(('API密钥配置', api_result))
    
    # 2. 测试缓存系统
    cache_result = test_cache_system()
    results.append(('缓存系统', cache_result))
    
    # 3. 测试中国股票数据源
    china_result = test_china_data_source()
    results.append(('中国股票数据源', china_result))
    
    # 4. 测试美股数据源
    us_result = test_us_data_source()
    results.append(('美股数据源', us_result))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 测试结果汇总")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 总体结果:")
    print(f"   通过: {passed}/{total}")
    print(f"   成功率: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print(f"\n🎉 数据源系统运行良好！")
        print(f"✅ 主要功能正常")
        print(f"✅ 可以开始使用系统")
    else:
        print(f"\n⚠️ 数据源系统需要优化")
        print(f"❌ 请检查失败的组件")
        print(f"❌ 参考错误信息进行修复")
    
    print(f"\n💡 建议:")
    if not api_result:
        print("- 配置更多API密钥以提高数据源可用性")
    if not cache_result:
        print("- 检查缓存系统配置和权限")
    if not china_result:
        print("- 检查Tushare Token或AKShare安装")
    if not us_result:
        print("- 检查FinnHub API Key或网络连接")
    
    return success_rate >= 75

if __name__ == "__main__":
    try:
        success = main()
        
        print(f"\n{'='*50}")
        if success:
            print("🎯 测试完成！可以运行完整分析流程。")
            print("   下一步: python -m cli.main")
        else:
            print("🔧 需要修复配置后再次测试。")
            print("   重新测试: python tests/test_data_sources_simple.py")
            
    except Exception as e:
        print(f"❌ 测试程序异常: {e}")
        import traceback
        traceback.print_exc()
