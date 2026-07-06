#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试估值指标计算结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

def test_valuation_indicators():
    """测试估值指标计算"""
    print("测试300750估值指标计算...")
    
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
    
    print("\n=== 估值指标部分 ===")
    in_valuation_section = False
    
    for line in lines:
        if "估值指标" in line:
            in_valuation_section = True
            print(line)
        elif in_valuation_section:
            if "市盈率" in line or "市净率" in line or "市销率" in line or "股息收益率" in line:
                print(line)
            elif line.strip() == "" or line.startswith("##"):
                if line.startswith("##"):
                    break
    
    print("\n=== 完整结果预览 ===")
    # 只显示前2000个字符
    print(result[:2000])
    if len(result) > 2000:
        print("...(结果已截断)")

if __name__ == "__main__":
    test_valuation_indicators()