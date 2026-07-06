#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细调试000002股票PE计算问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider

def debug_000002_detailed():
    """详细调试000002股票PE计算"""
    print("详细调试000002股票PE计算...")
    
    # 创建数据提供器
    provider = OptimizedChinaDataProvider()
    
    # 获取基本面数据
    print("\n=== 获取基本面数据 ===")
    try:
        fundamentals = provider.get_fundamentals_data('000002')
        print(f"基本面数据长度: {len(fundamentals)}")
        
        # 查找估值指标
        lines = fundamentals.split('\n')
        print("\n=== 估值指标详情 ===")
        found_valuation = False
        for i, line in enumerate(lines):
            if "估值指标" in line:
                found_valuation = True
                print(f"找到估值指标部分 (第{i+1}行):")
                # 打印估值指标及其后面的几行
                for j in range(i, min(len(lines), i+10)):
                    if lines[j].strip():
                        print(f"  {lines[j]}")
                        # 特别关注PE行
                        if "市盈率" in lines[j] or "PE" in lines[j]:
                            print(f"    *** PE行: {lines[j]} ***")
                    if j > i and lines[j].startswith("###"):
                        break
                break
        
        if not found_valuation:
            print("未找到估值指标部分")
            # 搜索所有包含PE的行
            print("\n=== 搜索所有PE相关行 ===")
            for i, line in enumerate(lines):
                if "PE" in line or "市盈率" in line:
                    print(f"第{i+1}行: {line}")
        
        # 测试内部方法
        print("\n=== 测试内部财务指标计算 ===")
        try:
            # 获取当前价格
            current_price_data = provider._get_stock_basic_info_only('000002')
            print(f"当前价格数据: {current_price_data[:200]}...")
            
            # 提取价格
            price_value = 6.5  # 假设价格
            for line in current_price_data.split('\n'):
                if "当前价格" in line or "最新价格" in line:
                    try:
                        price_str = line.split(':')[1].strip().replace('¥', '').replace('元', '')
                        price_value = float(price_str)
                        print(f"提取到价格: {price_value}")
                        break
                    except:
                        pass
            
            # 调用内部方法获取真实财务指标
            metrics = provider._get_real_financial_metrics('000002', price_value)
            print(f"\n真实财务指标:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
                if key == 'pe':
                    print(f"    *** PE值: {value} ***")
                    
        except Exception as e:
            print(f"内部方法测试失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"获取基本面数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_000002_detailed()