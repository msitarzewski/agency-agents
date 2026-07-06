#!/usr/bin/env python3
"""
测试000001历史数据同步
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.providers.tushare_provider import TushareProvider
from app.services.historical_data_service import get_historical_data_service
from app.core.database import init_database
from tradingagents.config.database_manager import get_mongodb_client


async def test_000001():
    print('🔍 测试000001历史数据同步')
    print('=' * 60)
    
    # 初始化
    await init_database()
    provider = TushareProvider()
    await provider.connect()
    service = await get_historical_data_service()
    
    # 检查数据库状态（保存前）
    client = get_mongodb_client()
    db = client.get_database('tradingagents')
    collection = db.stock_daily_quotes
    
    before_count = collection.count_documents({'symbol': '000001', 'data_source': 'tushare'})
    print(f'📊 000001 Tushare记录数（保存前）: {before_count}')
    
    # 获取并保存2024年1月的数据
    df = await provider.get_historical_data('000001', '2024-01-01', '2024-01-31')
    print(f'📥 获取到 {len(df)} 条记录')
    
    saved_count = await service.save_historical_data(
        symbol='000001',
        data=df,
        data_source='tushare',
        market='CN',
        period='daily'
    )
    print(f'💾 保存了 {saved_count} 条记录')
    
    # 检查数据库状态（保存后）
    after_count = collection.count_documents({'symbol': '000001', 'data_source': 'tushare'})
    print(f'📊 000001 Tushare记录数（保存后）: {after_count}')
    print(f'📈 新增记录数: {after_count - before_count}')
    
    # 查询2024年1月的数据
    jan_2024_count = collection.count_documents({
        'symbol': '000001',
        'data_source': 'tushare',
        'trade_date': {'$gte': '2024-01-01', '$lte': '2024-01-31'}
    })
    print(f'📅 2024年1月数据: {jan_2024_count} 条')
    
    # 显示前5条记录
    print('\n📋 2024年1月前5条记录:')
    records = list(collection.find({
        'symbol': '000001',
        'data_source': 'tushare',
        'trade_date': {'$gte': '2024-01-01', '$lte': '2024-01-31'}
    }).sort('trade_date', 1).limit(5))
    
    for record in records:
        trade_date = record.get('trade_date', 'N/A')
        close = record.get('close', 'N/A')
        volume = record.get('volume', 'N/A')
        print(f'  {trade_date}: 收盘={close}, 成交量={volume}')
    
    client.close()
    print('=' * 60)
    print('✅ 测试完成！')


if __name__ == "__main__":
    asyncio.run(test_000001())
