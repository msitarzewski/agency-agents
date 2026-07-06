"""
测试导入修复
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_fundamentals_analyst_import():
    """测试基本面分析师导入"""
    print("🧪 测试基本面分析师导入...")
    
    try:
        # 测试导入基本面分析师
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        print("  ✅ 基本面分析师导入成功")
        
        # 测试is_china_stock函数导入
        from tradingagents.utils.stock_utils import is_china_stock
        print("  ✅ is_china_stock函数导入成功")
        
        # 测试函数调用
        result = is_china_stock("000001")
        print(f"  ✅ is_china_stock('000001') = {result}")
        
        result = is_china_stock("0700.HK")
        print(f"  ✅ is_china_stock('0700.HK') = {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本面分析师导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stock_utils_functions():
    """测试股票工具函数"""
    print("\n🧪 测试股票工具函数...")
    
    try:
        from tradingagents.utils.stock_utils import (
            is_china_stock, 
            is_hk_stock, 
            is_us_stock,
            StockUtils
        )
        
        # 测试各种股票代码
        test_cases = [
            ("000001", "A股", True, False, False),
            ("600036", "A股", True, False, False),
            ("0700.HK", "港股", False, True, False),
            ("9988.HK", "港股", False, True, False),
            ("AAPL", "美股", False, False, True),
            ("TSLA", "美股", False, False, True),
        ]
        
        for ticker, market, expect_china, expect_hk, expect_us in test_cases:
            china_result = is_china_stock(ticker)
            hk_result = is_hk_stock(ticker)
            us_result = is_us_stock(ticker)
            
            print(f"  {ticker} ({market}):")
            print(f"    中国A股: {china_result} {'✅' if china_result == expect_china else '❌'}")
            print(f"    港股: {hk_result} {'✅' if hk_result == expect_hk else '❌'}")
            print(f"    美股: {us_result} {'✅' if us_result == expect_us else '❌'}")
            
            if (china_result != expect_china or 
                hk_result != expect_hk or 
                us_result != expect_us):
                print(f"❌ {ticker} 识别结果不正确")
                return False
        
        print("  ✅ 所有股票工具函数测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 股票工具函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_analysis_runner():
    """测试Web分析运行器"""
    print("\n🧪 测试Web分析运行器...")
    
    try:
        from web.utils.analysis_runner import validate_analysis_params
        
        # 测试港股验证
        is_valid, errors = validate_analysis_params(
            stock_symbol="0700.HK",
            analysis_date="2025-07-14",
            analysts=["market", "fundamentals"],
            research_depth=3,
            market_type="港股"
        )
        
        print(f"  港股验证结果: {'通过' if is_valid else '失败'}")
        if not is_valid:
            print(f"  错误信息: {errors}")
            return False
        
        print("  ✅ Web分析运行器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Web分析运行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_analysis_flow():
    """测试完整分析流程（不实际运行）"""
    print("\n🧪 测试完整分析流程导入...")
    
    try:
        # 测试所有必要的导入
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        
        print("  ✅ 交易图导入成功")
        print("  ✅ 默认配置导入成功")
        print("  ✅ 基本面分析师导入成功")
        
        # 测试配置创建
        config = DEFAULT_CONFIG.copy()
        print("  ✅ 配置创建成功")
        
        print("  ✅ 完整分析流程导入测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 完整分析流程导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有导入测试"""
    print("🔧 导入修复测试")
    print("=" * 40)
    
    tests = [
        test_fundamentals_analyst_import,
        test_stock_utils_functions,
        test_web_analysis_runner,
        test_complete_analysis_flow
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 40)
    print(f"🔧 导入修复测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有导入测试通过！")
        print("\n现在可以正常进行港股分析了")
        print("建议重新启动Web应用并测试0700.HK分析")
    else:
        print("⚠️ 部分导入测试失败，请检查失败的测试")

if __name__ == "__main__":
    main()
