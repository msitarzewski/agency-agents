#!/usr/bin/env python3
"""
测试多周期数据同步功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.providers.tushare_provider import TushareProvider
from app.services.historical_data_service import get_historical_data_service
from app.core.database import init_database
from tradingagents.config.database_manager import get_mongodb_client


async def test_multi_period_sync():
    """测试多周期数据同步"""
    print('🔍 测试多周期数据同步功能')
    print('=' * 60)
    
    # 测试参数
    test_symbol = "000001"
    start_date = "2024-01-01"
    end_date = "2024-03-31"  # 测试3个月的数据
    
    print(f"📊 测试参数:")
    print(f"   股票代码: {test_symbol}")
    print(f"   日期范围: {start_date} 到 {end_date}")
    print()
    
    try:
        # 初始化
        print("1️⃣ 初始化数据库和提供者")
        await init_database()
        provider = TushareProvider()
        await provider.connect()
        service = await get_historical_data_service()
        print("   ✅ 初始化完成\n")
        
        # 获取MongoDB连接
        client = get_mongodb_client()
        db = client.get_database('tradingagents')
        collection = db.stock_daily_quotes
        
        # 测试三种周期
        periods = [
            ("daily", "日线"),
            ("weekly", "周线"),
            ("monthly", "月线")
        ]
        
        for period, period_name in periods:
            print(f"{'='*60}")
            print(f"📊 测试{period_name}数据同步")
            print(f"{'='*60}")
            
            # 检查数据库状态（保存前）
            before_count = collection.count_documents({
                'symbol': test_symbol,
                'data_source': 'tushare',
                'period': period
            })
            print(f"   📊 保存前{period_name}记录数: {before_count}")
            
            # 获取历史数据
            print(f"   📥 获取{period_name}数据...")
            df = await provider.get_historical_data(test_symbol, start_date, end_date, period=period)
            
            if df is None or df.empty:
                print(f"   ⚠️ 未获取到{period_name}数据")
                continue
            
            print(f"   ✅ 获取到 {len(df)} 条记录")
            
            # 显示数据样本
            print(f"   📋 数据样本（前3条）:")
            for i, (date, row) in enumerate(df.head(3).iterrows()):
                close = row.get('close', 'N/A')
                volume = row.get('volume', 'N/A')
                print(f"     {date.strftime('%Y-%m-%d')}: 收盘={close}, 成交量={volume}")
            
            # 保存历史数据
            print(f"   💾 保存{period_name}数据...")
            saved_count = await service.save_historical_data(
                symbol=test_symbol,
                data=df,
                data_source='tushare',
                market='CN',
                period=period
            )
            print(f"   ✅ 保存完成: {saved_count} 条记录")
            
            # 检查数据库状态（保存后）
            after_count = collection.count_documents({
                'symbol': test_symbol,
                'data_source': 'tushare',
                'period': period
            })
            print(f"   📊 保存后{period_name}记录数: {after_count}")
            print(f"   📈 新增记录数: {after_count - before_count}")
            
            # 验证保存的数据
            saved_records = list(collection.find({
                'symbol': test_symbol,
                'data_source': 'tushare',
                'period': period,
                'trade_date': {'$gte': start_date, '$lte': end_date}
            }).sort('trade_date', 1).limit(3))
            
            if saved_records:
                print(f"   📋 数据库中的记录（前3条）:")
                for record in saved_records:
                    trade_date = record.get('trade_date', 'N/A')
                    close = record.get('close', 'N/A')
                    period_field = record.get('period', 'N/A')
                    print(f"     {trade_date}: 收盘={close}, 周期={period_field}")
            
            # 结果评估
            if saved_count > 0 and after_count > before_count:
                print(f"   ✅ {period_name}数据同步成功！")
            else:
                print(f"   ⚠️ {period_name}数据同步可能存在问题")
            
            print()
        
        # 总结
        print(f"{'='*60}")
        print("📊 多周期数据统计")
        print(f"{'='*60}")
        
        for period, period_name in periods:
            count = collection.count_documents({
                'symbol': test_symbol,
                'data_source': 'tushare',
                'period': period
            })
            print(f"   {period_name}: {count} 条记录")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_multi_period_sync())
