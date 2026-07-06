"""
测试成交额单位修复
验证 Tushare 数据的成交额单位转换是否正确
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.database import get_mongo_db
from tradingagents.dataflows.providers.china.tushare import get_tushare_provider

async def test_amount_fix():
    """测试成交额单位修复"""
    print("=" * 80)
    print("测试成交额单位修复")
    print("=" * 80)
    
    # 测试股票：300750 宁德时代
    test_code = "300750"
    
    print(f"\n1️⃣ 测试 Tushare Provider 标准化")
    print(f"   股票代码: {test_code}")
    
    provider = get_tushare_provider()
    if not provider.is_available():
        print("   ❌ Tushare 不可用，请检查 TUSHARE_TOKEN 配置")
        return
    
    # 获取历史数据（最近1天）
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    print(f"\n2️⃣ 获取历史数据")
    print(f"   日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    df = await provider.get_historical_data(
        symbol=test_code,
        start_date=start_date,
        end_date=end_date,
        period="daily"
    )
    
    if df is None or df.empty:
        print("   ❌ 未获取到数据")
        return
    
    print(f"   ✅ 获取到 {len(df)} 条记录")
    
    # 显示最新一条数据
    latest = df.iloc[-1]
    print(f"\n3️⃣ 最新数据（已标准化）")
    print(f"   日期: {latest.name}")
    print(f"   收盘价: {latest.get('close')}")
    print(f"   成交量: {latest.get('volume')}")
    print(f"   成交额(元): {latest.get('amount'):,.0f}")
    print(f"   成交额(亿元): {latest.get('amount') / 1e8:.2f}")
    print(f"   成交额(万元): {latest.get('amount') / 1e4:.2f}")
    
    # 检查数据库中的数据
    print(f"\n4️⃣ 检查数据库 stock_daily_quotes 集合")
    db = get_mongo_db()
    coll = db["stock_daily_quotes"]
    
    doc = coll.find_one(
        {"symbol": test_code, "period": "daily", "data_source": "tushare"},
        sort=[("trade_date", -1)]
    )
    
    if doc:
        print(f"   ✅ 找到数据库记录")
        print(f"   交易日期: {doc.get('trade_date')}")
        print(f"   收盘价: {doc.get('close')}")
        print(f"   成交额(元): {doc.get('amount'):,.0f}")
        print(f"   成交额(亿元): {doc.get('amount') / 1e8:.2f}")
        print(f"   成交额(万元): {doc.get('amount') / 1e4:.2f}")
    else:
        print(f"   ⚠️ 数据库中未找到记录")
    
    # 检查 market_quotes 集合
    print(f"\n5️⃣ 检查数据库 market_quotes 集合")
    quotes_coll = db["market_quotes"]
    
    quote_doc = quotes_coll.find_one({"code": test_code})
    
    if quote_doc:
        print(f"   ✅ 找到行情记录")
        print(f"   交易日期: {quote_doc.get('trade_date')}")
        print(f"   收盘价: {quote_doc.get('close')}")
        print(f"   成交额(元): {quote_doc.get('amount'):,.0f}")
        print(f"   成交额(亿元): {quote_doc.get('amount') / 1e8:.2f}")
        print(f"   成交额(万元): {quote_doc.get('amount') / 1e4:.2f}")
    else:
        print(f"   ⚠️ market_quotes 中未找到记录")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    print("\n💡 验证标准:")
    print("   - 如果成交额显示为 90.92亿 左右，说明修复成功 ✅")
    print("   - 如果成交额显示为 909.18万 或 0.0091亿，说明仍有问题 ❌")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_amount_fix())

