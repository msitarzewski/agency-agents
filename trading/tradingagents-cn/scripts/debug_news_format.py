#!/usr/bin/env python3
"""
调试新闻数据格式
"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.providers.tushare_provider import get_tushare_provider


async def debug_news_format():
    """调试新闻数据格式"""
    print("=" * 60)
    print("🔍 调试新闻数据格式")
    print("=" * 60)
    print()
    
    try:
        # 1. 获取 Tushare Provider
        provider = get_tushare_provider()
        await provider.connect()
        print("✅ Tushare连接成功")
        print()
        
        # 2. 获取测试股票的新闻
        test_symbol = "000001"
        print(f"🔍 获取 {test_symbol} 的新闻数据...")
        print()
        
        news_data = await provider.get_stock_news(
            symbol=test_symbol,
            limit=5,
            hours_back=24
        )
        
        # 3. 显示新闻数据
        if news_data:
            print(f"✅ 获取到 {len(news_data)} 条新闻")
            print()
            
            for i, news in enumerate(news_data, 1):
                print(f"📰 新闻 {i}:")
                print(json.dumps(news, indent=2, ensure_ascii=False, default=str))
                print()
        else:
            print("⚠️ 未获取到新闻数据")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_news_format())

