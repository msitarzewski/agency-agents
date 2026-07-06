#!/usr/bin/env python3
"""
测试 pre_close 字段修复

验证港股历史数据的 pre_close 字段是否正确添加
"""

import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_pre_close_calculation():
    """测试 pre_close 字段计算"""
    
    print("=" * 80)
    print("🔍 测试 pre_close 字段计算")
    print("=" * 80)
    
    # 模拟 AKShare 返回的数据（没有 pre_close 字段）
    data = pd.DataFrame({
        'date': ['2025-11-03', '2025-11-04', '2025-11-05', '2025-11-06', '2025-11-07'],
        'open': [630.5, 631.0, 621.0, 629.5, 638.0],
        'high': [634.0, 640.0, 632.0, 645.5, 643.0],
        'low': [622.5, 625.5, 613.0, 629.5, 628.5],
        'close': [628.0, 629.0, 629.0, 644.0, 634.0],
        'volume': [11591004.0, 14972125.0, 13309811.0, 13081287.0, 13314360.0]
    })
    
    print("\n📊 原始数据（模拟 AKShare 返回）:")
    print(data.to_string(index=False))
    
    # 应用修复逻辑：添加 pre_close 字段
    if 'pre_close' not in data.columns and 'close' in data.columns:
        data['pre_close'] = data['close'].shift(1)
        print("\n✅ 添加 pre_close 字段（使用 shift(1)）")
    
    print("\n📊 添加 pre_close 后的数据:")
    print(data[['date', 'open', 'close', 'pre_close']].to_string(index=False))
    
    # 验证最新一天的数据
    print("\n" + "=" * 80)
    print("🔍 验证最新一天的数据 (2025-11-07)")
    print("=" * 80)
    
    latest = data.iloc[-1]
    print(f"\n今日开盘: {latest['open']}")
    print(f"今日收盘: {latest['close']}")
    print(f"昨日收盘 (pre_close): {latest['pre_close']}")
    
    # 检查是否正确
    expected_pre_close = 644.0
    actual_pre_close = latest['pre_close']
    
    if actual_pre_close == expected_pre_close:
        print(f"\n✅ pre_close 字段正确: {actual_pre_close} == {expected_pre_close}")
    else:
        print(f"\n❌ pre_close 字段错误: {actual_pre_close} != {expected_pre_close}")
    
    # 计算涨跌幅
    if pd.notna(latest['pre_close']) and latest['pre_close'] > 0:
        change = latest['close'] - latest['pre_close']
        pct_chg = (change / latest['pre_close']) * 100
        
        print(f"\n📈 涨跌数据:")
        print(f"  涨跌额: {change:.2f}")
        print(f"  涨跌幅: {pct_chg:.2f}%")
    
    # 检查第一天的 pre_close（应该是 NaN）
    print("\n" + "=" * 80)
    print("🔍 检查第一天的 pre_close（应该是 NaN）")
    print("=" * 80)
    
    first = data.iloc[0]
    print(f"\n第一天日期: {first['date']}")
    print(f"第一天 pre_close: {first['pre_close']}")
    
    if pd.isna(first['pre_close']):
        print("✅ 第一天的 pre_close 正确为 NaN（没有前一天数据）")
    else:
        print(f"❌ 第一天的 pre_close 应该是 NaN，但是: {first['pre_close']}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_pre_close_calculation()

