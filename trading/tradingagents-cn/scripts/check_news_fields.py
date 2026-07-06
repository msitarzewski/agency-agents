#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库中新闻数据的字段"""

from pymongo import MongoClient

# 连接数据库
client = MongoClient('mongodb://admin:tradingagents123@localhost:27017/?authSource=admin')
db = client['tradingagents']

print("=" * 80)
print("📰 检查数据库中新闻数据的字段")
print("=" * 80)

# 查看一条新闻的完整字段
news = db.stock_news.find_one()

if news:
    print(f"\n📋 新闻字段列表:")
    for key in sorted(news.keys()):
        value = news.get(key)
        value_type = type(value).__name__
        
        # 显示值的预览
        if isinstance(value, str):
            value_preview = value[:50] + '...' if len(value) > 50 else value
        elif isinstance(value, list):
            value_preview = f"[{len(value)} items]"
        elif isinstance(value, dict):
            value_preview = f"{{...}}"
        else:
            value_preview = str(value)
        
        print(f"  - {key:20s} ({value_type:15s}): {value_preview}")
    
    # 检查是否有 symbol 或 stock_code 字段
    print(f"\n🔍 关键字段检查:")
    print(f"  - symbol: {news.get('symbol')}")
    print(f"  - stock_code: {news.get('stock_code')}")
    print(f"  - symbols: {news.get('symbols')}")
    print(f"  - full_symbol: {news.get('full_symbol')}")
    
else:
    print("❌ 数据库中没有新闻数据")

print("\n" + "=" * 80)
client.close()

