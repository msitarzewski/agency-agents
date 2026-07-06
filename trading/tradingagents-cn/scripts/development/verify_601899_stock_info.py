#!/usr/bin/env python3
"""
验证股票 601899 的信息

检查：
1. MongoDB 中 601899 的数据
2. symbol 字段是否存在
3. 股票名称是否正确
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings


async def verify_stock_601899():
    """验证股票 601899 的信息"""
    print("\n" + "=" * 80)
    print("验证股票 601899 的信息")
    print("=" * 80)
    
    # 连接 MongoDB
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_basic_info"]
    
    # 查询 601899
    print("\n🔍 查询股票 601899...")
    
    # 方式1：使用 code 字段查询
    doc_by_code = await collection.find_one({"code": "601899"}, {"_id": 0})
    
    # 方式2：使用 symbol 字段查询
    doc_by_symbol = await collection.find_one({"symbol": "601899"}, {"_id": 0})
    
    # 方式3：使用 $or 查询
    doc_by_or = await collection.find_one(
        {"$or": [{"symbol": "601899"}, {"code": "601899"}]},
        {"_id": 0}
    )
    
    print("\n📊 查询结果：")
    print("-" * 80)
    
    # 显示结果
    if doc_by_code:
        print("\n✅ 使用 code 字段查询成功:")
        print(f"  code: {doc_by_code.get('code')}")
        print(f"  symbol: {doc_by_code.get('symbol')}")
        print(f"  name: {doc_by_code.get('name')}")
        print(f"  full_symbol: {doc_by_code.get('full_symbol')}")
        print(f"  industry: {doc_by_code.get('industry')}")
        print(f"  market: {doc_by_code.get('market')}")
    else:
        print("\n❌ 使用 code 字段查询失败")
    
    if doc_by_symbol:
        print("\n✅ 使用 symbol 字段查询成功:")
        print(f"  code: {doc_by_symbol.get('code')}")
        print(f"  symbol: {doc_by_symbol.get('symbol')}")
        print(f"  name: {doc_by_symbol.get('name')}")
        print(f"  full_symbol: {doc_by_symbol.get('full_symbol')}")
    else:
        print("\n❌ 使用 symbol 字段查询失败")
    
    if doc_by_or:
        print("\n✅ 使用 $or 查询成功:")
        print(f"  code: {doc_by_or.get('code')}")
        print(f"  symbol: {doc_by_or.get('symbol')}")
        print(f"  name: {doc_by_or.get('name')}")
        print(f"  full_symbol: {doc_by_or.get('full_symbol')}")
    else:
        print("\n❌ 使用 $or 查询失败")
    
    # 验证数据一致性
    print("\n" + "=" * 80)
    print("数据一致性验证")
    print("=" * 80)
    
    if doc_by_code and doc_by_symbol and doc_by_or:
        if (doc_by_code == doc_by_symbol == doc_by_or):
            print("\n✅ 三种查询方式返回的数据完全一致")
        else:
            print("\n⚠️ 三种查询方式返回的数据不一致")
    
    # 验证 symbol 字段
    if doc_by_code:
        if "symbol" in doc_by_code:
            print(f"\n✅ symbol 字段存在: {doc_by_code['symbol']}")
            if doc_by_code["symbol"] == doc_by_code["code"]:
                print("✅ symbol 和 code 字段值一致")
            else:
                print(f"⚠️ symbol ({doc_by_code['symbol']}) 和 code ({doc_by_code['code']}) 不一致")
        else:
            print("\n❌ symbol 字段不存在")
    
    # 验证股票名称
    if doc_by_code:
        name = doc_by_code.get("name")
        print(f"\n📝 股票名称: {name}")
        
        if name == "紫金矿业":
            print("✅ 股票名称正确（紫金矿业）")
        elif name == "中国神华":
            print("❌ 股票名称错误（显示为中国神华，应该是紫金矿业）")
        else:
            print(f"⚠️ 股票名称为: {name}")
    
    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(verify_stock_601899())

