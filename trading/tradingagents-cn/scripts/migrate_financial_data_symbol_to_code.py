#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 stock_financial_data 集合的 symbol 字段统一改为 code

背景：
- stock_basic_info 使用 code 字段（6位数字）
- stock_financial_data 使用 symbol 字段（6位数字）
- 为了统一，将 symbol 改为 code

步骤：
1. 为所有文档添加 code 字段（值为 symbol）
2. 删除 symbol 字段
3. 为 code 字段创建索引
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongo_db, init_database

async def main():
    await init_database()
    db = get_mongo_db()
    
    collection = db['stock_financial_data']
    
    print("🔍 检查集合状态...")
    total = await collection.count_documents({})
    print(f"  总记录数: {total}")
    
    # 检查有多少记录有 symbol 字段
    with_symbol = await collection.count_documents({"symbol": {"$exists": True}})
    print(f"  有 symbol 字段的记录: {with_symbol}")
    
    # 检查有多少记录有 code 字段
    with_code = await collection.count_documents({"code": {"$exists": True}})
    print(f"  有 code 字段的记录: {with_code}")
    
    if with_symbol == 0:
        print("\n✅ 所有记录都没有 symbol 字段，无需迁移")
        return
    
    print(f"\n📝 开始迁移 {with_symbol} 条记录...")
    
    # 批量更新：添加 code 字段
    print("  步骤1: 添加 code 字段...")
    result = await collection.update_many(
        {"symbol": {"$exists": True}, "code": {"$exists": False}},
        [{"$set": {"code": "$symbol"}}]
    )
    print(f"    ✅ 更新了 {result.modified_count} 条记录")

    # 删除旧的唯一索引
    print("  步骤2: 删除旧的 symbol 唯一索引...")
    try:
        await collection.drop_index("symbol_period_source_unique")
        print("    ✅ 索引删除成功")
    except Exception as e:
        print(f"    ⚠️ 索引删除失败（可能不存在）: {e}")

    # 删除 symbol 字段
    print("  步骤3: 删除 symbol 字段...")
    result = await collection.update_many(
        {"symbol": {"$exists": True}},
        {"$unset": {"symbol": ""}}
    )
    print(f"    ✅ 删除了 {result.modified_count} 条记录的 symbol 字段")

    # 创建新的唯一索引
    print("  步骤4: 创建新的 code 唯一索引...")
    try:
        await collection.create_index(
            [("code", 1), ("report_period", -1), ("data_source", 1)],
            unique=True,
            name="code_period_source_unique"
        )
        print("    ✅ 唯一索引创建成功")
    except Exception as e:
        print(f"    ⚠️ 唯一索引创建失败: {e}")

    # 创建普通索引
    print("  步骤5: 创建 code 字段索引...")
    try:
        await collection.create_index("code")
        print("    ✅ 索引创建成功")
    except Exception as e:
        print(f"    ⚠️ 索引创建失败（可能已存在）: {e}")
    
    # 验证
    print("\n🔍 验证迁移结果...")
    with_symbol_after = await collection.count_documents({"symbol": {"$exists": True}})
    with_code_after = await collection.count_documents({"code": {"$exists": True}})
    print(f"  有 symbol 字段的记录: {with_symbol_after}")
    print(f"  有 code 字段的记录: {with_code_after}")
    
    if with_symbol_after == 0 and with_code_after == total:
        print("\n✅ 迁移成功！")
    else:
        print("\n⚠️ 迁移可能不完整，请检查")
    
    # 显示示例数据
    print("\n📊 示例数据:")
    doc = await collection.find_one({"code": {"$exists": True}})
    if doc:
        print(f"  code: {doc.get('code')}")
        print(f"  full_symbol: {doc.get('full_symbol')}")
        print(f"  roe: {doc.get('roe')}")

if __name__ == '__main__':
    asyncio.run(main())

