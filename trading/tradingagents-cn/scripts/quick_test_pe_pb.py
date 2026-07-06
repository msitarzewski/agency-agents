#!/usr/bin/env python3
"""
快速测试 PE/PB 修复

使用方法：
    python scripts/quick_test_pe_pb.py 600036
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_pe_pb_from_basic_info(code: str):
    """测试从 stock_basic_info 直接获取 PE/PB"""
    logger.info("=" * 80)
    logger.info(f"🧪 快速测试：从 stock_basic_info 获取 PE/PB")
    logger.info("=" * 80)
    
    from pymongo import MongoClient
    from app.core.config import settings
    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
    
    # 连接数据库
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    code6 = str(code).zfill(6)
    
    # 1. 获取 stock_basic_info
    basic_info = db.stock_basic_info.find_one({"code": code6})
    
    if not basic_info:
        logger.error(f"❌ 未找到股票 {code6} 的基础信息")
        client.close()
        return False
    
    logger.info(f"✅ 找到股票基础信息")
    logger.info(f"   股票代码: {basic_info.get('code', 'N/A')}")
    logger.info(f"   股票名称: {basic_info.get('name', 'N/A')}")
    logger.info(f"   PE: {basic_info.get('pe', 'N/A')}")
    logger.info(f"   PB: {basic_info.get('pb', 'N/A')}")
    logger.info(f"   PE_TTM: {basic_info.get('pe_ttm', 'N/A')}")
    
    # 2. 测试解析
    logger.info(f"\n🔧 测试 _parse_mongodb_financial_data...")
    
    provider = OptimizedChinaDataProvider()
    
    try:
        metrics = provider._parse_mongodb_financial_data(basic_info, 41.86)
        
        logger.info(f"\n✅ 解析成功！")
        logger.info(f"   PE: {metrics.get('pe', 'N/A')}")
        logger.info(f"   PB: {metrics.get('pb', 'N/A')}")
        
        # 验证
        if metrics.get('pe') != 'N/A' and metrics.get('pb') != 'N/A':
            logger.info(f"\n🎉 测试通过：PE/PB 数据正确获取！")
            client.close()
            return True
        else:
            logger.error(f"\n❌ 测试失败：PE/PB 仍然是 N/A")
            client.close()
            return False
    
    except Exception as e:
        logger.error(f"❌ 解析失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        client.close()
        return False


def main(code: str):
    """主函数"""
    logger.info("=" * 80)
    logger.info(f"🚀 快速测试 PE/PB 修复 - 股票代码: {code}")
    logger.info("=" * 80)
    
    success = test_pe_pb_from_basic_info(code)
    
    if success:
        logger.info(f"\n🎉 测试通过！现在可以运行完整测试：")
        logger.info(f"   python scripts/test_pe_pb_fix.py {code}")
    else:
        logger.error(f"\n❌ 测试失败，请检查日志")
    
    logger.info("=" * 80)
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="快速测试 PE/PB 修复",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "code",
        type=str,
        help="股票代码（6位）"
    )
    
    args = parser.parse_args()
    
    success = main(args.code)
    sys.exit(0 if success else 1)

