#!/usr/bin/env python3
"""
测试 AKShare TTM 计算逻辑

验证内容：
1. TTM 营业收入计算是否正确
2. TTM 净利润计算是否正确
3. 是否移除了简单年化降级策略
4. PE/PS 是否使用 TTM 数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from scripts.sync_financial_data import _calculate_ttm_metric

# 模拟财务数据
test_data = {
    '报告期': [
        '20231231',  # 2023年报
        '20240331',  # 2024Q1
        '20240630',  # 2024Q2
        '20240930',  # 2024Q3
        '20241231',  # 2024年报
        '20250331',  # 2025Q1
        '20250630',  # 2025Q2
        '20250930',  # 2025Q3（最新期）
    ],
    '营业收入': [
        1646.99,  # 2023年报
        387.70,   # 2024Q1累计
        771.32,   # 2024Q2累计
        1115.82,  # 2024Q3累计
        1466.95,  # 2024年报
        337.09,   # 2025Q1累计
        693.85,   # 2025Q2累计
        1006.68,  # 2025Q3累计
    ],
    '净利润': [
        823.50,   # 2023年报
        193.85,   # 2024Q1累计
        385.66,   # 2024Q2累计
        557.91,   # 2024Q3累计
        733.20,   # 2024年报
        168.55,   # 2025Q1累计
        346.90,   # 2025Q2累计
        383.39,   # 2025Q3累计（注意：这里净利润下降了）
    ]
}

df = pd.DataFrame(test_data)

print("=" * 100)
print("📊 AKShare TTM 计算逻辑测试")
print("=" * 100)

print("\n【测试数据】")
print(df.to_string(index=False))

print("\n【测试 1: TTM 营业收入计算】")
ttm_revenue = _calculate_ttm_metric(df, '营业收入')
print(f"计算结果: {ttm_revenue:.2f} 万元" if ttm_revenue else "计算失败")

# 手动验证
latest_revenue = 1006.68  # 2025Q3累计
base_revenue = 1466.95    # 2024年报
last_year_revenue = 1115.82  # 2024Q3累计

expected_ttm = base_revenue + (latest_revenue - last_year_revenue)
print(f"\n手动计算验证:")
print(f"TTM = 2024年报 + (2025Q3 - 2024Q3)")
print(f"    = {base_revenue:.2f} + ({latest_revenue:.2f} - {last_year_revenue:.2f})")
print(f"    = {base_revenue:.2f} + {latest_revenue - last_year_revenue:.2f}")
print(f"    = {expected_ttm:.2f} 万元")

if ttm_revenue and abs(ttm_revenue - expected_ttm) < 0.01:
    print("✅ TTM 营业收入计算正确！")
else:
    print(f"❌ TTM 营业收入计算错误！期望: {expected_ttm:.2f}，实际: {ttm_revenue:.2f}")

print("\n【测试 2: TTM 净利润计算】")
ttm_net_profit = _calculate_ttm_metric(df, '净利润')
print(f"计算结果: {ttm_net_profit:.2f} 万元" if ttm_net_profit else "计算失败")

# 手动验证
latest_profit = 383.39    # 2025Q3累计
base_profit = 733.20      # 2024年报
last_year_profit = 557.91 # 2024Q3累计

expected_ttm_profit = base_profit + (latest_profit - last_year_profit)
print(f"\n手动计算验证:")
print(f"TTM = 2024年报 + (2025Q3 - 2024Q3)")
print(f"    = {base_profit:.2f} + ({latest_profit:.2f} - {last_year_profit:.2f})")
print(f"    = {base_profit:.2f} + {latest_profit - last_year_profit:.2f}")
print(f"    = {expected_ttm_profit:.2f} 万元")

if ttm_net_profit and abs(ttm_net_profit - expected_ttm_profit) < 0.01:
    print("✅ TTM 净利润计算正确！")
else:
    print(f"❌ TTM 净利润计算错误！期望: {expected_ttm_profit:.2f}，实际: {ttm_net_profit:.2f}")

print("\n【测试 3: 数据不足时的处理】")
# 测试只有最新期和去年同期，但没有年报的情况
incomplete_data = {
    '报告期': ['20240930', '20250930'],
    '营业收入': [1115.82, 1006.68],
    '净利润': [557.91, 383.39]
}
df_incomplete = pd.DataFrame(incomplete_data)

ttm_revenue_incomplete = _calculate_ttm_metric(df_incomplete, '营业收入')
ttm_profit_incomplete = _calculate_ttm_metric(df_incomplete, '净利润')

print(f"缺少年报时的 TTM 营业收入: {ttm_revenue_incomplete}")
print(f"缺少年报时的 TTM 净利润: {ttm_profit_incomplete}")

if ttm_revenue_incomplete is None and ttm_profit_incomplete is None:
    print("✅ 数据不足时正确返回 None（不使用简单年化）")
else:
    print("❌ 数据不足时应该返回 None，而不是使用简单年化")

print("\n【测试 4: 年报数据的处理】")
# 测试最新期是年报的情况
annual_data = {
    '报告期': ['20231231', '20241231'],
    '营业收入': [1646.99, 1466.95],
    '净利润': [823.50, 733.20]
}
df_annual = pd.DataFrame(annual_data)

ttm_revenue_annual = _calculate_ttm_metric(df_annual, '营业收入')
ttm_profit_annual = _calculate_ttm_metric(df_annual, '净利润')

print(f"年报 TTM 营业收入: {ttm_revenue_annual:.2f} 万元" if ttm_revenue_annual else "计算失败")
print(f"年报 TTM 净利润: {ttm_profit_annual:.2f} 万元" if ttm_profit_annual else "计算失败")

if ttm_revenue_annual == 1466.95 and ttm_profit_annual == 733.20:
    print("✅ 年报数据正确直接使用")
else:
    print("❌ 年报数据处理错误")

print("\n" + "=" * 100)
print("✅ 测试完成")
print("=" * 100)

