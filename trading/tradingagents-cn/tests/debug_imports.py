#!/usr/bin/env python3
"""
调试导入问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_google_news_import():
    """测试Google News工具导入"""
    print("🧪 测试Google News工具导入")
    print("=" * 50)
    
    try:
        # 尝试不同的导入方式
        print("1. 尝试导入googlenews_utils模块...")
        from tradingagents.dataflows import googlenews_utils
        print("✅ googlenews_utils模块导入成功")
        
        # 检查模块中的函数
        print("2. 检查模块中的函数...")
        functions = [attr for attr in dir(googlenews_utils) if not attr.startswith('_')]
        print(f"   可用函数: {functions}")
        
        # 尝试导入特定函数
        print("3. 尝试导入特定函数...")
        if hasattr(googlenews_utils, 'get_google_news'):
            print("✅ get_google_news函数存在")
        else:
            print("❌ get_google_news函数不存在")
            
        if hasattr(googlenews_utils, 'getNewsData'):
            print("✅ getNewsData函数存在")
        else:
            print("❌ getNewsData函数不存在")
            
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_reddit_import():
    """测试Reddit工具导入"""
    print("\n🧪 测试Reddit工具导入")
    print("=" * 50)
    
    try:
        # 尝试不同的导入方式
        print("1. 尝试导入reddit_utils模块...")
        from tradingagents.dataflows import reddit_utils
        print("✅ reddit_utils模块导入成功")
        
        # 检查模块中的函数
        print("2. 检查模块中的函数...")
        functions = [attr for attr in dir(reddit_utils) if not attr.startswith('_')]
        print(f"   可用函数: {functions}")
        
        # 尝试导入特定函数
        print("3. 尝试导入特定函数...")
        if hasattr(reddit_utils, 'get_reddit_sentiment'):
            print("✅ get_reddit_sentiment函数存在")
        else:
            print("❌ get_reddit_sentiment函数不存在")
            
        # 检查其他可能的函数名
        possible_functions = ['get_reddit_data', 'fetch_reddit_posts', 'analyze_reddit_sentiment']
        for func_name in possible_functions:
            if hasattr(reddit_utils, func_name):
                print(f"✅ {func_name}函数存在")
            
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def check_dependencies():
    """检查依赖库"""
    print("\n🧪 检查依赖库")
    print("=" * 50)
    
    dependencies = {
        'requests': 'HTTP请求库',
        'beautifulsoup4': 'HTML解析库',
        'praw': 'Reddit API库',
        'tenacity': '重试机制库'
    }
    
    for package, description in dependencies.items():
        try:
            if package == 'beautifulsoup4':
                import bs4
                print(f"✅ {description}: 已安装")
            else:
                __import__(package)
                print(f"✅ {description}: 已安装")
        except ImportError:
            print(f"❌ {description}: 未安装 (pip install {package})")

def check_actual_file_contents():
    """检查实际文件内容"""
    print("\n🧪 检查实际文件内容")
    print("=" * 50)
    
    # 检查Google News文件
    try:
        google_file = Path("tradingagents/dataflows/googlenews_utils.py")
        if google_file.exists():
            print(f"✅ Google News文件存在: {google_file}")
            with open(google_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'def ' in content:
                    # 提取函数定义
                    import re
                    functions = re.findall(r'def (\w+)\(', content)
                    print(f"   文件中的函数: {functions}")
                else:
                    print("   文件中没有函数定义")
        else:
            print(f"❌ Google News文件不存在: {google_file}")
    except Exception as e:
        print(f"❌ 检查Google News文件失败: {e}")
    
    # 检查Reddit文件
    try:
        reddit_file = Path("tradingagents/dataflows/reddit_utils.py")
        if reddit_file.exists():
            print(f"✅ Reddit文件存在: {reddit_file}")
            with open(reddit_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'def ' in content:
                    # 提取函数定义
                    import re
                    functions = re.findall(r'def (\w+)\(', content)
                    print(f"   文件中的函数: {functions}")
                else:
                    print("   文件中没有函数定义")
        else:
            print(f"❌ Reddit文件不存在: {reddit_file}")
    except Exception as e:
        print(f"❌ 检查Reddit文件失败: {e}")

def main():
    """主函数"""
    print("🔍 诊断工具导入问题")
    print("=" * 60)
    
    # 检查依赖库
    check_dependencies()
    
    # 检查文件内容
    check_actual_file_contents()
    
    # 测试导入
    google_success = test_google_news_import()
    reddit_success = test_reddit_import()
    
    print(f"\n📊 诊断结果:")
    print(f"  Google News工具: {'✅ 可用' if google_success else '❌ 不可用'}")
    print(f"  Reddit工具: {'✅ 可用' if reddit_success else '❌ 不可用'}")

if __name__ == "__main__":
    main()
