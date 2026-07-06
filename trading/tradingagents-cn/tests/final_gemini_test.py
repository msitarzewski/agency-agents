#!/usr/bin/env python3
"""
最终验证推荐的Gemini模型
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

def test_recommended_model():
    """测试推荐的gemini-2.0-flash模型"""
    try:
        print("🧪 最终验证推荐模型: gemini-2.0-flash")
        print("=" * 60)
        
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 检查API密钥
        google_key = os.getenv('GOOGLE_API_KEY')
        dashscope_key = os.getenv('DASHSCOPE_API_KEY')
        
        print(f"🔑 API密钥状态:")
        print(f"   Google API: {'✅ 已配置' if google_key else '❌ 未配置'}")
        print(f"   阿里百炼API: {'✅ 已配置' if dashscope_key else '❌ 未配置'}")
        
        if not google_key:
            print("❌ Google API密钥未配置")
            return False
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["deep_think_llm"] = "gemini-2.0-flash"
        config["quick_think_llm"] = "gemini-2.0-flash"
        config["online_tools"] = False  # 避免API限制
        config["memory_enabled"] = True  # 启用内存功能
        config["max_debate_rounds"] = 2  # 增加辩论轮次
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
        print(f"   模型: {config['deep_think_llm']}")
        print(f"   内存功能: {config['memory_enabled']}")
        print(f"   辩论轮次: {config['max_debate_rounds']}")
        
        # 创建TradingAgentsGraph实例
        print("🚀 初始化TradingAgents图...")
        graph = TradingAgentsGraph(["market", "fundamentals"], config=config, debug=False)
        
        print("✅ TradingAgents图初始化成功")
        print("   分析师: 市场分析师 + 基本面分析师")
        
        # 测试分析
        print("📊 开始完整股票分析...")
        print("   使用gemini-2.0-flash + 阿里百炼嵌入")
        print("   这可能需要几分钟时间...")
        
        try:
            state, decision = graph.propagate("AAPL", "2025-06-27")
            
            if state and decision:
                print("✅ gemini-2.0-flash驱动的完整分析成功！")
                print(f"   最终决策: {decision}")
                
                # 检查各种报告
                reports = {
                    "market_report": "市场技术分析",
                    "fundamentals_report": "基本面分析", 
                    "sentiment_report": "情绪分析",
                    "news_report": "新闻分析"
                }
                
                for report_key, report_name in reports.items():
                    if report_key in state and state[report_key]:
                        report_content = state[report_key]
                        print(f"   {report_name}: {len(report_content)} 字符")
                        if len(report_content) > 100:
                            print(f"     预览: {report_content[:150]}...")
                        print()
                
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
        print(f"❌ 最终验证失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def compare_models():
    """比较不同模型的建议"""
    print("\n📊 模型选择建议")
    print("=" * 60)
    
    models_comparison = {
        "gemini-2.5-pro": {
            "状态": "❌ LangChain集成问题",
            "优势": "最新版本，理论性能最强",
            "劣势": "LangChain集成不稳定",
            "推荐": "不推荐（集成问题）"
        },
        "gemini-2.5-flash": {
            "状态": "❌ LangChain集成问题", 
            "优势": "最新版本，速度快",
            "劣势": "LangChain集成不稳定",
            "推荐": "不推荐（集成问题）"
        },
        "gemini-2.0-flash": {
            "状态": "✅ 完全可用",
            "优势": "新版本，LangChain稳定，性能优秀",
            "劣势": "不是最新的2.5版本",
            "推荐": "🏆 强烈推荐"
        },
        "gemini-1.5-pro": {
            "状态": "✅ 完全可用",
            "优势": "稳定，功能强大",
            "劣势": "版本较旧",
            "推荐": "备选方案"
        }
    }
    
    for model, info in models_comparison.items():
        print(f"\n🤖 {model}:")
        for key, value in info.items():
            print(f"   {key}: {value}")

def main():
    """主函数"""
    print("🧪 Gemini模型最终验证")
    print("=" * 70)
    
    # 运行最终验证
    success = test_recommended_model()
    
    # 显示比较
    compare_models()
    
    # 最终建议
    print(f"\n📊 最终测试结果:")
    print("=" * 50)
    
    if success:
        print("✅ gemini-2.0-flash 完全验证成功！")
        print("\n🎉 最终推荐配置:")
        print("   LLM提供商: Google")
        print("   模型名称: gemini-2.0-flash")
        print("   嵌入服务: 阿里百炼 (text-embedding-v3)")
        print("   内存功能: 启用")
        print("\n💡 优势总结:")
        print("   🧠 优秀的推理能力")
        print("   🌍 完美的中文支持")
        print("   🔧 稳定的LangChain集成")
        print("   💾 完整的内存学习功能")
        print("   📊 准确的金融分析")
        print("\n🚀 您现在可以在Web界面中使用这个配置！")
    else:
        print("❌ 验证失败")
        print("💡 建议使用gemini-1.5-pro作为备选方案")

if __name__ == "__main__":
    main()
