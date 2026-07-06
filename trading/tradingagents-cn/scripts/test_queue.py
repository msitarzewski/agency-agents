#!/usr/bin/env python3
"""
测试队列系统的脚本
"""

import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapi.core.database import init_database, close_database
from webapi.core.redis_client import init_redis, close_redis
from webapi.services.queue_service import get_queue_service


async def test_queue_operations():
    """测试队列基本操作"""
    print("🧪 测试队列基本操作...")
    
    # 初始化连接
    await init_database()
    await init_redis()
    
    queue_service = get_queue_service()
    
    try:
        # 测试入队
        print("\n📥 测试任务入队...")
        task_id1 = await queue_service.enqueue_task(
            user_id="test_user_1",
            symbol="AAPL",
            params={"analysis_type": "deep"},
            priority=1
        )
        print(f"✅ 任务1已入队: {task_id1}")
        
        task_id2 = await queue_service.enqueue_task(
            user_id="test_user_1",
            symbol="TSLA",
            params={"analysis_type": "quick"},
            priority=2  # 更高优先级
        )
        print(f"✅ 任务2已入队: {task_id2} (高优先级)")
        
        # 测试队列状态
        print("\n📊 队列统计:")
        stats = await queue_service.stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # 测试用户队列状态
        print("\n👤 用户队列状态:")
        user_status = await queue_service.get_user_queue_status("test_user_1")
        print(json.dumps(user_status, indent=2, ensure_ascii=False))
        
        # 测试出队（模拟Worker）
        print("\n📤 测试任务出队...")
        task_data = await queue_service.dequeue_task("test_worker_1")
        if task_data:
            print(f"✅ 任务已出队: {task_data['id']} - {task_data['symbol']}")
            
            # 模拟处理完成
            await asyncio.sleep(1)
            
            # 确认任务完成
            await queue_service.ack_task(task_data['id'], success=True)
            print(f"✅ 任务已确认完成: {task_data['id']}")
        else:
            print("❌ 没有可用任务")
        
        # 再次检查统计
        print("\n📊 处理后队列统计:")
        stats = await queue_service.stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # 测试取消任务
        print("\n❌ 测试任务取消...")
        if task_id2:
            success = await queue_service.cancel_task(task_id2)
            if success:
                print(f"✅ 任务已取消: {task_id2}")
            else:
                print(f"❌ 取消任务失败: {task_id2}")
        
        # 最终统计
        print("\n📊 最终队列统计:")
        stats = await queue_service.stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理连接
        await close_database()
        await close_redis()


async def test_concurrent_limits():
    """测试并发限制"""
    print("\n🔒 测试并发限制...")
    
    await init_database()
    await init_redis()
    
    queue_service = get_queue_service()
    
    try:
        # 尝试超过用户并发限制
        print(f"📊 用户并发限制: {queue_service.user_concurrent_limit}")
        
        tasks = []
        for i in range(queue_service.user_concurrent_limit + 2):
            try:
                task_id = await queue_service.enqueue_task(
                    user_id="test_user_concurrent",
                    symbol=f"STOCK{i:02d}",
                    params={"test": True}
                )
                tasks.append(task_id)
                print(f"✅ 任务{i+1}已入队: {task_id}")
            except ValueError as e:
                print(f"❌ 任务{i+1}入队失败: {e}")
        
        print(f"\n📈 成功入队任务数: {len(tasks)}")
        
        # 模拟处理一些任务以释放并发槽位
        for i in range(2):
            task_data = await queue_service.dequeue_task(f"worker_{i}")
            if task_data:
                print(f"📤 Worker{i}获取任务: {task_data['id']}")
                # 不立即确认，保持处理中状态
        
        # 检查用户状态
        user_status = await queue_service.get_user_queue_status("test_user_concurrent")
        print(f"\n👤 用户状态: {json.dumps(user_status, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 并发测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await close_database()
        await close_redis()


async def main():
    """主测试函数"""
    print("🧪 TradingAgents队列系统测试")
    print("=" * 50)
    
    # 基本操作测试
    await test_queue_operations()
    
    print("\n" + "=" * 50)
    
    # 并发限制测试
    await test_concurrent_limits()
    
    print("\n✅ 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
