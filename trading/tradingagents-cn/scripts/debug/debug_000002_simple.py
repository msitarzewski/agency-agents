#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化调试000002股票PE计算
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.data_source_manager import get_china_stock_data_unified

def debug_000002_simple():
    """简化调试000002股票PE计算"""
    print("调试000002股票PE计算...")
    
    # 调用统一数据获取函数
    print("\n=== 调用统一数据获取函数 ===")
    try:
        result = get_china_stock_data_unified('000002', '2025-06-01', '2025-07-15')
        print("数据获取成功，长度:", len(result))
        
        # 查找PE相关信息
        lines = result.split('\n')
        print("\n=== 查找PE相关信息 ===")
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['PE', '市盈率', 'PB', '市净率', 'PS', '市销率']):
                print(f"第{i+1}行: {line}")
        
        # 查找估值指标部分
        print("\n=== 估值指标部分 ===")
        found_valuation = False
        for i, line in enumerate(lines):
            if "估值指标" in line:
                found_valuation = True
                print(f"找到估值指标部分 (第{i+1}行):")
                # 打印估值指标及其后面的几行
                for j in range(i, min(len(lines), i+10)):
                    if lines[j].strip():
                        print(f"  {lines[j]}")
                    if j > i and lines[j].startswith("###"):
                        break
                break
        
        if not found_valuation:
            print("未找到估值指标部分")
            
        # 查找财务数据
        print("\n=== 财务数据部分 ===")
        for i, line in enumerate(lines):
            if "财务数据" in line or "基本面" in line:
                print(f"第{i+1}行: {line}")
                
    except Exception as e:
        print(f"数据获取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_000002_simple()