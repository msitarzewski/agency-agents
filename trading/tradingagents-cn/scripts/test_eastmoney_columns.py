#!/usr/bin/env python3
"""测试东方财富接口返回的列名"""

import akshare as ak

print("🔍 测试东方财富接口返回的列名...")

# 获取数据
df = ak.stock_zh_a_spot_em()

print(f"\n✅ 获取到 {len(df)} 条记录")
print(f"\n📋 列名: {list(df.columns)}")

# 显示前10条数据，查看代码格式
print(f"\n📊 前10条数据（查看代码格式）:")
print(df[['代码', '名称', '最新价']].head(10))

# 查找测试股票
test_codes = ['000001', '600000', '603175', '688485']

for code in test_codes:
    print(f"\n🔍 查找 {code}:")
    
    # 直接匹配
    stock_data = df[df['代码'] == code]
    if not stock_data.empty:
        print(f"  ✅ 找到:")
        print(f"     代码: {stock_data.iloc[0]['代码']}")
        print(f"     名称: {stock_data.iloc[0]['名称']}")
        print(f"     最新价: {stock_data.iloc[0]['最新价']}")
    else:
        print(f"  ❌ 未找到")

# 统计不同市场的股票数量
print(f"\n📊 市场分布:")
print(f"  60开头(沪市主板): {len(df[df['代码'].str.startswith('60', na=False)])} 只")
print(f"  00开头(深市主板): {len(df[df['代码'].str.startswith('00', na=False)])} 只")
print(f"  30开头(创业板): {len(df[df['代码'].str.startswith('30', na=False)])} 只")
print(f"  68开头(科创板): {len(df[df['代码'].str.startswith('68', na=False)])} 只")
print(f"  43/83/87开头(北交所): {len(df[df['代码'].str.match(r'^(43|83|87)', na=False)])} 只")

