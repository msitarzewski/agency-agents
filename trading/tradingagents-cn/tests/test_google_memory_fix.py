#!/usr/bin/env python3
"""
测试修复后的Google AI内存功能
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

def test_google_memory_fixed():
    """测试修复后的Google AI内存功能"""
    try:
        print("🧪 测试修复后的Google AI内存功能")
        print("=" * 60)
        
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 检查API密钥
        google_key = os.getenv('GOOGLE_API_KEY')
        dashscope_key = os.getenv('DASHSCOPE_API_KEY')
        
        print(f"🔑 API密钥状态:")
        print(f"   Google API: {'✅ 已配置' if google_key else '❌ 未配置'}")
        print(f"   阿里百炼API: {'✅ 已配置' if dashscope_key else '❌ 未配置'}")
        
        if not google_key:
            print("❌ Google API密钥未配置，无法测试")
            return False
        
        # 创建Google AI配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        
        print("\n📊 创建Google AI内存实例...")
        memory = FinancialSituationMemory("test_google_memory", config)
        
        print(f"✅ 内存实例创建成功")
        print(f"   LLM提供商: {memory.llm_provider}")
        print(f"   嵌入模型: {memory.embedding}")
        print(f"   客户端类型: {type(memory.client)}")
        
        # 测试嵌入功能
        print("\n📝 测试嵌入功能...")
        test_text = "苹果公司股票在高通胀环境下的投资价值分析"
        
        try:
            embedding = memory.get_embedding(test_text)
            print(f"✅ 嵌入生成成功")
            print(f"   嵌入维度: {len(embedding)}")
            print(f"   嵌入预览: {embedding[:5]}...")
            
            # 测试记忆存储
            print("\n💾 测试记忆存储...")
            memory.add_situations([
                ("高通胀环境，利率上升，科技股承压", "建议关注现金流稳定的大型科技公司，如苹果、微软等"),
                ("市场波动加剧，投资者情绪谨慎", "建议分散投资，关注防御性板块")
            ])
            print("✅ 记忆存储成功")
            
            # 测试记忆检索
            print("\n🔍 测试记忆检索...")
            similar_memories = memory.get_memories("通胀上升时期的科技股投资", n_matches=2)
            print(f"✅ 记忆检索成功")
            print(f"   检索到 {len(similar_memories)} 条相关记忆")

            for i, mem in enumerate(similar_memories, 1):
                situation = mem['matched_situation']
                recommendation = mem['recommendation']
                score = mem['similarity_score']
                print(f"   记忆{i} (相似度: {score:.3f}):")
                print(f"     情况: {situation}")
                print(f"     建议: {recommendation}")
            
            return True
            
        except Exception as e:
            print(f"❌ 嵌入功能测试失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Google AI内存测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_google_tradingagents_with_memory():
    """测试带内存的Google AI TradingAgents"""
    try:
        print("\n🧪 测试带内存的Google AI TradingAgents")
        print("=" * 60)
        
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 检查API密钥
        google_key = os.getenv('GOOGLE_API_KEY')
        dashscope_key = os.getenv('DASHSCOPE_API_KEY')
        
        if not google_key:
            print("❌ Google API密钥未配置")
            return False
        
        if not dashscope_key:
            print("⚠️ 阿里百炼API密钥未配置，内存功能可能不可用")
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["deep_think_llm"] = "gemini-2.5-flash-lite-preview-06-17"
        config["quick_think_llm"] = "gemini-2.5-flash-lite-preview-06-17"
        config["online_tools"] = False  # 避免API限制
        config["memory_enabled"] = True  # 启用内存功能
        config["max_debate_rounds"] = 1
        config["max_risk_discuss_rounds"] = 1
        
        # 修复路径
        config["data_dir"] = str(project_root / "data")
        config["results_dir"] = str(project_root / "results")
        config["data_cache_dir"] = str(project_root / "tradingagents" / "dataflows" / "data_cache")
        
        # 创建目录
        os.makedirs(config["data_dir"], exist_ok=True)
        os.makedirs(config["results_dir"], exist_ok=True)
        os.makedirs(config["data_cache_dir"], exist_ok=True)
        
        print("✅ 配置创建成功")
        print(f"   LLM提供商: {config['llm_provider']}")
        print(f"   模型: {config['deep_think_llm']}")
        print(f"   内存功能: {config['memory_enabled']}")
        
        # 创建TradingAgentsGraph实例
        print("🚀 初始化带内存的TradingAgents图...")
        graph = TradingAgentsGraph(["market"], config=config, debug=False)
        
        print("✅ TradingAgents图初始化成功")
        
        # 测试分析
        print("📊 开始带内存的股票分析...")
        
        try:
            state, decision = graph.propagate("AAPL", "2025-06-27")
            
            if state and decision:
                print("✅ 带内存的Gemini股票分析成功！")
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
            print(f"❌ 带内存的股票分析失败: {e}")
            import traceback
            print(traceback.format_exc())
            return False
            
    except Exception as e:
        print(f"❌ 带内存的TradingAgents测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Google AI内存功能修复测试")
    print("=" * 70)
    
    # 运行测试
    results = {}
    
    results['内存功能'] = test_google_memory_fixed()
    results['完整TradingAgents'] = test_google_tradingagents_with_memory()
    
    # 总结结果
    print(f"\n📊 测试结果总结:")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")
    
    if successful_tests == total_tests:
        print("🎉 Google AI内存功能修复成功！")
        print("\n💡 现在可以使用的功能:")
        print("   ✅ Google Gemini作为主要LLM")
        print("   ✅ 阿里百炼作为嵌入服务")
        print("   ✅ 完整的内存和学习功能")
        print("   ✅ 中文分析和推理")
        print("   ✅ 历史经验学习")
    elif successful_tests > 0:
        print("⚠️ 部分功能可用")
        if results['内存功能'] and not results['完整TradingAgents']:
            print("💡 内存功能正常，但完整流程有其他问题")
    else:
        print("❌ 修复失败，请检查API密钥配置")

if __name__ == "__main__":
    main()
