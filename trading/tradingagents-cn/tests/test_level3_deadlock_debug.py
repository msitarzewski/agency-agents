#!/usr/bin/env python3
"""
测试分析级别3死循环问题的调试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_init import init_logging
init_logging()

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.agents.utils.agent_states import AgentState
from langchain_core.messages import AIMessage
from app.services.simple_analysis_service import create_analysis_config

def test_level3_deadlock():
    """测试分析级别3的死循环问题"""
    
    print("=" * 80)
    print("🔍 分析级别3死循环问题调试")
    print("=" * 80)
    
    # 1. 对比不同级别的配置
    print("\n📊 1. 配置对比分析")
    print("-" * 50)
    
    levels = [
        ("快速", 1, "1级"),
        ("基础", 2, "2级"), 
        ("标准", 3, "3级")
    ]
    
    configs = {}
    for depth_name, level, desc in levels:
        config = create_analysis_config(
            research_depth=depth_name,
            selected_analysts=["market", "fundamentals"],
            quick_model="qwen-plus",
            deep_model="qwen-max",
            llm_provider="dashscope",
            market_type="A股"
        )
        configs[level] = config
        
        print(f"\n{desc} ({depth_name}):")
        print(f"  - max_debate_rounds: {config['max_debate_rounds']}")
        print(f"  - max_risk_discuss_rounds: {config['max_risk_discuss_rounds']}")
        print(f"  - memory_enabled: {config['memory_enabled']}")
        print(f"  - online_tools: {config['online_tools']}")
    
    # 2. 分析关键差异
    print("\n🔍 2. 关键差异分析")
    print("-" * 50)
    
    # 级别3的特殊配置
    level3_config = configs[3]
    level2_config = configs[2]
    level1_config = configs[1]
    
    print("级别3相比级别1、2的差异:")
    print(f"  - 风险讨论轮次: 级别1={level1_config['max_risk_discuss_rounds']}, 级别2={level2_config['max_risk_discuss_rounds']}, 级别3={level3_config['max_risk_discuss_rounds']}")
    print(f"  - 记忆功能: 级别1={level1_config['memory_enabled']}, 级别2={level2_config['memory_enabled']}, 级别3={level3_config['memory_enabled']}")
    print(f"  - 在线工具: 级别1={level1_config['online_tools']}, 级别2={level2_config['online_tools']}, 级别3={level3_config['online_tools']}")
    
    # 3. 模拟基本面分析师的条件判断
    print("\n🤖 3. 基本面分析师条件判断模拟")
    print("-" * 50)
    
    # 创建条件逻辑实例
    conditional_logic = ConditionalLogic(
        max_debate_rounds=level3_config['max_debate_rounds'],
        max_risk_discuss_rounds=level3_config['max_risk_discuss_rounds']
    )
    
    # 模拟不同的状态场景
    from langchain_core.messages.tool import ToolCall
    
    # 创建正确格式的tool_call
    tool_call = ToolCall(
        name="get_stock_fundamentals_unified",
        args={"ticker": "000001", "start_date": "2025-01-01", "end_date": "2025-01-15", "curr_date": "2025-01-15"},
        id="call_123"
    )
    
    scenarios = [
        {
            "name": "场景1: 空报告 + 有tool_calls",
            "state": {
                "messages": [AIMessage(content="分析中...", tool_calls=[tool_call])],
                "fundamentals_report": ""
            }
        },
        {
            "name": "场景2: 空报告 + 无tool_calls", 
            "state": {
                "messages": [AIMessage(content="分析完成")],
                "fundamentals_report": ""
            }
        },
        {
            "name": "场景3: 短报告 + 有tool_calls",
            "state": {
                "messages": [AIMessage(content="分析中...", tool_calls=[tool_call])],
                "fundamentals_report": "短报告"
            }
        },
        {
            "name": "场景4: 完整报告 + 有tool_calls",
            "state": {
                "messages": [AIMessage(content="分析完成", tool_calls=[tool_call])],
                "fundamentals_report": "这是一个完整的基本面分析报告，包含了详细的财务数据分析、估值模型计算、行业对比分析等内容，总长度超过100个字符，应该被认为是完成的报告。"
            }
        },
        {
            "name": "场景5: 完整报告 + 无tool_calls",
            "state": {
                "messages": [AIMessage(content="分析完成")],
                "fundamentals_report": "这是一个完整的基本面分析报告，包含了详细的财务数据分析、估值模型计算、行业对比分析等内容，总长度超过100个字符，应该被认为是完成的报告。"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        state = AgentState(scenario['state'])
        result = conditional_logic.should_continue_fundamentals(state)
        
        report_len = len(scenario['state']['fundamentals_report'])
        has_tool_calls = len(scenario['state']['messages']) > 0 and hasattr(scenario['state']['messages'][-1], 'tool_calls') and scenario['state']['messages'][-1].tool_calls
        
        print(f"  - 报告长度: {report_len}")
        print(f"  - 有tool_calls: {has_tool_calls}")
        print(f"  - 条件判断结果: {result}")
        
        # 分析是否可能导致死循环
        if result == "tools_fundamentals" and report_len == 0:
            print(f"  ⚠️  可能的死循环风险: 报告为空但继续调用工具")
        elif result == "tools_fundamentals" and report_len > 100:
            print(f"  🚨 潜在死循环: 报告已完成但仍要调用工具!")
        else:
            print(f"  ✅ 正常流程")
    
    # 4. 检查可能的死循环原因
    print("\n🔍 4. 死循环原因分析")
    print("-" * 50)
    
    print("可能的死循环原因:")
    print("1. 级别3的max_risk_discuss_rounds=2，可能影响工作流图的边缘连接")
    print("2. memory_enabled=True可能导致状态管理问题")
    print("3. 基本面分析师在级别3时可能使用不同的工具调用策略")
    print("4. 条件判断逻辑可能在特定配置下出现问题")
    
    # 5. 建议的修复方向
    print("\n💡 5. 建议的修复方向")
    print("-" * 50)
    
    print("基于分析，建议检查以下方面:")
    print("1. 检查基本面分析师在级别3时是否正确设置fundamentals_report")
    print("2. 验证条件判断逻辑是否正确处理tool_calls和报告状态")
    print("3. 检查工作流图在max_risk_discuss_rounds=2时的边缘配置")
    print("4. 验证Google工具调用处理器在级别3时的行为")
    print("5. 添加循环检测和超时保护机制")
    
    print("\n" + "=" * 80)
    print("调试分析完成")
    print("=" * 80)

if __name__ == "__main__":
    test_level3_deadlock()