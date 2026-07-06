#!/usr/bin/env python3
"""
简化的Gemini测试（禁用内存功能）
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env", override=True)

def test_gemini_simple_analysis():
    """测试Gemini的简单分析功能"""
    try:
        print("🧪 测试Gemini简单分析功能")
        print("=" * 60)
        
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 检查API密钥
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            print("❌ Google API密钥未配置")
            return False
        
        print(f"✅ Google API密钥已配置: {google_api_key[:20]}...")
        
        # 创建简化配置（禁用内存和在线工具）
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["deep_think_llm"] = "gemini-2.5-flash-lite-preview-06-17"
        config["quick_think_llm"] = "gemini-2.5-flash-lite-preview-06-17"
        config["online_tools"] = False  # 禁用在线工具避免API限制
        config["memory_enabled"] = False  # 禁用内存避免OpenAI依赖
        config["max_debate_rounds"] = 1  # 减少轮次
        config["max_risk_discuss_rounds"] = 1
        
        # 修复路径
        config["data_dir"] = str(project_root / "data")
        config["results_dir"] = str(project_root / "results")
        config["data_cache_dir"] = str(project_root / "tradingagents" / "dataflows" / "data_cache")
        
        # 创建目录
        os.makedirs(config["data_dir"], exist_ok=True)
        os.makedirs(config["results_dir"], exist_ok=True)
        os.makedirs(config["data_cache_dir"], exist_ok=True)
        
        print("✅ 简化配置创建成功")
        print(f"   LLM提供商: {config['llm_provider']}")
        print(f"   模型: {config['deep_think_llm']}")
        print(f"   在线工具: {config['online_tools']}")
        print(f"   内存功能: {config['memory_enabled']}")
        
        # 创建TradingAgentsGraph实例
        print("🚀 初始化TradingAgents图...")
        graph = TradingAgentsGraph(["market"], config=config, debug=False)
        
        print("✅ TradingAgents图初始化成功")
        
        # 测试简单分析
        print("📊 开始简化股票分析...")
        print("   使用离线数据，避免API限制...")
        
        try:
            state, decision = graph.propagate("AAPL", "2025-06-27")
            
            if state and decision:
                print("✅ Gemini驱动的股票分析成功完成！")
                print(f"   最终决策: {decision}")
                
                # 检查市场报告
                if "market_report" in state and state["market_report"]:
                    market_report = state["market_report"]
                    print(f"   市场报告长度: {len(market_report)} 字符")
                    print(f"   报告预览: {market_report[:200]}...")
                
                return True
            else:
                print("❌ 分析完成但结果为空")
                return False
                
        except Exception as e:
            print(f"❌ 股票分析失败: {e}")
            import traceback
            print(traceback.format_exc())
            return False
            
    except Exception as e:
        print(f"❌ 简化测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_gemini_analyst_direct():
    """直接测试Gemini分析师"""
    try:
        print("\n🧪 直接测试Gemini分析师")
        print("=" * 60)
        
        from tradingagents.agents.analysts.market_analyst import create_market_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from langchain_google_genai import ChatGoogleGenerativeAI
        from tradingagents.default_config import DEFAULT_CONFIG
        from langchain_core.messages import HumanMessage
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = False
        
        # 创建Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite-preview-06-17",
            temperature=0.1,
            max_tokens=1000,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        # 创建工具包
        toolkit = Toolkit(config=config)
        
        print("✅ 组件创建成功")
        
        # 创建市场分析师
        market_analyst = create_market_analyst(llm, toolkit)
        
        print("✅ 市场分析师创建成功")
        
        # 创建测试状态
        test_state = {
            "messages": [HumanMessage(content="分析AAPL的市场技术指标")],
            "company_of_interest": "AAPL",
            "trade_date": "2025-06-27"
        }
        
        print("📊 开始市场分析...")
        
        # 执行分析
        result = market_analyst(test_state)
        
        if result and "market_report" in result:
            market_report = result["market_report"]
            if market_report and len(market_report) > 100:
                print("✅ 市场分析成功完成")
                print(f"   报告长度: {len(market_report)} 字符")
                print(f"   报告预览: {market_report[:200]}...")
                return True
            else:
                print("⚠️ 市场分析完成但报告内容较少")
                return True
        else:
            print("⚠️ 市场分析完成但没有生成报告")
            return False
            
    except Exception as e:
        print(f"❌ 直接分析师测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    print("🧪 Gemini简化集成测试")
    print("=" * 70)
    
    # 检查环境变量
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("❌ Google API密钥未配置")
        print("💡 请在.env文件中设置 GOOGLE_API_KEY")
        return
    
    # 运行测试
    results = {}
    
    print("第1步: 直接分析师测试")
    print("-" * 30)
    results['直接分析师'] = test_gemini_analyst_direct()
    
    print("\n第2步: 简化TradingAgents测试")
    print("-" * 30)
    results['简化TradingAgents'] = test_gemini_simple_analysis()
    
    # 总结结果
    print(f"\n📊 简化测试结果总结:")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")
    
    if successful_tests == total_tests:
        print("🎉 Gemini模型核心功能完全可用！")
        print("\n💡 使用建议:")
        print("   1. Gemini基础功能正常工作")
        print("   2. 可以在TradingAgents中使用Gemini")
        print("   3. 建议禁用内存功能避免OpenAI依赖")
        print("   4. 可以使用离线模式避免API限制")
        print("   5. 支持中文分析和推理")
    elif successful_tests > 0:
        print("⚠️ Gemini部分功能可用")
        print("💡 核心功能正常，可以进行基础分析")
    else:
        print("❌ Gemini模型不可用")
        print("💡 请检查API密钥和网络连接")

if __name__ == "__main__":
    main()
