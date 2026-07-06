"""
测试选择性数据同步功能
"""
import asyncio
import logging
from datetime import datetime
from tradingagents.config.database_manager import get_mongodb_client
from app.core.database import init_database
from app.worker.tushare_init_service import get_tushare_init_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_data_counts():
    """检查各类数据的数量"""
    client = get_mongodb_client()
    db = client.get_database('tradingagents')
    
    counts = {
        'basic_info': db.stock_basic_info.count_documents({}),
        'daily': db.stock_daily_quotes.count_documents({'period': 'daily'}),
        'weekly': db.stock_daily_quotes.count_documents({'period': 'weekly'}),
        'monthly': db.stock_daily_quotes.count_documents({'period': 'monthly'}),
        'financial': db.stock_financial_data.count_documents({}),
        'quotes': db.market_quotes.count_documents({})
    }
    
    return counts


async def test_selective_sync():
    """测试选择性同步"""
    print("🔍 测试选择性数据同步功能")
    print("="*60)
    
    # 初始化数据库
    print("\n1️⃣ 初始化数据库")
    await init_database()
    
    # 获取初始数据量
    print("\n2️⃣ 检查初始数据量")
    before_counts = await check_data_counts()
    print(f"   基础信息: {before_counts['basic_info']:,} 条")
    print(f"   日线数据: {before_counts['daily']:,} 条")
    print(f"   周线数据: {before_counts['weekly']:,} 条")
    print(f"   月线数据: {before_counts['monthly']:,} 条")
    print(f"   财务数据: {before_counts['financial']:,} 条")
    print(f"   行情数据: {before_counts['quotes']:,} 条")
    
    # 测试1: 仅同步历史数据
    print("\n3️⃣ 测试1: 仅同步历史数据（日线）")
    print("   命令: python cli/tushare_init.py --full --sync-items historical --historical-days 30")
    service = await get_tushare_init_service()
    
    result1 = await service.run_full_initialization(
        historical_days=30,
        skip_if_exists=False,
        sync_items=['historical']
    )
    
    print(f"   ✅ 同步完成: {result1['success']}")
    print(f"   ⏱️  耗时: {result1['duration']:.2f}秒")
    
    # 检查数据量变化
    after_test1 = await check_data_counts()
    print(f"   📊 日线数据变化: {before_counts['daily']:,} → {after_test1['daily']:,} (+{after_test1['daily'] - before_counts['daily']:,})")
    
    # 测试2: 仅同步周线数据
    print("\n4️⃣ 测试2: 仅同步周线数据")
    print("   命令: python cli/tushare_init.py --full --sync-items weekly --historical-days 30")
    
    result2 = await service.run_full_initialization(
        historical_days=30,
        skip_if_exists=False,
        sync_items=['weekly']
    )
    
    print(f"   ✅ 同步完成: {result2['success']}")
    print(f"   ⏱️  耗时: {result2['duration']:.2f}秒")
    
    # 检查数据量变化
    after_test2 = await check_data_counts()
    print(f"   📊 周线数据变化: {after_test1['weekly']:,} → {after_test2['weekly']:,} (+{after_test2['weekly'] - after_test1['weekly']:,})")
    
    # 测试3: 同步多个数据类型
    print("\n5️⃣ 测试3: 同步财务数据和行情数据")
    print("   命令: python cli/tushare_init.py --full --sync-items financial,quotes")
    
    result3 = await service.run_full_initialization(
        historical_days=30,
        skip_if_exists=False,
        sync_items=['financial', 'quotes']
    )
    
    print(f"   ✅ 同步完成: {result3['success']}")
    print(f"   ⏱️  耗时: {result3['duration']:.2f}秒")
    
    # 检查数据量变化
    after_test3 = await check_data_counts()
    print(f"   📊 财务数据变化: {after_test2['financial']:,} → {after_test3['financial']:,} (+{after_test3['financial'] - after_test2['financial']:,})")
    print(f"   📊 行情数据变化: {after_test2['quotes']:,} → {after_test3['quotes']:,} (+{after_test3['quotes'] - after_test2['quotes']:,})")
    
    # 最终统计
    print("\n6️⃣ 最终数据统计")
    final_counts = await check_data_counts()
    print(f"   基础信息: {final_counts['basic_info']:,} 条")
    print(f"   日线数据: {final_counts['daily']:,} 条")
    print(f"   周线数据: {final_counts['weekly']:,} 条")
    print(f"   月线数据: {final_counts['monthly']:,} 条")
    print(f"   财务数据: {final_counts['financial']:,} 条")
    print(f"   行情数据: {final_counts['quotes']:,} 条")
    
    print("\n" + "="*60)
    print("🎯 测试完成！")
    print("="*60)
    
    # 显示使用示例
    print("\n📝 CLI使用示例:")
    print("   # 仅同步历史数据")
    print("   python cli/tushare_init.py --full --sync-items historical")
    print()
    print("   # 仅同步财务数据")
    print("   python cli/tushare_init.py --full --sync-items financial")
    print()
    print("   # 同步周线和月线数据")
    print("   python cli/tushare_init.py --full --sync-items weekly,monthly")
    print()
    print("   # 同步多个数据类型")
    print("   python cli/tushare_init.py --full --sync-items historical,financial,quotes")
    print()


if __name__ == "__main__":
    asyncio.run(test_selective_sync())

