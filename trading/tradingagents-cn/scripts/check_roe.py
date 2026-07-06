import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongo_db, init_database

async def main():
    await init_database()
    db = get_mongo_db()
    
    codes = ['601398', '300033', '000001']
    
    for code in codes:
        doc = await db['stock_basic_info'].find_one({'code': code})
        if doc:
            print(f"\n{code} ({doc.get('name')}):")
            print(f"  pe: {doc.get('pe')}")
            print(f"  pb: {doc.get('pb')}")
            print(f"  roe: {doc.get('roe')}")
            print(f"  total_mv: {doc.get('total_mv')}")
        else:
            print(f"\n{code}: 未找到数据")

if __name__ == '__main__':
    asyncio.run(main())

