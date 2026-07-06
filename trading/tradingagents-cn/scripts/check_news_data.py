#!/usr/bin/env python3
"""
检查新闻数据库中的数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_db, get_database
from datetime import datetime, timedelta


async def check_news_data():
    """检查新闻数据"""
    print("=" * 80)
    print("📰 检查新闻数据库")
    print("=" * 80)
    
    try:
        # 初始化数据库
        await init_db()
        db = get_database()
        collection = db.stock_news
        
        # 1. 统计总数
        total_count = await collection.count_documents({})
        print(f"\n📊 新闻总数: {total_count}")
        
        if total_count == 0:
            print("\n❌ 数据库中没有新闻数据！")
            print("\n💡 建议：")
            print("   1. 运行新闻同步脚本：python scripts/sync_market_news.py")
            print("   2. 或在前端仪表板点击「同步市场新闻」按钮")
            print("   3. 或调用 API：POST /api/news-data/sync/start")
            return
        
        # 2. 按数据源统计
        print("\n📊 按数据源统计:")
        pipeline = [
            {"$group": {"_id": "$data_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        sources = await collection.aggregate(pipeline).to_list(length=None)
        for source in sources:
            print(f"   - {source['_id']}: {source['count']} 条")
        
        # 3. 最新的10条新闻
        print("\n📰 最新的 10 条新闻:")
        latest_news = await collection.find({}).sort("publish_time", -1).limit(10).to_list(length=10)
        for i, news in enumerate(latest_news, 1):
            publish_time = news.get('publish_time', 'N/A')
            if isinstance(publish_time, datetime):
                publish_time = publish_time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n   {i}. {news.get('title', 'N/A')}")
            print(f"      来源: {news.get('source', 'N/A')}")
            print(f"      时间: {publish_time}")
            print(f"      股票: {news.get('symbol', 'N/A')}")
            print(f"      URL: {news.get('url', 'N/A')[:80]}...")
        
        # 4. 检查最近24小时的新闻
        print("\n⏰ 最近 24 小时的新闻:")
        start_time = datetime.utcnow() - timedelta(hours=24)
        recent_count = await collection.count_documents({
            "publish_time": {"$gte": start_time}
        })
        print(f"   数量: {recent_count} 条")
        
        if recent_count == 0:
            print("\n⚠️ 最近 24 小时没有新闻数据！")
            print("   建议运行新闻同步脚本更新数据")
        
        # 5. 检查索引
        print("\n📑 数据库索引:")
        indexes = await collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"   - {idx['name']}")
        
        print("\n" + "=" * 80)
        print("✅ 检查完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_news_data())

