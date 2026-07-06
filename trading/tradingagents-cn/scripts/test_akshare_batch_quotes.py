#!/usr/bin/env python3
"""测试 AKShare 批量获取行情功能"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database
from tradingagents.dataflows.providers.china.akshare import AKShareProvider


async def main():
    print("🔧 测试 AKShare 批量获取行情功能...")
    
    # 初始化数据库
    await init_database()
    
    # 创建 Provider
    provider = AKShareProvider()
    await provider.connect()
    
    # 测试股票列表（包含一些科创板股票）
    test_codes = [
        "000001",  # 平安银行
        "600000",  # 浦发银行
        "688485",  # 科创板
        "688502",  # 科创板
        "688484",  # 科创板
        "603175",  # 测试股票
    ]
    
    print(f"\n📊 测试批量获取 {len(test_codes)} 只股票的行情...")
    print(f"   股票列表: {test_codes}")
    
    # 批量获取
    quotes_map = await provider.get_batch_stock_quotes(test_codes)
    
    print(f"\n✅ 获取完成: 找到 {len(quotes_map)} 只股票的行情")
    
    # 显示结果
    for code in test_codes:
        if code in quotes_map:
            quote = quotes_map[code]
            print(f"\n✅ {code} - {quote.get('name')}")
            print(f"   价格: {quote.get('price')}")
            print(f"   涨跌幅: {quote.get('change_percent')}%")
            print(f"   成交量: {quote.get('volume')}")
        else:
            print(f"\n❌ {code} - 未找到行情数据")
    
    await provider.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

