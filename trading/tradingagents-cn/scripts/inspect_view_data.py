#!/usr/bin/env python3
"""
检查视图数据
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from app.core.database import init_database, get_mongo_db, close_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def inspect_view():
    """检查视图数据"""
    try:
        await init_database()
        db = get_mongo_db()
        view = db["stock_screening_view"]
        
        # 查询几条示例数据
        logger.info("=" * 60)
        logger.info("查询视图中的示例数据")
        logger.info("=" * 60)
        
        cursor = view.find().limit(5)
        count = 0
        async for doc in cursor:
            count += 1
            logger.info(f"\n示例 {count}:")
            logger.info(f"  code: {doc.get('code')}")
            logger.info(f"  name: {doc.get('name')}")
            logger.info(f"  source: {doc.get('source')}")
            logger.info(f"  industry: {doc.get('industry')}")
            logger.info(f"  total_mv: {doc.get('total_mv')}")
            logger.info(f"  pe: {doc.get('pe')}")
            logger.info(f"  pb: {doc.get('pb')}")
            logger.info(f"  roe: {doc.get('roe')}")
            logger.info(f"  close: {doc.get('close')}")
            logger.info(f"  pct_chg: {doc.get('pct_chg')}")
            logger.info(f"  amount: {doc.get('amount')}")
        
        # 统计各数据源的数量
        logger.info("\n" + "=" * 60)
        logger.info("统计各数据源的数量")
        logger.info("=" * 60)
        
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        async for doc in view.aggregate(pipeline):
            logger.info(f"  {doc['_id']}: {doc['count']} 条")
        
        # 统计有 ROE 数据的记录数
        logger.info("\n" + "=" * 60)
        logger.info("统计有 ROE 数据的记录数")
        logger.info("=" * 60)
        
        total = await view.count_documents({})
        has_roe = await view.count_documents({"roe": {"$ne": None, "$exists": True}})
        has_pct_chg = await view.count_documents({"pct_chg": {"$ne": None, "$exists": True}})
        has_amount = await view.count_documents({"amount": {"$ne": None, "$exists": True}})
        
        logger.info(f"  总记录数: {total}")
        logger.info(f"  有 ROE 数据: {has_roe} ({has_roe/total*100:.1f}%)")
        logger.info(f"  有 pct_chg 数据: {has_pct_chg} ({has_pct_chg/total*100:.1f}%)")
        logger.info(f"  有 amount 数据: {has_amount} ({has_amount/total*100:.1f}%)")
        
        # 查询有 ROE 和 pct_chg 的记录
        logger.info("\n" + "=" * 60)
        logger.info("查询有 ROE 和 pct_chg 的记录")
        logger.info("=" * 60)
        
        query = {
            "roe": {"$ne": None, "$exists": True, "$gt": 0},
            "pct_chg": {"$ne": None, "$exists": True}
        }
        
        count_with_both = await view.count_documents(query)
        logger.info(f"  同时有 ROE 和 pct_chg 的记录: {count_with_both}")
        
        if count_with_both > 0:
            logger.info("\n  示例数据:")
            cursor = view.find(query).limit(3)
            async for doc in cursor:
                logger.info(f"    {doc.get('code')} {doc.get('name')}: "
                           f"ROE={doc.get('roe')}, pct_chg={doc.get('pct_chg')}, "
                           f"source={doc.get('source')}")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await close_database()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(inspect_view())
    exit(exit_code)

