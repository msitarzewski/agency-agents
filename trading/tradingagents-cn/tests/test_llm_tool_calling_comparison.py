#!/usr/bin/env python3
"""
测试不同LLM模型在工具调用和技术分析方面的行为差异
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def test_deepseek_tool_calling():
    """测试DeepSeek的工具调用行为"""
    print("🤖 测试DeepSeek工具调用行为")
    print("=" * 60)

    try:
        # 直接导入DeepSeek适配器，避免导入dashscope
        import sys
        sys.path.insert(0, str(project_root / "tradingagents" / "llm_adapters"))
        from deepseek_adapter import ChatDeepSeek
        from langchain_core.tools import BaseTool
        
        # 创建DeepSeek实例
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=2000
        )
        
        # 创建模拟的股票数据工具
        class MockChinaStockDataTool(BaseTool):
            name: str = "get_china_stock_data"
            description: str = "获取中国A股股票000002的市场数据和技术指标"
            
            def _run(self, query: str = "") -> str:
                return """# 000002 万科A 股票数据分析

## 📊 实时行情
- 股票名称: 万科A
- 当前价格: ¥6.56
- 涨跌幅: 0.61%
- 成交量: 934,783手

## 📈 技术指标
- 10日EMA: ¥6.45
- 50日SMA: ¥6.78
- 200日SMA: ¥7.12
- RSI: 42.5
- MACD: -0.08
- MACD信号线: -0.12
- 布林带上轨: ¥7.20
- 布林带中轨: ¥6.80
- 布林带下轨: ¥6.40
- ATR: 0.25"""
        
        tools = [MockChinaStockDataTool()]
        
        # 测试提示词
        prompt = """请对中国A股股票000002进行详细的技术分析。

执行步骤：
1. 使用get_china_stock_data工具获取股票市场数据
2. 基于获取的真实数据进行深入的技术指标分析
3. 输出完整的技术分析报告内容

重要要求：
- 必须调用工具获取数据
- 必须输出完整的技术分析报告内容，不要只是描述报告已完成
- 报告必须基于工具获取的真实数据进行分析"""
        
        # 绑定工具并调用
        chain = deepseek_llm.bind_tools(tools)
        result = chain.invoke(prompt)
        
        print(f"📊 DeepSeek响应类型: {type(result)}")
        print(f"📊 DeepSeek工具调用数量: {len(result.tool_calls) if hasattr(result, 'tool_calls') else 0}")
        print(f"📊 DeepSeek响应内容长度: {len(result.content)}")
        print(f"📊 DeepSeek响应内容前500字符:")
        print("-" * 50)
        print(result.content[:500])
        print("-" * 50)
        
        if hasattr(result, 'tool_calls') and result.tool_calls:
            print(f"📊 DeepSeek工具调用详情:")
            for i, call in enumerate(result.tool_calls):
                print(f"   工具{i+1}: {call.get('name', 'unknown')}")
                print(f"   参数: {call.get('args', {})}")
        
        return result
        
    except Exception as e:
        print(f"❌ DeepSeek测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_dashscope_tool_calling():
    """测试百炼模型的工具调用行为"""
    print("\n🌟 测试百炼模型工具调用行为")
    print("=" * 60)
    
    try:
        from tradingagents.llm_adapters.dashscope_adapter import ChatDashScope
        from langchain_core.tools import BaseTool
        
        # 创建百炼实例
        dashscope_llm = ChatDashScope(
            model="qwen-plus",
            temperature=0.1,
            max_tokens=2000
        )
        
        # 创建相同的模拟工具
        class MockChinaStockDataTool(BaseTool):
            name: str = "get_china_stock_data"
            description: str = "获取中国A股股票000002的市场数据和技术指标"
            
            def _run(self, query: str = "") -> str:
                return """# 000002 万科A 股票数据分析

## 📊 实时行情
- 股票名称: 万科A
- 当前价格: ¥6.56
- 涨跌幅: 0.61%
- 成交量: 934,783手

## 📈 技术指标
- 10日EMA: ¥6.45
- 50日SMA: ¥6.78
- 200日SMA: ¥7.12
- RSI: 42.5
- MACD: -0.08
- MACD信号线: -0.12
- 布林带上轨: ¥7.20
- 布林带中轨: ¥6.80
- 布林带下轨: ¥6.40
- ATR: 0.25"""
        
        tools = [MockChinaStockDataTool()]
        
        # 使用相同的提示词
        prompt = """请对中国A股股票000002进行详细的技术分析。

执行步骤：
1. 使用get_china_stock_data工具获取股票市场数据
2. 基于获取的真实数据进行深入的技术指标分析
3. 输出完整的技术分析报告内容

