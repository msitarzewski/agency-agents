#!/usr/bin/env python3
"""
深度调试数据保存过程
逐步检查每个环节
"""
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from tradingagents.dataflows.providers.tushare_provider import TushareProvider
from app.services.historical_data_service import get_historical_data_service
from app.core.database import init_database
from tradingagents.config.database_manager import get_mongodb_client
from pymongo import ReplaceOne

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_data_save_process():
    """深度调试数据保存过程"""
    
    print("🔍 深度调试数据保存过程")
    print("=" * 60)
    
    # 测试参数
    test_symbol = "000002"  # 换个股票避免干扰
    start_date = "2024-01-01"
    end_date = "2024-01-05"  # 只测试几天
    
    print(f"📊 测试参数:")
    print(f"   股票代码: {test_symbol}")
    print(f"   日期范围: {start_date} 到 {end_date}")
    print()
    
    try:
        # 1. 初始化数据库
        print("1️⃣ 初始化数据库连接")
        await init_database()
        print("   ✅ 数据库连接成功")
        
        # 2. 连接Tushare提供者
        print("\n2️⃣ 连接Tushare提供者")
        provider = TushareProvider()
        connect_success = await provider.connect()
        if not connect_success:
            print("   ❌ Tushare连接失败")
            return
        print("   ✅ Tushare连接成功")
        
        # 3. 获取历史数据
        print(f"\n3️⃣ 获取 {test_symbol} 历史数据")
        df = await provider.get_historical_data(test_symbol, start_date, end_date)
        if df is None or df.empty:
            print("   ❌ 未获取到历史数据")
            return
        
        print(f"   ✅ 获取到 {len(df)} 条记录")
        print(f"   📋 列名: {list(df.columns)}")
        print(f"   📅 索引类型: {type(df.index)}")
        print(f"   📅 日期范围: {df.index.min()} 到 {df.index.max()}")
        
        # 显示原始数据
        print("   📊 原始数据前3条:")
        for i, (date, row) in enumerate(df.head(3).iterrows()):
            print(f"     {date}: {dict(row)}")
        
        # 4. 检查数据库状态（保存前）
        print(f"\n4️⃣ 检查数据库状态（保存前）")
        client = get_mongodb_client()
        db = client.get_database('tradingagents')
        collection = db.stock_daily_quotes
        
        before_count = collection.count_documents({"symbol": test_symbol})
        print(f"   📊 {test_symbol} 保存前记录数: {before_count}")
        
        # 5. 手动模拟数据标准化过程
        print(f"\n5️⃣ 手动模拟数据标准化")
        
        operations = []
        processed_records = []
        
        for i, (date, row) in enumerate(df.iterrows()):
            # 模拟 _standardize_record 方法
            now = datetime.utcnow()
            
            # 处理日期
            if hasattr(date, 'strftime'):
                trade_date = date.strftime('%Y-%m-%d')
            else:
                trade_date = str(date)[:10]
            
            doc = {
                "symbol": test_symbol,
                "full_symbol": f"{test_symbol}.SZ",
                "market": "CN",
                "trade_date": trade_date,
                "period": "daily",
                "data_source": "tushare",
                "created_at": now,
                "updated_at": now,
                "version": 1,
                "open": float(row.get('open', 0)),
                "high": float(row.get('high', 0)),
                "low": float(row.get('low', 0)),
                "close": float(row.get('close', 0)),
                "pre_close": float(row.get('pre_close', 0)),
                "volume": float(row.get('volume', 0)),
                "amount": float(row.get('amount', 0)),
                "change": float(row.get('change', 0)),
                "pct_chg": float(row.get('pct_chg', 0))
            }
            
            processed_records.append(doc)
            
            # 创建upsert操作
            filter_doc = {
                "symbol": doc["symbol"],
                "trade_date": doc["trade_date"],
                "data_source": doc["data_source"],
                "period": doc["period"]
            }
            
            operations.append(ReplaceOne(
                filter=filter_doc,
                replacement=doc,
                upsert=True
            ))
            
            if i < 3:  # 只显示前3条
                print(f"   📋 记录 {i+1}:")
                print(f"     过滤条件: {filter_doc}")
                print(f"     数据: symbol={doc['symbol']}, date={doc['trade_date']}, close={doc['close']}")
        
        print(f"   ✅ 准备了 {len(operations)} 个操作")
        
        # 6. 执行批量写入
        print(f"\n6️⃣ 执行批量写入")
        try:
            result = collection.bulk_write(operations)
            print(f"   ✅ 批量写入完成:")
            print(f"     插入数量: {result.upserted_count}")
            print(f"     更新数量: {result.modified_count}")
            print(f"     匹配数量: {result.matched_count}")
            print(f"     总操作数: {len(operations)}")
            
            # 检查写入结果
            if hasattr(result, 'upserted_ids'):
                print(f"     新插入的ID数量: {len(result.upserted_ids)}")
            
        except Exception as e:
            print(f"   ❌ 批量写入失败: {e}")
            return
        
        # 7. 检查数据库状态（保存后）
        print(f"\n7️⃣ 检查数据库状态（保存后）")
        after_count = collection.count_documents({"symbol": test_symbol})
        print(f"   📊 {test_symbol} 保存后记录数: {after_count}")
        print(f"   📈 新增记录数: {after_count - before_count}")
        
        # 查询刚保存的数据
        saved_records = list(collection.find(
            {"symbol": test_symbol, "data_source": "tushare"},
            sort=[("trade_date", 1)]
        ))
        
        print(f"   📋 数据库中的记录 ({len(saved_records)}条):")
        for record in saved_records:
            trade_date = record.get('trade_date', 'N/A')
            close = record.get('close', 'N/A')
            data_source = record.get('data_source', 'N/A')
            print(f"     {trade_date}: 收盘={close}, 数据源={data_source}")
        
        # 8. 对比原始数据和保存的数据
        print(f"\n8️⃣ 数据对比验证")
        if len(saved_records) == len(df):
            print("   ✅ 记录数量匹配")
        else:
            print(f"   ❌ 记录数量不匹配: 原始{len(df)}条 vs 保存{len(saved_records)}条")
        
        # 检查具体数据
        for i, (date, row) in enumerate(df.iterrows()):
            original_date = date.strftime('%Y-%m-%d')
            original_close = float(row.get('close', 0))
            
            # 查找对应的保存记录
            saved_record = next((r for r in saved_records if r.get('trade_date') == original_date), None)
            
            if saved_record:
                saved_close = saved_record.get('close', 0)
                if abs(original_close - saved_close) < 0.01:
                    print(f"   ✅ {original_date}: 数据一致 (收盘={original_close})")
                else:
                    print(f"   ❌ {original_date}: 数据不一致 原始={original_close} vs 保存={saved_close}")
            else:
                print(f"   ❌ {original_date}: 未找到保存的记录")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 调试过程失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 深度调试完成！")


if __name__ == "__main__":
    asyncio.run(debug_data_save_process())
