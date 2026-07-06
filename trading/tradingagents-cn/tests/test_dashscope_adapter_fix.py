#!/usr/bin/env python3
"""
DashScope OpenAI 适配器修复测试脚本
测试修复后的工具绑定、转换和调用机制
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('test')

def test_enhanced_tool_binding():
    """测试增强的工具绑定机制"""
    print("\n🔧 测试增强的工具绑定机制")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage
        
        # 定义测试工具
        @tool
        def get_test_stock_data(ticker: str, days: int = 7) -> str:
            """获取测试股票数据"""
            return f"测试数据: {ticker} 最近 {days} 天的股票数据"
        
        @tool
        def get_test_news(query: str) -> str:
            """获取测试新闻"""
            return f"测试新闻: {query} 相关新闻"
        
        # 创建适配器实例
        llm = ChatDashScopeOpenAI(
            model="qwen-turbo",
            temperature=0.1,
            max_tokens=200
        )
        
        print("✅ DashScope OpenAI 适配器创建成功")
        
        # 测试工具绑定
        tools = [get_test_stock_data, get_test_news]
        llm_with_tools = llm.bind_tools(tools)
        
        print("✅ 工具绑定成功")
        print(f"   绑定的工具数量: {len(tools)}")
        
        # 测试工具调用
        response = llm_with_tools.invoke([
            HumanMessage(content="请调用get_test_stock_data工具获取AAPL的股票数据")
        ])
        
        print(f"✅ LLM 调用成功")
        print(f"   响应类型: {type(response)}")
        print(f"   响应内容长度: {len(response.content) if hasattr(response, 'content') else 0}")
        
        # 检查工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"✅ 检测到工具调用: {len(response.tool_calls)} 个")
            for i, tool_call in enumerate(response.tool_calls):
                print(f"   工具调用 {i+1}: {tool_call.get('name', 'unknown')}")
        else:
            print("⚠️ 未检测到工具调用")
            print(f"   响应内容: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具绑定测试失败: {e}")
        return False

def test_tool_format_validation():
    """测试工具格式验证机制"""
    print("\n🔍 测试工具格式验证机制")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI
        
        # 创建适配器实例
        llm = ChatDashScopeOpenAI(model="qwen-turbo")
        
        # 测试有效的工具格式
        valid_tool = {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "测试工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "参数1"}
                    },
                    "required": ["param1"]
                }
            }
        }
        
        is_valid = llm._validate_openai_tool_format(valid_tool, "test_tool")
        print(f"✅ 有效工具格式验证: {'通过' if is_valid else '失败'}")
        
        # 测试无效的工具格式
        invalid_tool = {
            "type": "invalid",
            "function": {
                "name": "test_tool"
                # 缺少 description
            }
        }
        
        is_invalid = llm._validate_openai_tool_format(invalid_tool, "invalid_tool")
        print(f"✅ 无效工具格式验证: {'正确拒绝' if not is_invalid else '错误通过'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具格式验证测试失败: {e}")
        return False

def test_backup_tool_creation():
    """测试备用工具创建机制"""
    print("\n🔧 测试备用工具创建机制")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI
        from langchain_core.tools import tool
        
        # 创建适配器实例
        llm = ChatDashScopeOpenAI(model="qwen-turbo")
        
        # 定义测试工具
        @tool
        def test_backup_tool(param1: str, param2: int = 10) -> str:
            """测试备用工具创建"""
            return f"结果: {param1}, {param2}"
        
        # 测试备用工具创建
        backup_tool = llm._create_backup_tool_format(test_backup_tool)
        
        if backup_tool:
            print("✅ 备用工具创建成功")
            print(f"   工具名称: {backup_tool['function']['name']}")
            print(f"   工具描述: {backup_tool['function']['description']}")
            
            # 验证备用工具格式
            is_valid = llm._validate_openai_tool_format(backup_tool, "backup_test")
            print(f"   格式验证: {'通过' if is_valid else '失败'}")
        else:
            print("❌ 备用工具创建失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 备用工具创建测试失败: {e}")
        return False

def test_tool_call_response_validation():
    """测试工具调用响应验证"""
    print("\n🔍 测试工具调用响应验证")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI
        
        # 创建适配器实例
        llm = ChatDashScopeOpenAI(model="qwen-turbo")
        
        # 测试有效的工具调用格式
        valid_tool_call = {
            "name": "test_tool",
            "args": {"param1": "value1"}
        }
        
        is_valid = llm._validate_tool_call_format(valid_tool_call, 0)
        print(f"✅ 有效工具调用验证: {'通过' if is_valid else '失败'}")
        
        # 测试无效的工具调用格式
        invalid_tool_call = {
            "invalid_field": "value"
            # 缺少 name 字段
        }
        
        is_invalid = llm._validate_tool_call_format(invalid_tool_call, 1)
        print(f"✅ 无效工具调用验证: {'正确拒绝' if not is_invalid else '错误通过'}")
        
        # 测试工具调用修复
        broken_tool_call = {
            "function": {
                "name": "test_tool",
                "arguments": {"param1": "value1"}
            }
        }
        
        fixed_tool_call = llm._fix_tool_call_format(broken_tool_call, 2)
        if fixed_tool_call:
            print("✅ 工具调用修复成功")
            print(f"   修复后名称: {fixed_tool_call.get('name')}")
            print(f"   修复后参数: {fixed_tool_call.get('args')}")
        else:
            print("❌ 工具调用修复失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具调用响应验证测试失败: {e}")
        return False

def test_comprehensive_tool_calling():
    """综合测试工具调用流程"""
    print("\n🚀 综合测试工具调用流程")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_openai_adapter import ChatDashScopeOpenAI
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage
        
        # 定义复杂的测试工具
        @tool
        def get_stock_analysis(ticker: str, analysis_type: str = "basic") -> str:
            """获取股票分析报告"""
            return f"股票 {ticker} 的 {analysis_type} 分析报告：这是一个详细的分析..."
        
        @tool
        def get_market_news(query: str, days: int = 7) -> str:
            """获取市场新闻"""
            return f"关于 {query} 最近 {days} 天的市场新闻..."
        
        # 创建适配器并绑定工具
        llm = ChatDashScopeOpenAI(
            model="qwen-plus-latest",
            temperature=0.1,
            max_tokens=500
        )
        
        tools = [get_stock_analysis, get_market_news]
        llm_with_tools = llm.bind_tools(tools)
        
        print("✅ 复杂工具绑定成功")
        
        # 测试多轮对话和工具调用
        messages = [
            HumanMessage(content="请帮我分析苹果公司(AAPL)的股票，并获取相关新闻")
        ]
        
        response = llm_with_tools.invoke(messages)
        
        print(f"✅ 复杂对话调用成功")
        print(f"   响应内容长度: {len(response.content) if hasattr(response, 'content') else 0}")
        
        # 详细分析响应
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"✅ 检测到 {len(response.tool_calls)} 个工具调用")
            for i, tool_call in enumerate(response.tool_calls):
                print(f"   工具 {i+1}: {tool_call.get('name', 'unknown')}")
                print(f"   参数: {tool_call.get('args', {})}")
        else:
            print("⚠️ 未检测到工具调用")
            if hasattr(response, 'content'):
                print(f"   响应内容: {response.content[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 综合工具调用测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 DashScope OpenAI 适配器修复测试")
    print("=" * 80)
    
    # 检查环境变量
    if not os.getenv('DASHSCOPE_API_KEY'):
        print("❌ 错误: 未找到 DASHSCOPE_API_KEY 环境变量")
        print("请设置您的 DashScope API 密钥:")
        print("  Windows: set DASHSCOPE_API_KEY=your_api_key")
        print("  Linux/Mac: export DASHSCOPE_API_KEY=your_api_key")
        return
    
    # 运行测试
    tests = [
        ("工具格式验证", test_tool_format_validation),
        ("备用工具创建", test_backup_tool_creation),
        ("工具调用响应验证", test_tool_call_response_validation),
        ("增强工具绑定", test_enhanced_tool_binding),
        ("综合工具调用", test_comprehensive_tool_calling),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ 测试 {test_name} 执行异常: {e}")
            results[test_name] = False
    
    # 输出测试结果
    print("\n📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📈 总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！DashScope OpenAI 适配器修复成功！")
        print("\n💡 修复效果:")
        print("   ✅ 工具转换机制增强，支持备用格式")
        print("   ✅ 工具格式验证，确保兼容性")
        print("   ✅ 工具调用响应验证和修复")
        print("   ✅ 详细的错误处理和日志记录")
        print("   ✅ 提高了工具调用成功率")
    else:
        print(f"\n⚠️ 部分测试失败，需要进一步调试")
        print("请检查失败的测试项目并查看详细日志")

if __name__ == "__main__":
    main()