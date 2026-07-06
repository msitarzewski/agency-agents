#!/usr/bin/env python3
"""等待一段时间后重试，避免频率限制"""

import time
import akshare as ak

print("⏰ 等待 30 秒，避免频率限制...")
time.sleep(30)

print("\n🔍 测试东方财富接口...")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"✅ 成功获取 {len(df)} 条记录")
    print(f"📋 列名: {list(df.columns)}")
    
    # 查找测试股票
    test_codes = ['000001', '600000', '603175']
    for code in test_codes:
        stock_data = df[df['代码'] == code]
        if not stock_data.empty:
            print(f"\n✅ 找到 {code}:")
            print(f"   名称: {stock_data.iloc[0]['名称']}")
            print(f"   最新价: {stock_data.iloc[0]['最新价']}")
        else:
            print(f"\n❌ 未找到 {code}")
    
    # 显示前5条
    print(f"\n📊 前5条数据:")
    print(df[['代码', '名称', '最新价']].head(5))
    
except Exception as e:
    print(f"❌ 东方财富接口失败: {e}")

print("\n" + "="*70)
print("\n⏰ 再等待 10 秒...")
time.sleep(10)

print("\n🔍 测试新浪接口...")
try:
    df = ak.stock_zh_a_spot()
    print(f"✅ 成功获取 {len(df)} 条记录")
    print(f"📋 列名: {list(df.columns)}")
    
    # 查找测试股票
    test_codes = ['000001', '600000', '603175']
    for code in test_codes:
        # 尝试不同的匹配方式
        stock_data = df[df['代码'] == code]
        if stock_data.empty:
            # 尝试带前缀
            for prefix in ['sh', 'sz', 'bj']:
                stock_data = df[df['代码'] == f"{prefix}{code}"]
                if not stock_data.empty:
                    break
        
        if not stock_data.empty:
            print(f"\n✅ 找到 {code}:")
            print(f"   代码: {stock_data.iloc[0]['代码']}")
            print(f"   名称: {stock_data.iloc[0]['名称']}")
            print(f"   最新价: {stock_data.iloc[0]['最新价']}")
        else:
            print(f"\n❌ 未找到 {code}")
    
    # 显示前5条
    print(f"\n📊 前5条数据:")
    print(df[['代码', '名称', '最新价']].head(5))
    
    # 统计代码格式
    print(f"\n📊 代码格式统计:")
    has_prefix = df[df['代码'].str.match(r'^(sh|sz|bj)', na=False)]
    print(f"   带前缀(sh/sz/bj): {len(has_prefix)} 只")
    print(f"   不带前缀: {len(df) - len(has_prefix)} 只")
    
except Exception as e:
    print(f"❌ 新浪接口失败: {e}")

