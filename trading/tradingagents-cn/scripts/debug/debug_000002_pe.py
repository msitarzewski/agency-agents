#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试000002股票PE为N/A的原因
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.data_source_manager import get_china_stock_data_unified
from pymongo import MongoClient
import pandas as pd

def debug_000002_pe():
    """调试000002股票PE计算"""
    print("调试000002股票PE计算...")
    
    # 连接MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['stock_data']
    
    # 1. 检查stock_basic_info中的PE数据
    print("\n=== 检查stock_basic_info中的PE数据 ===")
    basic_info = db.stock_basic_info.find_one({'ts_code': '000002.SZ'})
    if basic_info:
        print(f"找到基本信息:")
        print(f"  股票代码: {basic_info.get('ts_code')}")
        print(f"  股票名称: {basic_info.get('name')}")
        print(f"  PE: {basic_info.get('pe')}")
        print(f"  PB: {basic_info.get('pb')}")
        print(f"  PE_TTM: {basic_info.get('pe_ttm')}")
        print(f"  总市值: {basic_info.get('total_mv')}")
    else:
        print("未找到基本信息")
    
    # 2. 检查财务数据
    print("\n=== 检查财务数据 ===")
    financial_data = list(db.stock_financial_data.find(
        {'ts_code': '000002.SZ'}
    ).sort('end_date', -1).limit(5))
    
    if financial_data:
        print(f"找到 {len(financial_data)} 条财务数据:")
        for i, data in enumerate(financial_data):
            print(f"  第{i+1}条 - 报告期: {data.get('end_date')}")
            print(f"    净利润: {data.get('n_income')}")
            print(f"    营业收入: {data.get('revenue')}")
            print(f"    净资产: {data.get('total_hldr_eqy_exc_min_int')}")
    else:
        print("未找到财务数据")
    
    # 3. 手动计算PE
    print("\n=== 手动计算PE ===")
    if basic_info and financial_data:
        total_mv = basic_info.get('total_mv')  # 总市值（万元）
        latest_financial = financial_data[0]
        net_income = latest_financial.get('n_income')  # 净利润（万元）
        
        print(f"总市值: {total_mv} 万元")
        print(f"最新净利润: {net_income} 万元")
        
        if total_mv and net_income and net_income > 0:
            pe_calculated = total_mv / net_income
            print(f"手动计算PE: {total_mv} / {net_income} = {pe_calculated:.2f}")
        else:
            print("无法计算PE - 净利润为负或数据缺失")
            if net_income and net_income <= 0:
                print(f"净利润为负: {net_income}")
    
    # 4. 调用统一数据获取函数
    print("\n=== 调用统一数据获取函数 ===")
    try:
        result = get_china_stock_data_unified('000002', depth='full')
        print("数据获取成功，长度:", len(result))
        
        # 查找PE相关信息
        lines = result.split('\n')
        for line in lines:
            if 'PE' in line or '市盈率' in line:
                print(f"  {line}")
    except Exception as e:
        print(f"数据获取失败: {e}")

if __name__ == "__main__":
    debug_000002_pe()