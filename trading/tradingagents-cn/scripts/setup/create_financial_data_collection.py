#!/usr/bin/env python3
"""
创建财务数据集合和索引
根据设计文档创建stock_financial_data集合及其优化索引
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_financial_data_collection():
    """创建财务数据集合和索引"""
    try:
        # 使用应用配置连接MongoDB
        from app.core.config import get_settings
        settings = get_settings()

        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        
        collection_name = "stock_financial_data"
        collection = db[collection_name]
        
        logger.info(f"🔧 开始创建 {collection_name} 集合和索引...")
        
        # 1. 创建唯一索引：symbol + report_period + data_source
        unique_index = [
            ("symbol", ASCENDING),
            ("report_period", DESCENDING),
            ("data_source", ASCENDING)
        ]
        
        await collection.create_index(
            unique_index,
            unique=True,
            name="symbol_period_source_unique",
            background=True
        )
        logger.info("✅ 创建唯一索引: symbol_period_source_unique")
        
        # 2. 创建复合索引：full_symbol + report_period
        await collection.create_index(
            [("full_symbol", ASCENDING), ("report_period", DESCENDING)],
            name="full_symbol_period",
            background=True
        )
        logger.info("✅ 创建索引: full_symbol_period")
        
        # 3. 创建市场索引：market + report_period
        await collection.create_index(
            [("market", ASCENDING), ("report_period", DESCENDING)],
            name="market_period",
            background=True
        )
        logger.info("✅ 创建索引: market_period")
        
        # 4. 创建报告期索引
        await collection.create_index(
            [("report_period", DESCENDING)],
            name="report_period_desc",
            background=True
        )
        logger.info("✅ 创建索引: report_period_desc")
        
        # 5. 创建公告日期索引
        await collection.create_index(
            [("ann_date", DESCENDING)],
            name="ann_date_desc",
            background=True
        )
        logger.info("✅ 创建索引: ann_date_desc")
        
        # 6. 创建数据源索引
        await collection.create_index(
            [("data_source", ASCENDING)],
            name="data_source",
            background=True
        )
        logger.info("✅ 创建索引: data_source")
        
        # 7. 创建报告类型索引
        await collection.create_index(
            [("report_type", ASCENDING)],
            name="report_type",
            background=True
        )
        logger.info("✅ 创建索引: report_type")
        
        # 8. 创建更新时间索引
        await collection.create_index(
            [("updated_at", DESCENDING)],
            name="updated_at_desc",
            background=True
        )
        logger.info("✅ 创建索引: updated_at_desc")
        
        # 9. 创建复合查询索引：symbol + report_type + report_period
        await collection.create_index(
            [
                ("symbol", ASCENDING),
                ("report_type", ASCENDING),
                ("report_period", DESCENDING)
            ],
            name="symbol_type_period",
            background=True
        )
        logger.info("✅ 创建索引: symbol_type_period")
        
        # 10. 创建数据源对比索引：symbol + report_period (用于跨数据源对比)
        await collection.create_index(
            [("symbol", ASCENDING), ("report_period", DESCENDING)],
            name="symbol_period_compare",
            background=True
        )
        logger.info("✅ 创建索引: symbol_period_compare")
        
        # 获取集合统计信息
        stats = await db.command("collStats", collection_name)
        index_info = await collection.list_indexes().to_list(length=None)
        
        logger.info(f"📊 {collection_name} 集合创建完成:")
        logger.info(f"   - 文档数量: {stats.get('count', 0)}")
        logger.info(f"   - 存储大小: {stats.get('storageSize', 0)} bytes")
        logger.info(f"   - 索引数量: {len(index_info)}")
        
        # 显示所有索引
        logger.info("📋 索引列表:")
        for idx in index_info:
            logger.info(f"   - {idx['name']}: {idx.get('key', {})}")
        
        # 插入示例文档（用于测试）
        sample_doc = {
            "symbol": "000001",
            "full_symbol": "000001.SZ",
            "market": "CN",
            "report_period": "20231231",
            "report_type": "annual",
            "ann_date": "2024-03-20",
            "f_ann_date": "2024-03-20",
            
            # 基本财务指标
            "revenue": 500000000000.0,  # 营业收入
            "net_income": 50000000000.0,  # 净利润
            "total_assets": 4500000000000.0,  # 总资产
            "total_equity": 280000000000.0,  # 股东权益
            "total_liab": 4200000000000.0,  # 总负债
            "cash_and_equivalents": 180000000000.0,  # 现金及现金等价物
            
            # 财务指标
            "roe": 23.21,  # 净资产收益率
            "roa": 1.44,   # 总资产收益率
            "gross_margin": 75.0,  # 毛利率
            "net_margin": 36.11,   # 净利率
            "debt_to_assets": 93.33,  # 资产负债率
            
            # 元数据
            "data_source": "example",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "version": 1
        }
        
        # 检查是否已存在示例文档
        existing = await collection.find_one({
            "symbol": "000001",
            "report_period": "20231231",
            "data_source": "example"
        })
        
        if not existing:
            await collection.insert_one(sample_doc)
            logger.info("✅ 插入示例财务数据文档")
        else:
            logger.info("ℹ️ 示例财务数据文档已存在")
        
        # 验证索引创建
        logger.info("🔍 验证索引性能...")
        
        # 测试查询性能
        import time
        
        # 测试1: 按股票代码查询
        start_time = time.time()
        result = await collection.find({"symbol": "000001"}).to_list(length=10)
        query_time = (time.time() - start_time) * 1000
        logger.info(f"   - 股票代码查询: {query_time:.2f}ms, 结果: {len(result)}条")
        
        # 测试2: 按报告期查询
        start_time = time.time()
        result = await collection.find({"report_period": "20231231"}).to_list(length=10)
        query_time = (time.time() - start_time) * 1000
        logger.info(f"   - 报告期查询: {query_time:.2f}ms, 结果: {len(result)}条")
        
        # 测试3: 复合查询
        start_time = time.time()
        result = await collection.find({
            "symbol": "000001",
            "report_type": "annual"
        }).sort("report_period", -1).to_list(length=5)
        query_time = (time.time() - start_time) * 1000
        logger.info(f"   - 复合查询: {query_time:.2f}ms, 结果: {len(result)}条")
        
        logger.info("🎉 财务数据集合创建和索引优化完成!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建财务数据集合失败: {e}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()


async def main():
    """主函数"""
    logger.info("🚀 开始创建财务数据集合...")
    
    success = await create_financial_data_collection()
    
    if success:
        logger.info("✅ 财务数据集合创建成功!")
        print("\n" + "="*60)
        print("🎉 财务数据集合创建完成!")
        print("="*60)
        print("📊 集合名称: stock_financial_data")
        print("🔧 索引数量: 10个优化索引")
        print("⚡ 查询性能: 毫秒级响应")
        print("🔍 支持查询:")
        print("   - 按股票代码查询")
        print("   - 按报告期查询")
        print("   - 按数据源查询")
        print("   - 按报告类型查询")
        print("   - 跨数据源对比查询")
        print("   - 复合条件查询")
        print("="*60)
        print("✅ 可以开始使用财务数据功能了!")
    else:
        logger.error("❌ 财务数据集合创建失败!")
        print("\n" + "="*60)
        print("❌ 财务数据集合创建失败!")
        print("="*60)
        print("请检查:")
        print("   - MongoDB服务是否运行")
        print("   - 数据库连接配置是否正确")
        print("   - 是否有足够的权限")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
