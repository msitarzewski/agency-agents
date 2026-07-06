"""
测试 TTM 计算逻辑的正确性

这个脚本使用模拟数据来验证 TTM 计算公式是否正确
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.dataflows.providers.china.tushare import TushareProvider


def test_ttm_calculation():
    """测试 TTM 计算逻辑"""
    
    provider = TushareProvider()
    
    print("=" * 80)
    print("TTM 计算逻辑测试")
    print("=" * 80)
    
    # 测试场景 1：正常情况 - 有完整的年报和去年同期数据
    print("\n【测试场景 1】正常情况 - 2025Q2，有 2024年报 和 2024Q2")
    print("-" * 80)
    
    income_statements_1 = [
        {'end_date': '20250630', 'revenue': 600.0},  # 2025Q2: 600万（1-6月累计）
        {'end_date': '20250331', 'revenue': 300.0},  # 2025Q1: 300万（1-3月累计）
        {'end_date': '20241231', 'revenue': 1100.0}, # 2024年报: 1100万（1-12月累计）
        {'end_date': '20240930', 'revenue': 800.0},  # 2024Q3: 800万（1-9月累计）
        {'end_date': '20240630', 'revenue': 500.0},  # 2024Q2: 500万（1-6月累计）
        {'end_date': '20240331', 'revenue': 250.0},  # 2024Q1: 250万（1-3月累计）
    ]
    
    ttm = provider._calculate_ttm_from_tushare(income_statements_1, 'revenue')
    
    print(f"输入数据:")
    print(f"  2025Q2: 600万（2025年1-6月累计）")
    print(f"  2024年报: 1100万（2024年1-12月累计）")
    print(f"  2024Q2: 500万（2024年1-6月累计）")
    print(f"\n计算过程:")
    print(f"  TTM = 2024年报 + (2025Q2 - 2024Q2)")
    print(f"      = 1100 + (600 - 500)")
    print(f"      = 1100 + 100")
    print(f"      = 1200万")
    print(f"\n实际计算结果: {ttm:.2f}万")
    print(f"预期结果: 1200.00万")
    print(f"测试结果: {'✅ 通过' if abs(ttm - 1200.0) < 0.01 else '❌ 失败'}")
    
    # 验证：用单季度累加
    print(f"\n验证（单季度累加）:")
    q4_2024 = 1100.0 - 800.0  # 2024Q4单季 = 2024年报 - 2024Q3
    q1_2025 = 300.0           # 2025Q1单季
    q2_2025 = 600.0 - 300.0   # 2025Q2单季 = 2025Q2累计 - 2025Q1累计
    q3_2024 = 800.0 - 500.0   # 2024Q3单季 = 2024Q3累计 - 2024Q2累计
    
    print(f"  2024Q3单季 = 2024Q3累计 - 2024Q2累计 = 800 - 500 = {q3_2024:.2f}万")
    print(f"  2024Q4单季 = 2024年报 - 2024Q3累计 = 1100 - 800 = {q4_2024:.2f}万")
    print(f"  2025Q1单季 = 2025Q1累计 = {q1_2025:.2f}万")
    print(f"  2025Q2单季 = 2025Q2累计 - 2025Q1累计 = 600 - 300 = {q2_2025:.2f}万")
    print(f"  TTM = {q3_2024:.2f} + {q4_2024:.2f} + {q1_2025:.2f} + {q2_2025:.2f} = {q3_2024 + q4_2024 + q1_2025 + q2_2025:.2f}万")
    
    # 测试场景 2：最新期是年报
    print("\n" + "=" * 80)
    print("【测试场景 2】最新期是年报 - 2025年报")
    print("-" * 80)
    
    income_statements_2 = [
        {'end_date': '20251231', 'revenue': 1300.0}, # 2025年报: 1300万
        {'end_date': '20250930', 'revenue': 950.0},  # 2025Q3: 950万
        {'end_date': '20250630', 'revenue': 600.0},  # 2025Q2: 600万
    ]
    
    ttm = provider._calculate_ttm_from_tushare(income_statements_2, 'revenue')
    
    print(f"输入数据:")
    print(f"  2025年报: 1300万（2025年1-12月累计）")
    print(f"\n计算过程:")
    print(f"  最新期是年报，直接使用")
    print(f"  TTM = 1300万")
    print(f"\n实际计算结果: {ttm:.2f}万")
    print(f"预期结果: 1300.00万")
    print(f"测试结果: {'✅ 通过' if abs(ttm - 1300.0) < 0.01 else '❌ 失败'}")
    
    # 测试场景 3：缺少去年同期数据
    print("\n" + "=" * 80)
    print("【测试场景 3】缺少去年同期数据 - 2025Q2，但没有 2024Q2")
    print("-" * 80)
    
    income_statements_3 = [
        {'end_date': '20250630', 'revenue': 600.0},  # 2025Q2: 600万
        {'end_date': '20250331', 'revenue': 300.0},  # 2025Q1: 300万
        {'end_date': '20241231', 'revenue': 1100.0}, # 2024年报: 1100万
        {'end_date': '20240930', 'revenue': 800.0},  # 2024Q3: 800万
        # 缺少 2024Q2
        {'end_date': '20240331', 'revenue': 250.0},  # 2024Q1: 250万
    ]
    
    ttm = provider._calculate_ttm_from_tushare(income_statements_3, 'revenue')
    
    print(f"输入数据:")
    print(f"  2025Q2: 600万")
    print(f"  2024年报: 1100万")
    print(f"  ❌ 缺少 2024Q2")
    print(f"\n计算过程:")
    print(f"  无法计算 TTM，因为缺少去年同期数据")
    print(f"\n实际计算结果: {ttm}")
    print(f"预期结果: None")
    print(f"测试结果: {'✅ 通过' if ttm is None else '❌ 失败'}")
    
    # 测试场景 4：缺少基准年报（年报未公布）
    print("\n" + "=" * 80)
    print("【测试场景 4】缺少基准年报 - 2025Q1，但 2024年报未公布")
    print("-" * 80)
    
    income_statements_4 = [
        {'end_date': '20250331', 'revenue': 300.0},  # 2025Q1: 300万
        {'end_date': '20240930', 'revenue': 800.0},  # 2024Q3: 800万
        {'end_date': '20240630', 'revenue': 500.0},  # 2024Q2: 500万
        {'end_date': '20240331', 'revenue': 250.0},  # 2024Q1: 250万
        # 缺少 2024年报（通常在 2025年3-4月才公布）
        {'end_date': '20231231', 'revenue': 1000.0}, # 2023年报: 1000万（太旧了）
    ]
    
    ttm = provider._calculate_ttm_from_tushare(income_statements_4, 'revenue')
    
    print(f"输入数据:")
    print(f"  2025Q1: 300万")
    print(f"  2024Q1: 250万")
    print(f"  ❌ 缺少 2024年报（需要在 2024Q1 之后的年报）")
    print(f"  2023年报: 1000万（在 2024Q1 之前，不能用）")
    print(f"\n计算过程:")
    print(f"  无法计算 TTM，因为缺少基准年报")
    print(f"\n实际计算结果: {ttm}")
    print(f"预期结果: None")
    print(f"测试结果: {'✅ 通过' if ttm is None else '❌ 失败'}")
    
    # 测试场景 5：2025Q3 的 TTM 计算
    print("\n" + "=" * 80)
    print("【测试场景 5】2025Q3 TTM 计算")
    print("-" * 80)
    
    income_statements_5 = [
        {'end_date': '20250930', 'revenue': 900.0},  # 2025Q3: 900万（1-9月累计）
        {'end_date': '20250630', 'revenue': 600.0},  # 2025Q2: 600万
        {'end_date': '20250331', 'revenue': 300.0},  # 2025Q1: 300万
        {'end_date': '20241231', 'revenue': 1100.0}, # 2024年报: 1100万
        {'end_date': '20240930', 'revenue': 800.0},  # 2024Q3: 800万（1-9月累计）
        {'end_date': '20240630', 'revenue': 500.0},  # 2024Q2: 500万
    ]
    
    ttm = provider._calculate_ttm_from_tushare(income_statements_5, 'revenue')
    
    print(f"输入数据:")
    print(f"  2025Q3: 900万（2025年1-9月累计）")
    print(f"  2024年报: 1100万（2024年1-12月累计）")
    print(f"  2024Q3: 800万（2024年1-9月累计）")
    print(f"\n计算过程:")
    print(f"  TTM = 2024年报 + (2025Q3 - 2024Q3)")
    print(f"      = 1100 + (900 - 800)")
    print(f"      = 1100 + 100")
    print(f"      = 1200万")
    print(f"\n实际计算结果: {ttm:.2f}万")
    print(f"预期结果: 1200.00万")
    print(f"测试结果: {'✅ 通过' if abs(ttm - 1200.0) < 0.01 else '❌ 失败'}")
    
    # 验证：用单季度累加
    print(f"\n验证（单季度累加）:")
    q4_2024 = 1100.0 - 800.0  # 2024Q4单季
    q1_2025 = 300.0           # 2025Q1单季
    q2_2025 = 600.0 - 300.0   # 2025Q2单季
    q3_2025 = 900.0 - 600.0   # 2025Q3单季
    
    print(f"  2024Q4单季 = 2024年报 - 2024Q3累计 = 1100 - 800 = {q4_2024:.2f}万")
    print(f"  2025Q1单季 = {q1_2025:.2f}万")
    print(f"  2025Q2单季 = 2025Q2累计 - 2025Q1累计 = 600 - 300 = {q2_2025:.2f}万")
    print(f"  2025Q3单季 = 2025Q3累计 - 2025Q2累计 = 900 - 600 = {q3_2025:.2f}万")
    print(f"  TTM = {q4_2024:.2f} + {q1_2025:.2f} + {q2_2025:.2f} + {q3_2025:.2f} = {q4_2024 + q1_2025 + q2_2025 + q3_2025:.2f}万")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_ttm_calculation()

