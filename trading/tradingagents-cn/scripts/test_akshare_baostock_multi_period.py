"""
测试AKShare和BaoStock多周期数据同步功能
"""
import asyncio
import logging
from datetime import datetime, timedelta
from tradingagents.config.database_manager import get_mongodb_client
from tradingagents.dataflows.providers.akshare_provider import AKShareProvider
from tradingagents.dataflows.providers.baostock_provider import BaoStockProvider
from app.services.historical_data_service import get_historical_data_service
from app.core.database import init_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_provider_multi_period(provider_name: str, provider, symbol: str):
    """测试单个Provider的多周期功能"""
    print(f"\n{'='*60}")
    print(f"📊 测试{provider_name}多周期数据同步")
    print(f"{'='*60}")
    
    # 连接Provider
    await provider.connect()
    
    # 测试日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    print(f"   股票代码: {symbol}")
    print(f"   日期范围: {start_date} 到 {end_date}\n")
    
    # 获取历史数据服务
    service = await get_historical_data_service()
    
    # 获取MongoDB客户端
    client = get_mongodb_client()
    db = client.get_database('tradingagents')
    collection = db.stock_daily_quotes
    
    # 测试三种周期
    periods = ["daily", "weekly", "monthly"]
    period_names = {"daily": "日线", "weekly": "周线", "monthly": "月线"}
    
    for period in periods:
        print(f"\n{'='*60}")
        print(f"📊 测试{period_names[period]}数据")
        print(f"{'='*60}")
        
        # 查询保存前的记录数
        before_count = collection.count_documents({
            'symbol': symbol,
            'data_source': provider_name.lower(),
            'period': period
        })
        print(f"   📊 保存前{period_names[period]}记录数: {before_count}")
        
        try:
            # 获取数据
            print(f"   📥 获取{period_names[period]}数据...")
            data = await provider.get_historical_data(symbol, start_date, end_date, period)
            
            if data is not None and not data.empty:
                print(f"   ✅ 获取到 {len(data)} 条记录")
                print(f"   📋 数据样本（前3条）:")
                for idx in range(min(3, len(data))):
                    row = data.iloc[idx]
                    date_val = data.index[idx] if hasattr(data.index[idx], 'strftime') else data.index[idx]
                    close_val = row.get('close', row.get('收盘', 'N/A'))
                    volume_val = row.get('volume', row.get('成交量', 'N/A'))
                    print(f"     {date_val}: 收盘={close_val}, 成交量={volume_val}")
                
                # 保存数据
                print(f"   💾 保存{period_names[period]}数据...")
                saved_count = await service.save_historical_data(
                    symbol=symbol,
                    data=data,
                    data_source=provider_name.lower(),
                    market="CN",
                    period=period
                )
                print(f"   ✅ 保存完成: {saved_count} 条记录")
                
                # 查询保存后的记录数
                after_count = collection.count_documents({
                    'symbol': symbol,
                    'data_source': provider_name.lower(),
                    'period': period
                })
                print(f"   📊 保存后{period_names[period]}记录数: {after_count}")
                print(f"   📈 新增记录数: {after_count - before_count}")
                
                # 查询并显示数据库中的记录
                records = list(collection.find({
                    'symbol': symbol,
                    'data_source': provider_name.lower(),
                    'period': period
                }).sort('trade_date', 1).limit(3))

                print(f"   📋 数据库中的记录（前3条）:")
                for record in records:
                    trade_date = record.get('trade_date', 'N/A')
                    close = record.get('close', 'N/A')
                    period_val = record.get('period', 'N/A')
                    print(f"     {trade_date}: 收盘={close}, 周期={period_val}")
                
                print(f"   ✅ {period_names[period]}数据同步成功！")
            else:
                print(f"   ⚠️ 未获取到{period_names[period]}数据")
                
        except Exception as e:
            print(f"   ❌ {period_names[period]}数据同步失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主测试函数"""
    print("🔍 测试AKShare和BaoStock多周期数据同步功能")
    print("="*60)
    
    # 初始化数据库
    print("1️⃣ 初始化数据库和提供者")
    await init_database()
    
    # 测试股票代码
    test_symbol = "000001"
    
    # 测试AKShare
    try:
        print("\n" + "="*60)
        print("📊 测试AKShare Provider")
        print("="*60)
        akshare_provider = AKShareProvider()
        await test_provider_multi_period("AKShare", akshare_provider, test_symbol)
    except Exception as e:
        print(f"❌ AKShare测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试BaoStock
    try:
        print("\n" + "="*60)
        print("📊 测试BaoStock Provider")
        print("="*60)
        baostock_provider = BaoStockProvider()
        await test_provider_multi_period("BaoStock", baostock_provider, test_symbol)
    except Exception as e:
        print(f"❌ BaoStock测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 统计所有数据源的多周期数据
    print("\n" + "="*60)
    print("📊 多周期数据统计（所有数据源）")
    print("="*60)
    
    client = get_mongodb_client()
    db = client.get_database('tradingagents')
    collection = db.stock_daily_quotes
    
    for source in ["tushare", "akshare", "baostock"]:
        print(f"\n{source.upper()}:")
        for period in ["daily", "weekly", "monthly"]:
            count = collection.count_documents({
                'symbol': test_symbol,
                'data_source': source,
                'period': period
            })
            period_name = {"daily": "日线", "weekly": "周线", "monthly": "月线"}[period]
            print(f"   {period_name}: {count} 条记录")
    
    print("\n" + "="*60)
    print("🎯 测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

