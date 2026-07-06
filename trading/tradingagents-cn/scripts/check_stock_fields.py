#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查股票基础信息字段"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_mongo_db, init_database


async def check_fields():
    """检查股票基础信息字段"""
    await init_database()
    db = get_mongo_db()
    
    doc = await db['stock_basic_info'].find_one(
        {'code': '000001'}, 
        {'_id': 0, 'code': 1, 'name': 1, 'industry': 1, 'market': 1, 'sse': 1, 'sec': 1, 'sector': 1}
    )
    
    print('\n股票基础信息字段示例 (000001 平安银行):')
    print('=' * 80)
    print(f'  code (代码): {doc.get("code")}')
    print(f'  name (名称): {doc.get("name")}')
    print(f'  industry (行业): {doc.get("industry")}')
    print(f'  market (交易所): {doc.get("market")}')
    print(f'  sse (板块): {doc.get("sse")}')
    print(f'  sec (分类): {doc.get("sec")}')
    print(f'  sector (板块): {doc.get("sector")}')
    print('=' * 80)
    
    print('\n字段说明:')
    print('  - industry: 所属行业（如：银行、软件服务等）')
    print('  - market: 交易所/市场（如：主板、创业板、科创板等）')
    print('  - sse: 板块标识（如：sz、sh等）')
    print('  - sec: 分类标识（如：stock_cn等）')
    print('  - sector: 板块（扩展字段，可能为空）')


if __name__ == "__main__":
    asyncio.run(check_fields())

