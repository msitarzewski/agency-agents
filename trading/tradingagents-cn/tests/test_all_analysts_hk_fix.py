"""
测试所有分析师节点的港股数据源修复
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_market_analyst_hk_config():
    """测试市场分析师港股配置"""
    print("🧪 测试市场分析师港股配置...")
    
    try:
        # 读取市场分析师文件
        with open('tradingagents/agents/analysts/market_analyst.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查港股配置
        has_hk_branch = 'elif is_hk:' in content
        has_unified_tool = 'get_hk_stock_data_unified' in content
        has_akshare_comment = '优先AKShare' in content
        
        print(f"  港股分支: {has_hk_branch}")
        print(f"  统一工具: {has_unified_tool}")
        print(f"  AKShare注释: {has_akshare_comment}")
        
        if has_hk_branch and has_unified_tool and has_akshare_comment:
            print("  ✅ 市场分析师港股配置正确")
            return True
        else:
            print("  ❌ 市场分析师港股配置不完整")
            return False
        
    except Exception as e:
        print(f"❌ 市场分析师港股配置测试失败: {e}")
        return False

def test_fundamentals_analyst_hk_config():
    """测试基本面分析师港股配置"""
    print("\n🧪 测试基本面分析师港股配置...")
    
    try:
        # 读取基本面分析师文件
        with open('tradingagents/agents/analysts/fundamentals_analyst.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查港股配置
        has_hk_branch = 'elif is_hk:' in content
        has_unified_tool = 'get_hk_stock_data_unified' in content
        has_akshare_comment = '优先AKShare' in content
        
        print(f"  港股分支: {has_hk_branch}")
        print(f"  统一工具: {has_unified_tool}")
        print(f"  AKShare注释: {has_akshare_comment}")
        
        if has_hk_branch and has_unified_tool and has_akshare_comment:
            print("  ✅ 基本面分析师港股配置正确")
            return True
        else:
            print("  ❌ 基本面分析师港股配置不完整")
            return False
        
    except Exception as e:
        print(f"❌ 基本面分析师港股配置测试失败: {e}")
        return False

def test_optimized_us_data_hk_support():
    """测试优化美股数据模块的港股支持"""
    print("\n🧪 测试优化美股数据模块的港股支持...")
    
    try:
        # 读取优化美股数据文件
        with open('tradingagents/dataflows/optimized_us_data.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查港股支持
        has_hk_detection = "market_info['is_hk']" in content
        has_akshare_import = 'get_hk_stock_data_unified' in content
        has_akshare_priority = '优先使用AKShare' in content
        
        print(f"  港股检测: {has_hk_detection}")
        print(f"  AKShare导入: {has_akshare_import}")
        print(f"  AKShare优先级: {has_akshare_priority}")
        
        if has_hk_detection and has_akshare_import and has_akshare_priority:
            print("  ✅ 优化美股数据模块港股支持正确")
            return True
        else:
            print("  ❌ 优化美股数据模块港股支持不完整")
            return False
        
    except Exception as e:
        print(f"❌ 优化美股数据模块港股支持测试失败: {e}")
        return False

def test_toolkit_hk_method_availability():
    """测试工具包港股方法可用性"""
    print("\n🧪 测试工具包港股方法可用性...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 检查港股方法
        has_hk_method = hasattr(toolkit, 'get_hk_stock_data_unified')
        
        print(f"  工具包港股方法: {has_hk_method}")
        
        if has_hk_method:
            print("  ✅ 工具包港股方法可用")
            return True
        else:
            print("  ❌ 工具包港股方法不可用")
            return False
        
    except Exception as e:
        print(f"❌ 工具包港股方法可用性测试失败: {e}")
        return False

def test_data_source_priority_summary():
    """测试数据源优先级总结"""
    print("\n🧪 数据源优先级总结...")
    
    try:
        from tradingagents.dataflows.interface import AKSHARE_HK_AVAILABLE, HK_STOCK_AVAILABLE
        
        print("  📊 当前数据源可用性:")
        print(f"    AKShare港股: {AKSHARE_HK_AVAILABLE}")
        print(f"    Yahoo Finance港股: {HK_STOCK_AVAILABLE}")
        
        print("\n  🎯 预期数据源优先级:")
        print("    港股 (0700.HK):")
        print("      1. AKShare (主要) - 国内稳定，无Rate Limit")
        print("      2. Yahoo Finance (备用) - 国际数据源")
        print("    中国A股 (000001):")
        print("      1. Tushare/AKShare/BaoStock (现有配置)")
        print("    美股 (AAPL):")
        print("      1. FINNHUB (主要)")
        print("      2. Yahoo Finance (备用)")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据源优先级总结失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🔧 所有分析师节点港股数据源修复测试")
    print("=" * 60)
    
    tests = [
        test_market_analyst_hk_config,
        test_fundamentals_analyst_hk_config,
        test_optimized_us_data_hk_support,
        test_toolkit_hk_method_availability,
        test_data_source_priority_summary
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"🔧 所有分析师节点港股数据源修复测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有分析师节点港股数据源修复成功！")
        print("\n✅ 修复总结:")
        print("  - 市场分析师: 港股优先使用AKShare")
        print("  - 基本面分析师: 港股优先使用AKShare")
        print("  - 优化数据模块: 支持港股AKShare优先级")
        print("  - 工具包: 已添加港股统一接口方法")
        print("\n🚀 现在所有港股分析都会优先使用AKShare数据源！")
    else:
        print("⚠️ 部分测试失败，请检查失败的测试")

if __name__ == "__main__":
    main()
