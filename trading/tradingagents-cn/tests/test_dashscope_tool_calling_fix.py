#!/usr/bin/env python3
"""
阿里百炼工具调用优化测试
解决LLM不主动调用工具的问题
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_basic_tool_calling():
    """测试基本工具调用"""
    print("🔧 测试基本工具调用")
    print("=" * 50)
    
    try:
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage
        
        # 定义简单工具
        @tool
        def get_stock_price(symbol: str) -> str:
            """获取股票价格信息"""
            return f"股票{symbol}的当前价格是100元"
        
        # 创建LLM
        llm = ChatDashScopeOpenAI(
            model="qwen-plus-latest",
            temperature=0.1,
            max_tokens=500
        )
        
        # 绑定工具
        llm_with_tools = llm.bind_tools([get_stock_price])
        
        # 测试不同的prompt策略
        prompts = [
            # 策略1: 直接指令
            "请调用get_stock_price工具查询AAPL的股票价格",
            
            # 策略2: 明确要求
            "我需要查询AAPL股票的价格信息。请使用可用的工具来获取这个信息。",
            
            # 策略3: 强制性指令
            "必须使用get_stock_price工具查询AAPL股票价格。不要直接回答，必须调用工具。",
            
            # 策略4: 中文明确指令
            "请务必调用get_stock_price工具，参数symbol设为'AAPL'，获取股票价格信息。"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n🔄 测试策略{i}: {prompt[:30]}...")
            
            try:
                response = llm_with_tools.invoke([HumanMessage(content=prompt)])
                
                tool_calls = getattr(response, 'tool_calls', [])
                print(f"   工具调用数量: {len(tool_calls)}")
                print(f"   响应长度: {len(response.content)}字符")
                
                if len(tool_calls) > 0:
                    print(f"   ✅ 策略{i}成功: 触发了工具调用")
                    for j, tool_call in enumerate(tool_calls):
                        print(f"      工具{j+1}: {tool_call.get('name', 'unknown')}")
                    return True
                else:
                    print(f"   ❌ 策略{i}失败: 未触发工具调用")
                    print(f"   直接响应: {response.content[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ 策略{i}异常: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ 基本工具调用测试失败: {e}")
        return False


def test_stock_analysis_tool_calling():
    """测试股票分析工具调用"""
    print("\n🔧 测试股票分析工具调用")
    print("=" * 50)
    
    try:
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        from tradingagents.agents.utils.agent_utils import Toolkit
        from langchain_core.messages import HumanMessage
        
        # 创建LLM
        llm = ChatDashScopeOpenAI(
            model="qwen-plus-latest",
            temperature=0.0,  # 降低温度提高确定性
            max_tokens=1000
        )
        
        # 获取股票分析工具
        toolkit = Toolkit()
        tools = [
            toolkit.get_china_stock_data,
            toolkit.get_china_fundamentals
        ]
        
        # 绑定工具
        llm_with_tools = llm.bind_tools(tools)
        
        # 测试专门的股票分析prompt
        stock_prompts = [
            # 策略1: 明确的工具调用指令
            """请分析股票688656。

步骤：
1. 首先调用get_china_stock_data工具获取股票数据，参数：stock_code='688656', start_date='2025-06-01', end_date='2025-07-11'
2. 然后调用get_china_fundamentals工具获取基本面数据，参数：ticker='688656', curr_date='2025-07-11'

请严格按照上述步骤执行，必须调用工具。""",

            # 策略2: 问题导向
            """我想了解688656这只股票的详细情况，包括：
- 最近的价格走势和交易数据
- 基本面分析和财务状况

