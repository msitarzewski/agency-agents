#!/usr/bin/env python3
"""
创建新闻数据集合和索引
根据设计文档创建stock_news集合的完整数据库结构
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.core.database import init_db, get_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_news_collection():
    """创建新闻数据集合和索引"""
    logger.info("🚀 开始创建新闻数据集合...")
    
    try:
        # 初始化数据库连接
        await init_db()

        # 获取数据库连接
        db = get_database()
        collection = db.stock_news
        
        logger.info("📊 创建新闻数据集合索引...")
        
        # 1. 唯一索引：防止重复新闻
        unique_index = [
            ("url", 1),
            ("title", 1),
            ("publish_time", 1)
        ]
        await collection.create_index(
            unique_index, 
            unique=True, 
            name="url_title_time_unique",
            background=True
        )
        logger.info("✅ 创建唯一索引: url_title_time_unique")
        
        # 2. 股票代码索引
        await collection.create_index(
            [("symbol", 1)], 
            name="symbol_index",
            background=True
        )
        logger.info("✅ 创建股票代码索引: symbol_index")
        
        # 3. 多股票代码索引
        await collection.create_index(
            [("symbols", 1)], 
            name="symbols_index",
            background=True
        )
        logger.info("✅ 创建多股票代码索引: symbols_index")
        
        # 4. 发布时间索引（用于时间范围查询）
        await collection.create_index(
            [("publish_time", -1)], 
            name="publish_time_desc",
            background=True
        )
        logger.info("✅ 创建发布时间索引: publish_time_desc")
        
        # 5. 复合索引：股票+时间（最常用查询）
        await collection.create_index(
            [("symbol", 1), ("publish_time", -1)], 
            name="symbol_time_desc",
            background=True
        )
        logger.info("✅ 创建股票时间复合索引: symbol_time_desc")
        
        # 6. 复合索引：多股票+时间
        await collection.create_index(
            [("symbols", 1), ("publish_time", -1)], 
            name="symbols_time_desc",
            background=True
        )
        logger.info("✅ 创建多股票时间复合索引: symbols_time_desc")
        
        # 7. 新闻类别索引
        await collection.create_index(
            [("category", 1)], 
            name="category_index",
            background=True
        )
        logger.info("✅ 创建新闻类别索引: category_index")
        
        # 8. 情绪分析索引
        await collection.create_index(
            [("sentiment", 1)], 
            name="sentiment_index",
            background=True
        )
        logger.info("✅ 创建情绪分析索引: sentiment_index")
        
        # 9. 重要性索引
        await collection.create_index(
            [("importance", 1)], 
            name="importance_index",
            background=True
        )
        logger.info("✅ 创建重要性索引: importance_index")
        
        # 10. 数据源索引
        await collection.create_index(
            [("data_source", 1)], 
            name="data_source_index",
            background=True
        )
        logger.info("✅ 创建数据源索引: data_source_index")
        
        # 11. 复合索引：股票+类别+时间
        await collection.create_index(
            [("symbol", 1), ("category", 1), ("publish_time", -1)], 
            name="symbol_category_time",
            background=True
        )
        logger.info("✅ 创建股票类别时间复合索引: symbol_category_time")
        
        # 12. 复合索引：情绪+重要性+时间（用于情绪分析查询）
        await collection.create_index(
            [("sentiment", 1), ("importance", 1), ("publish_time", -1)], 
            name="sentiment_importance_time",
            background=True
        )
        logger.info("✅ 创建情绪重要性时间复合索引: sentiment_importance_time")
        
        # 13. 文本搜索索引
        await collection.create_index(
            [("title", "text"), ("content", "text"), ("summary", "text")], 
            name="text_search_index",
            background=True
        )
        logger.info("✅ 创建文本搜索索引: text_search_index")
        
        # 14. 创建时间索引（用于数据管理）
        await collection.create_index(
            [("created_at", -1)], 
            name="created_at_desc",
            background=True
        )
        logger.info("✅ 创建创建时间索引: created_at_desc")
        
        # 验证索引创建
        indexes = await collection.list_indexes().to_list(length=None)
        logger.info(f"📊 新闻数据集合索引创建完成，共 {len(indexes)} 个索引:")
        for idx in indexes:
            logger.info(f"   - {idx['name']}: {idx.get('key', {})}")
        
        # 插入示例数据
        await insert_sample_news_data(collection)
        
        logger.info("🎉 新闻数据集合创建完成!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建新闻数据集合失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def insert_sample_news_data(collection):
    """插入示例新闻数据"""
    logger.info("📝 插入示例新闻数据...")
    
    try:
        sample_news = [
            {
                "symbol": "000001",
                "full_symbol": "000001.SZ",
                "market": "CN",
                "symbols": ["000001"],
                "title": "平安银行发布2024年三季度业绩报告",
                "content": "平安银行股份有限公司今日发布2024年第三季度业绩报告，前三季度实现营业收入1,234.56亿元，同比增长5.2%，净利润456.78亿元，同比增长3.8%。",
                "summary": "平安银行三季度业绩稳健增长，营收净利双增",
                "url": "https://example.com/news/pingan-q3-2024",
                "source": "证券时报",
                "author": "财经记者",
                "publish_time": datetime(2024, 10, 25, 9, 0, 0),
                "category": "company_announcement",
                "sentiment": "positive",
                "sentiment_score": 0.75,
                "keywords": ["业绩报告", "营业收入", "净利润", "增长"],
                "importance": "high",
                "language": "zh-CN",
                "created_at": datetime.utcnow(),
                "data_source": "tushare",
                "version": 1
            },
            {
                "symbol": "000002",
                "full_symbol": "000002.SZ",
                "market": "CN",
                "symbols": ["000002"],
                "title": "万科A：房地产市场回暖，销售额环比上升",
                "content": "万科企业股份有限公司最新数据显示，10月份销售额环比上升15%，显示房地产市场出现回暖迹象。",
                "summary": "万科A销售数据向好，房地产市场现回暖信号",
                "url": "https://example.com/news/vanke-sales-oct-2024",
                "source": "财联社",
                "author": "地产记者",
                "publish_time": datetime(2024, 11, 1, 14, 30, 0),
                "category": "market_news",
                "sentiment": "positive",
                "sentiment_score": 0.65,
                "keywords": ["房地产", "销售额", "回暖", "环比上升"],
                "importance": "medium",
                "language": "zh-CN",
                "created_at": datetime.utcnow(),
                "data_source": "akshare",
                "version": 1
            },
            {
                "symbol": None,  # 市场新闻
                "full_symbol": None,
                "market": "CN",
                "symbols": ["000001", "000002", "600000", "600036"],
                "title": "央行降准释放流动性，银行股集体上涨",
                "content": "中国人民银行宣布下调存款准备金率0.25个百分点，释放长期流动性约5000亿元，银行股集体响应上涨。",
                "summary": "央行降准政策利好银行股，板块集体上涨",
                "url": "https://example.com/news/pboc-rrr-cut-2024",
                "source": "新华财经",
                "author": "宏观记者",
                "publish_time": datetime(2024, 11, 15, 16, 0, 0),
                "category": "policy_news",
                "sentiment": "positive",
                "sentiment_score": 0.85,
                "keywords": ["央行", "降准", "流动性", "银行股", "上涨"],
                "importance": "high",
                "language": "zh-CN",
                "created_at": datetime.utcnow(),
                "data_source": "finnhub",
                "version": 1
            }
        ]
        
        # 使用upsert避免重复插入
        for news in sample_news:
            await collection.replace_one(
                {
                    "url": news["url"],
                    "title": news["title"],
                    "publish_time": news["publish_time"]
                },
                news,
                upsert=True
            )
        
        logger.info(f"✅ 插入 {len(sample_news)} 条示例新闻数据")
        
    except Exception as e:
        logger.error(f"❌ 插入示例数据失败: {e}")


async def main():
    """主函数"""
    logger.info("🚀 开始新闻数据集合初始化...")
    
    success = await create_news_collection()
    
    if success:
        logger.info("🎉 新闻数据集合初始化完成!")
        print("\n✅ 新闻数据集合创建成功!")
        print("📊 已创建的索引:")
        print("   - 唯一索引: url_title_time_unique")
        print("   - 基础索引: symbol, symbols, publish_time, category, sentiment")
        print("   - 复合索引: symbol_time, symbols_time, symbol_category_time")
        print("   - 文本搜索索引: title, content, summary")
        print("   - 管理索引: created_at, data_source, importance")
        print("\n📝 已插入示例数据，可用于测试")
    else:
        logger.error("❌ 新闻数据集合初始化失败!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
