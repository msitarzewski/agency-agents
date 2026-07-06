#!/usr/bin/env python3
"""
验证扩展字段同步结果 - 使用直接 MongoDB 连接
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

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

def verify_extended_fields():
    """验证扩展字段的同步结果"""
    print("🔍 验证股票基础信息扩展字段同步结果")
    print("=" * 60)
    
    try:
        # 连接 MongoDB
        uri = build_mongo_uri()
        client = MongoClient(uri)
        dbname = os.getenv("MONGODB_DATABASE", "tradingagents")
        db = client[dbname]
        collection = db.stock_basic_info
        
        # 统计总记录数
        total_count = collection.count_documents({})
        print(f"📊 总股票数量: {total_count}")
        
        # 检查各字段的覆盖率
        fields_to_check = [
            "total_mv", "circ_mv", "pe", "pb", 
            "pe_ttm", "pb_mrq", "turnover_rate", "volume_ratio"
        ]
        
        print("\n📈 字段覆盖率统计:")
        print("-" * 60)
        for field in fields_to_check:
            count = collection.count_documents({field: {"$exists": True, "$ne": None}})
            coverage = (count / total_count * 100) if total_count > 0 else 0
            print(f"  {field:15} : {count:5d} 条 ({coverage:5.1f}%)")
        
        # 查看示例数据
        print("\n📋 示例股票数据 (前5条有完整财务数据的记录):")
        print("-" * 60)
        
        # 查找有完整财务数据的股票
        stocks = list(collection.find({
            "total_mv": {"$exists": True, "$ne": None},
            "pe": {"$exists": True, "$ne": None},
            "pb": {"$exists": True, "$ne": None}
        }).limit(5))
        
        for i, stock in enumerate(stocks, 1):
            print(f"\n  {i}. {stock.get('code')} - {stock.get('name')}")
            print(f"     行业: {stock.get('industry', 'N/A')}")
            print(f"     总市值: {stock.get('total_mv', 'N/A')} 亿元")
            print(f"     流通市值: {stock.get('circ_mv', 'N/A')} 亿元")
            print(f"     市盈率(PE): {stock.get('pe', 'N/A')}")
            print(f"     市净率(PB): {stock.get('pb', 'N/A')}")
            print(f"     换手率: {stock.get('turnover_rate', 'N/A')}%")
            print(f"     量比: {stock.get('volume_ratio', 'N/A')}")
        
        # 统计各行业的平均PE/PB
        print("\n📊 各行业平均估值指标 (前10个行业):")
        print("-" * 60)
        
        pipeline = [
            {"$match": {
                "industry": {"$exists": True, "$ne": ""},
                "pe": {"$exists": True, "$ne": None, "$gt": 0},
                "pb": {"$exists": True, "$ne": None, "$gt": 0}
            }},
            {"$group": {
                "_id": "$industry",
                "count": {"$sum": 1},
                "avg_pe": {"$avg": "$pe"},
                "avg_pb": {"$avg": "$pb"},
                "avg_total_mv": {"$avg": "$total_mv"}
            }},
            {"$match": {"count": {"$gte": 5}}},  # 至少5只股票
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        industries = list(collection.aggregate(pipeline))
        
        print(f"{'行业':15} {'股票数':>8} {'平均PE':>10} {'平均PB':>10} {'平均市值':>12}")
        print("-" * 60)
        for industry in industries:
            name = industry['_id'][:12] + "..." if len(industry['_id']) > 15 else industry['_id']
            print(f"{name:15} {industry['count']:8d} {industry['avg_pe']:10.2f} "
                  f"{industry['avg_pb']:10.2f} {industry['avg_total_mv']:10.1f}亿")
        
        print("\n✅ 扩展字段验证完成!")
        
        # 关闭连接
        client.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = verify_extended_fields()
    exit(0 if success else 1)
