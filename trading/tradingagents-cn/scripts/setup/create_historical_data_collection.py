#!/usr/bin/env python3
"""
创建股票历史数据集合
为三数据源的历史K线数据创建专门的MongoDB集合
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_historical_data_collection():
    """创建股票历史数据集合和索引"""
    try:
        # 连接MongoDB（使用配置）
        from app.core.config import settings
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        
        logger.info("🚀 开始创建股票历史数据集合...")
        
        # 创建stock_daily_quotes集合
        collection = db.stock_daily_quotes
        
        # 创建索引
        logger.info("📊 创建索引...")

        # 1. 复合唯一索引：股票代码+交易日期+数据源+周期
        await collection.create_index([
            ("symbol", 1),
            ("trade_date", 1),
            ("data_source", 1),
            ("period", 1)
        ], unique=True, name="symbol_date_source_period_unique")

        # 2. 股票代码索引（查询单只股票的历史数据）
        await collection.create_index([("symbol", 1)], name="symbol_index")

        # 3. 交易日期索引（按日期范围查询）
        await collection.create_index([("trade_date", -1)], name="trade_date_index")

        # 4. 数据源索引（按数据源查询）
        await collection.create_index([("data_source", 1)], name="data_source_index")

        # 5. 复合索引：股票代码+交易日期（常用查询）
        await collection.create_index([
            ("symbol", 1),
            ("trade_date", -1)
        ], name="symbol_date_index")

        # 6. 市场类型索引
        await collection.create_index([("market", 1)], name="market_index")

        # 7. 更新时间索引（数据维护）
        await collection.create_index([("updated_at", -1)], name="updated_at_index")

        # 8. 复合索引：市场+交易日期（市场级别查询）
        await collection.create_index([
            ("market", 1),
            ("trade_date", -1)
        ], name="market_date_index")

        # 9. 复合索引：数据源+更新时间（数据同步监控）
        await collection.create_index([
            ("data_source", 1),
            ("updated_at", -1)
        ], name="source_updated_index")

        # 10. 稀疏索引：成交量（用于筛选活跃股票）
        await collection.create_index([("volume", -1)], sparse=True, name="volume_index")

        # 11. 周期索引（用于按周期查询）
        await collection.create_index([("period", 1)], name="period_index")

        # 12. 复合索引：股票+周期+日期（常用查询）
        await collection.create_index([
            ("symbol", 1),
            ("period", 1),
            ("trade_date", -1)
        ], name="symbol_period_date_index")
        
        logger.info("✅ 索引创建完成")
        
        # 插入示例数据
        logger.info("📝 插入示例数据...")
        
        sample_data = {
            "symbol": "000001",
            "full_symbol": "000001.SZ",
            "market": "CN",
            "trade_date": "2024-01-15",
            "period": "daily",
            "open": 12.50,
            "high": 12.80,
            "low": 12.30,
            "close": 12.65,
            "pre_close": 12.45,
            "change": 0.20,
            "pct_chg": 1.61,
            "volume": 125000000,
            "amount": 1580000000,
            "turnover_rate": 0.64,
            "volume_ratio": 1.2,
            "pe": 5.2,
            "pb": 0.8,
            "ps": 1.1,
            "data_source": "example",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "version": 1
        }
        
        await collection.insert_one(sample_data)
        logger.info("✅ 示例数据插入完成")
        
        # 显示集合统计
        count = await collection.count_documents({})
        indexes = await collection.list_indexes().to_list(length=None)
        
        logger.info(f"\n📊 集合统计:")
        logger.info(f"  - 集合名: stock_daily_quotes")
        logger.info(f"  - 文档数量: {count}")
        logger.info(f"  - 索引数量: {len(indexes)}")
        
        logger.info(f"\n📋 索引列表:")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")
        
        logger.info("\n🎉 股票历史数据集合创建完成！")
        
        # 关闭连接
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建历史数据集合失败: {e}")
        return False


async def main():
    """主函数"""
    print("🎯 股票历史数据集合创建工具")
    print("📊 为Tushare、AKShare、BaoStock三数据源创建统一的历史数据存储")
    print("=" * 60)
    
    success = await create_historical_data_collection()
    
    if success:
        print("\n✅ 历史数据集合创建成功！")
        print("\n📝 集合结构:")
        print("  - 集合名: stock_daily_quotes")
        print("  - 用途: 存储股票历史K线数据")
        print("  - 支持: Tushare、AKShare、BaoStock三数据源")
        print("  - 索引: 7个高效查询索引")
        
        print("\n🔧 使用示例:")
        print("  # 查询单只股票历史数据")
        print("  db.stock_daily_quotes.find({\"symbol\": \"000001\"})")
        print("  ")
        print("  # 查询特定数据源的数据")
        print("  db.stock_daily_quotes.find({\"data_source\": \"tushare\"})")
        print("  ")
        print("  # 查询日期范围内的数据")
        print("  db.stock_daily_quotes.find({")
        print("    \"symbol\": \"000001\",")
        print("    \"trade_date\": {\"$gte\": \"2024-01-01\", \"$lte\": \"2024-12-31\"}")
        print("  })")
        
    else:
        print("\n❌ 历史数据集合创建失败，请检查MongoDB连接")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常退出: {e}")
        exit(1)
