#!/usr/bin/env python3
"""
分析股票数量差异 - 为什么有10854条记录而不是5427支股票
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import Counter

# 加载环境变量
load_dotenv()

def build_mongo_uri():
    host = os.getenv("MONGODB_HOST", "localhost")
    port = int(os.getenv("MONGODB_PORT", "27017"))
    db = os.getenv("MONGODB_DATABASE", "tradingagents")
    user = os.getenv("MONGODB_USERNAME", "")
    pwd = os.getenv("MONGODB_PASSWORD", "")
    auth_src = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    if user and pwd:
        return f"mongodb://{user}:{pwd}@{host}:{port}/{db}?authSource={auth_src}"
    return f"mongodb://{host}:{port}/{db}"

def analyze_stock_count():
    """分析股票数量差异"""
    print("🔍 分析股票数量差异")
    print("=" * 60)
    
    try:
        # 连接 MongoDB
        uri = build_mongo_uri()
        client = MongoClient(uri)
        dbname = os.getenv("MONGODB_DATABASE", "tradingagents")
        db = client[dbname]
        collection = db.stock_basic_info
        
        # 总记录数
        total_count = collection.count_documents({})
        print(f"📊 总记录数: {total_count}")
        
        # 按数据源分组统计
        print("\n📈 按数据源统计:")
        print("-" * 40)
        source_stats = list(collection.aggregate([
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        for stat in source_stats:
            print(f"  {stat['_id']:15}: {stat['count']:6d} 条")
        
        # 按市场分组统计
        print("\n📈 按市场统计:")
        print("-" * 40)
        market_stats = list(collection.aggregate([
            {"$group": {"_id": "$market", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        for stat in market_stats:
            market = stat['_id'] if stat['_id'] else "未知"
            print(f"  {market:15}: {stat['count']:6d} 条")
        
        # 按交易所统计
        print("\n📈 按交易所统计:")
        print("-" * 40)
        sse_stats = list(collection.aggregate([
            {"$group": {"_id": "$sse", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        for stat in sse_stats:
            sse = stat['_id'] if stat['_id'] else "未知"
            print(f"  {sse:15}: {stat['count']:6d} 条")
        
        # 按股票类型统计
        print("\n📈 按股票类型统计:")
        print("-" * 40)
        sec_stats = list(collection.aggregate([
            {"$group": {"_id": "$sec", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        for stat in sec_stats:
            sec = stat['_id'] if stat['_id'] else "未知"
            print(f"  {sec:15}: {stat['count']:6d} 条")
        
        # 检查是否有重复的股票代码
        print("\n🔍 检查重复股票代码:")
        print("-" * 40)
        duplicate_codes = list(collection.aggregate([
            {"$group": {"_id": "$code", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]))
        
        if duplicate_codes:
            print("发现重复股票代码:")
            for dup in duplicate_codes:
                print(f"  代码 {dup['_id']}: {dup['count']} 条记录")
                # 查看重复记录的详情
                records = list(collection.find({"code": dup['_id']}).limit(3))
                for i, record in enumerate(records, 1):
                    print(f"    {i}. {record.get('name', 'N/A')} - {record.get('market', 'N/A')} - {record.get('source', 'N/A')}")
        else:
            print("✅ 未发现重复股票代码")
        
        # 分析最近更新时间 (updated_at 是字符串格式)
        print("\n📅 最近更新时间分析:")
        print("-" * 40)
        update_stats = list(collection.aggregate([
            {"$group": {
                "_id": {"$substr": ["$updated_at", 0, 10]},  # 提取日期部分 YYYY-MM-DD
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 5}
        ]))

        for stat in update_stats:
            date = stat['_id'] if stat['_id'] else "未知日期"
            print(f"  {date}: {stat['count']:6d} 条")
        
        # 查看一些示例记录
        print("\n📋 示例记录 (最新10条):")
        print("-" * 60)
        recent_records = list(collection.find({}).sort("updated_at", -1).limit(10))
        for i, record in enumerate(recent_records, 1):
            print(f"  {i:2d}. {record.get('code', 'N/A'):8} - {record.get('name', 'N/A'):15} - "
                  f"{record.get('market', 'N/A'):8} - {record.get('source', 'N/A')}")
        
        print("\n✅ 分析完成!")
        
        # 关闭连接
        client.close()
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = analyze_stock_count()
    exit(0 if success else 1)
