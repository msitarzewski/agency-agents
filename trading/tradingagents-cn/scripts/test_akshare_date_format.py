"""
测试 AKShare 返回的日期格式
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.dataflows.providers.china.akshare import AKShareProvider


async def test_akshare_date_format():
    """测试 AKShare 返回的日期格式"""
    
    provider = AKShareProvider()
    await provider.connect()
    
    symbol = "000001"
    start_date = "2025-10-01"
    end_date = "2025-10-23"
    
    print("=" * 80)
    print(f"📊 测试 AKShare 返回的日期格式")
    print(f"  股票代码: {symbol}")
    print(f"  开始日期: {start_date}")
    print(f"  结束日期: {end_date}")
    print("=" * 80)
    
    # 获取历史数据
    hist_df = await provider.get_historical_data(symbol, start_date, end_date, period="daily")
    
    if hist_df is None or hist_df.empty:
        print("\n❌ 未获取到数据")
        return
    
    print(f"\n✅ 获取到 {len(hist_df)} 条记录")
    
    # 检查列名
    print(f"\n📋 列名: {list(hist_df.columns)}")
    
    # 检查 date 列的数据类型
    if 'date' in hist_df.columns:
        print(f"\n📅 date 列的数据类型: {hist_df['date'].dtype}")
        print(f"\n前5条 date 值:")
        for i, date_val in enumerate(hist_df['date'].head(5), 1):
            print(f"  {i}. {date_val} (type: {type(date_val).__name__})")
    else:
        print(f"\n⚠️ 没有 'date' 列")
    
    # 显示前5条完整记录
    print(f"\n📊 前5条完整记录:")
    print(hist_df.head(5).to_string())
    
    # 检查索引
    print(f"\n📑 索引类型: {type(hist_df.index).__name__}")
    print(f"📑 索引数据类型: {hist_df.index.dtype}")
    print(f"\n前5条索引值:")
    for i, idx_val in enumerate(hist_df.index[:5], 1):
        print(f"  {i}. {idx_val} (type: {type(idx_val).__name__})")
    
    await provider.disconnect()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_akshare_date_format())

