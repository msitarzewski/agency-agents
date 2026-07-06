"""
测试基本面分析师ReAct模式的港股修复
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_react_fundamentals_hk_config():
    """测试ReAct模式基本面分析师港股配置"""
    print("🧪 测试ReAct模式基本面分析师港股配置...")
    
    try:
        # 读取基本面分析师文件
        with open('tradingagents/agents/analysts/fundamentals_analyst.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查ReAct模式港股配置
        has_hk_react_branch = 'elif is_hk:' in content and 'ReAct Agent分析港股' in content
        has_hk_stock_data_tool = 'HKStockDataTool' in content
        has_hk_fundamentals_tool = 'HKFundamentalsTool' in content
        has_hk_unified_call = 'get_hk_stock_data_unified' in content
        has_hk_info_call = 'get_hk_stock_info_unified' in content
        
        print(f"  港股ReAct分支: {has_hk_react_branch}")
        print(f"  港股数据工具: {has_hk_stock_data_tool}")
        print(f"  港股基本面工具: {has_hk_fundamentals_tool}")
        print(f"  港股统一数据调用: {has_hk_unified_call}")
        print(f"  港股信息调用: {has_hk_info_call}")
        
        if all([has_hk_react_branch, has_hk_stock_data_tool, has_hk_fundamentals_tool, 
                has_hk_unified_call, has_hk_info_call]):
            print("  ✅ ReAct模式基本面分析师港股配置正确")
            return True
        else:
            print("  ❌ ReAct模式基本面分析师港股配置不完整")
            return False
        
    except Exception as e:
        print(f"❌ ReAct模式基本面分析师港股配置测试失败: {e}")
        return False

def test_us_stock_separation():
    """测试美股和港股的分离"""
    print("\n🧪 测试美股和港股的分离...")
    
    try:
        # 读取基本面分析师文件
        with open('tradingagents/agents/analysts/fundamentals_analyst.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查美股工具不再处理港股
        us_fundamentals_desc = 'description: str = f"获取美股{ticker}的基本面数据'
        no_hk_in_us_desc = '美股/港股' not in content.split('USFundamentalsTool')[1].split('def _run')[0]
        
        print(f"  美股工具描述正确: {us_fundamentals_desc in content}")
        print(f"  美股工具不包含港股: {no_hk_in_us_desc}")
        
        if us_fundamentals_desc in content and no_hk_in_us_desc:
            print("  ✅ 美股和港股分离正确")
            return True
        else:
            print("  ❌ 美股和港股分离不完整")
            return False
        
    except Exception as e:
        print(f"❌ 美股和港股分离测试失败: {e}")
        return False

def test_hk_query_format():
    """测试港股查询格式"""
    print("\n🧪 测试港股查询格式...")
    
    try:
        # 读取基本面分析师文件
        with open('tradingagents/agents/analysts/fundamentals_analyst.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查港股查询格式
        has_hk_query = '请对港股{ticker}进行详细的基本面分析' in content
        has_hk_currency = '价格以港币(HK$)计价' in content
        has_hk_features = 'T+0交易、港币汇率' in content
        has_hk_format = '🇭🇰 港股基本信息' in content
        
        print(f"  港股查询格式: {has_hk_query}")
        print(f"  港币计价说明: {has_hk_currency}")
        print(f"  港股特点说明: {has_hk_features}")
        print(f"  港股报告格式: {has_hk_format}")
        
        if all([has_hk_query, has_hk_currency, has_hk_features, has_hk_format]):
            print("  ✅ 港股查询格式正确")
            return True
        else:
            print("  ❌ 港股查询格式不完整")
            return False
        
    except Exception as e:
        print(f"❌ 港股查询格式测试失败: {e}")
        return False

def test_toolkit_method_usage():
    """测试工具包方法使用"""
    print("\n🧪 测试工具包方法使用...")
    
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
            # 检查方法是否可调用
            method = getattr(toolkit, 'get_hk_stock_data_unified')
            is_callable = callable(method)
            print(f"  方法可调用: {is_callable}")
            
            if is_callable:
                print("  ✅ 工具包方法使用正确")
                return True
            else:
                print("  ❌ 工具包方法不可调用")
                return False
        else:
            print("  ❌ 工具包港股方法不存在")
            return False
        
    except Exception as e:
        print(f"❌ 工具包方法使用测试失败: {e}")
        return False

def test_stock_type_detection():
    """测试股票类型检测"""
    print("\n🧪 测试股票类型检测...")
    
    try:
        from tradingagents.utils.stock_utils import StockUtils
        
        # 测试港股检测
        hk_stocks = ["0700.HK", "9988.HK", "3690.HK"]
        us_stocks = ["AAPL", "TSLA", "MSFT"]
        china_stocks = ["000001", "600036", "300001"]
        
        print("  港股检测:")
        for stock in hk_stocks:
            market_info = StockUtils.get_market_info(stock)
            is_hk = market_info['is_hk']
            print(f"    {stock}: {is_hk} ({'✅' if is_hk else '❌'})")
            if not is_hk:
                return False
        
        print("  美股检测:")
        for stock in us_stocks:
            market_info = StockUtils.get_market_info(stock)
            is_us = market_info['is_us']
            print(f"    {stock}: {is_us} ({'✅' if is_us else '❌'})")
            if not is_us:
                return False
        
        print("  A股检测:")
        for stock in china_stocks:
            market_info = StockUtils.get_market_info(stock)
            is_china = market_info['is_china']
            print(f"    {stock}: {is_china} ({'✅' if is_china else '❌'})")
            if not is_china:
                return False
        
        print("  ✅ 股票类型检测正确")
        return True
        
    except Exception as e:
        print(f"❌ 股票类型检测测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🔧 基本面分析师ReAct模式港股修复测试")
    print("=" * 60)
    
    tests = [
        test_react_fundamentals_hk_config,
        test_us_stock_separation,
        test_hk_query_format,
        test_toolkit_method_usage,
        test_stock_type_detection
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
    print(f"🔧 基本面分析师ReAct模式港股修复测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 基本面分析师ReAct模式港股修复成功！")
        print("\n✅ 修复总结:")
        print("  - ReAct模式添加了港股专用分支")
        print("  - 港股使用HKStockDataTool和HKFundamentalsTool")
        print("  - 港股优先使用AKShare数据源")
        print("  - 美股和港股处理完全分离")
        print("  - 港股查询格式包含港币计价和市场特点")
        print("\n🚀 现在港股基本面分析会使用正确的数据源！")
    else:
        print("⚠️ 部分测试失败，请检查失败的测试")

if __name__ == "__main__":
    main()
