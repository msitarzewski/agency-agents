#!/usr/bin/env python3
"""
检查成交额单位
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


async def check_amount_unit():
    """检查成交额单位"""
    try:
        await init_database()
        db = get_mongo_db()
        
        # 检查 market_quotes 集合
        logger.info("=" * 60)
        logger.info("检查 market_quotes 集合中的 amount 字段")
        logger.info("=" * 60)
        
        quotes = db["market_quotes"]
        cursor = quotes.find({"amount": {"$ne": None, "$gt": 0}}).limit(10)
        
        async for doc in cursor:
            logger.info(f"{doc.get('code')} {doc.get('name', 'N/A'):10s}: "
                       f"amount={doc.get('amount')}, "
                       f"volume={doc.get('volume')}, "
                       f"close={doc.get('close')}")
        
        # 检查视图
        logger.info("\n" + "=" * 60)
        logger.info("检查 stock_screening_view 视图中的 amount 字段")
        logger.info("=" * 60)
        
        view = db["stock_screening_view"]
        cursor = view.find({"amount": {"$ne": None, "$gt": 0}, "source": "tushare"}).limit(10)
        
        async for doc in cursor:
            logger.info(f"{doc.get('code')} {doc.get('name'):10s}: "
                       f"amount={doc.get('amount')}, "
                       f"volume={doc.get('volume')}, "
                       f"close={doc.get('close')}")
        
        # 计算一个合理的成交额（成交量 * 收盘价）
        logger.info("\n" + "=" * 60)
        logger.info("验证成交额计算（成交量 * 收盘价）")
        logger.info("=" * 60)
        
        cursor = view.find({
            "amount": {"$ne": None, "$gt": 0},
            "volume": {"$ne": None, "$gt": 0},
            "close": {"$ne": None, "$gt": 0},
            "source": "tushare"
        }).limit(5)
        
        async for doc in cursor:
            amount = doc.get('amount')
            volume = doc.get('volume')
            close = doc.get('close')
            
            # 计算理论成交额（假设 volume 单位是手，1手=100股）
            calculated_amount_yuan = volume * 100 * close  # 元
            calculated_amount_wan = calculated_amount_yuan / 10000  # 万元
            
            logger.info(f"\n{doc.get('code')} {doc.get('name')}:")
            logger.info(f"  数据库 amount: {amount:,.0f}")
            logger.info(f"  成交量: {volume:,.0f} 手")
            logger.info(f"  收盘价: {close:.2f} 元")
            logger.info(f"  计算的成交额: {calculated_amount_yuan:,.0f} 元 = {calculated_amount_wan:,.0f} 万元")
            logger.info(f"  比率: {amount / calculated_amount_wan:.2f}x")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await close_database()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(check_amount_unit())
    exit(exit_code)

