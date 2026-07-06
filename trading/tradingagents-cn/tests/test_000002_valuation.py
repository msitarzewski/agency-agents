#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试000002股票的估值指标计算
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

def test_000002_valuation():
    """测试000002股票的估值指标"""
    print("测试000002股票估值指标计算...")
    
    # 创建工具包
    config = DEFAULT_CONFIG.copy()
    config["online_tools"] = True
    toolkit = Toolkit(config)
    
    # 获取基本面数据
    result = toolkit.get_stock_fundamentals_unified.invoke({
        'ticker': '000002',
        'start_date': '2025-06-01',
        'end_date': '2025-07-15',
        'curr_date': '2025-07-15'
    })
    
    # 查找估值指标部分
    lines = result.split('\n')
    
    print("\n=== 000002股票基本信息 ===")
    for i, line in enumerate(lines):
        if "股票名称" in line or "所属行业" in line or "市场板块" in line:
            print(line)
    
    print("\n=== 000002估值指标 ===")
    found_valuation = False
    for i, line in enumerate(lines):
        if "估值指标" in line:
            found_valuation = True
            print(f"找到估值指标部分:")
            # 打印估值指标及其后面的几行
            for j in range(i, min(len(lines), i+8)):
                if lines[j].strip() and not lines[j].startswith("###"):
                    print(f"  {lines[j]}")
                elif lines[j].startswith("###") and j > i:
                    break
            break
    
    if not found_valuation:
        print("未找到估值指标部分，搜索相关关键词...")
        # 搜索包含PE、PB、PS的行
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ["市盈率", "市净率", "市销率", "PE", "PB", "PS"]):
                print(f"  {line}")
    
    print("\n=== 财务健康度指标 ===")
    for i, line in enumerate(lines):
        if "财务健康度" in line:
            # 打印财务健康度及其后面的几行
            for j in range(i, min(len(lines), i+8)):
                if lines[j].strip() and not lines[j].startswith("##"):
                    print(f"  {lines[j]}")
                elif lines[j].startswith("##") and j > i:
                    break
            break

if __name__ == "__main__":
    test_000002_valuation()