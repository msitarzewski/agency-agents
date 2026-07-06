#!/usr/bin/env python3
"""检查 code=null 的记录"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db


async def main():
    await init_database()
    db = get_mongo_db()
    
    # 检查 code=null 的记录数
    null_count = await db.market_quotes.count_documents({'code': None})
    print(f"code=null 的记录数: {null_count}")
    
    if null_count == 0:
        print("✅ 修复成功！没有 code=null 的记录")
    else:
        print(f"⚠️ 还有 {null_count} 条 code=null 的记录")


if __name__ == "__main__":
    asyncio.run(main())

