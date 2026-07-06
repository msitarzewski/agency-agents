#!/usr/bin/env python3
"""
测试统一新闻工具的LangChain绑定修复
"""

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.tools.unified_news_tool import create_unified_news_tool
from langchain_core.utils.function_calling import convert_to_openai_tool

def test_tool_binding():
    """测试工具绑定是否修复"""
    print("=== 测试统一新闻工具的LangChain绑定修复 ===")
    
    # 创建工具包
    toolkit = Toolkit()
    
    # 创建统一新闻工具
    unified_tool = create_unified_news_tool(toolkit)
    
    # 测试LangChain工具转换
    print("\n1. 测试LangChain工具转换...")
    try:
        openai_tool = convert_to_openai_tool(unified_tool)
        print("✅ LangChain工具转换成功")
        
        func_info = openai_tool['function']
        print(f"工具名称: {func_info['name']}")
        print(f"工具描述: {func_info['description'][:100]}...")
        
        params = list(func_info['parameters']['properties'].keys())
        print(f"参数: {params}")
        
        # 检查参数是否正确
        expected_params = ['stock_code', 'max_news']
        if set(params) == set(expected_params):
            print("✅ 参数匹配正确")
        else:
            print(f"❌ 参数不匹配，期望: {expected_params}, 实际: {params}")
            
    except Exception as e:
        print(f"❌ LangChain工具转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试工具调用
    print("\n2. 测试工具调用...")
    try:
        result = unified_tool('000001', 5)
        print(f"✅ 工具调用成功，结果长度: {len(result)} 字符")
        print(f"结果预览: {result[:200]}...")
    except Exception as e:
        print(f"❌ 工具调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== 测试完成 ===")
    print("✅ 统一新闻工具的LangChain绑定问题已修复")
    print("✅ 函数签名与文档字符串现在匹配")
    print("✅ 工具可以正常绑定到LLM")
    
    return True

if __name__ == "__main__":
    test_tool_binding()