#!/usr/bin/env python3
"""
测试同步历史修复
验证：
1. 每次同步创建新的历史记录
2. 时区显示正确
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

async def test_multiple_sync_records():
    """测试多次同步创建多条记录"""
    print("=" * 60)
    print("🔄 测试多次同步创建多条历史记录")
    print("=" * 60)
    
    try:
        from app.core.database import init_db, get_mongo_db
        from app.services.multi_source_basics_sync_service import get_multi_source_sync_service
        
        # 初始化数据库
        await init_db()
        db = get_mongo_db()
        service = get_multi_source_sync_service()
        
        print("✅ 服务初始化成功")
        
        # 1. 清空现有历史记录（用于测试）
        print("\n1. 🧹 清空现有历史记录...")
        result = await db.sync_status.delete_many({"job": "stock_basics_multi_source"})
        print(f"   删除了 {result.deleted_count} 条记录")
        
        # 2. 运行第一次同步
        print("\n2. 🚀 运行第一次同步...")
        start_time_1 = datetime.now()
        print(f"   开始时间: {start_time_1.strftime('%Y-%m-%d %H:%M:%S')}")
        
        result1 = await service.run_full_sync(force=True)
        print(f"   ✅ 第一次同步完成: {result1.get('status')}")
        
        # 等待一秒确保时间戳不同
        await asyncio.sleep(2)
        
        # 3. 运行第二次同步
        print("\n3. 🚀 运行第二次同步...")
        start_time_2 = datetime.now()
        print(f"   开始时间: {start_time_2.strftime('%Y-%m-%d %H:%M:%S')}")
        
        result2 = await service.run_full_sync(force=True)
        print(f"   ✅ 第二次同步完成: {result2.get('status')}")
        
        # 等待一秒确保时间戳不同
        await asyncio.sleep(2)
        
        # 4. 运行第三次同步
        print("\n4. 🚀 运行第三次同步...")
        start_time_3 = datetime.now()
        print(f"   开始时间: {start_time_3.strftime('%Y-%m-%d %H:%M:%S')}")
        
        result3 = await service.run_full_sync(force=True)
        print(f"   ✅ 第三次同步完成: {result3.get('status')}")
        
        # 5. 检查历史记录数量
        print("\n5. 📊 检查历史记录...")
        total_records = await db.sync_status.count_documents({"job": "stock_basics_multi_source"})
        print(f"   📈 总历史记录数: {total_records}")
        
        if total_records >= 3:
            print("   ✅ 成功！每次同步都创建了新记录")
        else:
            print("   ❌ 失败！记录数量不正确")
        
        # 6. 检查时间戳
        print("\n6. 🕐 检查时间戳...")
        records = await db.sync_status.find(
            {"job": "stock_basics_multi_source"}
        ).sort("started_at", -1).to_list(length=5)
        
        print("   最近的同步记录:")
        for i, record in enumerate(records):
            started_at = record.get('started_at', '')
            finished_at = record.get('finished_at', '')
            status = record.get('status', '')
            
            # 解析时间戳
            if started_at:
                try:
                    start_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    start_local = start_dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    start_local = started_at
            else:
                start_local = "未知"
                
            if finished_at:
                try:
                    finish_dt = datetime.fromisoformat(finished_at.replace('Z', '+00:00'))
                    finish_local = finish_dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    finish_local = finished_at
            else:
                finish_local = "未完成"
            
            print(f"   {i+1}. 状态: {status}")
            print(f"      开始: {start_local}")
            print(f"      完成: {finish_local}")
            print(f"      总数: {record.get('total', 0)}")
            print()
        
        # 7. 验证时区
        print("7. 🌍 验证时区...")
        if records:
            latest_record = records[0]
            started_at = latest_record.get('started_at', '')
            
            if started_at:
                try:
                    # 解析时间戳
                    record_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    current_dt = datetime.now()
                    
                    # 计算时间差（应该很小，因为刚刚同步的）
                    time_diff = abs((current_dt - record_dt).total_seconds())
                    
                    print(f"   记录时间: {record_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   当前时间: {current_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   时间差: {time_diff:.1f} 秒")
                    
                    if time_diff < 300:  # 5分钟内
                        print("   ✅ 时区正确！")
                    else:
                        print("   ❌ 时区可能有问题")
                        
                except Exception as e:
                    print(f"   ❌ 时间解析失败: {e}")
        
        return {
            'total_records': total_records,
            'records_created': total_records >= 3,
            'timezone_correct': time_diff < 300 if 'time_diff' in locals() else False
        }
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_api_response():
    """测试API响应"""
    print("\n" + "=" * 60)
    print("🌐 测试API响应")
    print("=" * 60)
    
    try:
        from app.routers.multi_source_sync import get_sync_history
        
        # 测试获取历史记录
        print("📡 调用历史记录API...")
        response = await get_sync_history(page=1, page_size=5)
        
        if response.success:
            records = response.data['records']
            print(f"✅ API调用成功，获取到 {len(records)} 条记录")
            
            if records:
                latest = records[0]
                print(f"📊 最新记录:")
                print(f"   状态: {latest.get('status')}")
                print(f"   开始时间: {latest.get('started_at')}")
                print(f"   完成时间: {latest.get('finished_at')}")
                print(f"   总数: {latest.get('total')}")
                print(f"   数据源: {latest.get('data_sources_used', [])}")
        else:
            print(f"❌ API调用失败: {response.message}")
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")

if __name__ == "__main__":
    print("🧪 开始同步历史修复测试")
    print("=" * 60)
    
    result = asyncio.run(test_multiple_sync_records())
    
    if result:
        print(f"\n📊 测试结果摘要:")
        print(f"   历史记录总数: {result['total_records']}")
        print(f"   记录创建正确: {'✅' if result['records_created'] else '❌'}")
        print(f"   时区显示正确: {'✅' if result['timezone_correct'] else '❌'}")
        
        if result['records_created'] and result['timezone_correct']:
            print(f"\n🎉 所有测试通过！修复成功！")
        else:
            print(f"\n⚠️ 部分测试失败，需要进一步检查")
    
    # 测试API
    asyncio.run(test_api_response())
    
    print(f"\n📝 现在你可以在前端测试:")
    print(f"   1. 多次点击'强制重新同步'")
    print(f"   2. 每次同步后刷新历史记录")
    print(f"   3. 应该能看到多条历史记录")
    print(f"   4. 时间显示应该是正确的本地时间")
