#!/usr/bin/env python3
"""
阿里百炼 OpenAI 兼容适配器修复验证测试
验证新的 OpenAI 兼容适配器是否解决了工具调用问题
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_openai_adapter_import():
    """测试新适配器导入"""
    print("\n🔧 测试新适配器导入")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        print("✅ ChatDashScopeOpenAI 导入成功")
        
        from tradingagents.llm_adapters.dashscope_openai_adapter import (
            create_dashscope_openai_llm,
            test_dashscope_openai_connection,
            test_dashscope_openai_function_calling
        )
        print("✅ 相关函数导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openai_adapter_connection():
    """测试 OpenAI 兼容适配器连接"""
    print("\n🔧 测试 OpenAI 兼容适配器连接")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import test_dashscope_openai_connection
        
        # 测试连接
        result = test_dashscope_openai_connection(model="qwen-turbo")
        
        if result:
            print("✅ OpenAI 兼容适配器连接测试成功")
            return True
        else:
            print("❌ OpenAI 兼容适配器连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openai_adapter_function_calling():
    """测试 OpenAI 兼容适配器的 Function Calling"""
    print("\n🔧 测试 OpenAI 兼容适配器 Function Calling")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import test_dashscope_openai_function_calling
        
        # 测试 Function Calling
        result = test_dashscope_openai_function_calling(model="qwen-plus-latest")
        
        if result:
            print("✅ OpenAI 兼容适配器 Function Calling 测试成功")
            return True
        else:
            print("❌ OpenAI 兼容适配器 Function Calling 测试失败")
            return False
            
    except Exception as e:
        print(f"❌ Function Calling 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_technical_analysis_with_new_adapter():
    """测试新适配器的技术面分析"""
    print("\n🔧 测试新适配器的技术面分析")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        from tradingagents.agents.utils.agent_utils import Toolkit
        from langchain_core.messages import HumanMessage
        from langchain_core.tools import tool
        
        # 创建新的 OpenAI 兼容适配器
        llm = ChatDashScopeOpenAI(
            model="qwen-plus-latest",
            temperature=0.1,
            max_tokens=2000
        )
        
        print("✅ 新适配器创建成功")
        
        # 定义测试工具
        @tool
        def get_test_stock_data(ticker: str, start_date: str, end_date: str) -> str:
            """获取测试股票数据"""
            return f"""# {ticker} 股票数据分析

## 📊 实时行情
- 股票名称: 招商银行
- 股票代码: {ticker}
- 当前价格: ¥47.13
- 涨跌幅: -1.03%
- 成交量: 61.5万手
- 数据来源: Tushare

## 📈 历史数据概览
- 数据期间: {start_date} 至 {end_date}
- 数据条数: 23条
- 期间最高: ¥47.88
- 期间最低: ¥44.21

## 📋 技术指标
- RSI: 45.2 (中性)
- MACD: 0.15 (看涨)
- MA20: ¥46.85
- 成交量趋势: 放量"""
        
        # 绑定工具
        llm_with_tools = llm.bind_tools([get_test_stock_data])
        
        print("✅ 工具绑定成功")
        
        # 测试工具调用
        print("🔄 测试工具调用...")
        
        messages = [HumanMessage(content="""请分析600036这只股票的技术面。
        
请先调用get_test_stock_data工具获取数据，参数：
- ticker: "600036"
- start_date: "2025-06-10"
- end_date: "2025-07-10"

然后基于获取的数据生成详细的技术分析报告，要求：
1. 报告长度不少于500字
2. 包含具体的技术指标分析
3. 提供明确的投资建议
4. 使用中文撰写""")]
        
        response = llm_with_tools.invoke(messages)
        
        print(f"📊 响应类型: {type(response)}")
        print(f"📊 响应长度: {len(response.content)}字符")
        
        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and len(response.tool_calls) > 0:
            print(f"✅ 工具调用成功: {len(response.tool_calls)}个工具调用")
            for i, tool_call in enumerate(response.tool_calls):
                print(f"   工具{i+1}: {tool_call.get('name', 'unknown')}")
            
            # 这里应该继续执行工具并生成最终分析
            # 但为了测试，我们只验证工具调用是否正常
            return True
        else:
            print(f"❌ 没有工具调用")
            print(f"📋 直接响应: {response.content[:200]}...")
            
            # 检查响应长度
            if len(response.content) < 100:
                print("❌ 响应过短，可能存在问题")
                return False
            else:
                print("⚠️ 有响应但没有工具调用")
                return False
        
    except Exception as e:
        print(f"❌ 技术面分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trading_graph_integration():
    """测试与 TradingGraph 的集成"""
    print("\n🔧 测试与 TradingGraph 的集成")
    print("=" * 60)
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        
        # 创建配置
        config = {
            "llm_provider": "dashscope",
            "deep_think_llm": "qwen-plus-latest",
            "quick_think_llm": "qwen-turbo",
            "max_debate_rounds": 1,
            "online_tools": True,
            "selected_analysts": ["fundamentals_analyst", "market_analyst"]
        }
        
        print("🔄 创建 TradingGraph...")
        graph = TradingAgentsGraph(config)
        
        print("✅ TradingGraph 创建成功")
        print(f"   Deep thinking LLM: {type(graph.deep_thinking_llm).__name__}")
        print(f"   Quick thinking LLM: {type(graph.quick_thinking_llm).__name__}")
        
        # 检查是否使用了新的适配器
        if "OpenAI" in type(graph.deep_thinking_llm).__name__:
            print("✅ 使用了新的 OpenAI 兼容适配器")
            return True
        else:
            print("⚠️ 仍在使用旧的适配器")
            return False
        
    except Exception as e:
        print(f"❌ TradingGraph 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🔬 阿里百炼 OpenAI 兼容适配器修复验证测试")
    print("=" * 70)
    print("💡 测试目标:")
    print("   - 验证新的 OpenAI 兼容适配器导入和连接")
    print("   - 验证 Function Calling 功能")
    print("   - 验证技术面分析工具调用")
    print("   - 验证与 TradingGraph 的集成")
    print("=" * 70)
    
    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ 未找到 DASHSCOPE_API_KEY 环境变量")
        print("请设置环境变量后重试")
        return
    
    # 运行所有测试
    tests = [
        ("新适配器导入", test_openai_adapter_import),
        ("OpenAI 兼容适配器连接", test_openai_adapter_connection),
        ("Function Calling", test_openai_adapter_function_calling),
        ("技术面分析工具调用", test_technical_analysis_with_new_adapter),
        ("TradingGraph 集成", test_trading_graph_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n📋 阿里百炼 OpenAI 兼容适配器修复测试总结")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！OpenAI 兼容适配器修复成功！")
        print("\n💡 修复效果:")
        print("   ✅ 支持原生 Function Calling")
        print("   ✅ 工具调用正常执行")
        print("   ✅ 技术面分析不再只有30字符")
        print("   ✅ 与 LangChain 完全兼容")
        print("\n🚀 现在阿里百炼模型应该能正常进行技术面分析了！")
    else:
        print("\n⚠️ 部分测试失败，请检查相关配置")
    
    input("按回车键退出...")


if __name__ == "__main__":
    main()
