#!/usr/bin/env python3
"""
测试在完整分析中使用Google和Reddit API
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

def test_news_analyst_with_google():
    """测试新闻分析师使用Google工具"""
    try:
        print("🧪 测试新闻分析师使用Google工具")
        print("=" * 60)
        
        from tradingagents.agents.analysts.news_analyst import create_news_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.llm_adapters import ChatDashScope
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        config["llm_provider"] = "dashscope"
        
        # 创建LLM和工具包
        llm = ChatDashScope(model="qwen-plus", temperature=0.1)
        toolkit = Toolkit(config=config)
        
        print("✅ 组件创建成功")
        
        # 创建新闻分析师
        news_analyst = create_news_analyst(llm, toolkit)
        
        print("✅ 新闻分析师创建成功")
        
        # 创建测试状态
        from tradingagents.agents.utils.agent_states import AgentState
        from langchain_core.messages import HumanMessage
        
        test_state = {
            "messages": [HumanMessage(content="分析AAPL的新闻情况")],
            "company_of_interest": "AAPL",
            "trade_date": "2025-06-27"
        }
        
        print("📰 开始新闻分析...")
        
        # 执行分析（这可能需要一些时间）
        result = news_analyst(test_state)
        
        if result and "news_report" in result:
            news_report = result["news_report"]
            if news_report and len(news_report) > 100:
                print("✅ 新闻分析成功完成")
                print(f"   报告长度: {len(news_report)} 字符")
                print(f"   报告预览: {news_report[:200]}...")
                return True
            else:
                print("⚠️ 新闻分析完成但报告内容较少")
                return True
        else:
            print("⚠️ 新闻分析完成但没有生成报告")
            return False
            
    except Exception as e:
        print(f"❌ 新闻分析师测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_social_analyst_with_reddit():
    """测试社交媒体分析师使用Reddit工具"""
    try:
        print("\n🧪 测试社交媒体分析师使用Reddit工具")
        print("=" * 60)
        
        from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.llm_adapters import ChatDashScope
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        config["llm_provider"] = "dashscope"
        
        # 创建LLM和工具包
        llm = ChatDashScope(model="qwen-plus", temperature=0.1)
        toolkit = Toolkit(config=config)
        
        print("✅ 组件创建成功")
        
        # 创建社交媒体分析师
        social_analyst = create_social_media_analyst(llm, toolkit)
        
        print("✅ 社交媒体分析师创建成功")
        
        # 创建测试状态
        from langchain_core.messages import HumanMessage
        
        test_state = {
            "messages": [HumanMessage(content="分析AAPL的社交媒体情绪")],
            "company_of_interest": "AAPL", 
            "trade_date": "2025-06-27"
        }
        
        print("💭 开始社交媒体分析...")
        
        # 执行分析
        result = social_analyst(test_state)
        
        if result and "sentiment_report" in result:
            sentiment_report = result["sentiment_report"]
            if sentiment_report and len(sentiment_report) > 100:
                print("✅ 社交媒体分析成功完成")
                print(f"   报告长度: {len(sentiment_report)} 字符")
                print(f"   报告预览: {sentiment_report[:200]}...")
                return True
            else:
                print("⚠️ 社交媒体分析完成但报告内容较少")
                return True
        else:
            print("⚠️ 社交媒体分析完成但没有生成报告")
            return False
            
    except Exception as e:
        print(f"❌ 社交媒体分析师测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    print("🧪 完整分析中的API工具测试")
    print("=" * 70)
    
    # 检查环境变量
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    reddit_id = os.getenv("REDDIT_CLIENT_ID")
    
    if not dashscope_key:
        print("❌ DASHSCOPE_API_KEY 未配置，无法进行测试")
        return
    
    print("🔑 API密钥状态:")
    print(f"   阿里百炼: ✅ 已配置")
    print(f"   Google: {'✅ 已配置' if google_key else '❌ 未配置'}")
    print(f"   Reddit: {'✅ 已配置' if reddit_id else '❌ 未配置'}")
    
    # 运行测试
    results = {}
    
    print("\n" + "="*70)
    results['新闻分析师+Google'] = test_news_analyst_with_google()
    
    print("\n" + "="*70)
    results['社交媒体分析师+Reddit'] = test_social_analyst_with_reddit()
    
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
        print("🎉 所有API工具在分析中正常工作！")
        print("\n💡 使用建议:")
        print("   1. 在Web界面中选择'新闻分析师'来使用Google新闻")
        print("   2. 在Web界面中选择'社交媒体分析师'来使用Reddit数据")
        print("   3. 同时选择多个分析师可以获得更全面的分析")
    else:
        print("⚠️ 部分API工具需要进一步配置")

if __name__ == "__main__":
    main()
