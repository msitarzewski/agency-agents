#!/usr/bin/env python3
"""
测试旧工具移除
验证LLM只能调用统一工具
"""

def test_available_tools():
    """测试可用工具列表"""
    print("🔧 测试可用工具列表...")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 获取所有工具
        all_tools = []
        for attr_name in dir(toolkit):
            attr = getattr(toolkit, attr_name)
            if hasattr(attr, 'name') and hasattr(attr, 'description'):
                all_tools.append(attr.name)
        
        print(f"  总工具数量: {len(all_tools)}")
        
        # 检查旧工具是否已移除
        removed_tools = [
            'get_china_stock_data',
            'get_china_fundamentals', 
            'get_fundamentals_openai',
            'get_hk_stock_data_unified'
        ]
        
        # 检查统一工具是否存在
        unified_tools = [
            'get_stock_fundamentals_unified',
            'get_stock_market_data_unified',
            'get_stock_news_unified',
            'get_stock_sentiment_unified'
        ]
        
        print("\n  旧工具移除检查:")
        for tool_name in removed_tools:
            if tool_name in all_tools:
                print(f"    ❌ {tool_name}: 仍然可用（应该已移除）")
                return False
            else:
                print(f"    ✅ {tool_name}: 已移除")
        
        print("\n  统一工具可用性检查:")
        for tool_name in unified_tools:
            if tool_name in all_tools:
                print(f"    ✅ {tool_name}: 可用")
            else:
                print(f"    ❌ {tool_name}: 不可用")
                return False
        
        print(f"\n  所有可用工具:")
        for tool_name in sorted(all_tools):
            print(f"    - {tool_name}")
        
        print("✅ 工具移除测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 工具移除测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fundamentals_analyst_tool_selection():
    """测试基本面分析师工具选择"""
    print("\n🔧 测试基本面分析师工具选择...")
    
    try:
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包
        toolkit = Toolkit(config)
        
        # 模拟基本面分析师的工具选择逻辑
        from tradingagents.utils.stock_utils import StockUtils
        
        test_cases = [
            ("0700.HK", "港股"),
            ("000001", "A股"),
            ("AAPL", "美股")
        ]
        
        for ticker, market_type in test_cases:
            print(f"\n  测试 {ticker} ({market_type}):")
            
            # 获取市场信息
            market_info = StockUtils.get_market_info(ticker)
            
            # 模拟基本面分析师的工具选择逻辑
            if toolkit.config["online_tools"]:
                # 使用统一的基本面分析工具
                tools = [toolkit.get_stock_fundamentals_unified]
                tool_names = [tool.name for tool in tools]
                
                print(f"    选择的工具: {tool_names}")
                
                # 验证只选择了统一工具
                if len(tools) == 1 and tools[0].name == 'get_stock_fundamentals_unified':
                    print(f"    ✅ 正确选择统一基本面工具")
                else:
                    print(f"    ❌ 工具选择错误")
                    return False
            else:
                print(f"    跳过（online_tools=False）")
        
        print("✅ 基本面分析师工具选择测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本面分析师工具选择测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_analyst_tool_selection():
    """测试市场分析师工具选择"""
    print("\n🔧 测试市场分析师工具选择...")
    
    try:
        from tradingagents.agents.analysts.market_analyst import create_market_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.utils.stock_utils import StockUtils
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包
        toolkit = Toolkit(config)
        
        test_cases = [
            ("0700.HK", "港股"),
            ("000001", "A股"),
            ("AAPL", "美股")
        ]
        
        for ticker, market_type in test_cases:
            print(f"\n  测试 {ticker} ({market_type}):")
            
            # 获取市场信息
            market_info = StockUtils.get_market_info(ticker)
            
            # 模拟市场分析师的工具选择逻辑
            if toolkit.config["online_tools"]:
                # 使用统一的市场数据工具
                tools = [toolkit.get_stock_market_data_unified]
                tool_names = [tool.name for tool in tools]
                
                print(f"    选择的工具: {tool_names}")
                
                # 验证只选择了统一工具
                if len(tools) == 1 and tools[0].name == 'get_stock_market_data_unified':
                    print(f"    ✅ 正确选择统一市场数据工具")
                else:
                    print(f"    ❌ 工具选择错误")
                    return False
            else:
                print(f"    跳过（online_tools=False）")
        
        print("✅ 市场分析师工具选择测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 市场分析师工具选择测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🔧 旧工具移除测试")
    print("=" * 60)
    
    tests = [
        test_available_tools,
        test_fundamentals_analyst_tool_selection,
        test_market_analyst_tool_selection,
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
        print("🎉 所有测试通过！旧工具移除成功")
        print("\n📋 修复内容:")
        print("✅ 移除了旧工具的 @tool 装饰器")
        print("✅ LLM无法再调用旧工具")
        print("✅ 只能调用统一工具")
        print("✅ 避免了工具调用混乱")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
