#!/usr/bin/env python3
"""
检查宁德时代的数据
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


async def check_ningde():
    """检查宁德时代的数据"""
    try:
        await init_database()
        db = get_mongo_db()
        
        # 检查 market_quotes 集合
        logger.info("=" * 60)
        logger.info("market_quotes 集合中的宁德时代数据")
        logger.info("=" * 60)
        
        quotes = db["market_quotes"]
        doc = await quotes.find_one({"code": "300750"})
        
        if doc:
            logger.info(f"code: {doc.get('code')}")
            logger.info(f"name: {doc.get('name')}")
            logger.info(f"amount: {doc.get('amount')}")
            logger.info(f"volume: {doc.get('volume')}")
            logger.info(f"close: {doc.get('close')}")
            
            # 计算验证
            amount = doc.get('amount', 0)
            volume = doc.get('volume', 0)
            close = doc.get('close', 0)
            
            logger.info("\n验证计算：")
            logger.info(f"如果 volume 是股数: {volume} 股 × {close} 元/股 = {volume * close:,.2f} 元")
            logger.info(f"如果 volume 是手数: {volume} 手 × 100 股/手 × {close} 元/股 = {volume * 100 * close:,.2f} 元")
            logger.info(f"数据库 amount: {amount:,.2f}")
            logger.info(f"amount / (volume × close) = {amount / (volume * close):.2f}")
            logger.info(f"amount / (volume × 100 × close) = {amount / (volume * 100 * close):.2f}")
        else:
            logger.warning("未找到宁德时代数据")
        
        # 检查视图
        logger.info("\n" + "=" * 60)
        logger.info("stock_screening_view 视图中的宁德时代数据")
        logger.info("=" * 60)
        
        view = db["stock_screening_view"]
        doc = await view.find_one({"code": "300750"})
        
        if doc:
            logger.info(f"code: {doc.get('code')}")
            logger.info(f"name: {doc.get('name')}")
            logger.info(f"amount: {doc.get('amount')}")
            logger.info(f"volume: {doc.get('volume')}")
            logger.info(f"close: {doc.get('close')}")
        else:
            logger.warning("未找到宁德时代数据")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await close_database()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(check_ningde())
    exit(exit_code)

