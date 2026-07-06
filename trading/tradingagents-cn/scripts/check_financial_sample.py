import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongo_db, init_database

async def main():
    await init_database()
    db = get_mongo_db()
    
    # 随机取5条记录看看数据结构
    print("🔍 查看 stock_financial_data 集合样本数据...\n")
    
    cursor = db['stock_financial_data'].find().limit(5)
    async for doc in cursor:
        code = doc.get('code')
        name = doc.get('name')
        print(f"📊 {code} ({name}):")
        print(f"  更新时间: {doc.get('updated_at')}")
        
        # 检查财务指标
        indicators = doc.get('financial_indicators', [])
        if indicators:
            print(f"  财务指标记录数: {len(indicators)}")
            latest = indicators[0] if indicators else {}
            print(f"  最新一期:")
            print(f"    报告期: {latest.get('end_date')}")
            print(f"    ROE: {latest.get('roe')}")
        else:
            print(f"  ⚠️ 无财务指标数据")
        print()

if __name__ == '__main__':
    asyncio.run(main())

