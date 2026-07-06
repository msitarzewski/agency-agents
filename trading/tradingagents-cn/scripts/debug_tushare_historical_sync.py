#!/usr/bin/env python3
"""
调试Tushare历史数据同步问题
检查数据流的每个环节
"""
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from tradingagents.dataflows.providers.tushare_provider import TushareProvider
from app.services.historical_data_service import get_historical_data_service
from tradingagents.config.database_manager import get_mongodb_client

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_tushare_historical_sync():
    """调试Tushare历史数据同步的完整流程"""
    
    print("🔍 Tushare历史数据同步调试")
    print("=" * 60)
    
    # 测试股票代码
    test_symbol = "000001"
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    print(f"📊 测试参数:")
    print(f"   股票代码: {test_symbol}")
    print(f"   日期范围: {start_date} 到 {end_date}")
    print()
    
    # 1. 测试Tushare提供者
    print("1️⃣ 测试Tushare提供者")
    try:
        provider = TushareProvider()

        # 先连接提供者
        print("   🔄 连接Tushare提供者...")
        connect_success = await provider.connect()

        if not connect_success or not provider.is_available():
            print("   ❌ Tushare提供者连接失败或不可用")
            return

        print("   ✅ Tushare提供者连接成功")
        
        # 获取历史数据
        print(f"   🔄 获取 {test_symbol} 历史数据...")
        df = await provider.get_historical_data(test_symbol, start_date, end_date)
        
        if df is None or df.empty:
            print("   ❌ 未获取到历史数据")
            return
        
        print(f"   ✅ 获取到历史数据: {len(df)} 条记录")
        print(f"   📋 数据列: {list(df.columns)}")
        print(f"   📅 日期范围: {df.index.min()} 到 {df.index.max()}")
        
        # 显示前几条数据
        print("   📊 前3条数据:")
        for i, (date, row) in enumerate(df.head(3).iterrows()):
            print(f"     {date.strftime('%Y-%m-%d')}: 开盘={row.get('open', 'N/A')}, "
                  f"收盘={row.get('close', 'N/A')}, 成交量={row.get('volume', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Tushare提供者测试失败: {e}")
        return
    
    print()
    
    # 2. 测试历史数据服务
    print("2️⃣ 测试历史数据服务")
    try:
        # 先初始化数据库连接
        from app.core.database import init_database
        await init_database()

        service = await get_historical_data_service()
        print("   ✅ 历史数据服务初始化成功")
        
        # 保存数据前检查数据库状态
        client = get_mongodb_client()
        db = client.get_database('tradingagents')
        collection = db.stock_daily_quotes
        
        before_count = collection.count_documents({"symbol": test_symbol})
        print(f"   📊 保存前 {test_symbol} 记录数: {before_count}")
        
        # 保存历史数据
        print(f"   💾 保存 {test_symbol} 历史数据...")
        saved_count = await service.save_historical_data(
            symbol=test_symbol,
            data=df,
            data_source="tushare",
            market="CN",
            period="daily"
        )
        
        print(f"   ✅ 保存完成: {saved_count} 条记录")
        
        # 检查保存后的状态
        after_count = collection.count_documents({"symbol": test_symbol})
        print(f"   📊 保存后 {test_symbol} 记录数: {after_count}")
        print(f"   📈 新增记录数: {after_count - before_count}")
        
        # 查询最新保存的记录
        latest_records = list(collection.find(
            {"symbol": test_symbol, "data_source": "tushare"},
            sort=[("trade_date", -1)]
        ).limit(3))
        
        print("   📋 最新保存的3条记录:")
        for record in latest_records:
            trade_date = record.get('trade_date', 'N/A')
            close = record.get('close', 'N/A')
            volume = record.get('volume', 'N/A')
            print(f"     {trade_date}: 收盘={close}, 成交量={volume}")
        
        client.close()
        
    except Exception as e:
        print(f"   ❌ 历史数据服务测试失败: {e}")
        return
    
    print()
    
    # 3. 测试数据标准化
    print("3️⃣ 测试数据标准化")
    try:
        # 检查DataFrame的索引和列
        print(f"   📊 DataFrame信息:")
        print(f"     索引类型: {type(df.index)}")
        print(f"     索引名称: {df.index.name}")
        print(f"     列名: {list(df.columns)}")
        
        # 检查第一行数据
        if not df.empty:
            first_row = df.iloc[0]
            print(f"   📋 第一行数据:")
            for col in df.columns:
                value = first_row[col]
                print(f"     {col}: {value} ({type(value)})")
            
            # 检查日期处理
            if hasattr(df.index, 'strftime'):
                first_date = df.index[0]
                print(f"   📅 第一个日期: {first_date} ({type(first_date)})")
                print(f"   📅 格式化后: {first_date.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        print(f"   ❌ 数据标准化测试失败: {e}")
    
    print()
    
    # 4. 检查数据库连接和集合
    print("4️⃣ 检查数据库连接和集合")
    try:
        client = get_mongodb_client()
        db = client.get_database('tradingagents')
        
        # 检查集合是否存在
        collections = db.list_collection_names()
        if 'stock_daily_quotes' in collections:
            print("   ✅ stock_daily_quotes 集合存在")
        else:
            print("   ❌ stock_daily_quotes 集合不存在")
        
        # 检查索引
        collection = db.stock_daily_quotes
        indexes = list(collection.list_indexes())
        print(f"   📊 集合索引数量: {len(indexes)}")
        for idx in indexes:
            print(f"     - {idx.get('name', 'unnamed')}: {idx.get('key', {})}")
        
        client.close()
        
    except Exception as e:
        print(f"   ❌ 数据库检查失败: {e}")
    
    print()
    print("=" * 60)
    print("🎯 调试完成！")


if __name__ == "__main__":
    asyncio.run(debug_tushare_historical_sync())