请使用可用的工具来获取这些信息。""",

            # 策略3: 强制工具调用
            """分析688656股票。注意：你必须使用工具来获取数据，不能凭空回答。请调用相关工具获取股票数据和基本面信息。"""
        ]
        
        for i, prompt in enumerate(stock_prompts, 1):
            print(f"\n🔄 测试股票分析策略{i}...")
            
            try:
                response = llm_with_tools.invoke([HumanMessage(content=prompt)])
                
                tool_calls = getattr(response, 'tool_calls', [])
                print(f"   工具调用数量: {len(tool_calls)}")
                print(f"   响应长度: {len(response.content)}字符")
                
                if len(tool_calls) > 0:
                    print(f"   ✅ 股票分析策略{i}成功")
                    for j, tool_call in enumerate(tool_calls):
                        tool_name = tool_call.get('name', 'unknown')
                        tool_args = tool_call.get('args', {})
                        print(f"      工具{j+1}: {tool_name}({tool_args})")
                    return True
                else:
                    print(f"   ❌ 股票分析策略{i}失败")
                    print(f"   直接响应: {response.content[:150]}...")
                    
            except Exception as e:
                print(f"   ❌ 股票分析策略{i}异常: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ 股票分析工具调用测试失败: {e}")
        return False


def test_parameter_optimization():
    """测试参数优化"""
    print("\n🔧 测试参数优化")
    print("=" * 50)
    
    try:
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage
        
        # 定义测试工具
        @tool
        def analyze_stock(symbol: str, period: str) -> str:
            """分析股票"""
            return f"分析{symbol}股票，时间周期{period}"
        
        # 测试不同参数配置
        configs = [
            {"temperature": 0.0, "max_tokens": 500, "description": "低温度"},
            {"temperature": 0.1, "max_tokens": 500, "description": "默认温度"},
            {"temperature": 0.3, "max_tokens": 500, "description": "中等温度"},
        ]
        
        prompt = "请调用analyze_stock工具分析AAPL股票，时间周期设为'1month'"
        
        for config in configs:
            print(f"\n🔄 测试{config['description']}配置...")
            
            try:
                llm = ChatDashScopeOpenAI(
                    model="qwen-plus-latest",
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )
                
                llm_with_tools = llm.bind_tools([analyze_stock])
                response = llm_with_tools.invoke([HumanMessage(content=prompt)])
                
                tool_calls = getattr(response, 'tool_calls', [])
                print(f"   工具调用数量: {len(tool_calls)}")
                
                if len(tool_calls) > 0:
                    print(f"   ✅ {config['description']}配置成功")
                    return config
                else:
                    print(f"   ❌ {config['description']}配置失败")
                    
            except Exception as e:
                print(f"   ❌ {config['description']}配置异常: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ 参数优化测试失败: {e}")
        return None


def test_model_comparison():
    """测试不同模型的工具调用能力"""
    print("\n🔧 测试不同模型的工具调用能力")
    print("=" * 50)
    
    try:
        from tradingagents.llm_adapters import ChatDashScopeOpenAI
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage
        
        # 定义测试工具
        @tool
        def get_info(query: str) -> str:
            """获取信息"""
            return f"查询结果: {query}"
        
        # 测试不同模型
        models = [
            "qwen-turbo",
            "qwen-plus",
            "qwen-plus-latest",
            "qwen-max-latest"
        ]
        
        prompt = "请调用get_info工具查询'股票市场今日表现'"
        
        for model in models:
            print(f"\n🔄 测试模型: {model}...")
            
            try:
                llm = ChatDashScopeOpenAI(
                    model=model,
                    temperature=0.1,
                    max_tokens=300
                )
                
                llm_with_tools = llm.bind_tools([get_info])
                response = llm_with_tools.invoke([HumanMessage(content=prompt)])
                
                tool_calls = getattr(response, 'tool_calls', [])
                print(f"   工具调用数量: {len(tool_calls)}")
                
                if len(tool_calls) > 0:
                    print(f"   ✅ {model}: 支持工具调用")
                else:
                    print(f"   ❌ {model}: 不支持工具调用")
                    print(f"   响应: {response.content[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ {model}: 测试异常 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型比较测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔬 阿里百炼工具调用优化测试")
    print("=" * 70)
    print("💡 目标: 解决LLM不主动调用工具的问题")
    print("=" * 70)
    
    # 检查API密钥
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ 未找到DASHSCOPE_API_KEY环境变量")
        return
    
    # 运行测试
    tests = [
        ("基本工具调用", test_basic_tool_calling),
        ("股票分析工具调用", test_stock_analysis_tool_calling),
        ("参数优化", test_parameter_optimization),
        ("模型比较", test_model_comparison)
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
    print("\n📋 工具调用优化测试总结")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        if result:
            status = "✅ 通过"
            passed += 1
        else:
            status = "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed > 0:
        print("\n💡 建议:")
        print("   1. 使用更明确的工具调用指令")
        print("   2. 调整temperature参数")
        print("   3. 尝试不同的模型版本")
        print("   4. 考虑使用强制工具调用模式")
    else:
        print("\n⚠️ 阿里百炼可能需要特殊的工具调用处理")
        print("   建议使用手动工具调用作为备用方案")


if __name__ == "__main__":
    main()
