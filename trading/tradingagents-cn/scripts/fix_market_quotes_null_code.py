#!/usr/bin/env python3
"""
修复 market_quotes 集合中 code=null 的记录

问题：
- market_quotes 集合有 code_1 唯一索引
- 部分记录的 code 字段为 null
- 导致插入新记录时触发唯一索引冲突

解决方案：
1. 删除所有 code=null 的记录
2. 或者将 code 字段设置为 symbol 的值
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db, init_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def fix_null_code_records():
    """修复 code=null 的记录"""
    try:
        db = get_mongo_db()
        collection = db.market_quotes
        
        # 1. 统计 code=null 的记录数
        null_count = await collection.count_documents({"code": None})
        logger.info(f"📊 发现 {null_count} 条 code=null 的记录")
        
        if null_count == 0:
            logger.info("✅ 没有需要修复的记录")
            return
        
        # 2. 查询所有 code=null 的记录
        cursor = collection.find({"code": None})
        records = await cursor.to_list(length=None)
        
        logger.info(f"📋 准备修复 {len(records)} 条记录...")
        
        fixed_count = 0
        deleted_count = 0
        
        for record in records:
            symbol = record.get("symbol")

            if symbol:
                # 检查是否已经存在 code=symbol 的记录
                existing = await collection.find_one({"code": symbol, "_id": {"$ne": record["_id"]}})

                if existing:
                    # 如果已经存在，说明是重复记录，删除 code=null 的这条
                    result = await collection.delete_one({"_id": record["_id"]})
                    if result.deleted_count > 0:
                        deleted_count += 1
                        logger.warning(f"🗑️ 删除重复记录: _id={record['_id']}, symbol={symbol} (已存在 code={symbol} 的记录)")
                else:
                    # 如果不存在，将 code 设置为 symbol
                    result = await collection.update_one(
                        {"_id": record["_id"]},
                        {"$set": {"code": symbol}}
                    )
                    if result.modified_count > 0:
                        fixed_count += 1
                        logger.info(f"✅ 修复记录: _id={record['_id']}, symbol={symbol}, code={symbol}")
            else:
                # 如果没有 symbol，删除这条记录
                result = await collection.delete_one({"_id": record["_id"]})
                if result.deleted_count > 0:
                    deleted_count += 1
                    logger.warning(f"🗑️ 删除无效记录: _id={record['_id']} (没有 symbol)")
        
        logger.info(f"✅ 修复完成: 修复 {fixed_count} 条, 删除 {deleted_count} 条")
        
        # 3. 验证修复结果
        remaining_null = await collection.count_documents({"code": None})
        if remaining_null == 0:
            logger.info("✅ 所有 code=null 的记录已修复")
        else:
            logger.warning(f"⚠️ 还有 {remaining_null} 条 code=null 的记录")
        
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}")
        raise


async def check_index():
    """检查索引信息"""
    try:
        db = get_mongo_db()
        collection = db.market_quotes
        
        # 获取所有索引
        indexes = await collection.index_information()
        
        logger.info("📊 market_quotes 集合的索引:")
        for index_name, index_info in indexes.items():
            logger.info(f"  - {index_name}: {index_info}")
        
        # 检查是否有 code_1 索引
        if "code_1" in indexes:
            logger.info("✅ 发现 code_1 唯一索引")
            logger.info(f"   索引信息: {indexes['code_1']}")
        
    except Exception as e:
        logger.error(f"❌ 检查索引失败: {e}")


async def main():
    """主函数"""
    logger.info("🔧 开始修复 market_quotes 集合中的 code=null 记录...")

    # 0. 初始化数据库连接
    logger.info("📡 初始化数据库连接...")
    await init_database()
    logger.info("✅ 数据库连接成功")

    # 1. 检查索引
    await check_index()

    # 2. 修复记录
    await fix_null_code_records()

    logger.info("✅ 修复完成")


if __name__ == "__main__":
    asyncio.run(main())

