#!/usr/bin/env python3
"""
测试工具包中的Google和Reddit工具
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

def test_toolkit_tools():
    """测试工具包中的工具"""
    try:
        print("🧪 测试工具包中的Google和Reddit工具")
        print("=" * 60)
        
        # 正确导入Toolkit
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["online_tools"] = True
        
        # 创建工具包实例
        toolkit = Toolkit(config=config)
        
        print("✅ Toolkit实例创建成功")
        
        # 检查所有可用方法
        all_methods = [method for method in dir(toolkit) if not method.startswith('_')]
        print(f"📊 工具包总方法数: {len(all_methods)}")
        
        # 查找Google相关方法
        google_methods = [m for m in all_methods if 'google' in m.lower()]
        print(f"🔍 Google相关方法: {google_methods}")
        
        # 查找Reddit相关方法
        reddit_methods = [m for m in all_methods if 'reddit' in m.lower()]
        print(f"🔍 Reddit相关方法: {reddit_methods}")
        
        # 查找新闻相关方法
        news_methods = [m for m in all_methods if 'news' in m.lower()]
        print(f"📰 新闻相关方法: {news_methods}")
        
        # 测试具体的Google工具
        if hasattr(toolkit, 'get_google_news'):
            print("\n✅ get_google_news 方法存在")
            try:
                # 测试调用
                print("📰 测试Google新闻获取...")
                news = toolkit.get_google_news(
                    query="Apple AAPL",
                    curr_date="2025-06-27",
                    look_back_days=3
                )
                if news and len(news) > 100:
                    print(f"✅ Google新闻获取成功 ({len(news)} 字符)")
                else:
                    print("⚠️ Google新闻获取成功但内容较少")
            except Exception as e:
                print(f"❌ Google新闻测试失败: {e}")
        else:
            print("❌ get_google_news 方法不存在")
        
        # 测试Reddit工具
        reddit_tools = ['get_reddit_global_news', 'get_reddit_company_news', 'get_reddit_stock_info', 'get_reddit_news']
        
        for tool_name in reddit_tools:
            if hasattr(toolkit, tool_name):
                print(f"✅ {tool_name} 方法存在")
            else:
                print(f"❌ {tool_name} 方法不存在")
        
        # 显示所有方法（用于调试）
        print(f"\n📋 所有可用方法:")
        for i, method in enumerate(sorted(all_methods), 1):
            print(f"  {i:2d}. {method}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具包测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_social_news_analysts():
    """测试社交媒体和新闻分析师是否能使用这些工具"""
    try:
        print("\n🧪 测试分析师工具集成")
        print("=" * 60)
        
        # 检查社交媒体分析师
        try:
            from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
            print("✅ 社交媒体分析师模块可用")
        except ImportError as e:
            print(f"❌ 社交媒体分析师导入失败: {e}")
        
        # 检查新闻分析师
        try:
            from tradingagents.agents.analysts.news_analyst import create_news_analyst
            print("✅ 新闻分析师模块可用")
        except ImportError as e:
            print(f"❌ 新闻分析师导入失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析师测试失败: {e}")
        return False

def check_data_requirements():
    """检查数据要求"""
    print("\n🧪 检查数据要求")
    print("=" * 60)
    
    # 检查Reddit数据目录
    reddit_data_paths = [
        "tradingagents/dataflows/data_cache/reddit_data",
        "data/reddit_data",
        "reddit_data"
    ]
    
    reddit_data_found = False
    for path in reddit_data_paths:
        reddit_path = Path(path)
        if reddit_path.exists():
            print(f"✅ Reddit数据目录找到: {reddit_path}")
            subdirs = [d.name for d in reddit_path.iterdir() if d.is_dir()]
            if subdirs:
                print(f"   子目录: {subdirs}")
                reddit_data_found = True
            else:
                print("   目录为空")
            break
    
    if not reddit_data_found:
        print("⚠️ Reddit数据目录未找到")
        print("💡 Reddit工具需要预先下载的数据文件")
        print("   可能的解决方案:")
        print("   1. 下载Reddit数据集")
        print("   2. 配置正确的数据路径")
        print("   3. 使用在线Reddit API（如果支持）")
    
    # 检查Google API要求
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print("✅ Google API密钥已配置")
        print("💡 Google新闻工具使用网页抓取，不需要API密钥")
    else:
        print("⚠️ Google API密钥未配置")
        print("💡 但Google新闻工具仍可能正常工作（使用网页抓取）")

def main():
    """主测试函数"""
    print("🧪 工具包Google和Reddit工具测试")
    print("=" * 70)
    
    # 检查API密钥状态
    print("🔑 API密钥状态:")
    google_key = os.getenv('GOOGLE_API_KEY')
    reddit_id = os.getenv('REDDIT_CLIENT_ID')
    print(f"   Google API: {'✅ 已配置' if google_key else '❌ 未配置'}")
    print(f"   Reddit API: {'✅ 已配置' if reddit_id else '❌ 未配置'}")
    
    # 运行测试
    results = {}
    
    results['工具包工具'] = test_toolkit_tools()
    results['分析师集成'] = test_social_news_analysts()
    
    # 检查数据要求
    check_data_requirements()
    
    # 总结结果
    print(f"\n📊 测试结果总结:")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")

if __name__ == "__main__":
    main()
