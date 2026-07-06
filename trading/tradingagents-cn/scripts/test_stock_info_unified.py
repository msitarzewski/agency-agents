#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试股票信息统一功能

验证股票信息是否被正确纳入 DataSourceManager 统一管理，
支持多数据源和自动降级
"""

import os
import sys

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
    print_section("测试数据源优先级")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    print("📊 股票信息数据源优先级:")
    print("   1. ✅ MongoDB（最高优先级） - stock_basic_info")
    print("   2. ✅ Tushare - 股票基本信息")
    print("   3. ✅ AKShare - 股票信息")
    print("   4. ✅ BaoStock - 股票信息")
    print()
    print("📝 数据获取流程:")
    print("   1. 首先尝试从 MongoDB 获取股票基本信息")
    print("   2. 如果 MongoDB 没有数据，自动降级到 Tushare")
    print("   3. 如果 Tushare 失败，继续降级到 AKShare")
    print("   4. 如果 AKShare 失败，继续降级到 BaoStock")

def test_mongodb_stock_info():
    """测试从 MongoDB 获取股票信息"""
    print_section("测试从 MongoDB 获取股票信息")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    print("📊 创建数据源管理器...")
    manager = get_data_source_manager()
    
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print(f"🔍 MongoDB缓存启用: {manager.use_mongodb_cache}")
    print()
    
    print("-" * 70)
    print("📊 测试获取股票信息")
    print("-" * 70)
    print()
    
    # 测试股票
    test_symbol = "000001"
    print(f"📊 测试股票: {test_symbol}")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_info(test_symbol)
    print()
    
    print("-" * 70)
    print("📊 股票信息获取结果")
    print("-" * 70)
    if result and result.get('name') and result['name'] != f'股票{test_symbol}':
        print(f"✅ 股票信息获取成功")
        print(f"📊 股票代码: {result.get('symbol')}")
        print(f"📊 股票名称: {result.get('name')}")
        print(f"📊 所属地区: {result.get('area')}")
        print(f"📊 所属行业: {result.get('industry')}")
        print(f"📊 上市市场: {result.get('market')}")
        print(f"📊 上市日期: {result.get('list_date')}")
        print(f"🔍 数据来源: {result.get('source')}")
        
        # 如果有行情数据
        if 'current_price' in result:
            print(f"📈 当前价格: {result.get('current_price')}")
            print(f"📈 涨跌幅: {result.get('change_pct')}%")
            print(f"📈 成交量: {result.get('volume')}")
            print(f"📈 行情日期: {result.get('quote_date')}")
    else:
        print(f"❌ 股票信息获取失败")
        print(f"📊 返回结果: {result}")

def test_tushare_stock_info():
    """测试从 Tushare 获取股票信息"""
    print_section("测试从 Tushare 获取股票信息")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager, ChinaDataSource
    
    print("📊 创建数据源管理器...")
    manager = get_data_source_manager()
    
    # 临时切换数据源
    original_source = manager.current_source
    manager.current_source = ChinaDataSource.TUSHARE
    print(f"🔄 临时切换数据源: {original_source.value} → {manager.current_source.value}")
    print()
    
    # 测试股票
    test_symbol = "000001"
    print(f"📊 测试股票: {test_symbol}")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_info(test_symbol)
    print()
    
    print("-" * 70)
    print("📊 股票信息获取结果")
    print("-" * 70)
    if result and result.get('name') and result['name'] != f'股票{test_symbol}':
        print(f"✅ 股票信息获取成功")
        print(f"📊 股票代码: {result.get('symbol')}")
        print(f"📊 股票名称: {result.get('name')}")
        print(f"🔍 数据来源: {result.get('source')}")
    else:
        print(f"❌ 股票信息获取失败")
    
    # 恢复数据源
    manager.current_source = original_source
    print()
    print(f"🔄 恢复数据源: {manager.current_source.value}")

def test_fallback_mechanism():
    """测试股票信息降级机制"""
    print_section("测试股票信息降级机制")
    
    from tradingagents.dataflows.data_source_manager import get_data_source_manager
    
    manager = get_data_source_manager()
    
    # 测试一个可能在 MongoDB 中不存在的股票
    test_symbol = "688999"  # 科创板股票，可能不在 MongoDB 中
    print(f"📊 测试股票: {test_symbol}")
    print(f"📝 预期行为: MongoDB 无数据 → 自动降级到 Tushare/AKShare")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print()
    
    print("-" * 70)
    result = manager.get_stock_info(test_symbol)
    print()
    
    print("-" * 70)
    print("📊 降级测试结果")
    print("-" * 70)
    if result and result.get('name') and result['name'] != f'股票{test_symbol}':
        print(f"✅ 降级成功，从备用数据源获取到股票信息")
        print(f"🔍 最终数据来源: {result.get('source')}")
        print(f"📊 股票名称: {result.get('name')}")
    else:
        print(f"⚠️ 所有数据源都无法获取该股票信息")
        print(f"📊 返回结果: {result}")

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 股票信息统一功能测试")
    print("=" * 70)
    print()
    print("📝 测试说明:")
    print("   本测试验证股票信息是否被正确纳入 DataSourceManager")
    print("   统一管理，支持多数据源和自动降级")
    print()
    print("💡 配置要求:")
    print("   - TA_USE_APP_CACHE=true  # 启用 MongoDB 缓存")
    print("   - MongoDB 服务正常运行")
    print("   - 数据库中有股票基本信息")
    print()
    
    try:
        # 测试数据源优先级
        test_data_source_priority()
        
        # 测试从 MongoDB 获取股票信息
        test_mongodb_stock_info()
        
        # 测试从 Tushare 获取股票信息
        test_tushare_stock_info()
        
        # 测试降级机制
        test_fallback_mechanism()
        
        print_section("✅ 所有测试完成")
        print()
        print("💡 提示：检查上面的日志，确认")
        print("   1. 股票信息是否从 MongoDB 优先获取")
        print("   2. 数据获取日志中是否显示 [数据来源: mongodb]")
        print("   3. 降级机制是否正常工作")
        print("   4. 统一接口是否正确调用")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

