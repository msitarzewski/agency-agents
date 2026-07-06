#!/usr/bin/env python3
"""检查数据库中的数据"""
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
import json


async def check():
    client = AsyncIOMotorClient(os.getenv('MONGODB_CONNECTION_STRING'))
    db = client[os.getenv('MONGODB_DATABASE_NAME')]
    
    code = sys.argv[1] if len(sys.argv) > 1 else '600036'
    
    print(f"检查股票: {code}\n")
    
    # 检查 stock_basic_info
    info = await db.stock_basic_info.find_one({'code': code})
    print("=" * 80)
    print("stock_basic_info:")
    print("=" * 80)
    if info:
        print(json.dumps(info, indent=2, default=str, ensure_ascii=False))
    else:
        print("未找到数据")
    
    # 检查 stock_financial_data
    fin = await db.stock_financial_data.find_one({'code': code})
    print("\n" + "=" * 80)
    print("stock_financial_data:")
    print("=" * 80)
    if fin:
        print(json.dumps(fin, indent=2, default=str, ensure_ascii=False))
    else:
        print("未找到数据")
    
    # 检查 market_quotes
    quote = await db.market_quotes.find_one({'code': code})
    print("\n" + "=" * 80)
    print("market_quotes:")
    print("=" * 80)
    if quote:
        print(json.dumps(quote, indent=2, default=str, ensure_ascii=False))
    else:
        print("未找到数据")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(check())

