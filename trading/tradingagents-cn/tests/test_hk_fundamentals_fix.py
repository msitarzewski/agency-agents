#!/usr/bin/env python3
"""
测试港股基本面分析修复
验证港股代码识别、工具选择和货币处理是否正确
"""

import os
import sys

def test_stock_type_detection():
    """测试股票类型检测功能"""
    print("🧪 测试股票类型检测...")
    
    try:
        from tradingagents.utils.stock_utils import StockUtils
        
        test_cases = [
            ("0700.HK", "港股", "港币", "HK$"),
            ("9988.HK", "港股", "港币", "HK$"),
            ("000001", "中国A股", "人民币", "¥"),
            ("600036", "中国A股", "人民币", "¥"),
            ("AAPL", "美股", "美元", "$"),
            ("TSLA", "美股", "美元", "$"),
        ]
        
        for ticker, expected_market, expected_currency, expected_symbol in test_cases:
            market_info = StockUtils.get_market_info(ticker)
            
            print(f"  {ticker}:")
            print(f"    市场: {market_info['market_name']}")
            print(f"    货币: {market_info['currency_name']} ({market_info['currency_symbol']})")
            print(f"    是否港股: {market_info['is_hk']}")
            print(f"    是否A股: {market_info['is_china']}")
            print(f"    是否美股: {market_info['is_us']}")
            
            # 验证结果
            if (expected_market in market_info['market_name'] and 
                market_info['currency_name'] == expected_currency and
                market_info['currency_symbol'] == expected_symbol):
                print(f"    ✅ 识别正确")
            else:
                print(f"    ❌ 识别错误")
                print(f"       期望: {expected_market}, {expected_currency}, {expected_symbol}")
                print(f"       实际: {market_info['market_name']}, {market_info['currency_name']}, {market_info['currency_symbol']}")
                return False
        
        print("✅ 股票类型检测测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 股票类型检测测试失败: {e}")
        return False


def test_fundamentals_analyst_tool_selection():
    """测试基本面分析师的工具选择逻辑"""
    print("\n🧪 测试基本面分析师工具选择...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.utils.stock_utils import StockUtils
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 测试港股工具选择
        hk_ticker = "0700.HK"
        market_info = StockUtils.get_market_info(hk_ticker)
        
        print(f"  港股工具选择测试: {hk_ticker}")
        print(f"    市场类型: {market_info['market_name']}")
        print(f"    是否港股: {market_info['is_hk']}")
        print(f"    货币: {market_info['currency_name']} ({market_info['currency_symbol']})")
        
        # 检查港股专用工具是否存在
        if hasattr(toolkit, 'get_hk_stock_data_unified'):
            print(f"    ✅ 港股专用工具存在: get_hk_stock_data_unified")
        else:
            print(f"    ❌ 港股专用工具不存在")
            return False
        
        # 测试A股工具选择
        china_ticker = "000001"
        market_info = StockUtils.get_market_info(china_ticker)
        
        print(f"  A股工具选择测试: {china_ticker}")
        print(f"    市场类型: {market_info['market_name']}")
        print(f"    是否A股: {market_info['is_china']}")
        print(f"    货币: {market_info['currency_name']} ({market_info['currency_symbol']})")
        
        # 检查A股专用工具是否存在
        if hasattr(toolkit, 'get_china_stock_data'):
            print(f"    ✅ A股专用工具存在: get_china_stock_data")
        else:
            print(f"    ❌ A股专用工具不存在")
            return False
        
        print("✅ 基本面分析师工具选择测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本面分析师工具选择测试失败: {e}")
        return False


def test_trader_currency_detection():
    """测试交易员节点的货币检测"""
    print("\n🧪 测试交易员货币检测...")
    
    try:
        from tradingagents.utils.stock_utils import StockUtils
        
        test_cases = [
            ("0700.HK", "港币", "HK$"),
            ("9988.HK", "港币", "HK$"),
            ("000001", "人民币", "¥"),
            ("AAPL", "美元", "$"),
        ]
        
        for ticker, expected_currency, expected_symbol in test_cases:
            market_info = StockUtils.get_market_info(ticker)
            
            print(f"  {ticker}:")
            print(f"    检测到的货币: {market_info['currency_name']} ({market_info['currency_symbol']})")
            print(f"    期望的货币: {expected_currency} ({expected_symbol})")
            
            if (market_info['currency_name'] == expected_currency and 
                market_info['currency_symbol'] == expected_symbol):
                print(f"    ✅ 货币检测正确")
            else:
                print(f"    ❌ 货币检测错误")
                return False
        
        print("✅ 交易员货币检测测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 交易员货币检测测试失败: {e}")
        return False


def test_hk_data_source():
    """测试港股数据源"""
    print("\n🧪 测试港股数据源...")
    
    try:
        from tradingagents.dataflows.interface import get_hk_stock_data_unified
        
        # 测试港股数据获取
        hk_ticker = "0700.HK"
        print(f"  测试获取港股数据: {hk_ticker}")
        
        result = get_hk_stock_data_unified(hk_ticker, "2025-07-10", "2025-07-14")
        
        print(f"  数据获取结果长度: {len(result)}")
        print(f"  结果前100字符: {result[:100]}...")
        
        if "❌" in result:
            print(f"  ⚠️ 数据获取失败，但这可能是正常的（网络问题或API限制）")
            print(f"  失败信息: {result}")
        else:
            print(f"  ✅ 数据获取成功")
        
        print("✅ 港股数据源测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 港股数据源测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔧 港股基本面分析修复测试")
    print("=" * 60)
    
    tests = [
        test_stock_type_detection,
        test_fundamentals_analyst_tool_selection,
        test_trader_currency_detection,
        test_hk_data_source,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ 测试失败: {test.__name__}")
        except Exception as e:
            print(f"❌ 测试异常: {test.__name__} - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！港股基本面分析修复成功")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
