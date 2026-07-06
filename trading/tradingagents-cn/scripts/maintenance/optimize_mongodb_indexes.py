#!/usr/bin/env python3
"""
MongoDB 索引优化脚本

功能：
1. 分析慢查询日志
2. 为 stock_daily_quotes 集合创建优化索引
3. 删除冗余索引
4. 生成索引使用报告

使用方法：
    python scripts/maintenance/optimize_mongodb_indexes.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging_config import logger


async def analyze_existing_indexes(collection):
    """分析现有索引"""
    logger.info("📊 分析现有索引...")
    
    indexes = await collection.list_indexes().to_list(length=None)
    
    logger.info(f"\n当前索引列表（共 {len(indexes)} 个）：")
    for idx in indexes:
        name = idx.get("name", "unknown")
        keys = idx.get("key", {})
        unique = idx.get("unique", False)
        
        # 格式化索引键
        key_str = ", ".join([f"{k}: {v}" for k, v in keys.items()])
        unique_str = " [UNIQUE]" if unique else ""
        
        logger.info(f"  - {name}: {{ {key_str} }}{unique_str}")
    
    return indexes


async def create_optimized_indexes(collection):
    """创建优化索引"""
    logger.info("\n🔧 创建优化索引...")
    
    indexes_to_create = [
        {
            "name": "symbol_date_source_period_unique",
            "keys": [("symbol", 1), ("trade_date", 1), ("data_source", 1), ("period", 1)],
            "unique": True,
            "description": "复合唯一索引：防止重复数据"
        },
        {
            "name": "symbol_period_date_idx",
            "keys": [("symbol", 1), ("period", 1), ("trade_date", -1)],
            "unique": False,
            "description": "查询优化索引：按股票代码+周期查询历史数据"
        },
        {
            "name": "symbol_date_idx",
            "keys": [("symbol", 1), ("trade_date", -1)],
            "unique": False,
            "description": "查询优化索引：按股票代码查询历史数据"
        },
        {
            "name": "date_idx",
            "keys": [("trade_date", -1)],
            "unique": False,
            "description": "查询优化索引：按日期查询数据"
        },
        {
            "name": "data_source_idx",
            "keys": [("data_source", 1)],
            "unique": False,
            "description": "查询优化索引：按数据源查询"
        },
        {
            "name": "symbol_source_date_period_idx",
            "keys": [("symbol", 1), ("data_source", 1), ("trade_date", -1), ("period", 1)],
            "unique": False,
            "description": "🔥 慢查询优化索引：匹配 update 操作的查询条件顺序"
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for idx_config in indexes_to_create:
        name = idx_config["name"]
        keys = idx_config["keys"]
        unique = idx_config["unique"]
        description = idx_config["description"]
        
        try:
            # 检查索引是否已存在
            existing_indexes = await collection.list_indexes().to_list(length=None)
            index_exists = any(idx.get("name") == name for idx in existing_indexes)
            
            if index_exists:
                logger.info(f"⏭️  索引已存在，跳过: {name}")
                skipped_count += 1
                continue
            
            # 创建索引
            await collection.create_index(
                keys,
                unique=unique,
                name=name,
                background=True  # 后台创建，不阻塞数据库操作
            )
            
            logger.info(f"✅ 创建索引: {name}")
            logger.info(f"   描述: {description}")
            logger.info(f"   键: {keys}")
            created_count += 1
            
        except Exception as e:
            logger.error(f"❌ 创建索引失败: {name}, 错误: {e}")
    
    logger.info(f"\n📊 索引创建完成: 新建 {created_count} 个, 跳过 {skipped_count} 个")
    
    return created_count


async def drop_redundant_indexes(collection):
    """删除冗余索引（可选）"""
    logger.info("\n🗑️  检查冗余索引...")
    
    # 这里可以定义需要删除的冗余索引
    # 注意：_id_ 索引不能删除
    redundant_indexes = [
        # 示例：如果有旧的索引需要删除，可以在这里添加
        # "old_index_name",
    ]
    
    dropped_count = 0
    
    for index_name in redundant_indexes:
        try:
            await collection.drop_index(index_name)
            logger.info(f"✅ 删除冗余索引: {index_name}")
            dropped_count += 1
        except Exception as e:
            logger.warning(f"⚠️  删除索引失败: {index_name}, 错误: {e}")
    
    if dropped_count == 0:
        logger.info("✅ 没有需要删除的冗余索引")
    else:
        logger.info(f"📊 删除了 {dropped_count} 个冗余索引")
    
    return dropped_count


async def get_collection_stats(collection):
    """获取集合统计信息"""
    logger.info("\n📊 获取集合统计信息...")
    
    try:
        stats = await collection.database.command("collStats", collection.name)
        
        count = stats.get("count", 0)
        size = stats.get("size", 0) / (1024 * 1024)  # MB
        avg_obj_size = stats.get("avgObjSize", 0)
        storage_size = stats.get("storageSize", 0) / (1024 * 1024)  # MB
        total_index_size = stats.get("totalIndexSize", 0) / (1024 * 1024)  # MB
        
        logger.info(f"  - 文档数量: {count:,}")
        logger.info(f"  - 数据大小: {size:.2f} MB")
        logger.info(f"  - 平均文档大小: {avg_obj_size:.2f} bytes")
        logger.info(f"  - 存储大小: {storage_size:.2f} MB")
        logger.info(f"  - 索引总大小: {total_index_size:.2f} MB")
        
        return stats
    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        return None


async def test_query_performance(collection):
    """测试查询性能"""
    logger.info("\n🧪 测试查询性能...")
    
    # 测试慢查询场景
    test_queries = [
        {
            "name": "慢查询场景（update条件）",
            "filter": {
                "symbol": "688188",
                "trade_date": "2024-12-10",
                "data_source": "tushare",
                "period": "daily"
            }
        },
        {
            "name": "按股票代码查询",
            "filter": {
                "symbol": "000001"
            }
        },
        {
            "name": "按股票代码+日期范围查询",
            "filter": {
                "symbol": "000001",
                "trade_date": {"$gte": "2024-01-01", "$lte": "2024-12-31"}
            }
        }
    ]
    
    for test in test_queries:
        name = test["name"]
        filter_query = test["filter"]
        
        try:
            # 使用 explain 分析查询计划
            explain = await collection.find(filter_query).explain()
            
            execution_stats = explain.get("executionStats", {})
            execution_time_ms = execution_stats.get("executionTimeMillis", 0)
            total_docs_examined = execution_stats.get("totalDocsExamined", 0)
            total_keys_examined = execution_stats.get("totalKeysExamined", 0)
            n_returned = execution_stats.get("nReturned", 0)
            
            # 获取查询计划
            winning_plan = explain.get("queryPlanner", {}).get("winningPlan", {})
            input_stage = winning_plan.get("inputStage", {})
            stage = input_stage.get("stage", "UNKNOWN")
            index_name = input_stage.get("indexName", "无索引")
            
            logger.info(f"\n  测试: {name}")
            logger.info(f"    - 执行时间: {execution_time_ms} ms")
            logger.info(f"    - 扫描文档数: {total_docs_examined}")
            logger.info(f"    - 扫描索引键数: {total_keys_examined}")
            logger.info(f"    - 返回文档数: {n_returned}")
            logger.info(f"    - 查询阶段: {stage}")
            logger.info(f"    - 使用索引: {index_name}")
            
            # 判断是否使用了索引
            if stage == "COLLSCAN":
                logger.warning(f"    ⚠️  警告: 全集合扫描（COLLSCAN），建议添加索引！")
            elif stage == "IXSCAN":
                logger.info(f"    ✅ 使用了索引扫描（IXSCAN）")
            
        except Exception as e:
            logger.error(f"❌ 测试查询失败: {name}, 错误: {e}")


async def main():
    """主函数"""
    logger.info("🚀 开始 MongoDB 索引优化...")
    logger.info(f"📍 数据库: {settings.MONGO_DB}")
    logger.info(f"📍 集合: stock_daily_quotes")
    
    try:
        # 连接 MongoDB
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        collection = db.stock_daily_quotes
        
        # 1. 分析现有索引
        await analyze_existing_indexes(collection)
        
        # 2. 获取集合统计信息
        await get_collection_stats(collection)
        
        # 3. 创建优化索引
        created_count = await create_optimized_indexes(collection)
        
        # 4. 删除冗余索引（可选）
        # await drop_redundant_indexes(collection)
        
        # 5. 测试查询性能
        await test_query_performance(collection)
        
        # 关闭连接
        client.close()
        
        logger.info("\n✅ MongoDB 索引优化完成！")
        logger.info(f"📊 新建索引: {created_count} 个")
        
        if created_count > 0:
            logger.info("\n💡 建议:")
            logger.info("  1. 监控慢查询日志，确认优化效果")
            logger.info("  2. 定期运行此脚本，保持索引最新")
            logger.info("  3. 如果数据量很大，索引创建可能需要一些时间")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 索引优化失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

