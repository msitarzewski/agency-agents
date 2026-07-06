#!/usr/bin/env python3
"""
测试修复后的市场分析师
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def test_deepseek_market_analyst():
    """测试DeepSeek的市场分析师"""
    print("🤖 测试DeepSeek市场分析师修复效果")
    print("=" * 60)
    
    try:
        from tradingagents.agents.analysts.market_analyst import create_market_analyst
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建DeepSeek LLM
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=2000
        )
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 创建市场分析师
        market_analyst = create_market_analyst(deepseek_llm, toolkit)
        
        # 模拟状态
        state = {
            "company_of_interest": "000002",
            "trade_date": "2025-07-08",
            "messages": []
        }
        
        print(f"📊 开始分析股票: {state['company_of_interest']}")
        
        # 执行分析
        result = market_analyst(state)
        
        print(f"📊 分析结果:")
        print(f"   消息数量: {len(result.get('messages', []))}")
        
        market_report = result.get('market_report', '')
        print(f"   市场报告长度: {len(market_report)}")
        print(f"   市场报告前500字符:")
        print("-" * 50)
        print(market_report[:500])
        print("-" * 50)
        
        # 检查报告质量
        has_data = any(keyword in market_report for keyword in ["¥", "RSI", "MACD", "万科", "技术指标"])
        has_analysis = len(market_report) > 500
        not_placeholder = "正在调用工具" not in market_report
        
        print(f"📊 报告质量检查:")
        print(f"   包含实际数据: {'✅' if has_data else '❌'}")
        print(f"   分析内容充实: {'✅' if has_analysis else '❌'}")
        print(f"   非占位符内容: {'✅' if not_placeholder else '❌'}")
        
        success = has_data and has_analysis and not_placeholder
        print(f"   整体评估: {'✅ 成功' if success else '❌ 需要改进'}")
        
        return success
        
    except Exception as e:
        print(f"❌ DeepSeek市场分析师测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashscope_market_analyst():
    """测试百炼的市场分析师（ReAct模式）"""
    print("\n🌟 测试百炼市场分析师（ReAct模式）")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("DASHSCOPE_API_KEY"):
            print("⚠️ 未找到DASHSCOPE_API_KEY，跳过百炼测试")
            return True  # 跳过不算失败
        
        from tradingagents.agents.analysts.market_analyst import create_market_analyst_react
        from tradingagents.llm_adapters.dashscope_adapter import ChatDashScope
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建百炼LLM
        dashscope_llm = ChatDashScope(
            model="qwen-plus",
            temperature=0.1,
            max_tokens=2000
        )
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 创建ReAct市场分析师
        market_analyst = create_market_analyst_react(dashscope_llm, toolkit)
        
        # 模拟状态
        state = {
            "company_of_interest": "000002",
            "trade_date": "2025-07-08",
            "messages": []
        }
        
        print(f"📊 开始分析股票: {state['company_of_interest']}")
        
        # 执行分析
        result = market_analyst(state)
        
        print(f"📊 分析结果:")
        print(f"   消息数量: {len(result.get('messages', []))}")
        
        market_report = result.get('market_report', '')
        print(f"   市场报告长度: {len(market_report)}")
        print(f"   市场报告前500字符:")
        print("-" * 50)
        print(market_report[:500])
        print("-" * 50)
        
        # 检查报告质量
        has_data = any(keyword in market_report for keyword in ["¥", "RSI", "MACD", "万科", "技术指标"])
        has_analysis = len(market_report) > 500
        not_placeholder = "正在调用工具" not in market_report
        
        print(f"📊 报告质量检查:")
        print(f"   包含实际数据: {'✅' if has_data else '❌'}")
        print(f"   分析内容充实: {'✅' if has_analysis else '❌'}")
        print(f"   非占位符内容: {'✅' if not_placeholder else '❌'}")
        
        success = has_data and has_analysis and not_placeholder
        print(f"   整体评估: {'✅ 成功' if success else '❌ 需要改进'}")
        
        return success
        
    except Exception as e:
        print(f"❌ 百炼市场分析师测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 市场分析师修复效果测试")
    print("=" * 80)
    
    # 检查API密钥
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not deepseek_key:
        print("⚠️ 未找到DEEPSEEK_API_KEY，无法测试")
        return False
    
    # 测试DeepSeek
    deepseek_success = test_deepseek_market_analyst()
    
    # 测试百炼（如果有API密钥）
    dashscope_success = test_dashscope_market_analyst()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    print(f"DeepSeek市场分析师: {'✅ 修复成功' if deepseek_success else '❌ 仍需修复'}")
    print(f"百炼ReAct分析师: {'✅ 工作正常' if dashscope_success else '❌ 需要检查'}")
    
    overall_success = deepseek_success and dashscope_success
    
    if overall_success:
        print("\n🎉 市场分析师修复成功！")
        print("   - DeepSeek现在能正确执行工具调用并生成完整分析")
        print("   - 百炼ReAct模式继续正常工作")
        print("   - 两个模型都能基于真实数据生成技术分析报告")
    else:
        print("\n⚠️ 仍有问题需要解决")
        if not deepseek_success:
            print("   - DeepSeek市场分析师需要进一步修复")
        if not dashscope_success:
            print("   - 百炼ReAct分析师需要检查")
    
    print("\n🎯 测试完成！")
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
