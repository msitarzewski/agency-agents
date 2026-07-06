"""
迁移脚本：为 stock_financial_data 集合添加 symbol 字段
将 code 字段的值复制到 symbol 字段，统一字段命名
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_financial_data():
    """为 stock_financial_data 集合添加 symbol 字段"""
    
    logger.info("=" * 80)
    logger.info("开始迁移：stock_financial_data 集合添加 symbol 字段")
    logger.info("=" * 80)
    
    # 连接数据库
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_financial_data"]
    
    try:
        # 1. 检查集合是否存在
        collections = await db.list_collection_names()
        if "stock_financial_data" not in collections:
            logger.error("❌ stock_financial_data 集合不存在！")
            return False
        
        # 2. 统计总数
        total_count = await collection.count_documents({})
        logger.info(f"📊 集合总记录数: {total_count}")
        
        if total_count == 0:
            logger.warning("⚠️ 集合为空，无需迁移")
            return True
        
        # 3. 检查已有 symbol 字段的记录数
        has_symbol = await collection.count_documents({"symbol": {"$exists": True}})
        logger.info(f"📊 已有 symbol 字段的记录: {has_symbol}")
        
        # 4. 检查只有 code 字段的记录数
        only_code = await collection.count_documents({
            "code": {"$exists": True},
            "symbol": {"$exists": False}
        })
        logger.info(f"📊 需要迁移的记录: {only_code}")
        
        if only_code == 0:
            logger.info("✅ 所有记录都已有 symbol 字段，无需迁移")
            return True
        
        # 5. 显示示例数据
        logger.info("\n" + "=" * 80)
        logger.info("示例数据（迁移前）")
        logger.info("=" * 80)
        
        sample = await collection.find_one(
            {"code": {"$exists": True}, "symbol": {"$exists": False}},
            {"_id": 0, "code": 1, "symbol": 1, "report_period": 1}
        )
        
        if sample:
            logger.info(f"示例记录: {sample}")
        
        # 6. 执行迁移
        logger.info("\n" + "=" * 80)
        logger.info("开始迁移...")
        logger.info("=" * 80)
        
        # 使用批量更新
        batch_size = 1000
        migrated_count = 0
        error_count = 0
        
        cursor = collection.find(
            {"code": {"$exists": True}, "symbol": {"$exists": False}},
            {"_id": 1, "code": 1}
        )
        
        batch = []
        async for doc in cursor:
            code = doc.get("code")
            if code:
                batch.append({
                    "_id": doc["_id"],
                    "code": code
                })
            
            if len(batch) >= batch_size:
                # 批量更新
                result = await process_batch(collection, batch)
                migrated_count += result["success"]
                error_count += result["error"]
                
                logger.info(f"📈 进度: {migrated_count}/{only_code} "
                          f"(成功: {migrated_count}, 失败: {error_count})")
                
                batch = []
        
        # 处理剩余的批次
        if batch:
            result = await process_batch(collection, batch)
            migrated_count += result["success"]
            error_count += result["error"]
        
        # 7. 验证迁移结果
        logger.info("\n" + "=" * 80)
        logger.info("验证迁移结果")
        logger.info("=" * 80)
        
        after_has_symbol = await collection.count_documents({"symbol": {"$exists": True}})
        after_only_code = await collection.count_documents({
            "code": {"$exists": True},
            "symbol": {"$exists": False}
        })
        
        logger.info(f"📊 迁移后统计:")
        logger.info(f"   有 symbol 字段: {after_has_symbol}")
        logger.info(f"   仅有 code 字段: {after_only_code}")
        logger.info(f"   成功迁移: {migrated_count}")
        logger.info(f"   失败: {error_count}")
        
        # 8. 显示迁移后的示例
        logger.info("\n" + "=" * 80)
        logger.info("示例数据（迁移后）")
        logger.info("=" * 80)
        
        sample_after = await collection.find_one(
            {"symbol": {"$exists": True}},
            {"_id": 0, "code": 1, "symbol": 1, "report_period": 1}
        )
        
        if sample_after:
            logger.info(f"示例记录: {sample_after}")
        
        # 9. 创建索引
        logger.info("\n" + "=" * 80)
        logger.info("创建/更新索引")
        logger.info("=" * 80)
        
        # 创建 symbol 字段索引
        await collection.create_index("symbol", background=True)
        logger.info("✅ 创建 symbol 索引")
        
        # 创建复合索引：symbol + report_period
        await collection.create_index(
            [("symbol", 1), ("report_period", -1)],
            background=True,
            name="symbol_report_period"
        )
        logger.info("✅ 创建 symbol + report_period 复合索引")
        
        # 列出所有索引
        indexes = await collection.index_information()
        logger.info(f"\n📋 当前索引:")
        for idx_name, idx_info in indexes.items():
            logger.info(f"   {idx_name}: {idx_info.get('key', [])}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 迁移完成！")
        logger.info("=" * 80)
        logger.info(f"总记录数: {total_count}")
        logger.info(f"成功迁移: {migrated_count}")
        logger.info(f"失败: {error_count}")
        logger.info(f"剩余未迁移: {after_only_code}")
        
        return error_count == 0 and after_only_code == 0
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}", exc_info=True)
        return False
    finally:
        client.close()


async def process_batch(collection, batch):
    """处理一批数据"""
    success = 0
    error = 0
    
    for item in batch:
        try:
            result = await collection.update_one(
                {"_id": item["_id"]},
                {"$set": {"symbol": item["code"]}}
            )
            if result.modified_count > 0:
                success += 1
        except Exception as e:
            logger.error(f"更新失败 {item['code']}: {e}")
            error += 1
    
    return {"success": success, "error": error}


async def rollback_migration():
    """回滚迁移（删除 symbol 字段）"""
    logger.info("=" * 80)
    logger.info("回滚迁移：删除 symbol 字段")
    logger.info("=" * 80)
    
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_financial_data"]
    
    try:
        result = await collection.update_many(
            {"symbol": {"$exists": True}},
            {"$unset": {"symbol": ""}}
        )
        
        logger.info(f"✅ 回滚完成，删除了 {result.modified_count} 条记录的 symbol 字段")
        return True
        
    except Exception as e:
        logger.error(f"❌ 回滚失败: {e}", exc_info=True)
        return False
    finally:
        client.close()


async def main():
    """主函数"""
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        result = await rollback_migration()
    else:
        result = await migrate_financial_data()
    
    if result:
        logger.info("\n🎉 操作成功！")
    else:
        logger.error("\n❌ 操作失败！")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

