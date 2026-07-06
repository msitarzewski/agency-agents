#!/usr/bin/env python3
"""
AKShare财务数据获取调试脚本
"""

import sys
import os
import logging

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.akshare_utils import AKShareProvider

def test_akshare_financial_data():
    """测试AKShare财务数据获取"""
    print("=" * 60)
    print("🔍 AKShare财务数据获取调试测试")
    print("=" * 60)
    
    # 1. 获取AKShare提供者
    print("\n1. 获取AKShare提供者...")
    provider = AKShareProvider()
    print(f"   连接状态: {provider.connected}")
    
    if not provider.connected:
        print("❌ AKShare未连接，无法继续测试")
        return
    
    # 2. 直接调用get_financial_data方法
    print("\n2. 直接调用get_financial_data方法...")
    symbol = "600519"
    
    try:
        financial_data = provider.get_financial_data(symbol)
        print(f"   返回结果类型: {type(financial_data)}")
        print(f"   返回结果: {financial_data}")
        
        if financial_data:
            print("✅ 成功获取财务数据")
            for key, value in financial_data.items():
                if hasattr(value, '__len__'):
                    print(f"   - {key}: {len(value)}条记录")
                else:
                    print(f"   - {key}: {type(value)}")
        else:
            print("❌ 未获取到财务数据")
            
    except Exception as e:
        print(f"❌ 调用get_financial_data失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试条件判断
    print("\n3. 测试条件判断...")
    test_data = {}
    print(f"   空字典 any(test_data.values()): {any(test_data.values())}")
    
    test_data = {'main_indicators': None}
    print(f"   包含None any(test_data.values()): {any(test_data.values())}")
    
    test_data = {'main_indicators': {}}
    print(f"   包含空字典 any(test_data.values()): {any(test_data.values())}")
    
    test_data = {'main_indicators': {'pe': 18.5}}
    print(f"   包含数据 any(test_data.values()): {any(test_data.values())}")
    
    print("\n" + "=" * 60)
    print("✅ 调试测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_akshare_financial_data()