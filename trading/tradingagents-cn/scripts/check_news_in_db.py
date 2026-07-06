#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库中的新闻数据"""

from pymongo import MongoClient
from datetime import datetime, timedelta

# 连接数据库
client = MongoClient('mongodb://admin:tradingagents123@localhost:27017/?authSource=admin')
db = client['tradingagents']

print("=" * 80)
print("📰 检查数据库中的新闻数据")
print("=" * 80)

# 1. 检查 stock_news 集合
print("\n1️⃣ 检查 stock_news 集合:")
news_count = db.stock_news.count_documents({})
print(f"总新闻数: {news_count}")

if news_count > 0:
    # 查看最新的几条新闻
    latest_news = list(db.stock_news.find().sort('publish_time', -1).limit(5))
    print(f"\n📋 最新 5 条新闻:")
    for i, news in enumerate(latest_news, 1):
        print(f"\n  新闻 {i}:")
        print(f"    - 股票代码: {news.get('stock_code')}")
        print(f"    - 标题: {news.get('title', '')[:50]}...")
        print(f"    - 发布时间: {news.get('publish_time')}")
        print(f"    - 来源: {news.get('source')}")
        print(f"    - 情绪: {news.get('sentiment')}")
    
    # 检查 000002 的新闻
    print(f"\n2️⃣ 检查 000002 的新闻:")
    news_000002 = list(db.stock_news.find({'stock_code': '000002'}).sort('publish_time', -1).limit(5))
    print(f"000002 新闻数: {len(news_000002)}")
    
    if news_000002:
        print(f"\n📋 000002 最新 5 条新闻:")
        for i, news in enumerate(news_000002, 1):
            print(f"\n  新闻 {i}:")
            print(f"    - 标题: {news.get('title', '')[:50]}...")
            print(f"    - 发布时间: {news.get('publish_time')}")
            print(f"    - 来源: {news.get('source')}")
    else:
        print("❌ 000002 没有新闻数据")
    
    # 检查最近7天的新闻
    print(f"\n3️⃣ 检查最近7天的新闻:")
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_news_count = db.stock_news.count_documents({
        'publish_time': {'$gte': seven_days_ago}
    })
    print(f"最近7天新闻数: {recent_news_count}")
    
else:
    print("❌ 数据库中没有新闻数据")

print("\n" + "=" * 80)
client.close()

