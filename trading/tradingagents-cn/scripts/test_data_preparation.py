#!/usr/bin/env python3
"""
测试A股数据准备功能
验证数据库检查和自动同步功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingagents.utils.stock_validator import prepare_stock_data
import logging

logger = logging.getLogger(__name__)


def test_data_preparation():
    """测试数据准备功能"""
    
    # 测试股票列表
    test_stocks = [
        ("000001", "A股"),  # 平安银行
        ("600519", "A股"),  # 贵州茅台
        ("002146", "A股"),  # 荣盛发展
    ]
    
    print("=" * 80)
    print("🧪 测试A股数据准备功能")
    print("=" * 80)
    
    for stock_code, market_type in test_stocks:
        print(f"\n{'=' * 80}")
        print(f"📊 测试股票: {stock_code} ({market_type})")
        print(f"{'=' * 80}")
        
        try:
            # 调用数据准备函数
            result = prepare_stock_data(
                stock_code=stock_code,
                market_type=market_type,
                period_days=30,  # 30天历史数据
                analysis_date=None  # 使用今天
            )
            
            # 打印结果
            print(f"\n✅ 数据准备结果:")
            print(f"   - 是否有效: {result.is_valid}")
            print(f"   - 股票代码: {result.stock_code}")
            print(f"   - 股票名称: {result.stock_name}")
            print(f"   - 市场类型: {result.market_type}")
            print(f"   - 有基本信息: {result.has_basic_info}")
            print(f"   - 有历史数据: {result.has_historical_data}")
            print(f"   - 数据周期: {result.data_period_days}天")
            print(f"   - 缓存状态: {result.cache_status}")
            
            if not result.is_valid:
                print(f"\n❌ 错误信息: {result.error_message}")
                print(f"💡 建议: {result.suggestion}")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 80}")
    print("✅ 测试完成")
    print(f"{'=' * 80}")


def test_database_check():
    """测试数据库检查功能"""
    from tradingagents.utils.stock_validator import StockDataPreparer
    from datetime import datetime, timedelta
    
    print("\n" + "=" * 80)
    print("🧪 测试数据库检查功能")
    print("=" * 80)
    
    preparer = StockDataPreparer()
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    test_stocks = ["000001", "600519", "002146"]
    
    for stock_code in test_stocks:
        print(f"\n📊 检查股票: {stock_code}")
        print(f"   日期范围: {start_date_str} 到 {end_date_str}")
        
        try:
            result = preparer._check_database_data(stock_code, start_date_str, end_date_str)
            
            print(f"   - 有数据: {result['has_data']}")
            print(f"   - 是最新: {result['is_latest']}")
            print(f"   - 记录数: {result['record_count']}")
            print(f"   - 最新日期: {result['latest_date']}")
            print(f"   - 消息: {result['message']}")
            
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")


async def test_data_sync_async():
    """测试数据同步功能（异步版本）"""
    from tradingagents.utils.stock_validator import StockDataPreparer
    from datetime import datetime, timedelta
    from app.core.database import init_database, close_database

    print("\n" + "=" * 80)
    print("🧪 测试数据同步功能（异步）")
    print("=" * 80)

    try:
        # 初始化数据库连接
        print("\n🔄 初始化数据库连接...")
        await init_database()
        print("✅ 数据库连接初始化成功")

        preparer = StockDataPreparer()

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # 测试一个股票的同步
        stock_code = "000001"

        print(f"\n📊 同步股票: {stock_code}")
        print(f"   日期范围: {start_date_str} 到 {end_date_str}")

        try:
            result = await preparer._trigger_data_sync_async(stock_code, start_date_str, end_date_str)

            print(f"   - 成功: {result['success']}")
            print(f"   - 消息: {result['message']}")
            print(f"   - 同步记录数: {result['synced_records']}")
            print(f"   - 数据源: {result.get('data_source', 'N/A')}")

        except Exception as e:
            print(f"   ❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()

    finally:
        # 关闭数据库连接
        print("\n🔄 关闭数据库连接...")
        await close_database()
        print("✅ 数据库连接已关闭")


def test_data_sync():
    """测试数据同步功能（同步包装器）"""
    import asyncio

    # 运行异步测试
    asyncio.run(test_data_sync_async())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试A股数据准备功能")
    parser.add_argument("--test", choices=["all", "prepare", "check", "sync"], 
                       default="all", help="测试类型")
    
    args = parser.parse_args()
    
    if args.test == "all":
        test_database_check()
        test_data_preparation()
        # test_data_sync()  # 注释掉，避免频繁同步
    elif args.test == "prepare":
        test_data_preparation()
    elif args.test == "check":
        test_database_check()
    elif args.test == "sync":
        test_data_sync()

