#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查报告详情中的字段"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def check_report():
    """检查报告详情"""
    # 连接MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.tradingagents
    
    report_id = "68e9a2e425d0ae5962b54318"
    
    print(f"🔍 查询报告: {report_id}")
    
    # 尝试多种查询方式
    queries = [
        {"_id": ObjectId(report_id)},
        {"analysis_id": report_id},
        {"task_id": report_id}
    ]
    
    doc = None
    for query in queries:
        try:
            doc = await db.analysis_reports.find_one(query)
            if doc:
                print(f"✅ 找到报告 (查询: {query})")
                break
        except Exception as e:
            print(f"⚠️ 查询失败 {query}: {e}")
    
    if not doc:
        print("❌ 未找到报告，尝试从 analysis_tasks 查询")
        doc = await db.analysis_tasks.find_one(
            {"$or": [{"task_id": report_id}, {"result.analysis_id": report_id}]}
        )
        if doc:
            print("✅ 从 analysis_tasks 找到")
            doc = doc.get("result", {})
    
    if not doc:
        print("❌ 完全找不到报告")
        return
    
    print(f"\n📊 报告基本信息:")
    print(f"  - stock_symbol: {doc.get('stock_symbol', 'N/A')}")
    print(f"  - analysis_id: {doc.get('analysis_id', 'N/A')}")
    print(f"  - status: {doc.get('status', 'N/A')}")
    
    reports = doc.get("reports", {})
    print(f"\n📋 报告字段 (共 {len(reports)} 个):")
    for key in reports.keys():
        content = reports[key]
        if isinstance(content, str):
            print(f"  ✅ {key}: {len(content)} 字符")
        else:
            print(f"  ⚠️ {key}: {type(content)}")
    
    print(f"\n🔍 检查是否有新增字段:")
    expected_fields = [
        'bull_researcher',
        'bear_researcher',
        'research_team_decision',
        'risky_analyst',
        'safe_analyst',
        'neutral_analyst',
        'risk_management_decision'
    ]
    
    for field in expected_fields:
        if field in reports:
            print(f"  ✅ {field}: 存在")
        else:
            print(f"  ❌ {field}: 缺失")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_report())

