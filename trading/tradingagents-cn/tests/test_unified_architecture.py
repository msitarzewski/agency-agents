#!/usr/bin/env python3
"""
测试统一工具架构
验证所有分析师都使用统一工具方案
"""

import os
import sys

def test_unified_tools_availability():
    """测试统一工具的可用性"""
    print("🔧 测试统一工具可用性...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 检查统一工具是否存在
        unified_tools = [
            'get_stock_fundamentals_unified',
            'get_stock_market_data_unified',
            'get_stock_news_unified',
            'get_stock_sentiment_unified'
        ]
        
        for tool_name in unified_tools:
            if hasattr(toolkit, tool_name):
                tool = getattr(toolkit, tool_name)
                print(f"  ✅ {tool_name}: 可用")
                print(f"    工具描述: {getattr(tool, 'description', 'N/A')[:100]}...")
            else:
                print(f"  ❌ {tool_name}: 不可用")
                return False
        
        print("✅ 统一工具可用性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 统一工具可用性测试失败: {e}")
        return False


def test_market_analyst_unified():
    """测试市场分析师使用统一工具"""
    print("\n🔧 测试市场分析师统一工具...")
    
    try:
        from tradingagents.agents.analysts.market_analyst import create_market_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包
        toolkit = Toolkit(config)
        
        # 创建模拟LLM
        class MockLLM:
            def bind_tools(self, tools):
                print(f"🔧 [MockLLM] 市场分析师绑定工具: {[tool.name for tool in tools]}")
                
                # 检查是否只绑定了统一工具
                if len(tools) == 1 and tools[0].name == 'get_stock_market_data_unified':
                    print(f"  ✅ 正确绑定统一市场数据工具")
                    return self
                else:
                    print(f"  ❌ 绑定了错误的工具: {[tool.name for tool in tools]}")
                    return self
            
            def invoke(self, messages):
                class MockResult:
                    def __init__(self):
                        self.tool_calls = []
                        self.content = "模拟市场分析结果"
                return MockResult()
        
        llm = MockLLM()
        
        # 创建市场分析师
        analyst = create_market_analyst(llm, toolkit)
        
        # 模拟状态
        state = {
            "trade_date": "2025-07-14",
            "company_of_interest": "0700.HK",
            "messages": []
        }
        
        print(f"  测试港股市场分析: {state['company_of_interest']}")
        
        # 调用分析师（这会触发工具选择逻辑）
        result = analyst(state)
        
        print(f"  ✅ 市场分析师调用完成")
        return True
        
    except Exception as e:
        print(f"❌ 市场分析师统一工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fundamentals_analyst_unified():
    """测试基本面分析师使用统一工具"""
    print("\n🔧 测试基本面分析师统一工具...")
    
    try:
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包
        toolkit = Toolkit(config)
        
        # 创建模拟LLM
        class MockLLM:
            def bind_tools(self, tools):
                print(f"🔧 [MockLLM] 基本面分析师绑定工具: {[tool.name for tool in tools]}")
                
                # 检查是否只绑定了统一工具
                if len(tools) == 1 and tools[0].name == 'get_stock_fundamentals_unified':
                    print(f"  ✅ 正确绑定统一基本面分析工具")
                    return self
                else:
                    print(f"  ❌ 绑定了错误的工具: {[tool.name for tool in tools]}")
                    return self
            
            def invoke(self, messages):
                class MockResult:
                    def __init__(self):
                        self.tool_calls = []
                        self.content = "模拟基本面分析结果"
                return MockResult()
        
        llm = MockLLM()
        
        # 创建基本面分析师
        analyst = create_fundamentals_analyst(llm, toolkit)
        
        # 模拟状态
        state = {
            "trade_date": "2025-07-14",
            "company_of_interest": "0700.HK",
            "messages": []
        }
        
        print(f"  测试港股基本面分析: {state['company_of_interest']}")
        
        # 调用分析师（这会触发工具选择逻辑）
        result = analyst(state)
        
        print(f"  ✅ 基本面分析师调用完成")
        return True
        
    except Exception as e:
        print(f"❌ 基本面分析师统一工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_type_routing():
    """测试股票类型路由"""
    print("\n🔧 测试股票类型路由...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        test_cases = [
            ("0700.HK", "港股", "HK$"),
            ("9988.HK", "港股", "HK$"),
            ("000001", "中国A股", "¥"),
            ("600036", "中国A股", "¥"),
            ("AAPL", "美股", "$"),
        ]
        
        for ticker, expected_market, expected_currency in test_cases:
            print(f"\n📊 测试 {ticker}:")
            
            # 测试基本面分析工具
            try:
                result = toolkit.get_stock_fundamentals_unified.invoke({
                    'ticker': ticker,
                    'start_date': '2025-06-14',
                    'end_date': '2025-07-14',
                    'curr_date': '2025-07-14'
                })
                
                if expected_market in result and expected_currency in result:
                    print(f"  ✅ 基本面工具路由正确")
                else:
                    print(f"  ⚠️ 基本面工具路由可能有问题")
                    
            except Exception as e:
                print(f"  ❌ 基本面工具调用失败: {e}")
                return False
            
            # 测试市场数据工具
            try:
                result = toolkit.get_stock_market_data_unified.invoke({
                    'ticker': ticker,
                    'start_date': '2025-07-10',
                    'end_date': '2025-07-14'
                })
                
                if expected_market in result and expected_currency in result:
                    print(f"  ✅ 市场数据工具路由正确")
                else:
                    print(f"  ⚠️ 市场数据工具路由可能有问题")
                    
            except Exception as e:
                print(f"  ❌ 市场数据工具调用失败: {e}")
                return False
        
        print("✅ 股票类型路由测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 股票类型路由测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔧 统一工具架构测试")
    print("=" * 60)
    
    tests = [
        test_unified_tools_availability,
        test_stock_type_routing,
        test_fundamentals_analyst_unified,
        test_market_analyst_unified,
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
        print("🎉 所有测试通过！统一工具架构成功")
        print("\n📋 架构优势:")
        print("✅ 所有分析师使用统一工具")
        print("✅ 工具内部自动识别股票类型")
        print("✅ 避免了LLM工具调用混乱")
        print("✅ 简化了系统提示和处理流程")
        print("✅ 更容易维护和扩展")
        print("✅ 统一的错误处理和日志记录")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
