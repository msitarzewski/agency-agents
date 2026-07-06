#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股同步服务测试脚本

功能：
1. 手动触发港股同步任务
2. 验证 yfinance 和 akshare 数据源
3. 检查数据是否正确存储到 stock_basic_info_hk 集合

使用方法：
    python scripts/test/test_hk_sync.py
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_hk_yfinance_sync():
    """测试港股 yfinance 数据源同步"""
    logger.info("\n" + "="*60)
    logger.info("🧪 测试港股 yfinance 数据源同步")
    logger.info("="*60)
    
    try:
        from app.worker.hk_sync_service import run_hk_yfinance_basic_info_sync
        
        # 执行同步
        await run_hk_yfinance_basic_info_sync()
        
        logger.info("✅ yfinance 同步测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ yfinance 同步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hk_akshare_sync():
    """测试港股 akshare 数据源同步"""
    logger.info("\n" + "="*60)
    logger.info("🧪 测试港股 AKShare 数据源同步")
    logger.info("="*60)
    
    try:
        from app.worker.hk_sync_service import run_hk_akshare_basic_info_sync
        
        # 执行同步
        await run_hk_akshare_basic_info_sync()
        
        logger.info("✅ AKShare 同步测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ AKShare 同步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_hk_data():
    """验证港股数据存储"""
    logger.info("\n" + "="*60)
    logger.info("🔍 验证港股数据存储")
    logger.info("="*60)

    try:
        from app.core.database import get_mongo_db

        db = get_mongo_db()
        collection = db.stock_basic_info_hk
        
        # 统计各数据源的记录数
        yfinance_count = await collection.count_documents({"source": "yfinance"})
        akshare_count = await collection.count_documents({"source": "akshare"})
        total_count = await collection.count_documents({})
        
        logger.info(f"📊 数据统计:")
        logger.info(f"  - yfinance 数据源: {yfinance_count} 条记录")
        logger.info(f"  - akshare 数据源: {akshare_count} 条记录")
        logger.info(f"  - 总计: {total_count} 条记录")
        
        # 显示示例数据
        if total_count > 0:
            logger.info(f"\n📋 示例数据:")
            
            # yfinance 示例
            yfinance_sample = await collection.find_one({"source": "yfinance"})
            if yfinance_sample:
                logger.info(f"\n  yfinance 示例:")
                logger.info(f"    代码: {yfinance_sample.get('code')}")
                logger.info(f"    名称: {yfinance_sample.get('name')}")
                logger.info(f"    市场: {yfinance_sample.get('market')}")
                logger.info(f"    数据源: {yfinance_sample.get('source')}")
                logger.info(f"    更新时间: {yfinance_sample.get('updated_at')}")
            
            # akshare 示例
            akshare_sample = await collection.find_one({"source": "akshare"})
            if akshare_sample:
                logger.info(f"\n  akshare 示例:")
                logger.info(f"    代码: {akshare_sample.get('code')}")
                logger.info(f"    名称: {akshare_sample.get('name')}")
                logger.info(f"    市场: {akshare_sample.get('market')}")
                logger.info(f"    数据源: {akshare_sample.get('source')}")
                logger.info(f"    更新时间: {akshare_sample.get('updated_at')}")
        
        # 验证索引
        logger.info(f"\n📋 索引验证:")
        indexes = await collection.list_indexes().to_list(length=None)
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")
        
        logger.info("\n✅ 数据验证完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_service():
    """测试统一数据访问服务"""
    logger.info("\n" + "="*60)
    logger.info("🧪 测试统一数据访问服务")
    logger.info("="*60)

    try:
        from app.services.unified_stock_service import UnifiedStockService
        from app.core.database import get_mongo_db

        db = get_mongo_db()
        service = UnifiedStockService(db)
        
        # 测试查询港股数据（按优先级自动选择数据源）
        logger.info("\n📊 测试查询港股数据（自动选择数据源）:")
        
        # 查询腾讯控股 00700
        stock_info = await service.get_stock_info("HK", "00700")
        if stock_info:
            logger.info(f"  ✅ 查询成功: {stock_info.get('code')} - {stock_info.get('name')}")
            logger.info(f"     数据源: {stock_info.get('source')}")
            logger.info(f"     市场: {stock_info.get('market')}")
        else:
            logger.warning(f"  ⚠️ 未找到数据: 00700")
        
        # 测试指定数据源查询
        logger.info("\n📊 测试指定数据源查询:")
        
        # 指定 yfinance 数据源
        stock_info_yf = await service.get_stock_info("HK", "00700", source="yfinance")
        if stock_info_yf:
            logger.info(f"  ✅ yfinance: {stock_info_yf.get('code')} - {stock_info_yf.get('name')}")
        else:
            logger.warning(f"  ⚠️ yfinance 未找到数据")
        
        # 指定 akshare 数据源
        stock_info_ak = await service.get_stock_info("HK", "00700", source="akshare")
        if stock_info_ak:
            logger.info(f"  ✅ akshare: {stock_info_ak.get('code')} - {stock_info_ak.get('name')}")
        else:
            logger.warning(f"  ⚠️ akshare 未找到数据")
        
        # 测试搜索功能
        logger.info("\n📊 测试搜索功能:")
        search_results = await service.search_stocks("HK", "腾讯", limit=5)
        logger.info(f"  搜索 '腾讯' 结果: {len(search_results)} 条")
        for result in search_results:
            logger.info(f"    - {result.get('code')}: {result.get('name')} (数据源: {result.get('source')})")
        
        logger.info("\n✅ 统一服务测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 统一服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始港股同步服务测试...")

    # 初始化数据库连接
    logger.info("📊 初始化数据库连接...")
    try:
        from app.core.database import init_db
        await init_db()
        logger.info("✅ 数据库连接初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接初始化失败: {e}")
        return False

    results = {
        "yfinance_sync": False,
        "akshare_sync": False,
        "data_verify": False,
        "unified_service": False
    }

    # 1. 测试 yfinance 同步
    results["yfinance_sync"] = await test_hk_yfinance_sync()

    # 2. 测试 akshare 同步
    results["akshare_sync"] = await test_hk_akshare_sync()

    # 3. 验证数据存储
    results["data_verify"] = await verify_hk_data()

    # 4. 测试统一服务
    results["unified_service"] = await test_unified_service()
    
    # 显示测试结果
    logger.info("\n" + "="*60)
    logger.info("📊 测试结果汇总")
    logger.info("="*60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 所有测试通过！")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查日志")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

