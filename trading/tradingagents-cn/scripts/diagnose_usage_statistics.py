"""
诊断使用统计与计费问题
检查数据是否正常保存到数据库
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def main():
    print("=" * 80)
    print("🔍 使用统计与计费诊断工具")
    print("=" * 80)
    
    # 1. 检查数据库连接
    print("\n1️⃣ 检查数据库连接...")
    try:
        from app.core.database import init_db, get_mongo_db
        await init_db()
        db = get_mongo_db()
        print("✅ MongoDB 连接成功")
        print(f"   数据库名称: {db.name}")
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        return
    
    # 2. 检查 token_usage 集合
    print("\n2️⃣ 检查 token_usage 集合...")
    try:
        collection = db["token_usage"]
        count = await collection.count_documents({})
        print(f"✅ token_usage 集合存在")
        print(f"   记录总数: {count}")
        
        if count == 0:
            print("   ⚠️  集合为空，没有任何使用记录")
        else:
            # 显示最近的记录
            latest = await collection.find_one(sort=[("timestamp", -1)])
            if latest:
                print(f"   最新记录时间: {latest.get('timestamp', 'N/A')}")
                print(f"   供应商: {latest.get('provider', 'N/A')}")
                print(f"   模型: {latest.get('model_name', 'N/A')}")
    except Exception as e:
        print(f"❌ 检查集合失败: {e}")
    
    # 3. 检查最近7天的数据
    print("\n3️⃣ 检查最近7天的数据...")
    try:
        from app.services.usage_statistics_service import UsageStatisticsService
        usage_service = UsageStatisticsService()
        
        stats = await usage_service.get_usage_statistics(days=7)
        
        print(f"   总请求数: {stats.total_requests}")
        print(f"   总输入 Token: {stats.total_input_tokens:,}")
        print(f"   总输出 Token: {stats.total_output_tokens:,}")
        print(f"   总成本: ¥{stats.total_cost:.4f}")
        
        if stats.total_requests == 0:
            print("   ⚠️  最近7天没有使用记录")
        else:
            print("\n   按供应商统计:")
            for provider, provider_stats in stats.by_provider.items():
                print(f"     • {provider}: {provider_stats['requests']} 次请求, ¥{provider_stats['cost']:.4f}")
    except Exception as e:
        print(f"❌ 获取统计数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 检查配置文件中的成本跟踪设置
    print("\n4️⃣ 检查配置文件...")
    try:
        from tradingagents.config.config_manager import config_manager
        settings = config_manager.load_settings()
        
        cost_tracking = settings.get("enable_cost_tracking", True)
        print(f"   成本跟踪启用: {cost_tracking}")
        
        if not cost_tracking:
            print("   ⚠️  成本跟踪已禁用！")
            print("   💡 解决方案: 在配置管理中启用成本跟踪")
    except Exception as e:
        print(f"❌ 检查配置失败: {e}")
    
    # 5. 检查定价配置
    print("\n5️⃣ 检查定价配置...")
    try:
        from tradingagents.config.config_manager import config_manager
        pricing_configs = config_manager.load_pricing()
        
        print(f"   定价配置数量: {len(pricing_configs)}")
        
        if len(pricing_configs) == 0:
            print("   ⚠️  没有定价配置！")
            print("   💡 解决方案: 在 config/pricing.json 中添加模型定价")
        else:
            print("\n   已配置的模型:")
            for pricing in pricing_configs[:5]:  # 只显示前5个
                print(f"     • {pricing.provider}/{pricing.model_name}: "
                      f"输入 ¥{pricing.input_price_per_1k}/1k, "
                      f"输出 ¥{pricing.output_price_per_1k}/1k")
    except Exception as e:
        print(f"❌ 检查定价配置失败: {e}")
    
    # 6. 测试添加使用记录
    print("\n6️⃣ 测试添加使用记录...")
    try:
        from app.services.usage_statistics_service import UsageStatisticsService
        from app.models.config import UsageRecord
        
        usage_service = UsageStatisticsService()
        
        test_record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            provider="test_provider",
            model_name="test_model",
            input_tokens=100,
            output_tokens=50,
            cost=0.001,
            session_id="diagnostic_test",
            analysis_type="diagnostic",
            stock_code="TEST"
        )
        
        success = await usage_service.add_usage_record(test_record)
        
        if success:
            print("✅ 测试记录添加成功")
            
            # 验证记录是否真的保存了
            collection = db["token_usage"]
            test_count = await collection.count_documents({"session_id": "diagnostic_test"})
            print(f"   验证: 找到 {test_count} 条测试记录")
            
            # 清理测试记录
            await collection.delete_many({"session_id": "diagnostic_test"})
            print("   测试记录已清理")
        else:
            print("❌ 测试记录添加失败")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. 检查最近的分析任务
    print("\n7️⃣ 检查最近的分析任务...")
    try:
        analysis_collection = db["analysis_tasks"]
        recent_tasks = await analysis_collection.find(
            {},
            sort=[("created_at", -1)],
            limit=5
        ).to_list(length=5)
        
        if recent_tasks:
            print(f"   找到 {len(recent_tasks)} 个最近的分析任务:")
            for task in recent_tasks:
                task_id = task.get("task_id", "N/A")
                symbol = task.get("symbol", "N/A")
                status = task.get("status", "N/A")
                created_at = task.get("created_at", "N/A")
                print(f"     • {task_id}: {symbol} - {status} ({created_at})")
                
                # 检查是否有对应的 token 使用记录
                token_records = await collection.count_documents({"session_id": task_id})
                if token_records > 0:
                    print(f"       ✅ 有 {token_records} 条 token 使用记录")
                else:
                    print(f"       ⚠️  没有 token 使用记录")
        else:
            print("   ⚠️  没有找到最近的分析任务")
    except Exception as e:
        print(f"❌ 检查分析任务失败: {e}")
    
    # 8. 诊断结论
    print("\n" + "=" * 80)
    print("📊 诊断结论")
    print("=" * 80)
    
    try:
        collection = db["token_usage"]
        total_count = await collection.count_documents({})
        
        # 检查最近3天的记录
        three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
        recent_count = await collection.count_documents({
            "timestamp": {"$gte": three_days_ago}
        })
        
        if total_count == 0:
            print("\n❌ 问题确认: 数据库中没有任何使用记录")
            print("\n可能的原因:")
            print("1. 成本跟踪功能被禁用")
            print("2. 分析服务没有正确调用 _record_token_usage 方法")
            print("3. UsageStatisticsService.add_usage_record 方法执行失败")
            print("4. 数据库写入权限问题")
            
            print("\n建议的解决步骤:")
            print("1. 检查 config/settings.json 中 enable_cost_tracking 是否为 true")
            print("2. 运行一次股票分析，观察日志中是否有 '💰 记录使用成本' 的信息")
            print("3. 检查日志中是否有 '❌ 添加使用记录失败' 的错误")
            print("4. 确认 MongoDB 用户有写入权限")
            
        elif recent_count == 0:
            print(f"\n⚠️  问题确认: 数据库中有 {total_count} 条历史记录，但最近3天没有新记录")
            print("\n可能的原因:")
            print("1. 最近3天没有进行股票分析")
            print("2. 成本跟踪功能最近被禁用")
            print("3. 代码更新导致记录功能失效")
            
            print("\n建议的解决步骤:")
            print("1. 运行一次股票分析测试")
            print("2. 检查最近的代码变更")
            print("3. 查看应用日志")
            
        else:
            print(f"\n✅ 数据正常: 数据库中有 {total_count} 条记录，最近3天有 {recent_count} 条新记录")
            print("\n如果前端显示没有数据，可能的原因:")
            print("1. 前端 API 调用失败")
            print("2. 前端时间范围筛选问题")
            print("3. 前端数据解析问题")
            
            print("\n建议的解决步骤:")
            print("1. 打开浏览器开发者工具，检查网络请求")
            print("2. 查看 API 响应数据")
            print("3. 检查前端控制台是否有错误")
    
    except Exception as e:
        print(f"\n❌ 生成诊断结论失败: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

