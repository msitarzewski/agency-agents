#!/usr/bin/env python3
"""
直接测试AKShare API
"""

import akshare as ak
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')

def test_akshare_apis():
    """测试AKShare各个财务数据API"""
    print("=" * 60)
    print("🔍 直接测试AKShare财务数据API")
    print("=" * 60)
    
    symbol = "600519"
    
    # 1. 测试主要财务指标API
    print(f"\n1. 测试主要财务指标API: stock_financial_abstract")
    try:
        data = ak.stock_financial_abstract(symbol=symbol)
        if data is not None and not data.empty:
            print(f"✅ 成功获取主要财务指标: {len(data)}条记录")
            print(f"   列名: {list(data.columns)}")
            print(f"   前3行数据:")
            print(data.head(3))
        else:
            print("❌ 主要财务指标为空")
    except Exception as e:
        print(f"❌ 主要财务指标API失败: {e}")
    
    # 2. 测试资产负债表API
    print(f"\n2. 测试资产负债表API: stock_balance_sheet_by_report_em")
    try:
        data = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        if data is not None and not data.empty:
            print(f"✅ 成功获取资产负债表: {len(data)}条记录")
            print(f"   列名: {list(data.columns)}")
        else:
            print("❌ 资产负债表为空")
    except Exception as e:
        print(f"❌ 资产负债表API失败: {e}")
    
    # 3. 测试利润表API
    print(f"\n3. 测试利润表API: stock_profit_sheet_by_report_em")
    try:
        data = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        if data is not None and not data.empty:
            print(f"✅ 成功获取利润表: {len(data)}条记录")
            print(f"   列名: {list(data.columns)}")
        else:
            print("❌ 利润表为空")
    except Exception as e:
        print(f"❌ 利润表API失败: {e}")
    
    # 4. 测试现金流量表API
    print(f"\n4. 测试现金流量表API: stock_cash_flow_sheet_by_report_em")
    try:
        data = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        if data is not None and not data.empty:
            print(f"✅ 成功获取现金流量表: {len(data)}条记录")
            print(f"   列名: {list(data.columns)}")
        else:
            print("❌ 现金流量表为空")
    except Exception as e:
        print(f"❌ 现金流量表API失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_akshare_apis()