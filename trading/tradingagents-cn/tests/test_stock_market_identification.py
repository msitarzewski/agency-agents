#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试股票市场识别逻辑
验证300750和300750.SZ的识别结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.utils.stock_utils import StockUtils

def test_stock_identification():
    """测试股票代码识别"""
    test_cases = [
        "300750",      # 纯A股代码
        "300750.SZ",   # 带后缀的A股代码
        "000001",      # 另一个A股代码
        "000001.SZ",   # 带后缀的A股代码
        "600000",      # 上海A股代码
        "600000.SH",   # 带后缀的上海A股代码
        "0700.HK",     # 港股代码
        "AAPL",        # 美股代码
    ]
    
    print("🔍 股票市场识别测试")
    print("=" * 50)
    
    for ticker in test_cases:
        market_info = StockUtils.get_market_info(ticker)
        print(f"股票代码: {ticker:12} | 市场: {market_info['market_name']:8} | 是否A股: {market_info['is_china']}")
    
    print("\n" + "=" * 50)
    print("🎯 重点测试300750相关代码:")
    
    # 重点测试300750
    for ticker in ["300750", "300750.SZ"]:
        market_info = StockUtils.get_market_info(ticker)
        print(f"\n📊 股票代码: {ticker}")
        print(f"   市场类型: {market_info['market']}")
        print(f"   市场名称: {market_info['market_name']}")
        print(f"   是否A股: {market_info['is_china']}")
        print(f"   数据源: {market_info['data_source']}")
        print(f"   货币: {market_info['currency_name']} ({market_info['currency_symbol']})")

if __name__ == "__main__":
    test_stock_identification()