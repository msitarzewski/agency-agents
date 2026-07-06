#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试从数据库获取新闻"""

import sys
import asyncio
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer

async def test_news_from_db():
    print("=" * 80)
    print("🧪 测试从数据库获取新闻")
    print("=" * 80)
    
    # 创建工具包
    toolkit = Toolkit()
    
    # 创建统一新闻分析器
    analyzer = UnifiedNewsAnalyzer(toolkit)
    
    # 测试获取 000001 的新闻（数据库中有）
    print("\n1️⃣ 测试获取 000001 的新闻（数据库中有）:")
    try:
        news_000001 = analyzer._get_news_from_database("000001", max_news=5)
        if news_000001:
            print(f"✅ 成功获取 000001 的新闻")
            print(f"📊 新闻长度: {len(news_000001)} 字符")
            print(f"📋 新闻预览 (前500字符):")
            print(news_000001[:500])
        else:
            print(f"❌ 未获取到 000001 的新闻")
    except Exception as e:
        print(f"❌ 获取 000001 新闻失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试获取 000002 的新闻（数据库中可能没有）
    print("\n2️⃣ 测试获取 000002 的新闻（数据库中可能没有）:")
    try:
        news_000002 = analyzer._get_news_from_database("000002", max_news=5)
        if news_000002:
            print(f"✅ 成功获取 000002 的新闻")
            print(f"📊 新闻长度: {len(news_000002)} 字符")
            print(f"📋 新闻预览 (前500字符):")
            print(news_000002[:500])
        else:
            print(f"⚠️ 数据库中没有 000002 的新闻")
    except Exception as e:
        print(f"❌ 获取 000002 新闻失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_news_from_db())

