"""
清理 stock_daily_quotes 集合中 trade_date 格式错误的数据
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def clean_invalid_trade_date():
    """清理 trade_date 格式错误的数据"""
    
    # 连接 MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db.stock_daily_quotes
    
    print("=" * 80)
    print("🧹 清理 trade_date 格式错误的数据")
    print("=" * 80)
    
    # 1. 统计总数据量
    total_count = await collection.count_documents({})
    print(f"\n📊 总数据量: {total_count} 条")
    
    # 2. 查找 trade_date 长度小于 8 的记录（正常应该是 YYYYMMDD 或 YYYY-MM-DD）
    print(f"\n🔍 查找 trade_date 格式错误的记录...")
    
    # 使用聚合管道查找长度异常的 trade_date
    pipeline = [
        {
            "$project": {
                "symbol": 1,
                "trade_date": 1,
                "period": 1,
                "data_source": 1,
                "trade_date_length": {"$strLenCP": {"$toString": "$trade_date"}}
            }
        },
        {
            "$match": {
                "trade_date_length": {"$lt": 8}
            }
        },
        {
            "$limit": 10
        }
    ]
    
    cursor = collection.aggregate(pipeline)
    invalid_records = await cursor.to_list(length=10)
    
    if invalid_records:
        print(f"\n  ❌ 找到 {len(invalid_records)} 条格式错误的记录（显示前10条）：")
        for i, doc in enumerate(invalid_records, 1):
            print(f"    {i}. symbol={doc.get('symbol')}, trade_date={doc.get('trade_date')}, "
                  f"period={doc.get('period')}, data_source={doc.get('data_source')}, "
                  f"length={doc.get('trade_date_length')}")
    else:
        print(f"\n  ✅ 没有找到格式错误的记录")
        client.close()
        return
    
    # 3. 统计格式错误的记录数量
    pipeline2 = [
        {
            "$project": {
                "trade_date_length": {"$strLenCP": {"$toString": "$trade_date"}}
            }
        },
        {
            "$match": {
                "trade_date_length": {"$lt": 8}
            }
        },
        {
            "$count": "total"
        }
    ]
    
    cursor2 = collection.aggregate(pipeline2)
    count_result = await cursor2.to_list(length=1)
    invalid_count = count_result[0]["total"] if count_result else 0
    
    print(f"\n📊 格式错误的记录总数: {invalid_count} 条")
    
    # 4. 询问用户是否删除
    print(f"\n⚠️ 警告：即将删除 {invalid_count} 条格式错误的记录")
    print(f"  这些记录的 trade_date 长度小于 8，无法用于正常查询")
    
    confirm = input(f"\n是否继续删除？(yes/no): ")
    
    if confirm.lower() != "yes":
        print(f"\n❌ 取消删除操作")
        client.close()
        return
    
    # 5. 删除格式错误的记录
    print(f"\n🗑️ 开始删除...")
    
    # 使用聚合管道找到所有格式错误的记录的 _id
    pipeline3 = [
        {
            "$project": {
                "_id": 1,
                "trade_date_length": {"$strLenCP": {"$toString": "$trade_date"}}
            }
        },
        {
            "$match": {
                "trade_date_length": {"$lt": 8}
            }
        }
    ]
    
    cursor3 = collection.aggregate(pipeline3)
    invalid_ids = [doc["_id"] async for doc in cursor3]
    
    if invalid_ids:
        result = await collection.delete_many({"_id": {"$in": invalid_ids}})
        print(f"\n✅ 删除完成: {result.deleted_count} 条记录")
    else:
        print(f"\n⚠️ 没有找到需要删除的记录")
    
    # 6. 验证删除结果
    new_total_count = await collection.count_documents({})
    print(f"\n📊 删除后的总数据量: {new_total_count} 条")
    print(f"📊 删除的数据量: {total_count - new_total_count} 条")
    
    print("\n" + "=" * 80)
    print("✅ 清理完成")
    print("=" * 80)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(clean_invalid_trade_date())

