#!/usr/bin/env python3
"""
测试 Token 跟踪功能
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def main():
    """测试 token 跟踪"""
    print("=" * 60)
    print("🧪 测试 Token 跟踪功能")
    print("=" * 60)
    
    # 1. 初始化数据库
    print("\n1️⃣ 初始化数据库连接...")
    from app.core.database import init_db, get_mongo_db
    await init_db()
    print("✅ 数据库连接成功")
    
    # 2. 创建测试使用记录
    print("\n2️⃣ 创建测试使用记录...")
    from app.services.usage_statistics_service import UsageStatisticsService
    from app.models.config import UsageRecord
    
    usage_service = UsageStatisticsService()
    
    # 创建测试记录
    test_record = UsageRecord(
        timestamp=datetime.now().isoformat(),
        provider="dashscope",
        model_name="qwen-plus",
        input_tokens=2000,
        output_tokens=1000,
        cost=0.006,  # 假设成本
        session_id="test_session_001",
        analysis_type="stock_analysis",
        stock_code="000001"
    )
    
    success = await usage_service.add_usage_record(test_record)
    
    if success:
        print("✅ 测试记录创建成功")
    else:
        print("❌ 测试记录创建失败")
        return
    
    # 3. 验证记录是否保存
    print("\n3️⃣ 验证记录是否保存...")
    db = get_mongo_db()
    count = await db.usage_records.count_documents({})
    print(f"📊 总记录数: {count}")
    
    if count > 0:
        # 显示最近的记录
        print("\n📋 最近的记录：")
        cursor = db.usage_records.find().sort("timestamp", -1).limit(1)
        async for doc in cursor:
            print(f"  • 时间: {doc.get('timestamp')}")
            print(f"    供应商: {doc.get('provider')}")
            print(f"    模型: {doc.get('model_name')}")
            print(f"    股票代码: {doc.get('stock_code')}")
            print(f"    输入 Token: {doc.get('input_tokens')}")
            print(f"    输出 Token: {doc.get('output_tokens')}")
            print(f"    成本: ¥{doc.get('cost', 0):.4f}")
    
    # 4. 测试统计功能
    print("\n4️⃣ 测试统计功能...")
    stats = await usage_service.get_usage_statistics(days=7)
    
    print(f"📊 统计结果：")
    print(f"  • 总请求数: {stats.total_requests}")
    print(f"  • 总输入 Token: {stats.total_input_tokens}")
    print(f"  • 总输出 Token: {stats.total_output_tokens}")
    print(f"  • 总成本: ¥{stats.total_cost:.4f}")
    
    if stats.by_provider:
        print(f"\n  按供应商统计：")
        for provider, data in stats.by_provider.items():
            print(f"    • {provider}: {data.get('requests', 0)} 次请求, ¥{data.get('cost', 0):.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Token 跟踪功能测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

