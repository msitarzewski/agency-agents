#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试多周期数据支持功能

验证DataSourceManager是否正确支持日线、周线、月线数据获取
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ['TA_USE_APP_CACHE'] = 'true'

def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"🎯 {title}")
    print("=" * 70 + "\n")

def test_data_source_priority():
    """测试数据源优先级"""
    print_section("测试多周期数据支持")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    print("📊 多周期数据支持:")
    print("   1. ✅ daily（日线） - 每个交易日的OHLCV数据")
    print("   2. ✅ weekly（周线） - 每周的OHLCV数据")
    print("   3. ✅ monthly（月线） - 每月的OHLCV数据")
    print()
    print("📝 数据获取流程:")
    print("   1. 首先尝试从 MongoDB 获取指定周期的数据")
    print("   2. 如果 MongoDB 没有数据，自动降级到 Tushare/AKShare")
    print("   3. 所有数据源都支持多周期参数")
    print()
    print("🔍 当前数据源: " + manager.current_source.value)
    print("🔍 MongoDB缓存启用: " + str(manager.use_mongodb_cache))

def test_daily_data():
    """测试日线数据获取"""
    print_section("测试日线数据获取")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    # 计算日期范围（最近30天）
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    test_symbol = "000001"
    print(f"📊 测试股票: {test_symbol}")
    print(f"📅 日期范围: {start_date} ~ {end_date}")
    print(f"📈 数据周期: daily")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_data(test_symbol, start_date, end_date, period="daily")
    print()
    
    print("-" * 70)
    print("📊 日线数据获取结果")
    print("-" * 70)
    if result and "❌" not in result:
        print(f"✅ 日线数据获取成功")
        print(f"📊 数据长度: {len(result)} 字符")
        print()
        print("📫 数据预览（前500字符）:")
        print(result[:500])
    else:
        print(f"❌ 日线数据获取失败")
        print(f"📊 返回结果: {result[:200] if result else 'None'}")

def test_weekly_data():
    """测试周线数据获取"""
    print_section("测试周线数据获取")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    # 计算日期范围（最近90天）
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
    
    test_symbol = "000001"
    print(f"📊 测试股票: {test_symbol}")
    print(f"📅 日期范围: {start_date} ~ {end_date}")
    print(f"📈 数据周期: weekly")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_data(test_symbol, start_date, end_date, period="weekly")
    print()
    
    print("-" * 70)
    print("📊 周线数据获取结果")
    print("-" * 70)
    if result and "❌" not in result:
        print(f"✅ 周线数据获取成功")
        print(f"📊 数据长度: {len(result)} 字符")
        print()
        print("📫 数据预览（前500字符）:")
        print(result[:500])
    else:
        print(f"❌ 周线数据获取失败")
        print(f"📊 返回结果: {result[:200] if result else 'None'}")

def test_monthly_data():
    """测试月线数据获取"""
    print_section("测试月线数据获取")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    # 计算日期范围（最近365天）
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    test_symbol = "000001"
    print(f"📊 测试股票: {test_symbol}")
    print(f"📅 日期范围: {start_date} ~ {end_date}")
    print(f"📈 数据周期: monthly")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_data(test_symbol, start_date, end_date, period="monthly")
    print()
    
    print("-" * 70)
    print("📊 月线数据获取结果")
    print("-" * 70)
    if result and "❌" not in result:
        print(f"✅ 月线数据获取成功")
        print(f"📊 数据长度: {len(result)} 字符")
        print()
        print("📫 数据预览（前500字符）:")
        print(result[:500])
    else:
        print(f"❌ 月线数据获取失败")
        print(f"📊 返回结果: {result[:200] if result else 'None'}")

def test_fallback_mechanism():
    """测试多周期数据降级机制"""
    print_section("测试多周期数据降级机制")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    # 测试一个可能在 MongoDB 中不存在的股票
    test_symbol = "688888"
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    print(f"📊 测试股票: {test_symbol}")
    print(f"📅 日期范围: {start_date} ~ {end_date}")
    print(f"📈 数据周期: weekly")
    print(f"📝 预期行为: MongoDB 无数据 → 自动降级到 Tushare/AKShare")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_data(test_symbol, start_date, end_date, period="weekly")
    print()
    
    print("-" * 70)
    print("📊 降级测试结果")
    print("-" * 70)
    if result and "❌" not in result:
        print(f"✅ 降级成功，从备用数据源获取到周线数据")
        print(f"📊 数据长度: {len(result)} 字符")
    else:
        print(f"⚠️ 所有数据源都无法获取该股票的周线数据")
        print(f"📊 返回结果: {result[:200] if result else 'None'}")

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 多周期数据支持功能测试")
    print("=" * 70)
    print()
    print("📝 测试说明:")
    print("   本测试验证DataSourceManager是否正确支持多周期数据获取")
    print("   包括日线（daily）、周线（weekly）、月线（monthly）")
    print()
    print("💡 配置要求:")
    print("   - TA_USE_APP_CACHE=true  # 启用 MongoDB 缓存")
    print("   - MongoDB 服务正常运行")
    print("   - 数据库中有多周期历史数据")
    print()
    
    try:
        # 测试数据源优先级
        test_data_source_priority()
        
        # 测试日线数据
        test_daily_data()
        
        # 测试周线数据
        test_weekly_data()
        
        # 测试月线数据
        test_monthly_data()
        
        # 测试降级机制
        test_fallback_mechanism()
        
        print_section("✅ 所有测试完成")
        print()
        print("💡 提示：检查上面的日志，确认")
        print("   1. 日线、周线、月线数据是否都能正确获取")
        print("   2. 数据获取日志中是否显示正确的周期标记")
        print("   3. 降级机制是否正常工作")
        print("   4. MongoDB优先级是否正确")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

