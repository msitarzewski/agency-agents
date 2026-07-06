#!/usr/bin/env python3
"""
股票数据模型使用示例
演示如何使用扩展后的股票数据模型和服务
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.stock_data_service import get_stock_data_service
from app.models import StockBasicInfoExtended, MarketQuotesExtended

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_basic_info():
    """演示获取股票基础信息"""
    logger.info("🔍 演示获取股票基础信息...")
    
    service = get_stock_data_service()
    
    # 测试股票代码
    test_codes = ["000001", "000002", "600000", "300001"]
    
    for code in test_codes:
        try:
            stock_info = await service.get_stock_basic_info(code)
            
            if stock_info:
                logger.info(f"✅ {code} - {stock_info.name}")
                logger.info(f"   完整代码: {stock_info.full_symbol}")
                logger.info(f"   行业: {stock_info.industry}")
                logger.info(f"   市场: {stock_info.market_info.exchange_name if stock_info.market_info else 'N/A'}")
                logger.info(f"   总市值: {stock_info.total_mv}亿元")
                logger.info(f"   市盈率: {stock_info.pe}")
                logger.info(f"   数据版本: {stock_info.data_version}")
            else:
                logger.warning(f"❌ {code} - 未找到数据")
                
        except Exception as e:
            logger.error(f"❌ {code} - 获取失败: {e}")
        
        logger.info("-" * 50)


async def demo_market_quotes():
    """演示获取实时行情"""
    logger.info("📈 演示获取实时行情...")
    
    service = get_stock_data_service()
    
    # 测试股票代码
    test_codes = ["000001", "000002", "600000"]
    
    for code in test_codes:
        try:
            quotes = await service.get_market_quotes(code)
            
            if quotes:
                logger.info(f"✅ {code} 行情数据:")
                logger.info(f"   完整代码: {quotes.full_symbol}")
                logger.info(f"   当前价格: {quotes.current_price}")
                logger.info(f"   涨跌幅: {quotes.pct_chg}%")
                logger.info(f"   成交额: {quotes.amount}")
                logger.info(f"   交易日期: {quotes.trade_date}")
                logger.info(f"   更新时间: {quotes.updated_at}")
            else:
                logger.warning(f"❌ {code} - 未找到行情数据")
                
        except Exception as e:
            logger.error(f"❌ {code} - 获取行情失败: {e}")
        
        logger.info("-" * 50)


async def demo_stock_list():
    """演示获取股票列表"""
    logger.info("📋 演示获取股票列表...")
    
    service = get_stock_data_service()
    
    try:
        # 获取银行行业股票
        bank_stocks = await service.get_stock_list(
            industry="银行",
            page=1,
            page_size=5
        )
        
        logger.info(f"✅ 银行行业股票 (前5只):")
        for stock in bank_stocks:
            logger.info(f"   {stock.code} - {stock.name}")
            logger.info(f"     完整代码: {stock.full_symbol}")
            logger.info(f"     总市值: {stock.total_mv}亿元")
            logger.info(f"     市盈率: {stock.pe}")
        
        logger.info("-" * 50)
        
        # 获取深交所股票
        szse_stocks = await service.get_stock_list(
            market="深圳证券交易所",
            page=1,
            page_size=3
        )
        
        logger.info(f"✅ 深交所股票 (前3只):")
        for stock in szse_stocks:
            logger.info(f"   {stock.code} - {stock.name}")
            logger.info(f"     交易所: {stock.market_info.exchange_name if stock.market_info else 'N/A'}")
            logger.info(f"     板块: {stock.board}")
        
    except Exception as e:
        logger.error(f"❌ 获取股票列表失败: {e}")


async def demo_data_update():
    """演示数据更新"""
    logger.info("🔄 演示数据更新...")
    
    service = get_stock_data_service()
    
    try:
        # 更新股票基础信息
        test_code = "000001"
        update_data = {
            "name_en": "Ping An Bank",
            "sector": "Financial Services",
            "data_version": 2,
            "last_updated_by": "demo_script"
        }
        
        success = await service.update_stock_basic_info(test_code, update_data)
        
        if success:
            logger.info(f"✅ {test_code} 基础信息更新成功")
            
            # 验证更新结果
            updated_info = await service.get_stock_basic_info(test_code)
            if updated_info:
                logger.info(f"   英文名称: {updated_info.name_en}")
                logger.info(f"   数据版本: {updated_info.data_version}")
        else:
            logger.warning(f"❌ {test_code} 基础信息更新失败")
        
        logger.info("-" * 50)
        
        # 更新行情数据
        quote_data = {
            "current_price": 12.88,
            "change": 0.23,
            "pct_chg": 1.82,
            "volume": 150000000,
            "data_version": 2
        }
        
        success = await service.update_market_quotes(test_code, quote_data)
        
        if success:
            logger.info(f"✅ {test_code} 行情数据更新成功")
            
            # 验证更新结果
            updated_quotes = await service.get_market_quotes(test_code)
            if updated_quotes:
                logger.info(f"   当前价格: {updated_quotes.current_price}")
                logger.info(f"   涨跌额: {updated_quotes.change}")
                logger.info(f"   数据版本: {updated_quotes.data_version}")
        else:
            logger.warning(f"❌ {test_code} 行情数据更新失败")
            
    except Exception as e:
        logger.error(f"❌ 数据更新失败: {e}")


async def demo_data_validation():
    """演示数据验证"""
    logger.info("🔍 演示数据验证...")
    
    try:
        # 创建股票基础信息实例
        stock_data = {
            "code": "000001",
            "name": "平安银行",
            "symbol": "000001",
            "full_symbol": "000001.SZ",
            "market_info": {
                "market": "CN",
                "exchange": "SZSE",
                "exchange_name": "深圳证券交易所",
                "currency": "CNY",
                "timezone": "Asia/Shanghai"
            },
            "total_mv": 2500.0,
            "pe": 5.2,
            "status": "L",
            "data_version": 1
        }
        
        # 验证数据模型
        stock_info = StockBasicInfoExtended(**stock_data)
        logger.info("✅ 股票基础信息数据验证通过")
        logger.info(f"   代码: {stock_info.code}")
        logger.info(f"   名称: {stock_info.name}")
        logger.info(f"   市场: {stock_info.market_info.market}")
        
        logger.info("-" * 50)
        
        # 创建行情数据实例
        quote_data = {
            "code": "000001",
            "symbol": "000001",
            "full_symbol": "000001.SZ",
            "market": "CN",
            "close": 12.65,
            "current_price": 12.65,
            "pct_chg": 1.61,
            "change": 0.20,
            "amount": 1580000000,
            "trade_date": "2024-01-15",
            "data_version": 1
        }
        
        # 验证数据模型
        quotes = MarketQuotesExtended(**quote_data)
        logger.info("✅ 实时行情数据验证通过")
        logger.info(f"   代码: {quotes.code}")
        logger.info(f"   当前价格: {quotes.current_price}")
        logger.info(f"   市场: {quotes.market}")
        
    except Exception as e:
        logger.error(f"❌ 数据验证失败: {e}")


async def main():
    """主函数"""
    logger.info("🚀 开始股票数据模型使用演示...")
    
    try:
        # 需要先连接数据库
        from app.core.database import init_database, close_database
        await init_database()

        # 演示各种功能
        await demo_basic_info()
        await demo_market_quotes()
        await demo_stock_list()
        await demo_data_update()
        await demo_data_validation()

        logger.info("🎉 股票数据模型演示完成！")

    except Exception as e:
        logger.error(f"❌ 演示过程失败: {e}")

    finally:
        # 关闭数据库连接
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
