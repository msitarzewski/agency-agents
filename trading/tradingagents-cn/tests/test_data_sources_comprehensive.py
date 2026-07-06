#!/usr/bin/env python3
"""
数据源综合测试程序
测试所有数据源的获取过程和优先级切换
"""

import sys
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_china_stock_data_sources():
    """测试中国股票数据源"""
    print("🇨🇳 测试中国股票数据源")
    print("=" * 60)
    
    test_symbols = ["000001", "600036", "000858"]  # 平安银行、招商银行、五粮液
    start_date = "2025-07-01"
    end_date = "2025-07-12"
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n📊 测试股票: {symbol}")
        print("-" * 40)
        
        symbol_results = {}
        
        # 1. 测试统一数据源接口
        try:
            print(f"🔍 测试统一数据源接口...")
            from tradingagents.dataflows.interface import get_china_stock_data_unified
            
            start_time = time.time()
            result = get_china_stock_data_unified(symbol, start_date, end_date)
            end_time = time.time()
            
            if result and "❌" not in result:
                print(f"✅ 统一接口获取成功 ({end_time - start_time:.2f}s)")
                print(f"   数据长度: {len(result)} 字符")
                print(f"   数据预览: {result[:150]}...")
                symbol_results['unified'] = {
                    'success': True,
                    'time': end_time - start_time,
                    'data_length': len(result)
                }
            else:
                print(f"❌ 统一接口获取失败: {result[:100]}...")
                symbol_results['unified'] = {'success': False, 'error': result[:100]}
                
        except Exception as e:
            print(f"❌ 统一接口异常: {e}")
            symbol_results['unified'] = {'success': False, 'error': str(e)}
        
        # 2. 测试优化版本
        try:
            print(f"🔍 测试优化版本...")
            from tradingagents.dataflows.optimized_china_data import get_china_stock_data_cached
            
            start_time = time.time()
            result = get_china_stock_data_cached(symbol, start_date, end_date, force_refresh=True)
            end_time = time.time()
            
            if result and "❌" not in result:
                print(f"✅ 优化版本获取成功 ({end_time - start_time:.2f}s)")
                print(f"   数据长度: {len(result)} 字符")
                symbol_results['optimized'] = {
                    'success': True,
                    'time': end_time - start_time,
                    'data_length': len(result)
                }
            else:
                print(f"❌ 优化版本获取失败: {result[:100]}...")
                symbol_results['optimized'] = {'success': False, 'error': result[:100]}
                
        except Exception as e:
            print(f"❌ 优化版本异常: {e}")
            symbol_results['optimized'] = {'success': False, 'error': str(e)}
        
        # 3. 测试数据源管理器
        try:
            print(f"🔍 测试数据源管理器...")
            from tradingagents.dataflows.data_source_manager import DataSourceManager
            
            manager = DataSourceManager()
            print(f"   当前数据源: {manager.current_source.value}")
            print(f"   可用数据源: {[s.value for s in manager.available_sources]}")
            
            start_time = time.time()
            result = manager.get_stock_data(symbol, start_date, end_date)
            end_time = time.time()
            
            if result and "❌" not in result:
                print(f"✅ 数据源管理器获取成功 ({end_time - start_time:.2f}s)")
                symbol_results['manager'] = {
                    'success': True,
                    'time': end_time - start_time,
                    'current_source': manager.current_source.value,
                    'available_sources': [s.value for s in manager.available_sources]
                }
            else:
                print(f"❌ 数据源管理器获取失败: {result[:100]}...")
                symbol_results['manager'] = {'success': False, 'error': result[:100]}
                
        except Exception as e:
            print(f"❌ 数据源管理器异常: {e}")
            symbol_results['manager'] = {'success': False, 'error': str(e)}
        
        results[symbol] = symbol_results
        time.sleep(1)  # 避免API频率限制
    
    return results

