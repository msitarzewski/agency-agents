"""
检查股票的 daily 数据
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def check_stock_daily_data(symbol: str = "000001"):
    """检查指定股票的 daily 数据"""
    
    # 连接 MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db.stock_daily_quotes
    
    code6 = symbol.zfill(6)
    
    print("=" * 80)
    print(f"📊 检查股票 {code6} 的 daily 数据")
    print("=" * 80)
    
    # 1. 检查是否有任何数据
    print(f"\n🔍 查询1：检查是否有任何数据（不限制 period）")
    query1 = {"symbol": code6}
    print(f"  查询条件: {query1}")
    
    count1 = await collection.count_documents(query1)
    print(f"  结果: {count1} 条记录")
    
    if count1 > 0:
        # 显示前5条
        cursor1 = collection.find(query1).limit(5)
        data1 = await cursor1.to_list(length=5)
        print(f"\n  前5条数据：")
        for i, doc in enumerate(data1, 1):
            print(f"    {i}. trade_date={doc.get('trade_date')}, period={doc.get('period')}, "
                  f"close={doc.get('close')}, data_source={doc.get('data_source')}")
    
    # 2. 检查 period="daily" 的数据
    print(f"\n🔍 查询2：检查 period='daily' 的数据")
    query2 = {"symbol": code6, "period": "daily"}
    print(f"  查询条件: {query2}")
    
    count2 = await collection.count_documents(query2)
    print(f"  结果: {count2} 条记录")
    
    if count2 > 0:
        # 显示前5条和最后5条
        cursor2 = collection.find(query2).sort("trade_date", 1).limit(5)
        data2 = await cursor2.to_list(length=5)
        print(f"\n  最早的5条数据：")
        for i, doc in enumerate(data2, 1):
            print(f"    {i}. trade_date={doc.get('trade_date')}, close={doc.get('close')}, "
                  f"data_source={doc.get('data_source')}")
        
        cursor3 = collection.find(query2).sort("trade_date", -1).limit(5)
        data3 = await cursor3.to_list(length=5)
        print(f"\n  最新的5条数据：")
        for i, doc in enumerate(data3, 1):
            print(f"    {i}. trade_date={doc.get('trade_date')}, close={doc.get('close')}, "
                  f"data_source={doc.get('data_source')}")
    
    # 3. 统计不同 period 的数据量
    print(f"\n📊 统计：{code6} 各周期的数据量")
    
    pipeline = [
        {"$match": {"symbol": code6}},
        {"$group": {"_id": "$period", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor4 = collection.aggregate(pipeline)
    stats = await cursor4.to_list(length=None)
    
    if stats:
        for stat in stats:
            print(f"  - {stat['_id']}: {stat['count']} 条")
    else:
        print(f"  ❌ 没有任何数据")
    
    # 4. 统计不同 data_source 的数据量
    print(f"\n📊 统计：{code6} 各数据源的数据量")
    
    pipeline2 = [
        {"$match": {"symbol": code6}},
        {"$group": {"_id": "$data_source", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor5 = collection.aggregate(pipeline2)
    stats2 = await cursor5.to_list(length=None)
    
    if stats2:
        for stat in stats2:
            print(f"  - {stat['_id']}: {stat['count']} 条")
    else:
        print(f"  ❌ 没有任何数据")
    
    # 5. 检查集合的索引
    print(f"\n📑 集合索引：")
    indexes = await collection.index_information()
    for index_name, index_info in indexes.items():
        print(f"  - {index_name}: {index_info.get('key')}")
    
    print("\n" + "=" * 80)
    print("✅ 检查完成")
    print("=" * 80)
    
    client.close()


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "000001"
    asyncio.run(check_stock_daily_data(symbol))

