"""
初始化定时任务元数据
为所有定时任务设置预定义的触发器名称和备注
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB 连接配置
MONGODB_URL = "mongodb://admin:tradingagents123@localhost:27017"
DATABASE_NAME = "tradingagents"

# 任务元数据定义
TASK_METADATA = {
    # 基础服务任务
    "basics_sync_service": {
        "display_name": "股票基础信息同步",
        "description": "每日同步所有股票的基础信息，包括股票代码、名称、上市日期、行业分类等基本数据。每天早上6:30执行。"
    },
    "quotes_ingestion_service": {
        "display_name": "实时行情入库",
        "description": "定期将实时行情数据写入MongoDB数据库，用于历史查询和分析。执行间隔30秒。"
    },
    
    # Tushare 数据源任务
    "tushare_basic_info_sync": {
        "display_name": "Tushare-基础信息同步",
        "description": "从Tushare数据源同步股票基础信息，包括股票列表、公司基本资料等。每日凌晨2点执行。"
    },
    "tushare_quotes_sync": {
        "display_name": "Tushare-实时行情同步",
        "description": "从Tushare数据源同步实时行情数据。交易日9:00-15:00每5分钟执行一次。"
    },
    "tushare_historical_sync": {
        "display_name": "Tushare-历史数据同步",
        "description": "从Tushare数据源同步历史K线数据（日线、周线、月线）。交易日收盘后16:00执行。"
    },
    "tushare_financial_sync": {
        "display_name": "Tushare-财务数据同步",
        "description": "从Tushare数据源同步上市公司财务报表数据，包括资产负债表、利润表、现金流量表等。每周日凌晨3点执行。"
    },
    "tushare_status_check": {
        "display_name": "Tushare-状态检查",
        "description": "检查Tushare数据源的连接状态和API调用额度。每小时执行一次。"
    },
    
    # AKShare 数据源任务
    "akshare_basic_info_sync": {
        "display_name": "AKShare-基础信息同步",
        "description": "从AKShare数据源同步股票基础信息。每日凌晨3点执行。"
    },
    "akshare_quotes_sync": {
        "display_name": "AKShare-实时行情同步",
        "description": "从AKShare数据源同步实时行情数据。交易日9:00-15:00每10分钟执行一次。"
    },
    "akshare_historical_sync": {
        "display_name": "AKShare-历史数据同步",
        "description": "从AKShare数据源同步历史K线数据。交易日收盘后17:00执行。"
    },
    "akshare_financial_sync": {
        "display_name": "AKShare-财务数据同步",
        "description": "从AKShare数据源同步上市公司财务数据。每周日凌晨4点执行。"
    },
    "akshare_status_check": {
        "display_name": "AKShare-状态检查",
        "description": "检查AKShare数据源的连接状态和可用性。每小时30分执行一次。"
    },
    
    # BaoStock 数据源任务
    "baostock_basic_info_sync": {
        "display_name": "BaoStock-基础信息同步",
        "description": "从BaoStock数据源同步股票基础信息。每日凌晨4点执行。"
    },
    "baostock_quotes_sync": {
        "display_name": "BaoStock-实时行情同步",
        "description": "从BaoStock数据源同步实时行情数据。交易日9:00-15:00每15分钟执行一次。"
    },
    "baostock_historical_sync": {
        "display_name": "BaoStock-历史数据同步",
        "description": "从BaoStock数据源同步历史K线数据。交易日收盘后18:00执行。"
    },
    "baostock_status_check": {
        "display_name": "BaoStock-状态检查",
        "description": "检查BaoStock数据源的连接状态和可用性。每小时45分执行一次。"
    },

    # 新闻数据同步任务
    "news_sync": {
        "display_name": "新闻数据同步（AKShare）",
        "description": "使用AKShare（东方财富）同步所有股票的个股新闻。每2小时执行一次，每只股票获取最新50条新闻。支持批量处理，自动去重和情绪分析。"
    },
}


async def init_metadata():
    """初始化任务元数据"""
    print("=" * 70)
    print("🔧 初始化定时任务元数据")
    print("=" * 70)
    
    # 连接MongoDB
    print(f"\n📡 连接MongoDB: {MONGODB_URL}")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    collection = db.scheduler_metadata
    
    try:
        # 统计信息
        total = len(TASK_METADATA)
        inserted = 0
        updated = 0
        skipped = 0
        
        print(f"\n📋 准备初始化 {total} 个任务的元数据...\n")
        
        for job_id, metadata in TASK_METADATA.items():
            # 检查是否已存在
            existing = await collection.find_one({"job_id": job_id})
            
            data = {
                "job_id": job_id,
                "display_name": metadata["display_name"],
                "description": metadata["description"],
                "updated_at": datetime.now()
            }
            
            if existing:
                # 如果已存在，检查是否需要更新
                if (existing.get("display_name") != metadata["display_name"] or 
                    existing.get("description") != metadata["description"]):
                    await collection.update_one(
                        {"job_id": job_id},
                        {"$set": data}
                    )
                    print(f"  ✅ 更新: {job_id}")
                    print(f"     名称: {metadata['display_name']}")
                    updated += 1
                else:
                    print(f"  ⏭️  跳过: {job_id} (已存在且无变化)")
                    skipped += 1
            else:
                # 插入新记录
                await collection.insert_one(data)
                print(f"  ✨ 新增: {job_id}")
                print(f"     名称: {metadata['display_name']}")
                inserted += 1
        
        print("\n" + "=" * 70)
        print("📊 初始化完成统计")
        print("=" * 70)
        print(f"  总任务数: {total}")
        print(f"  新增: {inserted}")
        print(f"  更新: {updated}")
        print(f"  跳过: {skipped}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        raise
    finally:
        client.close()
        print("\n✅ MongoDB连接已关闭")


async def list_metadata():
    """列出所有任务元数据"""
    print("\n" + "=" * 70)
    print("📋 当前所有任务元数据")
    print("=" * 70)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    collection = db.scheduler_metadata
    
    try:
        cursor = collection.find({})
        count = 0
        async for doc in cursor:
            count += 1
            print(f"\n{count}. 任务ID: {doc['job_id']}")
            print(f"   触发器名称: {doc.get('display_name', '(未设置)')}")
            print(f"   备注: {doc.get('description', '(未设置)')}")
            print(f"   更新时间: {doc.get('updated_at', '(未知)')}")
        
        if count == 0:
            print("\n  (暂无任务元数据)")
        
        print("\n" + "=" * 70)
        print(f"共 {count} 个任务")
        print("=" * 70)
        
    finally:
        client.close()


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        await list_metadata()
    else:
        await init_metadata()
        print("\n💡 提示: 使用 'python scripts/init_scheduler_metadata.py list' 查看所有元数据")


if __name__ == "__main__":
    asyncio.run(main())

