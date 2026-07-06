#!/usr/bin/env python3
"""
创建消息数据集合和索引
包括社媒消息和内部消息的数据库结构设置
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import get_database, init_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_social_media_collection():
    """创建社媒消息集合和索引"""
    try:
        db = get_database()
        collection = db.social_media_messages
        
        logger.info("🔧 创建社媒消息集合索引...")
        
        # 1. 唯一索引 - 防止重复消息
        unique_index = [
            ("message_id", 1),
            ("platform", 1)
        ]
        await collection.create_index(unique_index, unique=True, name="message_platform_unique")
        logger.info("✅ 创建唯一索引: message_id + platform")
        
        # 2. 股票代码索引
        await collection.create_index("symbol", name="symbol_index")
        logger.info("✅ 创建股票代码索引")
        
        # 3. 时间索引
        await collection.create_index("publish_time", name="publish_time_index")
        await collection.create_index([("publish_time", -1)], name="publish_time_desc")
        logger.info("✅ 创建时间索引")
        
        # 4. 平台和消息类型索引
        await collection.create_index("platform", name="platform_index")
        await collection.create_index("message_type", name="message_type_index")
        await collection.create_index([("platform", 1), ("message_type", 1)], name="platform_type_index")
        logger.info("✅ 创建平台和消息类型索引")
        
        # 5. 情绪和重要性索引
        await collection.create_index("sentiment", name="sentiment_index")
        await collection.create_index("importance", name="importance_index")
        await collection.create_index([("sentiment", 1), ("importance", 1)], name="sentiment_importance_index")
        logger.info("✅ 创建情绪和重要性索引")
        
        # 6. 作者相关索引
        await collection.create_index("author.user_id", name="author_user_id_index")
        await collection.create_index("author.verified", name="author_verified_index")
        await collection.create_index("author.influence_score", name="author_influence_index")
        logger.info("✅ 创建作者相关索引")
        
        # 7. 互动数据索引
        await collection.create_index("engagement.engagement_rate", name="engagement_rate_index")
        await collection.create_index("engagement.likes", name="likes_index")
        await collection.create_index("engagement.views", name="views_index")
        logger.info("✅ 创建互动数据索引")
        
        # 8. 复合查询索引
        await collection.create_index([
            ("symbol", 1),
            ("platform", 1),
            ("publish_time", -1)
        ], name="symbol_platform_time_index")
        
        await collection.create_index([
            ("symbol", 1),
            ("sentiment", 1),
            ("publish_time", -1)
        ], name="symbol_sentiment_time_index")
        
        await collection.create_index([
            ("platform", 1),
            ("author.verified", 1),
            ("publish_time", -1)
        ], name="platform_verified_time_index")
        logger.info("✅ 创建复合查询索引")
        
        # 9. 标签和关键词索引
        await collection.create_index("hashtags", name="hashtags_index")
        await collection.create_index("keywords", name="keywords_index")
        await collection.create_index("topics", name="topics_index")
        logger.info("✅ 创建标签和关键词索引")
        
        # 10. 全文搜索索引
        text_index = [
            ("content", "text"),
            ("hashtags", "text"),
            ("keywords", "text"),
            ("topics", "text")
        ]
        await collection.create_index(text_index, name="content_text_search")
        logger.info("✅ 创建全文搜索索引")
        
        # 11. 地理位置索引
        await collection.create_index("location.country", name="location_country_index")
        await collection.create_index("location.city", name="location_city_index")
        logger.info("✅ 创建地理位置索引")
        
        # 12. 数据源和爬虫版本索引
        await collection.create_index("data_source", name="data_source_index")
        await collection.create_index("crawler_version", name="crawler_version_index")
        logger.info("✅ 创建数据源索引")
        
        logger.info("🎉 社媒消息集合索引创建完成!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 社媒消息集合创建失败: {e}")
        return False


async def create_internal_messages_collection():
    """创建内部消息集合和索引"""
    try:
        db = get_database()
        collection = db.internal_messages
        
        logger.info("🔧 创建内部消息集合索引...")
        
        # 1. 唯一索引 - 防止重复消息
        await collection.create_index("message_id", unique=True, name="message_id_unique")
        logger.info("✅ 创建唯一索引: message_id")
        
        # 2. 股票代码索引
        await collection.create_index("symbol", name="symbol_index")
        logger.info("✅ 创建股票代码索引")
        
        # 3. 时间索引
        await collection.create_index("created_time", name="created_time_index")
        await collection.create_index([("created_time", -1)], name="created_time_desc")
        await collection.create_index("effective_time", name="effective_time_index")
        await collection.create_index("expiry_time", name="expiry_time_index")
        logger.info("✅ 创建时间索引")
        
        # 4. 消息类型和分类索引
        await collection.create_index("message_type", name="message_type_index")
        await collection.create_index("category", name="category_index")
        await collection.create_index("subcategory", name="subcategory_index")
        await collection.create_index([("message_type", 1), ("category", 1)], name="type_category_index")
        logger.info("✅ 创建消息类型和分类索引")
        
        # 5. 来源信息索引
        await collection.create_index("source.type", name="source_type_index")
        await collection.create_index("source.department", name="source_department_index")
        await collection.create_index("source.author", name="source_author_index")
        await collection.create_index("source.reliability", name="source_reliability_index")
        logger.info("✅ 创建来源信息索引")
        
        # 6. 重要性和影响索引
        await collection.create_index("importance", name="importance_index")
        await collection.create_index("impact_scope", name="impact_scope_index")
        await collection.create_index("time_sensitivity", name="time_sensitivity_index")
        await collection.create_index("confidence_level", name="confidence_level_index")
        logger.info("✅ 创建重要性和影响索引")
        
        # 7. 访问控制索引
        await collection.create_index("access_level", name="access_level_index")
        await collection.create_index("permissions", name="permissions_index")
        logger.info("✅ 创建访问控制索引")
        
        # 8. 评级和相关数据索引
        await collection.create_index("related_data.rating", name="rating_index")
        await collection.create_index("related_data.financial_metrics", name="financial_metrics_index")
        logger.info("✅ 创建评级和相关数据索引")
        
        # 9. 复合查询索引
        await collection.create_index([
            ("symbol", 1),
            ("message_type", 1),
            ("created_time", -1)
        ], name="symbol_type_time_index")
        
        await collection.create_index([
            ("symbol", 1),
            ("importance", 1),
            ("created_time", -1)
        ], name="symbol_importance_time_index")
        
        await collection.create_index([
            ("source.department", 1),
            ("message_type", 1),
            ("created_time", -1)
        ], name="department_type_time_index")
        
        await collection.create_index([
            ("access_level", 1),
            ("importance", 1),
            ("created_time", -1)
        ], name="access_importance_time_index")
        logger.info("✅ 创建复合查询索引")
        
        # 10. 标签和关键词索引
        await collection.create_index("tags", name="tags_index")
        await collection.create_index("keywords", name="keywords_index")
        await collection.create_index("risk_factors", name="risk_factors_index")
        await collection.create_index("opportunities", name="opportunities_index")
        logger.info("✅ 创建标签和关键词索引")
        
        # 11. 全文搜索索引
        text_index = [
            ("title", "text"),
            ("content", "text"),
            ("summary", "text"),
            ("keywords", "text"),
            ("tags", "text")
        ]
        await collection.create_index(text_index, name="content_text_search")
        logger.info("✅ 创建全文搜索索引")
        
        # 12. 数据源索引
        await collection.create_index("data_source", name="data_source_index")
        logger.info("✅ 创建数据源索引")
        
        logger.info("🎉 内部消息集合索引创建完成!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 内部消息集合创建失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始创建消息数据集合...")

    try:
        # 初始化数据库连接
        await init_db()
        logger.info("✅ 数据库连接初始化成功")
        # 创建社媒消息集合
        social_media_success = await create_social_media_collection()
        
        # 创建内部消息集合
        internal_messages_success = await create_internal_messages_collection()
        
        # 汇总结果
        logger.info("\n" + "="*60)
        logger.info("🎯 消息数据集合创建结果汇总")
        logger.info("="*60)
        
        social_status = "✅ 成功" if social_media_success else "❌ 失败"
        internal_status = "✅ 成功" if internal_messages_success else "❌ 失败"
        
        logger.info(f"社媒消息集合 (social_media_messages): {social_status}")
        logger.info(f"内部消息集合 (internal_messages): {internal_status}")
        
        if social_media_success and internal_messages_success:
            logger.info("🎉 所有消息数据集合创建成功!")
            logger.info("\n📊 集合统计:")
            logger.info("   - social_media_messages: 12个索引")
            logger.info("   - internal_messages: 12个索引")
            logger.info("\n🚀 消息数据系统已准备就绪!")
        else:
            logger.warning("⚠️ 部分集合创建失败，请检查错误信息")
        
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 消息数据集合创建过程异常: {e}")


if __name__ == "__main__":
    asyncio.run(main())
