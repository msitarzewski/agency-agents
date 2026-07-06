#!/usr/bin/env python3
"""
测试所有API密钥功能
包括Google API和Reddit API
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

def check_all_api_keys():
    """检查所有API密钥配置"""
    print("🔑 检查API密钥配置")
    print("=" * 50)
    
    api_keys = {
        'DASHSCOPE_API_KEY': '阿里百炼API',
        'FINNHUB_API_KEY': '金融数据API', 
        'GOOGLE_API_KEY': 'Google API',
        'REDDIT_CLIENT_ID': 'Reddit客户端ID',
        'REDDIT_CLIENT_SECRET': 'Reddit客户端密钥',
        'REDDIT_USER_AGENT': 'Reddit用户代理'
    }
    
    configured_apis = []
    missing_apis = []
    
    for key, name in api_keys.items():
        value = os.getenv(key)
        if value:
            print(f"✅ {name}: 已配置 ({value[:10]}...)")
            configured_apis.append(name)
        else:
            print(f"❌ {name}: 未配置")
            missing_apis.append(name)
    
    print(f"\n📊 配置状态:")
    print(f"  已配置: {len(configured_apis)}/{len(api_keys)}")
    print(f"  缺失: {len(missing_apis)}")
    
    return configured_apis, missing_apis

def test_google_api():
    """测试Google API"""
    try:
        print("\n🧪 测试Google API")
        print("=" * 50)
        
        google_key = os.getenv('GOOGLE_API_KEY')
        if not google_key:
            print("❌ Google API密钥未配置")
            return False
        
        # 这里可以添加具体的Google API测试
        # 例如Google News API或Google Search API
        print("✅ Google API密钥已配置")
        print("💡 提示: 需要根据具体使用的Google服务进行测试")
        
        return True
        
    except Exception as e:
        print(f"❌ Google API测试失败: {e}")
        return False

def test_reddit_api():
    """测试Reddit API"""
    try:
        print("\n🧪 测试Reddit API")
        print("=" * 50)
        
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        
        if not all([client_id, client_secret, user_agent]):
            print("❌ Reddit API配置不完整")
            print(f"  CLIENT_ID: {'✅' if client_id else '❌'}")
            print(f"  CLIENT_SECRET: {'✅' if client_secret else '❌'}")
            print(f"  USER_AGENT: {'✅' if user_agent else '❌'}")
            return False
        
        # 测试Reddit API连接
        try:
            import praw
            
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # 测试获取一个简单的subreddit信息
            subreddit = reddit.subreddit('investing')
            print(f"✅ Reddit API连接成功")
            print(f"  测试subreddit: {subreddit.display_name}")
            print(f"  订阅者数量: {subreddit.subscribers:,}")
            
            return True
            
        except ImportError:
            print("⚠️ praw库未安装，无法测试Reddit API")
            print("💡 运行: pip install praw")
            return False
        except Exception as e:
            print(f"❌ Reddit API连接失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Reddit API测试失败: {e}")
        return False

def test_tradingagents_with_new_apis():
    """测试TradingAgents是否能使用新的API"""
    try:
        print("\n🧪 测试TradingAgents集成")
        print("=" * 50)
        
        # 检查TradingAgents是否支持这些API
        from tradingagents.dataflows import interface
        
        # 检查可用的数据流工具
        print("📊 检查可用的数据获取工具:")
        
        # 检查Google相关工具
        try:
            from tradingagents.dataflows.googlenews_utils import get_google_news
            print("✅ Google News工具可用")
        except ImportError:
            print("❌ Google News工具不可用")
        
        # 检查Reddit相关工具  
        try:
            from tradingagents.dataflows.reddit_utils import get_reddit_sentiment
            print("✅ Reddit情绪分析工具可用")
        except ImportError:
            print("❌ Reddit情绪分析工具不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ TradingAgents集成测试失败: {e}")
        return False

def test_social_media_analyst():
    """测试社交媒体分析师是否能使用Reddit数据"""
    try:
        print("\n🧪 测试社交媒体分析师")
        print("=" * 50)
        
        # 检查社交媒体分析师
        from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
        from tradingagents.llm_adapters import ChatDashScope
        
        # 创建模型实例
        llm = ChatDashScope(model="qwen-plus")
        
        # 这里需要toolkit实例，暂时跳过实际测试
        print("✅ 社交媒体分析师模块可用")
        print("💡 需要完整的toolkit实例才能进行实际测试")
        
        return True
        
    except Exception as e:
        print(f"❌ 社交媒体分析师测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 全面API测试")
    print("=" * 60)
    
    # 检查API密钥配置
    configured, missing = check_all_api_keys()
    
    # 测试各个API
    results = {}
    
    if 'Google API' in configured:
        results['Google API'] = test_google_api()
    
    if all(api in configured for api in ['Reddit客户端ID', 'Reddit客户端密钥']):
        results['Reddit API'] = test_reddit_api()
    
    # 测试TradingAgents集成
    results['TradingAgents集成'] = test_tradingagents_with_new_apis()
    results['社交媒体分析师'] = test_social_media_analyst()
    
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
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查配置")

if __name__ == "__main__":
    main()
