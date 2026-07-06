#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的估值指标测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

def test_valuation_simple():
    """简化的估值指标测试"""
    print("简化测试300750估值指标...")
    
    # 创建工具包
    config = DEFAULT_CONFIG.copy()
    config["online_tools"] = True
    toolkit = Toolkit(config)
    
    # 获取基本面数据
    result = toolkit.get_stock_fundamentals_unified.invoke({
        'ticker': '300750',
        'start_date': '2025-06-01',
        'end_date': '2025-07-15',
        'curr_date': '2025-07-15'
    })
    
    # 查找估值指标部分
    lines = result.split('\n')
    
    print("\n=== 查找估值指标 ===")
    for i, line in enumerate(lines):
        if "估值指标" in line:
            print(f"找到估值指标部分在第{i+1}行:")
            # 打印估值指标及其后面的几行
            for j in range(max(0, i-1), min(len(lines), i+10)):
                print(f"{j+1:3d}: {lines[j]}")
            break
    else:
        print("未找到估值指标部分")
        
        # 搜索包含PE、PB、PS的行
        print("\n=== 搜索PE、PB、PS相关行 ===")
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ["市盈率", "市净率", "市销率", "PE", "PB", "PS"]):
                print(f"{i+1:3d}: {line}")

if __name__ == "__main__":
    test_valuation_simple()