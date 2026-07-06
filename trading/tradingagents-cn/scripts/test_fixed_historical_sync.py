#!/usr/bin/env python3
"""
测试修复后的历史数据同步
"""
import asyncio
import logging
from datetime import datetime, timedelta
from tradingagents.dataflows.providers.tushare_provider import TushareProvider
from app.services.historical_data_service import get_historical_data_service
from app.core.database import init_database
from tradingagents.config.database_manager import get_mongodb_client

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_fixed_historical_sync():
    """测试修复后的历史数据同步"""
    
    print("🔍 测试修复后的历史数据同步")
    print("=" * 60)
    
    # 测试参数 - 使用一个新的股票代码
    test_symbol = "000858"  # 五粮液
    start_date = "2024-01-01"
    end_date = "2024-01-10"  # 测试10天的数据
    
    print(f"📊 测试参数:")
    print(f"   股票代码: {test_symbol}")
    print(f"   日期范围: {start_date} 到 {end_date}")
    print()
    
    try:
        # 1. 初始化
        print("1️⃣ 初始化数据库和提供者")
        await init_database()
        
        provider = TushareProvider()
        await provider.connect()
        
        service = await get_historical_data_service()
        print("   ✅ 初始化完成")
        
        # 2. 检查数据库状态（保存前）
        print(f"\n2️⃣ 检查数据库状态（保存前）")
        client = get_mongodb_client()
        db = client.get_database('tradingagents')
        collection = db.stock_daily_quotes
        
        before_count = collection.count_documents({"symbol": test_symbol})
        before_tushare_count = collection.count_documents({
            "symbol": test_symbol, 
            "data_source": "tushare"
        })
        
        print(f"   📊 {test_symbol} 总记录数: {before_count}")
        print(f"   📊 {test_symbol} Tushare记录数: {before_tushare_count}")
        
        # 3. 获取历史数据
        print(f"\n3️⃣ 获取历史数据")
        df = await provider.get_historical_data(test_symbol, start_date, end_date)
        
        if df is None or df.empty:
            print("   ❌ 未获取到历史数据")
            return
        
        print(f"   ✅ 获取到 {len(df)} 条记录")
        
        # 4. 保存历史数据
        print(f"\n4️⃣ 保存历史数据")
        saved_count = await service.save_historical_data(
            symbol=test_symbol,
            data=df,
            data_source="tushare",
            market="CN",
            period="daily"
        )
        
        print(f"   ✅ 保存完成: {saved_count} 条记录")
        
        # 5. 检查数据库状态（保存后）
        print(f"\n5️⃣ 检查数据库状态（保存后）")
        
        after_count = collection.count_documents({"symbol": test_symbol})
        after_tushare_count = collection.count_documents({
            "symbol": test_symbol, 
            "data_source": "tushare"
        })
        
        print(f"   📊 {test_symbol} 总记录数: {after_count}")
        print(f"   📊 {test_symbol} Tushare记录数: {after_tushare_count}")
        print(f"   📈 新增总记录数: {after_count - before_count}")
        print(f"   📈 新增Tushare记录数: {after_tushare_count - before_tushare_count}")
        
        # 6. 验证保存的数据
        print(f"\n6️⃣ 验证保存的数据")
        
        saved_records = list(collection.find(
            {
                "symbol": test_symbol, 
                "data_source": "tushare",
                "trade_date": {"$gte": start_date, "$lte": end_date}
            },
            sort=[("trade_date", 1)]
        ))
        
        print(f"   📋 指定日期范围内的记录: {len(saved_records)} 条")
        
        if saved_records:
            print("   📊 前5条记录:")
            for i, record in enumerate(saved_records[:5]):
                trade_date = record.get('trade_date', 'N/A')
                close = record.get('close', 'N/A')
                volume = record.get('volume', 'N/A')
                print(f"     {i+1}. {trade_date}: 收盘={close}, 成交量={volume}")
        
        # 7. 结果评估
        print(f"\n7️⃣ 结果评估")
        
        if saved_count > 0:
            print("   ✅ 数据保存成功")
        else:
            print("   ❌ 数据保存失败")
        
        if after_tushare_count > before_tushare_count:
            print("   ✅ 数据库记录增加")
        else:
            print("   ⚠️ 数据库记录未增加（可能是更新现有记录）")
        
        if len(saved_records) == len(df):
            print("   ✅ 保存记录数与原始数据匹配")
        else:
            print(f"   ⚠️ 记录数不匹配: 原始{len(df)}条 vs 保存{len(saved_records)}条")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_fixed_historical_sync())
