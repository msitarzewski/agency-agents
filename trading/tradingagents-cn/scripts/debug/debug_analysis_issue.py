#!/usr/bin/env python3
"""
调试分析问题的脚本
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def debug_analysis_result():
    """调试分析结果问题"""
    print("🔍 调试分析结果问题")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = False  # 使用离线模式避免API调用
        config["llm_provider"] = "dashscope"
        config["debug"] = True  # 启用调试模式
        
        print(f"✅ 配置创建成功")
        print(f"   LLM提供商: {config['llm_provider']}")
        print(f"   在线工具: {config['online_tools']}")
        print(f"   调试模式: {config['debug']}")
        
        # 创建分析图
        graph = TradingAgentsGraph(
            selected_analysts=["market", "fundamentals"],
            debug=True,
            config=config
        )
        
        print(f"✅ TradingAgentsGraph创建成功")
        
        # 执行分析
        print(f"\n🚀 开始执行分析...")
        state, decision = graph.propagate("000002", "2025-08-20")
        
        print(f"✅ 分析执行完成")
        
        # 检查状态中的各个字段
        print(f"\n📊 检查分析结果:")
        print(f"   状态类型: {type(state)}")
        print(f"   状态键: {list(state.keys()) if isinstance(state, dict) else 'N/A'}")
        
        # 检查各个报告字段
        report_fields = [
            'market_report',
            'fundamentals_report', 
            'sentiment_report',
            'news_report',
            'investment_debate_state',
            'trader_investment_plan',
            'risk_debate_state',
            'final_trade_decision'
        ]
        
        for field in report_fields:
            if field in state:
                value = state[field]
                if isinstance(value, str):
                    print(f"   {field}: 字符串长度 {len(value)}")
                    if len(value) > 0:
                        print(f"     预览: {value[:100]}...")
                    else:
                        print(f"     内容: 空字符串")
                elif isinstance(value, dict):
                    print(f"   {field}: 字典，包含键 {list(value.keys())}")
                    for key, val in value.items():
                        if isinstance(val, str):
                            print(f"     {key}: 字符串长度 {len(val)}")
                        else:
                            print(f"     {key}: {type(val)}")
                else:
                    print(f"   {field}: {type(value)} - {str(value)[:100]}")
            else:
                print(f"   {field}: 缺失")
        
        # 检查决策结果
        print(f"\n🎯 检查决策结果:")
        print(f"   决策类型: {type(decision)}")
        if isinstance(decision, dict):
            for key, value in decision.items():
                print(f"   {key}: {value}")
        else:
            print(f"   决策内容: {decision}")
        
        return True
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_analysis_result()
