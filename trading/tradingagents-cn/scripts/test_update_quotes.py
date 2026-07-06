#!/usr/bin/env python3
"""测试更新行情功能"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db
from app.services.stock_data_service import get_stock_data_service


async def main():
    print("🔧 测试更新行情功能...")
    
    # 初始化数据库
    await init_database()
    
    # 获取服务
    service = get_stock_data_service()
    
    # 测试数据（不包含 code 字段）
    quote_data = {
        "price": 10.5,
        "volume": 1000000,
        "change": 0.5,
        "change_pct": 5.0,
        # 注意：不包含 code 字段
    }
    
    # 测试更新
    print(f"\n📊 测试更新股票 603175 的行情...")
    print(f"   数据: {quote_data}")
    
    success = await service.update_market_quotes("603175", quote_data)
    
    if success:
        print("✅ 更新成功")
        
        # 验证数据
        db = get_mongo_db()
        record = await db.market_quotes.find_one({"symbol": "603175"})
        
        if record:
            print(f"\n📋 验证数据:")
            print(f"   symbol: {record.get('symbol')}")
            print(f"   code: {record.get('code')}")
            print(f"   price: {record.get('price')}")
            
            if record.get('code') == "603175":
                print("\n✅ code 字段正确设置！")
            else:
                print(f"\n❌ code 字段错误: {record.get('code')}")
        else:
            print("❌ 未找到记录")
    else:
        print("❌ 更新失败")
    
    # 检查是否还有 code=null 的记录
    db = get_mongo_db()
    null_count = await db.market_quotes.count_documents({'code': None})
    print(f"\n📊 code=null 的记录数: {null_count}")
    
    if null_count == 0:
        print("✅ 没有 code=null 的记录")
    else:
        print(f"⚠️ 还有 {null_count} 条 code=null 的记录")


if __name__ == "__main__":
    asyncio.run(main())

