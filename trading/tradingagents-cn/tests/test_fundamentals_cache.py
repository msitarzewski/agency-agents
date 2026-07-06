#!/usr/bin/env python3
"""
测试基本面数据缓存功能
验证OpenAI和Finnhub基本面数据的缓存机制
"""

import os
import sys
import time
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def test_cache_manager_fundamentals():
    """测试缓存管理器的基本面数据功能"""
    print("🧪 测试基本面数据缓存管理器...")
    
    try:
        from tradingagents.dataflows.cache_manager import get_cache
        
        cache = get_cache()
        print(f"✅ 缓存管理器初始化成功")
        print(f"📁 缓存目录: {cache.cache_dir}")
        
        # 测试保存基本面数据
        test_symbol = "AAPL"
        test_data = f"""
# {test_symbol} 基本面分析报告（测试数据）

**数据获取时间**: {datetime.now().strftime('%Y-%m-%d')}
**数据来源**: 测试数据

## 公司概况
- **公司名称**: Apple Inc.
- **行业**: 科技
- **市值**: 3000000 百万美元

## 关键财务指标
| 指标 | 数值 |
|------|------|
| 市盈率 (PE) | 25.50 |
| 市销率 (PS) | 7.20 |
| 净资产收益率 (ROE) | 15.30% |

## 数据说明
- 这是测试数据，用于验证缓存功能
"""
        
        # 测试保存到缓存
        print(f"\n💾 测试保存基本面数据到缓存...")
        cache_key = cache.save_fundamentals_data(test_symbol, test_data, data_source="test")
        print(f"✅ 数据已保存，缓存键: {cache_key}")
        
        # 测试从缓存加载
        print(f"\n📖 测试从缓存加载基本面数据...")
        loaded_data = cache.load_fundamentals_data(cache_key)
        if loaded_data:
            print(f"✅ 数据加载成功，长度: {len(loaded_data)}")
            print(f"📄 数据预览: {loaded_data[:200]}...")
        else:
            print(f"❌ 数据加载失败")
        
        # 测试查找缓存
        print(f"\n🔍 测试查找基本面缓存数据...")
        found_key = cache.find_cached_fundamentals_data(test_symbol, data_source="test")
        if found_key:
            print(f"✅ 找到缓存数据，缓存键: {found_key}")
        else:
            print(f"❌ 未找到缓存数据")
        
        # 测试缓存统计
        print(f"\n📊 测试缓存统计...")
        stats = cache.get_cache_stats()
        print(f"缓存统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_fundamentals_with_cache():
    """测试基本面数据获取函数的缓存功能"""
    print(f"\n🧪 测试基本面数据获取函数的缓存功能...")
    
    try:
        from tradingagents.dataflows.interface import get_fundamentals_openai, get_fundamentals_finnhub
        
        test_symbol = "MSFT"
        curr_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n📊 第一次获取 {test_symbol} 基本面数据（应该从API获取）...")
        start_time = time.time()
        result1 = get_fundamentals_finnhub(test_symbol, curr_date)
        first_time = time.time() - start_time
        print(f"⏱️ 第一次获取耗时: {first_time:.2f}秒")
        print(f"📄 数据长度: {len(result1)}")
        
        print(f"\n📊 第二次获取 {test_symbol} 基本面数据（应该从缓存获取）...")
        start_time = time.time()
        result2 = get_fundamentals_finnhub(test_symbol, curr_date)
        second_time = time.time() - start_time
        print(f"⏱️ 第二次获取耗时: {second_time:.2f}秒")
        print(f"📄 数据长度: {len(result2)}")
        
        # 验证缓存效果
        if second_time < first_time:
            print(f"✅ 缓存生效！第二次获取速度提升了 {((first_time - second_time) / first_time * 100):.1f}%")
        else:
            print(f"⚠️ 缓存可能未生效，或者数据来源有变化")
        
        # 验证数据一致性
        if result1 == result2:
            print(f"✅ 两次获取的数据完全一致")
        else:
            print(f"⚠️ 两次获取的数据不一致，可能是缓存问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本面数据缓存测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_ttl():
    """测试缓存TTL（生存时间）功能"""
    print(f"\n🧪 测试缓存TTL功能...")
    
    try:
        from tradingagents.dataflows.cache_manager import get_cache
        
        cache = get_cache()
        
        # 检查缓存配置
        print(f"📋 缓存配置:")
        for cache_type, config in cache.cache_config.items():
            if 'fundamentals' in cache_type:
                print(f"  - {cache_type}: TTL={config['ttl_hours']}小时, 描述={config['description']}")
        
        # 测试美股和A股的不同TTL设置
        us_symbol = "GOOGL"
        china_symbol = "000001"  # 平安银行
        
        print(f"\n🇺🇸 测试美股基本面缓存 ({us_symbol})...")
        us_key = cache.find_cached_fundamentals_data(us_symbol, data_source="test")
        if us_key:
            print(f"找到美股缓存: {us_key}")
        else:
            print(f"未找到美股缓存")
        
        print(f"\n🇨🇳 测试A股基本面缓存 ({china_symbol})...")
        china_key = cache.find_cached_fundamentals_data(china_symbol, data_source="test")
        if china_key:
            print(f"找到A股缓存: {china_key}")
        else:
            print(f"未找到A股缓存")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存TTL测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始基本面数据缓存功能测试")
    print("=" * 50)
    
    # 检查环境
    print(f"📍 当前工作目录: {os.getcwd()}")
    print(f"📍 Python路径: {sys.path[0]}")
    
    # 运行测试
    tests = [
        ("缓存管理器基本功能", test_cache_manager_fundamentals),
        ("基本面数据缓存功能", test_fundamentals_with_cache),
        ("缓存TTL功能", test_cache_ttl),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 执行失败: {str(e)}")
            results.append((test_name, False))
    
    # 输出测试结果
    print(f"\n{'='*20} 测试结果汇总 {'='*20}")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n📊 测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！基本面数据缓存功能正常工作。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    main()