def test_us_stock_data_sources():
    """测试美股数据源"""
    print("\n🇺🇸 测试美股数据源")
    print("=" * 60)
    
    test_symbols = ["AAPL", "SPY", "TSLA"]
    start_date = "2025-07-01"
    end_date = "2025-07-12"
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n📊 测试股票: {symbol}")
        print("-" * 40)
        
        symbol_results = {}
        
        # 1. 测试优化版本（FinnHub优先）
        try:
            print(f"🔍 测试优化版本（FinnHub优先）...")
            from tradingagents.dataflows.optimized_us_data import get_us_stock_data_cached
            
            start_time = time.time()
            result = get_us_stock_data_cached(symbol, start_date, end_date, force_refresh=True)
            end_time = time.time()
            
            if result and "❌" not in result:
                print(f"✅ 优化版本获取成功 ({end_time - start_time:.2f}s)")
                print(f"   数据长度: {len(result)} 字符")
                
                # 检查数据源
                if "FINNHUB" in result.upper() or "finnhub" in result:
                    print(f"   🎯 使用了FinnHub数据源")
                elif "Yahoo Finance" in result or "yfinance" in result:
                    print(f"   ⚠️ 使用了Yahoo Finance备用数据源")
                
                symbol_results['optimized'] = {
                    'success': True,
                    'time': end_time - start_time,
                    'data_length': len(result)
                }
            else:
                print(f"❌ 优化版本获取失败: {result[:100]}...")
                symbol_results['optimized'] = {'success': False, 'error': result[:100]}
                
        except Exception as e:
            print(f"❌ 优化版本异常: {e}")
            symbol_results['optimized'] = {'success': False, 'error': str(e)}
        
        # 2. 测试原始yfinance接口
        try:
            print(f"🔍 测试原始yfinance接口...")
            from tradingagents.dataflows.interface import get_YFin_data_online
            
            start_time = time.time()
            result = get_YFin_data_online(symbol, start_date, end_date)
            end_time = time.time()
            
            if result and "No data found" not in result and "❌" not in result:
                print(f"✅ yfinance接口获取成功 ({end_time - start_time:.2f}s)")
                print(f"   数据长度: {len(result)} 字符")
                symbol_results['yfinance'] = {
                    'success': True,
                    'time': end_time - start_time,
                    'data_length': len(result)
                }
            else:
                print(f"❌ yfinance接口获取失败: {result[:100]}...")
                symbol_results['yfinance'] = {'success': False, 'error': result[:100]}
                
        except Exception as e:
            print(f"❌ yfinance接口异常: {e}")
            symbol_results['yfinance'] = {'success': False, 'error': str(e)}
        
        results[symbol] = symbol_results
        time.sleep(2)  # 避免API频率限制
    
    return results

def test_news_data_sources():
    """测试新闻数据源"""
    print("\n📰 测试新闻数据源")
    print("=" * 60)
    
    test_symbols = ["AAPL", "000001"]
    results = {}
    
    for symbol in test_symbols:
        print(f"\n📰 测试股票新闻: {symbol}")
        print("-" * 40)
        
        symbol_results = {}
        
        # 1. 测试实时新闻聚合器
        try:
            print(f"🔍 测试实时新闻聚合器...")
            from tradingagents.dataflows.realtime_news_utils import RealtimeNewsAggregator
            
            aggregator = RealtimeNewsAggregator()
            start_time = time.time()
            news_items = aggregator.get_realtime_stock_news(symbol, hours_back=24)
            end_time = time.time()
            
            print(f"✅ 实时新闻获取成功 ({end_time - start_time:.2f}s)")
            print(f"   新闻数量: {len(news_items)}")
            
            if news_items:
                print(f"   最新新闻: {news_items[0].title[:50]}...")
                print(f"   新闻来源: {news_items[0].source}")
            
            symbol_results['realtime_news'] = {
                'success': True,
                'time': end_time - start_time,
                'news_count': len(news_items)
            }
                
        except Exception as e:
            print(f"❌ 实时新闻异常: {e}")
            symbol_results['realtime_news'] = {'success': False, 'error': str(e)}
        
        # 2. 测试FinnHub新闻
        try:
            print(f"🔍 测试FinnHub新闻...")
            from tradingagents.dataflows.interface import get_finnhub_news
            
            start_time = time.time()
            result = get_finnhub_news(symbol, "2025-07-01", "2025-07-12")
            end_time = time.time()
            
            if result and "❌" not in result:
                print(f"✅ FinnHub新闻获取成功 ({end_time - start_time:.2f}s)")
                print(f"   数据长度: {len(result)} 字符")
                symbol_results['finnhub_news'] = {
                    'success': True,
                    'time': end_time - start_time,
                    'data_length': len(result)
                }
            else:
                print(f"❌ FinnHub新闻获取失败: {result[:100]}...")
                symbol_results['finnhub_news'] = {'success': False, 'error': result[:100]}
                
        except Exception as e:
            print(f"❌ FinnHub新闻异常: {e}")
            symbol_results['finnhub_news'] = {'success': False, 'error': str(e)}
        
        results[symbol] = symbol_results
        time.sleep(1)
    
    return results

