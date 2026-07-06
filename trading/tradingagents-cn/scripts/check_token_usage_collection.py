#!/usr/bin/env python3
"""
检查 token_usage 集合中的记录
"""

import asyncio
import sys
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def main():
    """主函数"""
    print("=" * 60)
    print("📊 检查 token_usage 集合")
    print("=" * 60)

    try:
        # 直接连接 MongoDB
        mongo_host = os.getenv("MONGODB_HOST", "localhost")
        mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongo_username = os.getenv("MONGODB_USERNAME", "admin")
        mongo_password = os.getenv("MONGODB_PASSWORD", "tradingagents123")
        mongo_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
        db_name = os.getenv("MONGODB_DATABASE", "tradingagents")

        mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/?authSource={mongo_auth_source}"

        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]
        collection = db["token_usage"]
        
        # 统计记录数
        total_count = await collection.count_documents({})
        print(f"\n✅ 总记录数: {total_count}")
        
        if total_count == 0:
            print("\n⚠️  集合为空，没有 token 使用记录")
            return
        
        # 获取最近的 5 条记录
        print("\n📋 最近的 5 条记录:")
        print("-" * 60)
        
        cursor = collection.find().sort("_created_at", -1).limit(5)
        records = await cursor.to_list(length=5)
        
        for i, record in enumerate(records, 1):
            print(f"\n记录 {i}:")
            print(f"  • 时间: {record.get('timestamp', 'N/A')}")
            print(f"  • 供应商: {record.get('provider', 'N/A')}")
            print(f"  • 模型: {record.get('model_name', 'N/A')}")
            print(f"  • 输入 Token: {record.get('input_tokens', 0)}")
            print(f"  • 输出 Token: {record.get('output_tokens', 0)}")
            print(f"  • 成本: ¥{record.get('cost', 0):.6f}")
            print(f"  • 会话 ID: {record.get('session_id', 'N/A')}")
            print(f"  • 分析类型: {record.get('analysis_type', 'N/A')}")
        
        # 按供应商统计
        print("\n" + "=" * 60)
        print("📊 按供应商统计:")
        print("-" * 60)
        
        pipeline = [
            {
                "$group": {
                    "_id": "$provider",
                    "count": {"$sum": 1},
                    "total_input_tokens": {"$sum": "$input_tokens"},
                    "total_output_tokens": {"$sum": "$output_tokens"},
                    "total_cost": {"$sum": "$cost"}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        cursor = collection.aggregate(pipeline)
        stats = await cursor.to_list(length=None)
        
        for stat in stats:
            provider = stat["_id"]
            count = stat["count"]
            total_input = stat["total_input_tokens"]
            total_output = stat["total_output_tokens"]
            total_cost = stat["total_cost"]
            
            print(f"\n{provider}:")
            print(f"  • 请求数: {count}")
            print(f"  • 总输入 Token: {total_input:,}")
            print(f"  • 总输出 Token: {total_output:,}")
            print(f"  • 总成本: ¥{total_cost:.6f}")
        
        print("\n" + "=" * 60)
        print("✅ 检查完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

