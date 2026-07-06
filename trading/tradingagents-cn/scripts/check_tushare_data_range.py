"""
检查Tushare数据的实际时间范围
"""
import asyncio
from tradingagents.dataflows.providers.tushare_provider import TushareProvider


async def check_data_range():
    """检查Tushare数据范围"""
    
    provider = TushareProvider()
    
    # 测试几只老股票
    test_symbols = [
        ('000001', '平安银行'),  # 深圳最早的股票之一
        ('600000', '浦发银行'),  # 上海最早的股票之一
        ('000002', '万科A'),     # 深圳早期股票
    ]
    
    print("=" * 80)
    print("检查Tushare历史数据的实际时间范围")
    print("=" * 80)
    
    for symbol, name in test_symbols:
        print(f"\n📊 {symbol} ({name})")
        print("-" * 80)
        
        # 请求从1990年至今的数据
        df = await provider.get_historical_data(symbol, '1990-01-01', '2025-09-30')
        
        if df is not None and not df.empty:
            print(f"  总记录数: {len(df)}")
            print(f"  最早日期: {df['trade_date'].min()}")
            print(f"  最晚日期: {df['trade_date'].max()}")
            
            # 显示最早的几条记录
            print(f"\n  最早的5条记录:")
            earliest = df.nsmallest(5, 'trade_date')
            for idx, row in earliest.iterrows():
                print(f"    {row['trade_date']}: 开盘={row['open']}, 收盘={row['close']}, 成交量={row['vol']}")
        else:
            print(f"  ❌ 无数据")
    
    print("\n" + "=" * 80)
    print("结论:")
    print("=" * 80)
    print("根据上述测试结果，可以确定Tushare的实际数据起始时间。")
    print()


if __name__ == "__main__":
    asyncio.run(check_data_range())

