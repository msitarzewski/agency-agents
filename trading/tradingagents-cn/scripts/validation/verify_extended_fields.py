#!/usr/bin/env python3
"""
验证扩展字段同步结果
检查 stock_basic_info 集合中新增的财务指标字段
"""
import asyncio
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import get_mongo_db


async def verify_extended_fields():
    """验证扩展字段的同步结果"""
    print("🔍 验证股票基础信息扩展字段同步结果")
    print("=" * 60)
    
    try:
        db = get_mongo_db()
        collection = db.stock_basic_info
        
        # 统计总记录数
        total_count = await collection.count_documents({})
        print(f"📊 总股票数量: {total_count}")
        
        # 检查各字段的覆盖率
        field_stats = {}
        fields_to_check = [
            "total_mv", "circ_mv", "pe", "pb", 
            "pe_ttm", "pb_mrq", "turnover_rate", "volume_ratio"
        ]
        
        for field in fields_to_check:
            count = await collection.count_documents({field: {"$exists": True, "$ne": None}})
            coverage = (count / total_count * 100) if total_count > 0 else 0
            field_stats[field] = {"count": count, "coverage": coverage}
        
        print("\n📈 字段覆盖率统计:")
        print("-" * 60)
        for field, stats in field_stats.items():
            print(f"  {field:15} : {stats['count']:5d} 条 ({stats['coverage']:5.1f}%)")
        
        # 查看示例数据
        print("\n📋 示例股票数据 (前5条有完整财务数据的记录):")
        print("-" * 60)
        
        # 查找有完整财务数据的股票
        pipeline = [
            {"$match": {
                "total_mv": {"$exists": True, "$ne": None},
                "pe": {"$exists": True, "$ne": None},
                "pb": {"$exists": True, "$ne": None}
            }},
            {"$limit": 5}
        ]
        
        cursor = collection.aggregate(pipeline)
        stocks = await cursor.to_list(length=5)
        
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
        
        cursor = collection.aggregate(pipeline)
        industries = await cursor.to_list(length=10)
        
        print(f"{'行业':15} {'股票数':>8} {'平均PE':>10} {'平均PB':>10} {'平均市值':>12}")
        print("-" * 60)
        for industry in industries:
            name = industry['_id'][:12] + "..." if len(industry['_id']) > 15 else industry['_id']
            print(f"{name:15} {industry['count']:8d} {industry['avg_pe']:10.2f} "
                  f"{industry['avg_pb']:10.2f} {industry['avg_total_mv']:10.1f}亿")
        
        print("\n✅ 扩展字段验证完成!")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify_extended_fields())
