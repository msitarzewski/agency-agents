#!/usr/bin/env python3
"""
测试同步用户反馈功能
模拟同步过程中的状态变化，验证用户反馈机制
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)

async def simulate_sync_with_feedback():
    """模拟同步过程，测试用户反馈"""
    print("=" * 60)
    print("🎭 模拟同步过程 - 测试用户反馈")
    print("=" * 60)
    
    try:
        from app.services.multi_source_basics_sync_service import get_multi_source_sync_service
        from app.core.database import init_db, get_mongo_db
        
        # 初始化数据库
        await init_db()
        service = get_multi_source_sync_service()
        db = get_mongo_db()
        
        print("✅ 服务初始化成功")
        
        # 1. 清空之前的状态
        print("\n1. 🧹 清空之前的状态...")
        await db.sync_status.delete_many({"job": "stock_basics_multi_source"})
        service._running = False
        print("   ✅ 状态已清空")
        
        # 2. 检查初始状态
        print("\n2. 📊 检查初始状态...")
        initial_status = await service.get_status()
        print(f"   📋 初始状态: {initial_status.get('status', 'unknown')}")
        
        # 3. 启动同步并监控状态变化
        print("\n3. 🚀 启动同步并监控状态变化...")
        
        # 启动同步任务
        sync_task = asyncio.create_task(service.run_full_sync(force=True))
        print("   🔄 同步任务已启动")
        
        # 监控状态变化
        previous_status = None
        previous_progress = 0
        monitor_count = 0
        
        while not sync_task.done() and monitor_count < 30:  # 最多监控30次
            await asyncio.sleep(2)  # 每2秒检查一次
            monitor_count += 1
            
            current_status = await service.get_status()
            status = current_status.get('status', 'unknown')
            total = current_status.get('total', 0)
            processed = current_status.get('inserted', 0) + current_status.get('updated', 0)
            progress = round((processed / total * 100) if total > 0 else 0, 1)
            
            # 检查状态变化
            if status != previous_status:
                print(f"   📈 状态变化: {previous_status} -> {status}")
                previous_status = status
            
            # 检查进度变化
            if progress != previous_progress and progress > 0:
                print(f"   📊 进度更新: {progress}% ({processed}/{total})")
                previous_progress = progress
            
            # 如果同步完成，退出监控
            if status in ['success', 'success_with_errors', 'failed']:
                print(f"   🎯 同步完成: {status}")
                break
        
        # 等待同步任务完成
        try:
            await asyncio.wait_for(sync_task, timeout=5)
        except asyncio.TimeoutError:
            print("   ⏰ 同步任务仍在运行，继续等待...")
            await sync_task
        
        # 4. 检查最终状态
        print("\n4. 📋 检查最终状态...")
        final_status = await service.get_status()
        
        status = final_status.get('status', 'unknown')
        total = final_status.get('total', 0)
        inserted = final_status.get('inserted', 0)
        updated = final_status.get('updated', 0)
        errors = final_status.get('errors', 0)
        sources = final_status.get('data_sources_used', [])
        started_at = final_status.get('started_at', '')
        finished_at = final_status.get('finished_at', '')
        
        print(f"   📊 最终状态: {status}")
        print(f"   📈 处理统计: 总数={total}, 新增={inserted}, 更新={updated}, 错误={errors}")
        print(f"   🔗 数据源: {', '.join(sources) if sources else '无'}")
        print(f"   🕐 开始时间: {started_at}")
        print(f"   🕑 结束时间: {finished_at}")
        
        # 5. 模拟前端用户反馈
        print("\n5. 🎭 模拟前端用户反馈...")
        
        if status == 'success':
            feedback_message = f"🎉 同步完成！处理了 {total} 条记录，新增 {inserted} 条，更新 {updated} 条"
            feedback_type = "成功通知"
        elif status == 'success_with_errors':
            feedback_message = f"⚠️ 同步完成但有错误！处理了 {total} 条记录，新增 {inserted} 条，更新 {updated} 条，错误 {errors} 条"
            feedback_type = "警告通知"
        elif status == 'failed':
            feedback_message = f"❌ 同步失败！{final_status.get('message', '未知错误')}"
            feedback_type = "错误通知"
        else:
            feedback_message = f"ℹ️ 同步状态: {status}"
            feedback_type = "信息通知"
        
        print(f"   📢 {feedback_type}: {feedback_message}")
        
        if sources:
            print(f"   📡 数据源通知: 使用的数据源: {', '.join(sources)}")
        
        # 6. 计算同步耗时
        if started_at and finished_at:
            try:
                start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(finished_at.replace('Z', '+00:00'))
                duration = (end_time - start_time).total_seconds()
                print(f"   ⏱️ 同步耗时: {duration:.1f} 秒")
            except Exception as e:
                print(f"   ⏱️ 无法计算耗时: {e}")
        
        print(f"\n🎉 用户反馈测试完成")
        
        return {
            'status': status,
            'total': total,
            'inserted': inserted,
            'updated': updated,
            'errors': errors,
            'sources': sources,
            'feedback_message': feedback_message,
            'feedback_type': feedback_type
        }
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_status_polling_simulation():
    """模拟前端状态轮询"""
    print("\n" + "=" * 60)
    print("🔄 模拟前端状态轮询")
    print("=" * 60)
    
    try:
        from app.services.multi_source_basics_sync_service import get_multi_source_sync_service
        
        service = get_multi_source_sync_service()
        
        print("📊 模拟前端每5秒轮询状态...")
        
        # 模拟轮询10次
        for i in range(10):
            status = await service.get_status()
            
            current_status = status.get('status', 'unknown')
            total = status.get('total', 0)
            processed = status.get('inserted', 0) + status.get('updated', 0)
            progress = round((processed / total * 100) if total > 0 else 0, 1)
            
            print(f"   轮询 #{i+1}: 状态={current_status}, 进度={progress}% ({processed}/{total})")
            
            # 如果不是运行状态，停止轮询
            if current_status != 'running':
                print(f"   🛑 检测到非运行状态，停止轮询")
                break
            
            await asyncio.sleep(1)  # 模拟轮询间隔
        
        print("🎯 状态轮询模拟完成")
        
    except Exception as e:
        print(f"❌ 轮询模拟失败: {e}")

if __name__ == "__main__":
    result = asyncio.run(simulate_sync_with_feedback())
    if result:
        print(f"\n📊 测试结果摘要:")
        print(f"   状态: {result['status']}")
        print(f"   处理: {result['total']} 条记录")
        print(f"   反馈: {result['feedback_message']}")
    
    asyncio.run(test_status_polling_simulation())
