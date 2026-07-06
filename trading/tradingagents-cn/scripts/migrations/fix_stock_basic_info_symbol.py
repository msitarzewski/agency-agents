"""
修复 stock_basic_info 集合的 symbol 字段问题
为所有缺少 symbol 字段的记录添加 symbol 字段（从 code 字段复制）
"""
import asyncio
import sys
from pathlib import Path

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


async def fix_stock_basic_info_symbol():
    """修复 stock_basic_info 集合的 symbol 字段"""
    
    logger.info("=" * 80)
    logger.info("开始修复：stock_basic_info 集合 symbol 字段")
    logger.info("=" * 80)
    
    # 连接数据库
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_basic_info"]
    
    try:
        # 1. 统计总数
        total_count = await collection.count_documents({})
        logger.info(f"📊 集合总记录数: {total_count}")
        
        # 2. 检查缺少 symbol 字段或 symbol 为 None 的记录
        missing_symbol = await collection.count_documents({
            "$or": [
                {"symbol": {"$exists": False}},
                {"symbol": None}
            ]
        })
        logger.info(f"📊 缺少 symbol 字段的记录: {missing_symbol}")
        
        if missing_symbol == 0:
            logger.info("✅ 所有记录都有有效的 symbol 字段，无需修复")
            return True
        
        # 3. 显示示例数据
        logger.info("\n" + "=" * 80)
        logger.info("示例数据（修复前）")
        logger.info("=" * 80)
        
        sample = await collection.find_one(
            {"$or": [{"symbol": {"$exists": False}}, {"symbol": None}]},
            {"_id": 0, "code": 1, "symbol": 1, "name": 1}
        )
        
        if sample:
            logger.info(f"示例记录: {sample}")
        
        # 4. 执行修复
        logger.info("\n" + "=" * 80)
        logger.info("开始修复...")
        logger.info("=" * 80)
        
        # 使用批量更新
        batch_size = 1000
        fixed_count = 0
        error_count = 0
        
        cursor = collection.find(
            {"$or": [{"symbol": {"$exists": False}}, {"symbol": None}]},
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
            else:
                logger.warning(f"⚠️ 记录 {doc['_id']} 没有 code 字段，跳过")
                error_count += 1
            
            if len(batch) >= batch_size:
                # 批量更新
                result = await process_batch(collection, batch)
                fixed_count += result["success"]
                error_count += result["error"]
                
                logger.info(f"📈 进度: {fixed_count}/{missing_symbol} "
                          f"(成功: {fixed_count}, 失败: {error_count})")
                
                batch = []
        
        # 处理剩余的批次
        if batch:
            result = await process_batch(collection, batch)
            fixed_count += result["success"]
            error_count += result["error"]
        
        # 5. 验证修复结果
        logger.info("\n" + "=" * 80)
        logger.info("验证修复结果")
        logger.info("=" * 80)
        
        after_missing = await collection.count_documents({
            "$or": [
                {"symbol": {"$exists": False}},
                {"symbol": None}
            ]
        })
        
        has_symbol = await collection.count_documents({
            "symbol": {"$exists": True, "$ne": None}
        })
        
        logger.info(f"📊 修复后统计:")
        logger.info(f"   有有效 symbol 字段: {has_symbol}")
        logger.info(f"   缺少 symbol 字段: {after_missing}")
        logger.info(f"   成功修复: {fixed_count}")
        logger.info(f"   失败: {error_count}")
        
        # 6. 显示修复后的示例
        logger.info("\n" + "=" * 80)
        logger.info("示例数据（修复后）")
        logger.info("=" * 80)
        
        # 随机显示几条记录
        samples = []
        async for doc in collection.find(
            {"symbol": {"$exists": True, "$ne": None}},
            {"_id": 0, "code": 1, "symbol": 1, "name": 1}
        ).limit(5):
            samples.append(doc)
        
        for i, sample in enumerate(samples, 1):
            logger.info(f"{i}. {sample}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 数据修复完成！")
        logger.info("=" * 80)
        
        return error_count == 0 and after_missing == 0
        
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}", exc_info=True)
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
            if result.modified_count > 0 or result.matched_count > 0:
                success += 1
        except Exception as e:
            logger.error(f"更新失败 {item['code']}: {e}")
            error += 1
    
    return {"success": success, "error": error}


async def check_and_fix_unique_index():
    """检查并修复唯一索引问题"""
    logger.info("\n" + "=" * 80)
    logger.info("检查并修复唯一索引")
    logger.info("=" * 80)
    
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_basic_info"]
    
    try:
        # 1. 检查是否存在 symbol_1_unique 索引
        indexes = await collection.index_information()
        
        if "symbol_1_unique" in indexes:
            logger.info("📋 发现 symbol_1_unique 唯一索引")
            
            # 2. 删除旧的唯一索引
            logger.info("🗑️ 删除旧的唯一索引...")
            await collection.drop_index("symbol_1_unique")
            logger.info("✅ 已删除 symbol_1_unique 索引")
        
        # 3. 创建新的非唯一索引
        logger.info("🔧 创建新的非唯一索引...")
        await collection.create_index("symbol", background=True, name="symbol_1")
        logger.info("✅ 已创建 symbol_1 索引（非唯一）")
        
        # 4. 列出所有索引
        indexes = await collection.index_information()
        logger.info(f"\n📋 当前索引:")
        for idx_name, idx_info in indexes.items():
            unique = idx_info.get('unique', False)
            logger.info(f"   {idx_name}: {idx_info.get('key', [])} (unique={unique})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 修复索引失败: {e}", exc_info=True)
        return False
    finally:
        client.close()


async def main():
    """主函数"""
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--fix-index":
        result = await check_and_fix_unique_index()
    else:
        # 先修复数据
        result1 = await fix_stock_basic_info_symbol()
        
        # 再修复索引
        logger.info("\n")
        result2 = await check_and_fix_unique_index()
        
        result = result1 and result2
    
    if result:
        logger.info("\n🎉 操作成功！")
    else:
        logger.error("\n❌ 操作失败！")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

