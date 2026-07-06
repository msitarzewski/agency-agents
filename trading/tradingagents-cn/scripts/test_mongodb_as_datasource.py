#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 MongoDB 作为数据源的功能

验证 DataSourceManager 是否正确将 MongoDB 作为最高优先级数据源
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingagents.dataflows.data_source_manager import DataSourceManager, ChinaDataSource
from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")


def test_mongodb_as_datasource():
    """测试 MongoDB 作为数据源"""
    print("\n" + "=" * 70)
    print("🧪 测试 MongoDB 作为数据源")
    print("=" * 70)
    
    # 创建数据源管理器
    print("\n📊 创建数据源管理器...")
    manager = DataSourceManager()
    
    # 检查当前数据源
    print(f"\n🔍 当前数据源: {manager.current_source.value}")
    print(f"🔍 默认数据源: {manager.default_source.value}")
    print(f"🔍 MongoDB缓存启用: {manager.use_mongodb_cache}")
    print(f"🔍 可用数据源: {[s.value for s in manager.available_sources]}")
    
    # 验证 MongoDB 是否在可用数据源列表中
    if manager.use_mongodb_cache:
        if ChinaDataSource.MONGODB in manager.available_sources:
            print("\n✅ MongoDB 已加入可用数据源列表")
        else:
            print("\n❌ MongoDB 未加入可用数据源列表")
        
        # 验证 MongoDB 是否是默认数据源
        if manager.default_source == ChinaDataSource.MONGODB:
            print("✅ MongoDB 是默认数据源（最高优先级）")
        else:
            print(f"❌ MongoDB 不是默认数据源，当前默认: {manager.default_source.value}")
    else:
        print("\n⚠️ MongoDB 缓存未启用（TA_USE_APP_CACHE=false）")
        print(f"   当前默认数据源: {manager.default_source.value}")
    
    # 测试数据获取
    print("\n" + "-" * 70)
    print("📈 测试数据获取")
    print("-" * 70)
    
    test_symbol = "000001"
    start_date = "2025-09-01"
    end_date = "2025-09-30"
    
    print(f"\n📊 测试股票: {test_symbol}")
    print(f"📅 日期范围: {start_date} 到 {end_date}")
    print(f"🔍 当前数据源: {manager.current_source.value}")
    print("\n" + "-" * 70)
    
    # 获取数据
    result = manager.get_stock_data(test_symbol, start_date, end_date)
    
    # 显示结果摘要
    print("\n" + "-" * 70)
    print("📊 数据获取结果")
    print("-" * 70)
    
    if result and "❌" not in result:
        print(f"✅ 数据获取成功")
        print(f"📏 数据长度: {len(result)} 字符")
        print(f"🔍 数据来源: {manager.current_source.value}")
        
        # 显示前200个字符
        print(f"\n📄 数据预览（前200字符）:")
        print(result[:200] + "...")
    else:
        print(f"❌ 数据获取失败")
        print(f"📄 错误信息: {result[:200]}")
    
    # 测试数据源优先级
    print("\n" + "=" * 70)
    print("🔄 测试数据源优先级")
    print("=" * 70)
    
    if manager.use_mongodb_cache and ChinaDataSource.MONGODB in manager.available_sources:
        print("\n✅ MongoDB 数据源优先级测试:")
        print("   1. MongoDB（最高优先级）")
        print("   2. AKShare")
        print("   3. Tushare")
        print("   4. BaoStock")
        print("   5. TDX")
        
        print("\n📝 数据获取流程:")
        print("   1. 首先尝试从 MongoDB 获取数据")
        print("   2. 如果 MongoDB 没有数据，自动降级到 AKShare")
        print("   3. 如果 AKShare 失败，继续降级到 Tushare")
        print("   4. 依此类推...")
    else:
        print("\n⚠️ MongoDB 未启用，使用传统数据源优先级:")
        print(f"   1. {manager.default_source.value}（默认）")
        print("   2. 其他可用数据源")


def test_mongodb_fallback():
    """测试 MongoDB 降级机制"""
    print("\n" + "=" * 70)
    print("🧪 测试 MongoDB 降级机制")
    print("=" * 70)
    
    manager = DataSourceManager()
    
    if not manager.use_mongodb_cache:
        print("\n⚠️ MongoDB 缓存未启用，跳过降级测试")
        return
    
    # 测试一个 MongoDB 中不存在的股票
    test_symbol = "999999"  # 不存在的股票代码
    start_date = "2025-09-01"
    end_date = "2025-09-30"
    
    print(f"\n📊 测试不存在的股票: {test_symbol}")
    print(f"📅 日期范围: {start_date} 到 {end_date}")
    print(f"🔍 预期行为: MongoDB 无数据 → 自动降级到其他数据源")
    print("\n" + "-" * 70)
    
    result = manager.get_stock_data(test_symbol, start_date, end_date)
    
    print("\n" + "-" * 70)
    print("📊 降级测试结果")
    print("-" * 70)
    
    if result and "❌" not in result:
        print(f"✅ 降级成功，从备用数据源获取到数据")
        print(f"🔍 最终数据来源: {manager.current_source.value}")
    else:
        print(f"⚠️ 所有数据源都无法获取数据（预期行为）")
        print(f"📄 结果: {result[:200]}")


if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print("🚀 MongoDB 数据源功能测试")
        print("=" * 70)
        
        print("\n📝 测试说明:")
        print("   本测试验证 MongoDB 是否被正确纳入 DataSourceManager")
        print("   作为最高优先级数据源进行管理")
        print("\n💡 配置要求:")
        print("   - TA_USE_APP_CACHE=true  # 启用 MongoDB 缓存")
        print("   - MongoDB 服务正常运行")
        print("   - 数据库中有测试数据")
        
        # 测试 MongoDB 作为数据源
        test_mongodb_as_datasource()
        
        # 测试降级机制
        test_mongodb_fallback()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试完成")
        print("=" * 70)
        
        print("\n💡 提示：检查上面的日志，确认:")
        print("   1. MongoDB 是否在可用数据源列表中")
        print("   2. MongoDB 是否是默认数据源（当 TA_USE_APP_CACHE=true 时）")
        print("   3. 数据获取日志中是否显示 [数据来源: mongodb]")
        print("   4. 降级机制是否正常工作")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

