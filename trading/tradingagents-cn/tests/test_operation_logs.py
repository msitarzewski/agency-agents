#!/usr/bin/env python3
"""
测试操作日志功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, get_mongo_db
from app.services.operation_log_service import log_operation, get_operation_log_service
from app.models.operation_log import ActionType

async def test_operation_logs():
    """测试操作日志功能"""
    print("🧪 开始测试操作日志功能...")
    
    try:
        # 初始化数据库
        await init_db()
        print("✅ 数据库初始化成功")
        
        # 获取服务实例
        service = get_operation_log_service()
        print("✅ 操作日志服务获取成功")
        
        # 测试1: 创建操作日志
        print("\n📝 测试1: 创建操作日志")
        log_id = await log_operation(
            user_id="admin",
            username="admin",
            action_type=ActionType.USER_LOGIN,
            action="测试用户登录",
            details={"test": True, "ip": "127.0.0.1"},
            success=True,
            duration_ms=100,
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        print(f"✅ 创建日志成功，ID: {log_id}")
        
        # 测试2: 创建更多测试日志
        print("\n📝 测试2: 创建更多测试日志")
        test_logs = [
            {
                "action_type": ActionType.STOCK_ANALYSIS,
                "action": "分析股票 000001",
                "details": {"stock_code": "000001", "analysis_type": "comprehensive"},
                "success": True,
                "duration_ms": 1500
            },
            {
                "action_type": ActionType.CONFIG_MANAGEMENT,
                "action": "更新大模型配置",
                "details": {"provider": "openai", "model": "gpt-4"},
                "success": False,
                "error_message": "API密钥验证失败",
                "duration_ms": 500
            },
            {
                "action_type": ActionType.DATABASE_OPERATION,
                "action": "数据库备份",
                "details": {"backup_type": "full", "size_mb": 150},
                "success": True,
                "duration_ms": 3000
            }
        ]
        
        for i, log_data in enumerate(test_logs):
            log_id = await log_operation(
                user_id="admin",
                username="admin",
                **log_data,
                ip_address="127.0.0.1",
                user_agent="Test Agent"
            )
            print(f"✅ 创建测试日志 {i+1} 成功，ID: {log_id}")
        
        # 测试3: 查询操作日志
        print("\n📋 测试3: 查询操作日志")
        from app.models.operation_log import OperationLogQuery
        
        query = OperationLogQuery(page=1, page_size=10)
        logs, total = await service.get_logs(query)
        print(f"✅ 查询成功，总数: {total}, 返回: {len(logs)} 条")
        
        for log in logs[:3]:  # 显示前3条
            print(f"  - {log.timestamp} | {log.username} | {log.action} | {'✅' if log.success else '❌'}")
        
        # 测试4: 获取统计信息
        print("\n📊 测试4: 获取统计信息")
        stats = await service.get_stats(days=30)
        print(f"✅ 统计信息获取成功:")
        print(f"  - 总日志数: {stats.total_logs}")
        print(f"  - 成功日志: {stats.success_logs}")
        print(f"  - 失败日志: {stats.failed_logs}")
        print(f"  - 成功率: {stats.success_rate}%")
        print(f"  - 操作类型分布: {stats.action_type_distribution}")
        
        # 测试5: 检查数据库中的记录
        print("\n🔍 测试5: 检查数据库记录")
        db = get_mongo_db()
        count = await db.operation_logs.count_documents({})
        print(f"✅ 数据库中共有 {count} 条操作日志记录")
        
        # 显示最新的几条记录
        cursor = db.operation_logs.find().sort("timestamp", -1).limit(3)
        recent_logs = await cursor.to_list(length=3)
        print("📝 最新的3条记录:")
        for log in recent_logs:
            print(f"  - {log.get('timestamp')} | {log.get('username')} | {log.get('action')} | {log.get('success')}")
        
        print("\n🎉 所有测试完成！操作日志功能正常工作。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_operation_logs())
