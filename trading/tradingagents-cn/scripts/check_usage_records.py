#!/usr/bin/env python3
"""
检查使用记录数据
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def main():
    """检查使用记录"""
    print("=" * 60)
    print("🔍 检查使用记录数据")
    print("=" * 60)
    
    # 1. 初始化数据库
    print("\n1️⃣ 初始化数据库连接...")
    from app.core.database import init_db, get_mongo_db
    await init_db()
    print("✅ 数据库连接成功")
    
    # 2. 检查 usage_records 集合
    print("\n2️⃣ 检查 usage_records 集合...")
    db = get_mongo_db()
    
    # 统计记录数
    count = await db.usage_records.count_documents({})
    print(f"📊 总记录数: {count}")
    
    if count > 0:
        # 显示最近的 5 条记录
        print("\n📋 最近的 5 条记录：")
        cursor = db.usage_records.find().sort("timestamp", -1).limit(5)
        async for doc in cursor:
            print(f"\n  • 时间: {doc.get('timestamp')}")
            print(f"    供应商: {doc.get('provider')}")
            print(f"    模型: {doc.get('model_name')}")
            print(f"    输入 Token: {doc.get('input_tokens')}")
            print(f"    输出 Token: {doc.get('output_tokens')}")
            print(f"    成本: ¥{doc.get('cost', 0):.4f}")
    else:
        print("⚠️  没有找到任何使用记录")
        print("\n💡 可能的原因：")
        print("  1. Token 跟踪功能未启用")
        print("  2. 还没有进行过分析")
        print("  3. LLM 适配器没有正确记录 token 使用")
    
    # 3. 检查 tradingagents 的 MongoDB 存储
    print("\n3️⃣ 检查 tradingagents 的 usage_records 集合...")
    try:
        from tradingagents.config.mongodb_storage import MongoDBStorage
        from tradingagents.config.config_manager import config_manager
        
        # 检查是否启用了 MongoDB 存储
        if config_manager.mongodb_storage and config_manager.mongodb_storage.is_connected():
            records = config_manager.mongodb_storage.load_usage_records(limit=5)
            print(f"📊 TradingAgents 记录数: {len(records)}")
            
            if records:
                print("\n📋 最近的 5 条记录：")
                for record in records[:5]:
                    print(f"\n  • 时间: {record.timestamp}")
                    print(f"    供应商: {record.provider}")
                    print(f"    模型: {record.model_name}")
                    print(f"    输入 Token: {record.input_tokens}")
                    print(f"    输出 Token: {record.output_tokens}")
                    print(f"    成本: ¥{record.cost:.4f}")
            else:
                print("⚠️  TradingAgents 也没有记录")
        else:
            print("⚠️  TradingAgents MongoDB 存储未连接")
    except Exception as e:
        print(f"❌ 检查 TradingAgents 存储失败: {e}")
    
    # 4. 检查配置
    print("\n4️⃣ 检查配置...")
    try:
        from app.services.config_service import config_service
        config = await config_service.get_system_config()
        
        if config and config.system_settings:
            enable_cost_tracking = config.system_settings.get('enable_cost_tracking', True)
            print(f"📝 成本跟踪启用状态: {enable_cost_tracking}")
        else:
            print("⚠️  无法获取系统配置")
    except Exception as e:
        print(f"❌ 检查配置失败: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

