#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试盈利股票的PE计算（如600036招商银行）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

def test_profitable_stock():
    """测试盈利股票的PE计算"""
    print("测试盈利股票的PE计算...")
    
    # 创建工具包
    config = DEFAULT_CONFIG.copy()
    config["online_tools"] = True
    toolkit = Toolkit(config)
    
    # 测试600036（招商银行）- 通常是盈利的
    print("\n=== 测试600036（招商银行）===")
    result = toolkit.get_stock_fundamentals_unified.invoke({
        'ticker': '600036',
        'start_date': '2025-06-01',
        'end_date': '2025-07-15',
        'curr_date': '2025-07-15'
    })
    
    # 查找估值指标
    lines = result.split('\n')
    
    print("\n📊 600036基本信息:")
    for i, line in enumerate(lines):
        if "股票名称" in line or "所属行业" in line:
            print(f"  {line}")
    
    print("\n💰 600036估值指标:")
    for i, line in enumerate(lines):
        if "估值指标" in line:
            # 打印估值指标及其后面的几行
            for j in range(i, min(len(lines), i+8)):
                if lines[j].strip() and not lines[j].startswith("###"):
                    print(f"  {lines[j]}")
                elif lines[j].startswith("###") and j > i:
                    break
            break
    
    print("\n📈 600036盈利能力:")
    for i, line in enumerate(lines):
        if "盈利能力指标" in line:
            # 打印盈利能力指标及其后面的几行
            for j in range(i, min(len(lines), i+8)):
                if lines[j].strip() and not lines[j].startswith("###"):
                    print(f"  {lines[j]}")
                elif lines[j].startswith("###") and j > i:
                    break
            break

if __name__ == "__main__":
    test_profitable_stock()