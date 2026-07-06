#!/usr/bin/env python3
"""
历史数据同步问题诊断脚本
分析为什么历史数据没有完整同步到MongoDB
"""
import asyncio
import logging
from datetime import datetime, timedelta
from tradingagents.config.database_manager import get_mongodb_client

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def diagnose_historical_data_sync():
    """诊断历史数据同步问题"""
    
    print("🔍 历史数据同步问题诊断")
    print("=" * 60)
    
    # 1. 检查MongoDB连接和数据状态
    print("\n1️⃣ 检查MongoDB数据状态")
    client = get_mongodb_client()
    db = client.get_database('tradingagents')
    collection = db.stock_daily_quotes
    
    total_count = collection.count_documents({})
    print(f"   总记录数: {total_count:,}")
    
    # 按数据源统计
    tushare_count = collection.count_documents({'data_source': 'tushare'})
    akshare_count = collection.count_documents({'data_source': 'akshare'})
    baostock_count = collection.count_documents({'data_source': 'baostock'})
    
    print(f"   Tushare: {tushare_count:,} 条")
    print(f"   AKShare: {akshare_count:,} 条")
    print(f"   BaoStock: {baostock_count:,} 条")
    
    # 按周期统计
    daily_count = collection.count_documents({'period': 'daily'})
    weekly_count = collection.count_documents({'period': 'weekly'})
    monthly_count = collection.count_documents({'period': 'monthly'})
    
    print(f"   日线: {daily_count:,} 条")
    print(f"   周线: {weekly_count:,} 条")
    print(f"   月线: {monthly_count:,} 条")
    
    # 2. 检查日期范围
    print("\n2️⃣ 检查数据日期范围")
    oldest = collection.find_one({}, sort=[('trade_date', 1)])
    newest = collection.find_one({}, sort=[('trade_date', -1)])
    
    if oldest and newest:
        oldest_date = oldest.get('trade_date', 'N/A')
        newest_date = newest.get('trade_date', 'N/A')
        print(f"   最早日期: {oldest_date}")
        print(f"   最新日期: {newest_date}")
        
        # 计算数据覆盖天数
        try:
            start_date = datetime.strptime(oldest_date, '%Y-%m-%d')
            end_date = datetime.strptime(newest_date, '%Y-%m-%d')
            days_covered = (end_date - start_date).days + 1
            print(f"   覆盖天数: {days_covered} 天")
        except:
            print("   无法计算覆盖天数")
    
    # 3. 检查股票覆盖情况
    print("\n3️⃣ 检查股票覆盖情况")
    
    # 获取基础信息中的股票总数
    basic_info_collection = db.stock_basic_info
    total_stocks = basic_info_collection.count_documents({})
    print(f"   基础信息中股票总数: {total_stocks:,}")
    
    # 获取历史数据中的股票数量
    pipeline = [
        {"$group": {"_id": "$symbol"}},
        {"$count": "unique_symbols"}
    ]
    result = list(collection.aggregate(pipeline))
    historical_stocks = result[0]['unique_symbols'] if result else 0
    print(f"   历史数据中股票数量: {historical_stocks:,}")
    
    coverage_rate = (historical_stocks / total_stocks * 100) if total_stocks > 0 else 0
    print(f"   股票覆盖率: {coverage_rate:.1f}%")
    
    # 4. 检查配置状态
    print("\n4️⃣ 检查同步服务配置")
    import os
    
    tushare_enabled = os.getenv('TUSHARE_UNIFIED_ENABLED', 'false').lower() == 'true'
    akshare_enabled = os.getenv('AKSHARE_UNIFIED_ENABLED', 'false').lower() == 'true'
    baostock_enabled = os.getenv('BAOSTOCK_UNIFIED_ENABLED', 'false').lower() == 'true'
    
    print(f"   Tushare同步: {'✅ 启用' if tushare_enabled else '❌ 禁用'}")
    print(f"   AKShare同步: {'✅ 启用' if akshare_enabled else '❌ 禁用'}")
    print(f"   BaoStock同步: {'✅ 启用' if baostock_enabled else '❌ 禁用'}")
    
    # 5. 分析问题原因
    print("\n5️⃣ 问题分析")
    
    issues = []
    
    # 检查是否只有最近一个月的数据
    if oldest_date and oldest_date >= '2025-09-01':
        issues.append("❌ 只有最近一个月的数据，缺少历史数据")
    
    # 检查是否缺少周线和月线数据
    if weekly_count == 0:
        issues.append("❌ 缺少周线数据")
    if monthly_count == 0:
        issues.append("❌ 缺少月线数据")
    
    # 检查BaoStock数据
    if baostock_count == 0 and baostock_enabled:
        issues.append("❌ BaoStock已启用但无数据")
    
    # 检查股票覆盖率
    if coverage_rate < 50:
        issues.append(f"❌ 股票覆盖率过低 ({coverage_rate:.1f}%)")
    
    if issues:
        print("   发现的问题:")
        for issue in issues:
            print(f"     {issue}")
    else:
        print("   ✅ 未发现明显问题")
    
    # 6. 提供解决方案
    print("\n6️⃣ 解决方案建议")
    
    if oldest_date and oldest_date >= '2025-09-01':
        print("   📋 历史数据不足的解决方案:")
        print("     1. 手动触发全量历史数据同步:")
        print("        python cli/sync_data.py --historical --all-history")
        print("     2. 或通过API触发:")
        print("        POST /api/multi-period-sync/start-full?all_history=true")
    
    if weekly_count == 0 or monthly_count == 0:
        print("   📋 多周期数据缺失的解决方案:")
        print("     1. 触发多周期同步:")
        print("        python cli/sync_data.py --multi-period")
        print("     2. 或通过API触发:")
        print("        POST /api/multi-period-sync/start-incremental")
    
    if not akshare_enabled and not baostock_enabled:
        print("   📋 数据源配置建议:")
        print("     1. 启用AKShare作为备用数据源:")
        print("        AKSHARE_UNIFIED_ENABLED=true")
        print("     2. 启用BaoStock获取更多历史数据:")
        print("        BAOSTOCK_UNIFIED_ENABLED=true")
    
    print("\n" + "=" * 60)
    print("🎯 诊断完成！请根据建议进行相应的修复操作。")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(diagnose_historical_data_sync())
