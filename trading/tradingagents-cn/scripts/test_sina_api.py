#!/usr/bin/env python3
"""测试 AkShare 中的新浪财经接口"""

import akshare as ak

print("🔍 测试 AkShare 中的新浪财经接口...")
print("=" * 70)

# 查看 AkShare 中所有包含 sina 的函数
print("\n📋 AkShare 中包含 'sina' 的函数:")
sina_functions = [func for func in dir(ak) if 'sina' in func.lower()]
for func in sina_functions:
    print(f"  - {func}")

print("\n" + "=" * 70)

# 测试一些常用的新浪接口
test_functions = [
    ('stock_zh_a_spot', '沪深A股实时行情（新浪）'),
    ('stock_hk_spot', '港股实时行情（新浪）'),
    ('stock_us_spot', '美股实时行情（新浪）'),
]

for func_name, description in test_functions:
    if hasattr(ak, func_name):
        print(f"\n📊 测试 {func_name} ({description}):")
        try:
            func = getattr(ak, func_name)
            df = func()
            if df is not None and not df.empty:
                print(f"   ✅ 成功: {len(df)}条记录")
                print(f"   列名: {list(df.columns)}")
                if len(df) > 0:
                    print(f"   前3条数据:")
                    print(df.head(3))
            else:
                print(f"   ❌ 无数据")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    else:
        print(f"\n⚠️ {func_name} 不存在")

print("\n" + "=" * 70)
print("✅ 测试完成")

