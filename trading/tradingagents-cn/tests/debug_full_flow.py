#!/usr/bin/env python3
"""
调试完整的AKShare数据获取和解析流程
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置详细的日志级别
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
from tradingagents.dataflows.akshare_utils import get_akshare_provider

def debug_full_flow():
    """调试完整的数据获取和解析流程"""
    symbol = "600519"
    
    print("🔍 开始调试完整流程...")
    
    # 1. 初始化数据提供器
    provider = OptimizedChinaDataProvider()
    print(f"✅ 数据提供器初始化完成")
    
    # 2. 获取AKShare财务数据
    print(f"\n📊 获取AKShare财务数据...")
    akshare_provider = get_akshare_provider()
    financial_data = akshare_provider.get_financial_data(symbol)
    stock_info = akshare_provider.get_stock_info(symbol)
    
    print(f"   财务数据键: {list(financial_data.keys()) if financial_data else 'None'}")
    print(f"   股票信息: {stock_info}")
    
    # 3. 模拟股价获取
    print(f"\n💰 模拟股价获取...")
    current_price = "1800.0"  # 模拟股价
    try:
        price_value = float(current_price.replace('¥', '').replace(',', ''))
        print(f"   解析股价: {price_value}")
    except Exception as e:
        print(f"   股价解析失败: {e}")
        price_value = 10.0
    
    # 4. 调用解析函数
    print(f"\n🔧 调用解析函数...")
    try:
        metrics = provider._parse_akshare_financial_data(financial_data, stock_info, price_value)
        if metrics:
            print(f"✅ 解析成功!")
            print(f"   PE: {metrics.get('pe', 'N/A')}")
            print(f"   PB: {metrics.get('pb', 'N/A')}")
            print(f"   ROE: {metrics.get('roe', 'N/A')}")
            print(f"   数据来源: {metrics.get('data_source', 'N/A')}")
        else:
            print(f"❌ 解析失败，返回None")
    except Exception as e:
        print(f"❌ 解析异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 测试_get_real_financial_metrics函数
    print(f"\n🔍 测试_get_real_financial_metrics函数...")
    try:
        print(f"   调用参数: symbol={symbol}, price_value={price_value}")
        real_metrics = provider._get_real_financial_metrics(symbol, price_value)
        print(f"   返回结果: {real_metrics}")
        if real_metrics:
            print(f"✅ 真实财务指标获取成功!")
            print(f"   PE: {real_metrics.get('pe', 'N/A')}")
            print(f"   PB: {real_metrics.get('pb', 'N/A')}")
            print(f"   ROE: {real_metrics.get('roe', 'N/A')}")
            print(f"   数据来源: {real_metrics.get('data_source', 'N/A')}")
        else:
            print(f"❌ 真实财务指标获取失败")
    except Exception as e:
        print(f"❌ 真实财务指标获取异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 测试_estimate_financial_metrics函数
    print(f"\n🔍 测试_estimate_financial_metrics函数...")
    try:
        print(f"   调用参数: symbol={symbol}, current_price={current_price}")
        estimated_metrics = provider._estimate_financial_metrics(symbol, current_price)
        print(f"   返回结果: {estimated_metrics}")
        if estimated_metrics:
            print(f"✅ 财务指标估算成功!")
            print(f"   PE: {estimated_metrics.get('pe', 'N/A')}")
            print(f"   PB: {estimated_metrics.get('pb', 'N/A')}")
            print(f"   ROE: {estimated_metrics.get('roe', 'N/A')}")
            print(f"   数据来源: {estimated_metrics.get('data_source', 'N/A')}")
        else:
            print(f"❌ 财务指标估算失败")
    except Exception as e:
        print(f"❌ 财务指标估算异常: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*60)
    print(f"✅ 调试完成")
    print(f"="*60)

if __name__ == "__main__":
    debug_full_flow()