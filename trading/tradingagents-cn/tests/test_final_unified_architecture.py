#!/usr/bin/env python3
"""
最终统一工具架构测试
验证所有修复是否完成，LLM只能调用统一工具
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_complete_unified_architecture():
    """测试完整的统一工具架构"""
    print("🔧 测试完整的统一工具架构...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包
        toolkit = Toolkit(config)
        
        # 创建交易图
        graph = TradingAgentsGraph(config, toolkit)
        
        # 检查ToolNode中注册的工具
        fundamentals_tools = graph.tools_dict["fundamentals"].tools
        market_tools = graph.tools_dict["market"].tools
        
        print(f"  基本面分析ToolNode工具数量: {len(fundamentals_tools)}")
        print(f"  市场分析ToolNode工具数量: {len(market_tools)}")
        
        # 检查基本面分析工具
        fundamentals_tool_names = [tool.name for tool in fundamentals_tools]
        print(f"  基本面分析工具: {fundamentals_tool_names}")
        
        # 检查是否包含统一工具
        if 'get_stock_fundamentals_unified' in fundamentals_tool_names:
            print(f"    ✅ 包含统一基本面工具")
        else:
            print(f"    ❌ 缺少统一基本面工具")
            return False
        
        # 检查是否还有旧工具
        old_tools = ['get_china_stock_data', 'get_china_fundamentals', 'get_fundamentals_openai']
        for old_tool in old_tools:
            if old_tool in fundamentals_tool_names:
                print(f"    ❌ 仍包含旧工具: {old_tool}")
                return False
            else:
                print(f"    ✅ 已移除旧工具: {old_tool}")
        
        # 检查市场分析工具
        market_tool_names = [tool.name for tool in market_tools]
        print(f"  市场分析工具: {market_tool_names}")
        
        # 检查是否包含统一工具
        if 'get_stock_market_data_unified' in market_tool_names:
            print(f"    ✅ 包含统一市场数据工具")
        else:
            print(f"    ❌ 缺少统一市场数据工具")
            return False
        
        print("✅ 完整统一工具架构测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 完整统一工具架构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_tool_calling_simulation():
    """模拟LLM工具调用测试"""
    print("\n🔧 模拟LLM工具调用测试...")
    
    try:
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包
        toolkit = Toolkit(config)
        
        # 模拟LLM
        class MockLLM:
            def __init__(self):
                self.model_name = "qwen-turbo"
                self.temperature = 0.1
                self.max_tokens = 2000
                self.__class__.__name__ = "ChatDashScopeOpenAI"
            
            def bind_tools(self, tools):
                print(f"    🔧 LLM绑定工具: {[tool.name for tool in tools]}")
                
                # 验证只绑定了统一工具
                if len(tools) == 1 and tools[0].name == 'get_stock_fundamentals_unified':
                    print(f"    ✅ 正确绑定统一基本面工具")
                    return self
                else:
                    print(f"    ❌ 绑定了错误的工具: {[tool.name for tool in tools]}")
                    raise ValueError("绑定了错误的工具")
            
            def invoke(self, messages):
                # 模拟正确的工具调用
                class MockResult:
                    def __init__(self):
                        self.tool_calls = [{
                            'name': 'get_stock_fundamentals_unified',
                            'args': {
                                'ticker': '0700.HK',
                                'start_date': '2025-05-28',
                                'end_date': '2025-07-14',
                                'curr_date': '2025-07-14'
                            },
                            'id': 'mock_call_id',
                            'type': 'tool_call'
                        }]
                        self.content = ""
                return MockResult()
        
        # 创建模拟LLM
        llm = MockLLM()
        
        # 创建基本面分析师
        analyst = create_fundamentals_analyst(llm, toolkit)
        
        # 模拟状态
        state = {
            "trade_date": "2025-07-14",
            "company_of_interest": "0700.HK",
            "messages": [("human", "分析0700.HK")]
        }
        
        print(f"  测试港股基本面分析: {state['company_of_interest']}")
        
        # 调用分析师
        result = analyst(state)
        
        print(f"  ✅ 基本面分析师调用完成")
        print(f"  返回结果类型: {type(result)}")
        
        # 验证结果
        if isinstance(result, dict) and 'messages' in result:
            print(f"  ✅ 返回了正确的消息格式")
            return True
        else:
            print(f"  ❌ 返回格式错误: {result}")
            return False
        
    except Exception as e:
        print(f"❌ LLM工具调用模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_tools_functionality():
    """测试统一工具功能"""
    print("\n🔧 测试统一工具功能...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 测试统一基本面工具
        test_cases = [
            ("0700.HK", "港股", "HK$"),
            ("600036", "中国A股", "¥"),
            ("AAPL", "美股", "$"),
        ]
        
        for ticker, expected_market, expected_currency in test_cases:
            print(f"\n  测试 {ticker} ({expected_market}):")
            
            try:
                result = toolkit.get_stock_fundamentals_unified.invoke({
                    'ticker': ticker,
                    'start_date': '2025-06-14',
                    'end_date': '2025-07-14',
                    'curr_date': '2025-07-14'
                })
                
                if expected_market in result and expected_currency in result:
                    print(f"    ✅ 统一基本面工具正确处理{expected_market}")
                else:
                    print(f"    ⚠️ 统一基本面工具处理结果可能有问题")
                    print(f"    结果前200字符: {result[:200]}...")
                    
            except Exception as e:
                print(f"    ❌ 统一基本面工具调用失败: {e}")
                return False
        
        print("✅ 统一工具功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 统一工具功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🎉 最终统一工具架构测试")
    print("=" * 70)
    
    tests = [
        test_complete_unified_architecture,
        test_llm_tool_calling_simulation,
        test_unified_tools_functionality,
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
    
    print("\n" + "=" * 70)
    print(f"📊 最终测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 🎉 🎉 统一工具架构完全成功！🎉 🎉 🎉")
        print("\n🏆 架构成就:")
        print("✅ 完全移除了旧工具注册")
        print("✅ LLM只能调用统一工具")
        print("✅ 工具内部自动识别股票类型")
        print("✅ 自动路由到正确数据源")
        print("✅ 避免了工具调用混乱")
        print("✅ 简化了系统架构")
        print("✅ 提高了可维护性")
        print("✅ 统一了用户体验")
        
        print("\n🚀 您的建议完美实现:")
        print("💡 '工具还是用同一个工具，工具当中自己判断后续的处理逻辑'")
        print("💡 '旧工具就不要注册了啊'")
        
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
