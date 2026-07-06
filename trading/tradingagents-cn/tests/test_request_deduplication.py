"""
测试请求去重机制
验证并发请求不会导致重复的API调用
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.foreign_stock_service import ForeignStockService


@pytest.mark.asyncio
async def test_concurrent_hk_quote_requests():
    """
    测试并发港股行情请求的去重机制
    
    场景：
    1. 同时发起10个相同股票的请求
    2. 验证只有1个实际的API调用
    3. 所有请求都应该返回相同的结果
    """
    # 创建服务实例
    service = ForeignStockService(db=None)
    
    # Mock 数据源优先级
    async def mock_get_source_priority(market):
        return ['akshare']
    
    service._get_source_priority = mock_get_source_priority
    
    # Mock AKShare API调用（记录调用次数）
    call_count = 0
    
    def mock_get_hk_quote_from_akshare(code):
        nonlocal call_count
        call_count += 1
        # 模拟API延迟
        import time
        time.sleep(0.1)
        return {
            'code': code,
            'name': '腾讯控股',
            'price': 350.0,
            'open': 348.0,
            'high': 352.0,
            'low': 347.0,
            'volume': 1000000,
            'change_percent': 0.5,
            'trade_date': '2025-11-12',
            'currency': 'HKD'
        }
    
    service._get_hk_quote_from_akshare = mock_get_hk_quote_from_akshare

    # 同时发起10个请求（使用 force_refresh=True 绕过缓存）
    code = '00700'
    tasks = [service._get_hk_quote(code, force_refresh=True) for _ in range(10)]
    
    # 等待所有请求完成
    results = await asyncio.gather(*tasks)
    
    # 验证结果
    assert len(results) == 10, "应该返回10个结果"
    assert call_count == 1, f"应该只调用1次API，实际调用了{call_count}次"
    
    # 验证所有结果相同
    for result in results:
        assert result['code'] == code
        assert result['price'] == 350.0
    
    print(f"✅ 测试通过：10个并发请求只触发了{call_count}次API调用")


@pytest.mark.asyncio
async def test_concurrent_us_quote_requests():
    """
    测试并发美股行情请求的去重机制
    """
    service = ForeignStockService(db=None)
    
    # Mock 数据源优先级
    async def mock_get_source_priority(market):
        return ['yahoo_finance']
    
    service._get_source_priority = mock_get_source_priority
    
    # Mock yfinance API调用
    call_count = 0
    
    def mock_get_us_quote_from_yfinance(code):
        nonlocal call_count
        call_count += 1
        import time
        time.sleep(0.1)
        return {
            'code': code,
            'name': 'Apple Inc.',
            'price': 180.0,
            'open': 179.0,
            'high': 181.0,
            'low': 178.5,
            'volume': 50000000,
            'change_percent': 0.56,
            'trade_date': '2025-11-12',
            'currency': 'USD'
        }
    
    service._get_us_quote_from_yfinance = mock_get_us_quote_from_yfinance

    # 同时发起10个请求（使用 force_refresh=True 绕过缓存）
    code = 'AAPL'
    tasks = [service._get_us_quote(code, force_refresh=True) for _ in range(10)]
    
    # 等待所有请求完成
    results = await asyncio.gather(*tasks)
    
    # 验证结果
    assert len(results) == 10
    assert call_count == 1, f"应该只调用1次API，实际调用了{call_count}次"
    
    for result in results:
        assert result['code'] == code
        assert result['price'] == 180.0
    
    print(f"✅ 测试通过：10个并发请求只触发了{call_count}次API调用")


@pytest.mark.asyncio
async def test_different_stocks_no_blocking():
    """
    测试不同股票的请求不会互相阻塞
    """
    service = ForeignStockService(db=None)

    # Mock 数据源优先级
    async def mock_get_source_priority(market):
        return ['akshare']

    service._get_source_priority = mock_get_source_priority

    # Mock API调用
    call_count = {}

    def mock_get_hk_quote_from_akshare(code):
        if code not in call_count:
            call_count[code] = 0
        call_count[code] += 1

        import time
        time.sleep(0.1)

        return {
            'code': code,
            'name': f'股票{code}',
            'price': 100.0,
            'open': 99.0,
            'high': 101.0,
            'low': 98.0,
            'volume': 1000000,
            'change_percent': 1.0,
            'trade_date': '2025-11-12',
            'currency': 'HKD'
        }

    service._get_hk_quote_from_akshare = mock_get_hk_quote_from_akshare

    # 同时请求3个不同的股票，每个股票5个并发请求（使用 force_refresh=True 绕过缓存）
    # 使用不同的股票代码，避免与之前的测试冲突
    codes = ['00001', '00002', '00003']
    tasks = []
    for code in codes:
        tasks.extend([service._get_hk_quote(code, force_refresh=True) for _ in range(5)])

    # 等待所有请求完成
    results = await asyncio.gather(*tasks)

    # 验证结果
    assert len(results) == 15  # 3个股票 × 5个请求

    # 每个股票应该只调用1次API
    for code in codes:
        assert call_count.get(code, 0) == 1, f"股票{code}应该只调用1次API，实际调用了{call_count.get(code, 0)}次"

    print(f"✅ 测试通过：3个不同股票各5个并发请求，每个股票只触发了1次API调用")


if __name__ == '__main__':
    # 运行测试
    asyncio.run(test_concurrent_hk_quote_requests())
    asyncio.run(test_concurrent_us_quote_requests())
    asyncio.run(test_different_stocks_no_blocking())

