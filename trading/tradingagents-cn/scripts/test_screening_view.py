#!/usr/bin/env python3
"""
测试股票筛选视图
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
from app.services.database_screening_service import get_database_screening_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_screening():
    """测试筛选功能"""
    try:
        # 初始化数据库
        logger.info("📡 连接数据库...")
        await init_database()
        
        # 获取筛选服务
        service = get_database_screening_service()
        
        # 测试1：只筛选涨跌幅
        logger.info("\n" + "=" * 60)
        logger.info("测试1：筛选涨跌幅在 1-10 之间的股票")
        logger.info("=" * 60)

        conditions1 = [
            {"field": "pct_chg", "operator": "between", "value": [1, 10]}
        ]
        
        results1, total1 = await service.screen_stocks(
            conditions=conditions1,
            limit=5,
            offset=0
        )
        
        logger.info(f"✅ 找到 {total1} 只股票，返回前 5 只:")
        for r in results1:
            logger.info(f"  - {r.get('code')} {r.get('name')}: ROE={r.get('roe')}, "
                       f"close={r.get('close')}, pct_chg={r.get('pct_chg')}")
        
        # 测试2：筛选涨跌幅 + 成交额
        logger.info("\n" + "=" * 60)
        logger.info("测试2：筛选涨跌幅在 1-10 且成交额>10000万的股票")
        logger.info("=" * 60)

        conditions2 = [
            {"field": "pct_chg", "operator": "between", "value": [1, 10]},
            {"field": "amount", "operator": ">", "value": 10000}
        ]
        
        results2, total2 = await service.screen_stocks(
            conditions=conditions2,
            limit=5,
            offset=0
        )
        
        logger.info(f"✅ 找到 {total2} 只股票，返回前 5 只:")
        for r in results2:
            logger.info(f"  - {r.get('code')} {r.get('name')}: ROE={r.get('roe')}, "
                       f"close={r.get('close')}, pct_chg={r.get('pct_chg')}")
        
        # 测试3：筛选 ROE + 涨跌幅 + 成交额（宽松条件）
        logger.info("\n" + "=" * 60)
        logger.info("测试3：筛选 ROE>0 且涨跌幅>1 且成交额>10000万的股票")
        logger.info("=" * 60)

        conditions3 = [
            {"field": "roe", "operator": ">", "value": 0},
            {"field": "pct_chg", "operator": ">", "value": 1},
            {"field": "amount", "operator": ">", "value": 10000}
        ]
        
        results3, total3 = await service.screen_stocks(
            conditions=conditions3,
            limit=5,
            offset=0,
            order_by=[{"field": "pct_chg", "direction": "desc"}]
        )
        
        logger.info(f"✅ 找到 {total3} 只股票，返回前 5 只（按涨跌幅降序）:")
        for r in results3:
            logger.info(f"  - {r.get('code')} {r.get('name')}: ROE={r.get('roe')}, "
                       f"close={r.get('close')}, pct_chg={r.get('pct_chg')}, amount={r.get('amount')}")
        
        logger.info("\n✅ 所有测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await close_database()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_screening())
    exit(exit_code)

