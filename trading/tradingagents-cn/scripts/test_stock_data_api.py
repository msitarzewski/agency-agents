#!/usr/bin/env python3
"""
测试股票数据API
验证新的股票数据模型和API接口是否正常工作
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "http://localhost:8000"

# 测试用的JWT Token (需要先登录获取)
# 这里使用一个示例token，实际使用时需要替换
TEST_TOKEN = "your_jwt_token_here"

class StockDataAPITester:
    """股票数据API测试器"""
    
    def __init__(self, base_url: str = BASE_URL, token: str = None):
        self.base_url = base_url
        self.token = token
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    async def test_basic_info_api(self):
        """测试股票基础信息API"""
        logger.info("🔍 测试股票基础信息API...")
        
        test_codes = ["000001", "000002", "600000"]
        
        async with aiohttp.ClientSession() as session:
            for code in test_codes:
                try:
                    url = f"{self.base_url}/api/stock-data/basic-info/{code}"
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("success"):
                                stock_info = data.get("data", {})
                                logger.info(f"✅ {code} - {stock_info.get('name')}")
                                logger.info(f"   完整代码: {stock_info.get('full_symbol')}")
                                logger.info(f"   市场: {stock_info.get('market_info', {}).get('exchange_name')}")
                                logger.info(f"   行业: {stock_info.get('industry')}")
                                logger.info(f"   总市值: {stock_info.get('total_mv')}亿元")
                            else:
                                logger.warning(f"❌ {code} - {data.get('message')}")
                        else:
                            logger.error(f"❌ {code} - HTTP {response.status}")
                            
                except Exception as e:
                    logger.error(f"❌ {code} - 请求失败: {e}")
                
                logger.info("-" * 50)
    
    async def test_quotes_api(self):
        """测试实时行情API"""
        logger.info("📈 测试实时行情API...")
        
        test_codes = ["000001", "600000"]
        
        async with aiohttp.ClientSession() as session:
            for code in test_codes:
                try:
                    url = f"{self.base_url}/api/stock-data/quotes/{code}"
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("success"):
                                quotes = data.get("data", {})
                                logger.info(f"✅ {code} 行情数据:")
                                logger.info(f"   当前价格: {quotes.get('current_price')}")
                                logger.info(f"   涨跌幅: {quotes.get('pct_chg')}%")
                                logger.info(f"   成交额: {quotes.get('amount')}")
                                logger.info(f"   交易日期: {quotes.get('trade_date')}")
                            else:
                                logger.warning(f"❌ {code} - {data.get('message')}")
                        else:
                            logger.error(f"❌ {code} - HTTP {response.status}")
                            
                except Exception as e:
                    logger.error(f"❌ {code} - 请求失败: {e}")
                
                logger.info("-" * 50)
    
    async def test_stock_list_api(self):
        """测试股票列表API"""
        logger.info("📋 测试股票列表API...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 测试按行业筛选
                url = f"{self.base_url}/api/stock-data/list"
                params = {"industry": "银行", "page": 1, "page_size": 3}
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            stocks = data.get("data", [])
                            logger.info(f"✅ 银行行业股票 (前3只):")
                            for stock in stocks:
                                logger.info(f"   {stock.get('code')} - {stock.get('name')}")
                                logger.info(f"     完整代码: {stock.get('full_symbol')}")
                                logger.info(f"     总市值: {stock.get('total_mv')}亿元")
                        else:
                            logger.warning(f"❌ 股票列表 - {data.get('message')}")
                    else:
                        logger.error(f"❌ 股票列表 - HTTP {response.status}")
                        
            except Exception as e:
                logger.error(f"❌ 股票列表 - 请求失败: {e}")
            
            logger.info("-" * 50)
    
    async def test_combined_api(self):
        """测试综合数据API"""
        logger.info("🔄 测试综合数据API...")
        
        async with aiohttp.ClientSession() as session:
            try:
                code = "000001"
                url = f"{self.base_url}/api/stock-data/combined/{code}"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            combined_data = data.get("data", {})
                            basic_info = combined_data.get("basic_info")
                            quotes = combined_data.get("quotes")
                            
                            logger.info(f"✅ {code} 综合数据:")
                            if basic_info:
                                logger.info(f"   名称: {basic_info.get('name')}")
                                logger.info(f"   行业: {basic_info.get('industry')}")
                                logger.info(f"   总市值: {basic_info.get('total_mv')}亿元")
                            if quotes:
                                logger.info(f"   当前价格: {quotes.get('current_price')}")
                                logger.info(f"   涨跌幅: {quotes.get('pct_chg')}%")
                        else:
                            logger.warning(f"❌ 综合数据 - {data.get('message')}")
                    else:
                        logger.error(f"❌ 综合数据 - HTTP {response.status}")
                        
            except Exception as e:
                logger.error(f"❌ 综合数据 - 请求失败: {e}")
            
            logger.info("-" * 50)
    
    async def test_search_api(self):
        """测试搜索API"""
        logger.info("🔍 测试搜索API...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 测试按代码搜索
                url = f"{self.base_url}/api/stock-data/search"
                params = {"keyword": "000001", "limit": 5}
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            results = data.get("data", [])
                            logger.info(f"✅ 搜索 '000001' 结果:")
                            for result in results:
                                logger.info(f"   {result.get('code')} - {result.get('name')}")
                        else:
                            logger.warning(f"❌ 搜索 - {data.get('message')}")
                    else:
                        logger.error(f"❌ 搜索 - HTTP {response.status}")
                
                # 测试按名称搜索
                params = {"keyword": "银行", "limit": 3}
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            results = data.get("data", [])
                            logger.info(f"✅ 搜索 '银行' 结果:")
                            for result in results:
                                logger.info(f"   {result.get('code')} - {result.get('name')}")
                        else:
                            logger.warning(f"❌ 搜索 - {data.get('message')}")
                    else:
                        logger.error(f"❌ 搜索 - HTTP {response.status}")
                        
            except Exception as e:
                logger.error(f"❌ 搜索 - 请求失败: {e}")
            
            logger.info("-" * 50)
    
    async def test_market_summary_api(self):
        """测试市场概览API"""
        logger.info("🌍 测试市场概览API...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/api/stock-data/markets"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            market_data = data.get("data", {})
                            logger.info(f"✅ 市场概览:")
                            logger.info(f"   总股票数: {market_data.get('total_stocks')}")
                            logger.info(f"   支持市场: {market_data.get('supported_markets')}")
                            
                            breakdown = market_data.get("market_breakdown", [])
                            logger.info("   市场分布:")
                            for item in breakdown[:5]:  # 显示前5个
                                logger.info(f"     {item.get('_id')}: {item.get('count')} 只")
                        else:
                            logger.warning(f"❌ 市场概览 - {data.get('message')}")
                    else:
                        logger.error(f"❌ 市场概览 - HTTP {response.status}")
                        
            except Exception as e:
                logger.error(f"❌ 市场概览 - 请求失败: {e}")
            
            logger.info("-" * 50)


async def main():
    """主函数"""
    logger.info("🚀 开始股票数据API测试...")
    
    # 注意：这里没有使用真实的JWT token，所以可能会返回401错误
    # 在实际测试中，需要先通过登录API获取有效的token
    tester = StockDataAPITester()
    
    try:
        await tester.test_basic_info_api()
        await tester.test_quotes_api()
        await tester.test_stock_list_api()
        await tester.test_combined_api()
        await tester.test_search_api()
        await tester.test_market_summary_api()
        
        logger.info("🎉 股票数据API测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 测试过程失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
