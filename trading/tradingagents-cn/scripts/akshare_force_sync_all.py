#!/usr/bin/env python3
"""
AKShare 强制全量同步股票基础信息

功能：
1. 强制更新所有股票的基础信息（忽略24小时缓存）
2. 显示详细的同步进度和错误信息
3. 统计成功/失败的股票数量

使用方法：
    python scripts/akshare_force_sync_all.py
    python scripts/akshare_force_sync_all.py --batch-size 10  # 调整批次大小
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.worker.akshare_sync_service import AKShareSyncService
from app.core.database import init_database
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main(batch_size: int = 50):
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 AKShare 强制全量同步股票基础信息")
    logger.info("=" * 80)
    
    # 初始化数据库
    await init_database()
    
    # 创建同步服务
    service = AKShareSyncService(batch_size=batch_size)
    
    # 强制全量同步
    logger.info("⚠️  使用 force_update=True，将更新所有股票（忽略24小时缓存）")
    stats = await service.sync_stock_basic_info(force_update=True)
    
    # 输出统计
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 同步完成统计")
    logger.info("=" * 80)
    logger.info(f"   总计: {stats['total_processed']} 只股票")
    logger.info(f"   成功: {stats['success_count']} 只")
    logger.info(f"   失败: {stats['error_count']} 只")
    logger.info(f"   跳过: {stats['skipped_count']} 只")
    logger.info(f"   耗时: {stats['duration']:.2f} 秒")
    logger.info(f"   成功率: {stats['success_count']*100//stats['total_processed'] if stats['total_processed'] > 0 else 0}%")
    logger.info("=" * 80)
    
    # 输出错误详情
    if stats['errors']:
        logger.info("")
        logger.info(f"❌ 失败的股票 ({len(stats['errors'])} 只):")
        for i, error in enumerate(stats['errors'][:20], 1):  # 只显示前20个错误
            logger.info(f"   {i}. {error.get('code', 'unknown')}: {error.get('error', 'unknown error')}")
        
        if len(stats['errors']) > 20:
            logger.info(f"   ... 还有 {len(stats['errors']) - 20} 个错误未显示")
    
    logger.info("")
    logger.info("✅ 同步完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AKShare 强制全量同步股票基础信息",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="批次大小（默认：50）"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(batch_size=args.batch_size))