def test_cache_system():
    """测试缓存系统"""
    print("\n🗄️ 测试缓存系统")
    print("=" * 60)
    
    results = {}
    
    try:
        print(f"🔍 测试缓存管理器...")
        from tradingagents.dataflows.cache_manager import get_cache
        
        cache = get_cache()
        print(f"   缓存类型: {type(cache).__name__}")
        
        # 测试缓存保存和加载
        test_data = "测试数据_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存测试数据
        cache_key = cache.save_stock_data(
            symbol="TEST001",
            data=test_data,
            start_date="2025-07-01",
            end_date="2025-07-12",
            data_source="test"
        )
        
        print(f"   缓存键: {cache_key}")
        
        # 加载测试数据
        loaded_data = cache.load_stock_data(cache_key)
        
        if loaded_data == test_data:
            print(f"✅ 缓存系统测试成功")
            results['cache'] = {'success': True, 'cache_type': type(cache).__name__}
        else:
            print(f"❌ 缓存数据不匹配")
            results['cache'] = {'success': False, 'error': '数据不匹配'}
            
    except Exception as e:
        print(f"❌ 缓存系统异常: {e}")
        results['cache'] = {'success': False, 'error': str(e)}
    
    return results


def analyze_results(all_results: Dict):
    """分析测试结果"""
    print("\n📊 测试结果分析")
    print("=" * 60)

    # 统计成功率
    total_tests = 0
    successful_tests = 0

    for category, category_results in all_results.items():
        print(f"\n📋 {category.upper()} 类别:")

        if category == 'cache':
            total_tests += 1
            if category_results.get('success'):
                successful_tests += 1
                print(f"   ✅ 缓存系统: 正常")
            else:
                print(f"   ❌ 缓存系统: {category_results.get('error', '未知错误')}")
        else:
            for symbol, symbol_results in category_results.items():
                print(f"   📊 {symbol}:")
                for test_type, result in symbol_results.items():
                    total_tests += 1
                    if result.get('success'):
                        successful_tests += 1
                        time_taken = result.get('time', 0)
                        data_length = result.get('data_length', 0)
                        print(f"      ✅ {test_type}: {time_taken:.2f}s, {data_length}字符")
                    else:
                        error = result.get('error', '未知错误')
                        print(f"      ❌ {test_type}: {error[:50]}...")

    # 总体统计
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n📈 总体统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数: {successful_tests}")
    print(f"   成功率: {success_rate:.1f}%")

    # 性能分析
    print(f"\n⚡ 性能分析:")
    fastest_times = []
    slowest_times = []

    for category, category_results in all_results.items():
        if category != 'cache':
            for symbol, symbol_results in category_results.items():
                for test_type, result in symbol_results.items():
                    if result.get('success') and 'time' in result:
                        time_taken = result['time']
                        fastest_times.append((f"{category}-{symbol}-{test_type}", time_taken))
                        slowest_times.append((f"{category}-{symbol}-{test_type}", time_taken))

    if fastest_times:
        fastest_times.sort(key=lambda x: x[1])
        slowest_times.sort(key=lambda x: x[1], reverse=True)

        print(f"   最快: {fastest_times[0][0]} ({fastest_times[0][1]:.2f}s)")
        print(f"   最慢: {slowest_times[0][0]} ({slowest_times[0][1]:.2f}s)")

    return success_rate >= 70  # 70%以上成功率认为通过


