#!/usr/bin/env python3
"""
测试涨跌幅筛选
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


async def test_pct_chg_filter():
    """测试涨跌幅筛选"""
    try:
        await init_database()
        db = get_mongo_db()
        view = db["stock_screening_view"]
        
        # 测试1：直接查询视图，筛选涨跌幅在 0-8 之间的股票
        logger.info("=" * 60)
        logger.info("测试1：直接查询视图，筛选涨跌幅在 0-8 之间")
        logger.info("=" * 60)
        
        query = {
            "pct_chg": {"$gte": 0, "$lte": 8},
            "source": "tushare"
        }
        
        count = await view.count_documents(query)
        logger.info(f"✅ 找到 {count} 只股票")
        
        if count > 0:
            cursor = view.find(query).limit(5)
            logger.info("\n前5只股票:")
            async for doc in cursor:
                logger.info(f"  {doc.get('code')} {doc.get('name')}: "
                           f"pct_chg={doc.get('pct_chg')}, close={doc.get('close')}")
        
        # 测试2：查询涨跌幅字段不为空的记录
        logger.info("\n" + "=" * 60)
        logger.info("测试2：统计涨跌幅字段的数据情况")
        logger.info("=" * 60)
        
        total = await view.count_documents({"source": "tushare"})
        has_pct_chg = await view.count_documents({
            "pct_chg": {"$ne": None, "$exists": True},
            "source": "tushare"
        })
        
        logger.info(f"总记录数: {total}")
        logger.info(f"有 pct_chg 数据: {has_pct_chg} ({has_pct_chg/total*100:.1f}%)")
        
        # 测试3：查看 pct_chg 的值分布
        logger.info("\n" + "=" * 60)
        logger.info("测试3：pct_chg 值分布")
        logger.info("=" * 60)
        
        pipeline = [
            {"$match": {"source": "tushare", "pct_chg": {"$ne": None}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$pct_chg"},
                "max": {"$max": "$pct_chg"},
                "avg": {"$avg": "$pct_chg"},
                "count": {"$sum": 1}
            }}
        ]
        
        async for doc in view.aggregate(pipeline):
            logger.info(f"最小值: {doc.get('min'):.2f}%")
            logger.info(f"最大值: {doc.get('max'):.2f}%")
            logger.info(f"平均值: {doc.get('avg'):.2f}%")
            logger.info(f"记录数: {doc.get('count')}")
        
        # 测试4：查询涨跌幅 > 5% 的股票
        logger.info("\n" + "=" * 60)
        logger.info("测试4：查询涨跌幅 > 5% 的股票")
        logger.info("=" * 60)
        
        query = {
            "pct_chg": {"$gt": 5},
            "source": "tushare"
        }
        
        count = await view.count_documents(query)
        logger.info(f"✅ 找到 {count} 只股票")
        
        if count > 0:
            cursor = view.find(query).sort("pct_chg", -1).limit(10)
            logger.info("\n涨幅最大的10只股票:")
            async for doc in cursor:
                logger.info(f"  {doc.get('code')} {doc.get('name')}: "
                           f"pct_chg={doc.get('pct_chg'):.2f}%, close={doc.get('close')}")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await close_database()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_pct_chg_filter())
    exit(exit_code)

