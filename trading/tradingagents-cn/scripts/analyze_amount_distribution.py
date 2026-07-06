#!/usr/bin/env python3
"""
分析成交额分布
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


async def analyze_amount():
    """分析成交额分布"""
    try:
        await init_database()
        db = get_mongo_db()
        view = db["stock_screening_view"]
        
        # 统计成交额分布
        logger.info("=" * 60)
        logger.info("成交额分布分析")
        logger.info("=" * 60)
        
        pipeline = [
            {"$match": {"source": "tushare", "amount": {"$ne": None, "$gt": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$amount"},
                "max": {"$max": "$amount"},
                "avg": {"$avg": "$amount"},
                "count": {"$sum": 1}
            }}
        ]
        
        async for doc in view.aggregate(pipeline):
            logger.info(f"最小成交额: {doc.get('min'):.2f} 万元")
            logger.info(f"最大成交额: {doc.get('max'):.2f} 万元")
            logger.info(f"平均成交额: {doc.get('avg'):.2f} 万元")
            logger.info(f"总记录数: {doc.get('count')}")
        
        # 按成交额区间统计
        logger.info("\n" + "=" * 60)
        logger.info("成交额区间分布")
        logger.info("=" * 60)
        
        ranges = [
            ("< 1000万", 0, 1000),
            ("1000万 - 5000万", 1000, 5000),
            ("5000万 - 1亿", 5000, 10000),
            ("1亿 - 5亿", 10000, 50000),
            ("5亿 - 10亿", 50000, 100000),
            ("10亿 - 50亿", 100000, 500000),
            ("> 50亿", 500000, float('inf'))
        ]
        
        for label, min_val, max_val in ranges:
            if max_val == float('inf'):
                count = await view.count_documents({
                    "source": "tushare",
                    "amount": {"$gte": min_val}
                })
            else:
                count = await view.count_documents({
                    "source": "tushare",
                    "amount": {"$gte": min_val, "$lt": max_val}
                })
            logger.info(f"{label:20s}: {count:5d} 只股票")
        
        # 查看不同成交额区间的示例股票
        logger.info("\n" + "=" * 60)
        logger.info("各区间示例股票")
        logger.info("=" * 60)
        
        sample_ranges = [
            ("低成交额 (< 1000万)", 0, 1000),
            ("中等成交额 (1亿-5亿)", 10000, 50000),
            ("高成交额 (> 10亿)", 100000, float('inf'))
        ]
        
        for label, min_val, max_val in sample_ranges:
            logger.info(f"\n{label}:")
            if max_val == float('inf'):
                query = {"source": "tushare", "amount": {"$gte": min_val}}
            else:
                query = {"source": "tushare", "amount": {"$gte": min_val, "$lt": max_val}}
            
            cursor = view.find(query).sort("amount", -1).limit(3)
            async for doc in cursor:
                logger.info(f"  {doc.get('code')} {doc.get('name'):10s}: "
                           f"成交额={doc.get('amount')/10000:.2f}亿元, "
                           f"涨跌幅={doc.get('pct_chg'):.2f}%")
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await close_database()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(analyze_amount())
    exit(exit_code)