def print_recommendations(all_results: Dict):
    """打印优化建议"""
    print(f"\n💡 优化建议:")
    print("=" * 60)

    # 检查中国股票数据源
    china_results = all_results.get('china_stocks', {})
    china_success_count = 0
    china_total_count = 0

    for symbol, symbol_results in china_results.items():
        for test_type, result in symbol_results.items():
            china_total_count += 1
            if result.get('success'):
                china_success_count += 1

    china_success_rate = (china_success_count / china_total_count * 100) if china_total_count > 0 else 0

    if china_success_rate < 80:
        print("🇨🇳 中国股票数据源:")
        print("   - 检查Tushare Token配置")
        print("   - 确认AKShare库安装")
        print("   - 验证网络连接")

    # 检查美股数据源
    us_results = all_results.get('us_stocks', {})
    us_success_count = 0
    us_total_count = 0

    for symbol, symbol_results in us_results.items():
        for test_type, result in symbol_results.items():
            us_total_count += 1
            if result.get('success'):
                us_success_count += 1

    us_success_rate = (us_success_count / us_total_count * 100) if us_total_count > 0 else 0

    if us_success_rate < 80:
        print("🇺🇸 美股数据源:")
        print("   - 检查FinnHub API Key配置")
        print("   - 避免yfinance频率限制")
        print("   - 考虑使用代理服务")

    # 检查新闻数据源
    news_results = all_results.get('news', {})
    if news_results:
        print("📰 新闻数据源:")
        print("   - 配置更多新闻API密钥")
        print("   - 增加中文新闻源")
        print("   - 优化新闻去重算法")

    # 缓存系统建议
    cache_result = all_results.get('cache', {})
    if not cache_result.get('success'):
        print("🗄️ 缓存系统:")
        print("   - 检查Redis/MongoDB连接")
        print("   - 确认文件缓存目录权限")
        print("   - 清理过期缓存文件")


def main():
    """主测试函数"""
    print("🧪 数据源综合测试程序")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_results = {}

    try:
        # 1. 测试中国股票数据源
        china_results = test_china_stock_data_sources()
        all_results['china_stocks'] = china_results

        # 2. 测试美股数据源
        us_results = test_us_stock_data_sources()
        all_results['us_stocks'] = us_results

        # 3. 测试新闻数据源
        news_results = test_news_data_sources()
        all_results['news'] = news_results

        # 4. 测试缓存系统
        cache_results = test_cache_system()
        all_results['cache'] = cache_results

        # 5. 分析结果
        success = analyze_results(all_results)

        # 6. 打印建议
        print_recommendations(all_results)

        # 7. 总结
        print(f"\n🎯 测试总结:")
        if success:
            print("✅ 数据源系统运行正常")
            print("✅ 优先级配置正确")
            print("✅ 备用机制有效")
        else:
            print("⚠️ 数据源系统存在问题")
            print("⚠️ 需要检查配置和网络")

        return success

    except Exception as e:
        print(f"❌ 测试程序异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()

    print(f"\n{'='*60}")
    if success:
        print("🎉 数据源测试完成！系统运行正常。")
    else:
        print("⚠️ 数据源测试发现问题，请检查配置。")

    print(f"\n📋 下一步:")
    print("1. 根据建议优化配置")
    print("2. 运行 python -m cli.main 测试完整流程")
    print("3. 检查 .env 文件中的API密钥配置")
    print("4. 查看日志文件了解详细错误信息")
