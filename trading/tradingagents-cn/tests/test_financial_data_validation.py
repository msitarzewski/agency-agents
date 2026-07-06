#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试财务数据验证逻辑
验证毛利率、净利率、ROE、ROA 等指标的范围检查
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataFlow


def test_financial_data_validation():
    """测试财务数据验证"""
    
    dataflow = OptimizedChinaDataFlow()
    
    # 测试用例 1: 正常数据
    print("\n" + "="*80)
    print("测试用例 1: 正常数据")
    print("="*80)
    
    normal_data = {
        'roe': 15.5,
        'roa': 8.2,
        'gross_margin': 45.3,
        'netprofit_margin': 12.8,
        'code': '000001'
    }
    
    result = dataflow._parse_mongodb_financial_data(normal_data, 10.0)
    print(f"ROE: {result.get('roe')}")
    print(f"ROA: {result.get('roa')}")
    print(f"毛利率: {result.get('gross_margin')}")
    print(f"净利率: {result.get('net_margin')}")
    
    # 测试用例 2: 异常数据 (毛利率超出范围)
    print("\n" + "="*80)
    print("测试用例 2: 异常数据 (毛利率 = 339904690.2)")
    print("="*80)
    
    abnormal_data = {
        'roe': 9.5,
        'roa': 8.4,
        'gross_margin': 339904690.2,  # 异常值
        'netprofit_margin': 15.3,
        'code': '000001'
    }
    
    result = dataflow._parse_mongodb_financial_data(abnormal_data, 10.0)
    print(f"ROE: {result.get('roe')}")
    print(f"ROA: {result.get('roa')}")
    print(f"毛利率: {result.get('gross_margin')} (应该是 N/A)")
    print(f"净利率: {result.get('net_margin')}")
    
    # 测试用例 3: 边界值
    print("\n" + "="*80)
    print("测试用例 3: 边界值")
    print("="*80)
    
    boundary_data = {
        'roe': 100.0,  # 边界值
        'roa': -50.0,  # 负值
        'gross_margin': 99.9,  # 接近上限
        'netprofit_margin': -10.5,  # 负值
        'code': '000001'
    }
    
    result = dataflow._parse_mongodb_financial_data(boundary_data, 10.0)
    print(f"ROE: {result.get('roe')}")
    print(f"ROA: {result.get('roa')}")
    print(f"毛利率: {result.get('gross_margin')}")
    print(f"净利率: {result.get('net_margin')}")
    
    # 测试用例 4: 超出边界
    print("\n" + "="*80)
    print("测试用例 4: 超出边界")
    print("="*80)
    
    out_of_range_data = {
        'roe': 250.0,  # 超出范围
        'roa': 150.0,  # 超出范围
        'gross_margin': 120.0,  # 超出范围
        'netprofit_margin': -150.0,  # 超出范围
        'code': '000001'
    }
    
    result = dataflow._parse_mongodb_financial_data(out_of_range_data, 10.0)
    print(f"ROE: {result.get('roe')} (应该是 N/A)")
    print(f"ROA: {result.get('roa')} (应该是 N/A)")
    print(f"毛利率: {result.get('gross_margin')} (应该是 N/A)")
    print(f"净利率: {result.get('net_margin')} (应该是 N/A)")
    
    print("\n" + "="*80)
    print("✅ 测试完成!")
    print("="*80)


if __name__ == '__main__':
    test_financial_data_validation()