重要要求：
- 必须调用工具获取数据
- 必须输出完整的技术分析报告内容，不要只是描述报告已完成
- 报告必须基于工具获取的真实数据进行分析"""
        
        # 绑定工具并调用
        chain = dashscope_llm.bind_tools(tools)
        result = chain.invoke(prompt)
        
        print(f"📊 百炼响应类型: {type(result)}")
        print(f"📊 百炼工具调用数量: {len(result.tool_calls) if hasattr(result, 'tool_calls') else 0}")
        print(f"📊 百炼响应内容长度: {len(result.content)}")
        print(f"📊 百炼响应内容前500字符:")
        print("-" * 50)
        print(result.content[:500])
        print("-" * 50)
        
        if hasattr(result, 'tool_calls') and result.tool_calls:
            print(f"📊 百炼工具调用详情:")
            for i, call in enumerate(result.tool_calls):
                print(f"   工具{i+1}: {call.get('name', 'unknown')}")
                print(f"   参数: {call.get('args', {})}")
        
        return result
        
    except Exception as e:
        print(f"❌ 百炼测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_results(deepseek_result, dashscope_result):
    """对比两个模型的结果"""
    print("\n🔍 结果对比分析")
    print("=" * 60)
    
    if deepseek_result and dashscope_result:
        # 工具调用对比
        deepseek_tools = len(deepseek_result.tool_calls) if hasattr(deepseek_result, 'tool_calls') else 0
        dashscope_tools = len(dashscope_result.tool_calls) if hasattr(dashscope_result, 'tool_calls') else 0
        
        print(f"📊 工具调用对比:")
        print(f"   DeepSeek: {deepseek_tools} 次工具调用")
        print(f"   百炼: {dashscope_tools} 次工具调用")
        
        # 内容长度对比
        deepseek_length = len(deepseek_result.content)
        dashscope_length = len(dashscope_result.content)
        
        print(f"\n📝 响应内容对比:")
        print(f"   DeepSeek: {deepseek_length} 字符")
        print(f"   百炼: {dashscope_length} 字符")
        
        # 内容类型分析
        print(f"\n🔍 内容类型分析:")
        
        # 检查是否包含实际数据分析
        deepseek_has_data = any(keyword in deepseek_result.content for keyword in ["¥6.56", "RSI", "MACD", "万科A"])
        dashscope_has_data = any(keyword in dashscope_result.content for keyword in ["¥6.56", "RSI", "MACD", "万科A"])
        
        print(f"   DeepSeek包含实际数据: {'✅' if deepseek_has_data else '❌'}")
        print(f"   百炼包含实际数据: {'✅' if dashscope_has_data else '❌'}")
        
        # 检查是否只是描述过程
        deepseek_describes_process = any(keyword in deepseek_result.content for keyword in ["首先", "然后", "接下来", "步骤"])
        dashscope_describes_process = any(keyword in dashscope_result.content for keyword in ["首先", "然后", "接下来", "步骤"])
        
        print(f"   DeepSeek描述分析过程: {'⚠️' if deepseek_describes_process else '✅'}")
        print(f"   百炼描述分析过程: {'⚠️' if dashscope_describes_process else '✅'}")
        
        # 总结
        print(f"\n📋 总结:")
        if deepseek_tools > 0 and deepseek_has_data:
            print(f"   ✅ DeepSeek: 正确调用工具并分析数据")
        else:
            print(f"   ❌ DeepSeek: 未正确执行工具调用或数据分析")
            
        if dashscope_tools > 0 and dashscope_has_data:
            print(f"   ✅ 百炼: 正确调用工具并分析数据")
        else:
            print(f"   ❌ 百炼: 未正确执行工具调用或数据分析")

def main():
    """主函数"""
    print("🔬 LLM工具调用行为对比测试")
    print("=" * 80)
    
    # 检查API密钥
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not deepseek_key:
        print("⚠️ 未找到DEEPSEEK_API_KEY，跳过DeepSeek测试")
        deepseek_result = None
    else:
        deepseek_result = test_deepseek_tool_calling()
    
    if not dashscope_key:
        print("⚠️ 未找到DASHSCOPE_API_KEY，跳过百炼测试")
        dashscope_result = None
    else:
        dashscope_result = test_dashscope_tool_calling()
    
    # 对比结果
    if deepseek_result or dashscope_result:
        compare_results(deepseek_result, dashscope_result)
    else:
        print("❌ 无法进行对比，两个模型都测试失败")
    
    print("\n" + "=" * 80)
    print("🎯 测试完成！")

if __name__ == "__main__":
    main()
