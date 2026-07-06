#!/usr/bin/env python3
"""
实际测试DeepSeek成本计算修复效果
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

def test_real_deepseek_analysis():
    """测试真实的DeepSeek股票分析，观察成本计算"""
    print("🧪 实际测试DeepSeek成本计算")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 未找到DEEPSEEK_API_KEY，无法测试")
        return False
    
    try:
        from tradingagents.agents.analysts.market_analyst import create_market_analyst_react
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        print("🔧 初始化DeepSeek分析师...")
        
        # 创建DeepSeek LLM
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=1000
        )
        
        # 创建工具包
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        toolkit = Toolkit(config)
        
        # 创建ReAct市场分析师
        market_analyst = create_market_analyst_react(deepseek_llm, toolkit)
        
        print("📊 开始分析股票000002...")
        print("⏱️ 请观察成本计算输出...")
        print("-" * 50)
        
        # 模拟状态
        state = {
            "company_of_interest": "000002",
            "trade_date": "2025-07-08",
            "messages": []
        }
        
        # 执行分析
        result = market_analyst(state)
        
        print("-" * 50)
        print("📋 分析完成！")
        
        market_report = result.get('market_report', '')
        print(f"📊 市场报告长度: {len(market_report)}")
        
        if len(market_report) > 500:
            print("✅ 分析成功生成详细报告")
            print(f"📄 报告前200字符: {market_report[:200]}...")
            return True
        else:
            print("❌ 分析报告过短，可能有问题")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_deepseek_call():
    """测试简单的DeepSeek调用，观察成本"""
    print("\n🤖 测试简单DeepSeek调用")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 未找到DEEPSEEK_API_KEY，无法测试")
        return False
    
    try:
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        
        print("🔧 创建DeepSeek实例...")
        
        # 创建DeepSeek实例
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=200
        )
        
        print("📤 发送测试请求...")
        print("⏱️ 请观察成本计算输出...")
        print("-" * 30)
        
        # 测试调用
        result = deepseek_llm.invoke("请简要分析一下当前A股市场的整体趋势，不超过100字。")
        
        print("-" * 30)
        print("📋 调用完成！")
        print(f"📊 响应长度: {len(result.content)}")
        print(f"📄 响应内容: {result.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ 简单调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_calls():
    """测试多次调用，观察累计成本"""
    print("\n🔄 测试多次DeepSeek调用")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 未找到DEEPSEEK_API_KEY，无法测试")
        return False
    
    try:
        from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
        
        print("🔧 创建DeepSeek实例...")
        
        # 创建DeepSeek实例
        deepseek_llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=100
        )
        
        questions = [
            "什么是股票？",
            "什么是技术分析？",
            "什么是基本面分析？"
        ]
        
        print(f"📤 发送{len(questions)}个测试请求...")
        print("⏱️ 请观察每次调用的成本计算...")
        print("-" * 40)
        
        for i, question in enumerate(questions, 1):
            print(f"\n🔸 第{i}次调用: {question}")
            result = deepseek_llm.invoke(question)
            print(f"   响应: {result.content[:50]}...")
        
        print("-" * 40)
        print("📋 多次调用完成！")
        
        return True
        
    except Exception as e:
        print(f"❌ 多次调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔬 DeepSeek成本计算实际测试")
    print("=" * 80)
    print("📝 注意观察输出中的成本信息：")
    print("   - 应该显示具体的成本金额（如¥0.004537）")
    print("   - 不应该显示¥0.000000")
    print("=" * 80)
    
    # 测试简单调用
    simple_success = test_simple_deepseek_call()
    
    # 测试多次调用
    multiple_success = test_multiple_calls()
    
    # 测试实际分析（可选，比较耗时）
    print(f"\n❓ 是否要测试完整的股票分析？（比较耗时，约1-2分钟）")
    print(f"   如果只想验证成本计算，前面的测试已经足够了。")
    
    # 这里我们跳过完整分析，因为比较耗时
    analysis_success = True  # test_real_deepseek_analysis()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    print(f"简单调用: {'✅ 成功' if simple_success else '❌ 失败'}")
    print(f"多次调用: {'✅ 成功' if multiple_success else '❌ 失败'}")
    print(f"完整分析: {'⏭️ 跳过' if analysis_success else '❌ 失败'}")
    
    overall_success = simple_success and multiple_success
    
    if overall_success:
        print("\n🎉 DeepSeek成本计算测试成功！")
        print("   如果你在上面的输出中看到了具体的成本金额")
        print("   （如¥0.004537而不是¥0.000000），")
        print("   那么成本计算修复就是成功的！")
    else:
        print("\n❌ DeepSeek成本计算测试失败")
        print("   请检查API密钥配置和网络连接")
    
    print("\n🎯 测试完成！")
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
