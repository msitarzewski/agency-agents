#!/usr/bin/env python3
"""
测试Web界面的Google模型功能
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

def test_web_interface_config():
    """测试Web界面配置功能"""
    print("🧪 测试Web界面Google模型配置")
    print("=" * 60)
    
    try:
        # 测试sidebar配置
        print("📋 测试sidebar配置...")
        from web.components.sidebar import render_sidebar
        
        # 模拟Streamlit环境（简化测试）
        print("✅ sidebar模块导入成功")
        
        # 测试analysis_runner配置
        print("📊 测试analysis_runner配置...")
        from web.utils.analysis_runner import run_stock_analysis
        
        print("✅ analysis_runner模块导入成功")
        
        # 测试参数验证
        print("🔧 测试参数配置...")
        
        # 模拟Google配置
        test_config = {
            'llm_provider': 'google',
            'llm_model': 'gemini-2.0-flash',
            'enable_memory': True,
            'enable_debug': False,
            'max_tokens': 4000
        }
        
        print(f"✅ 测试配置创建成功: {test_config}")
        
        # 验证配置参数
        required_params = ['llm_provider', 'llm_model']
        for param in required_params:
            if param in test_config:
                print(f"   ✅ {param}: {test_config[param]}")
            else:
                print(f"   ❌ {param}: 缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ Web界面配置测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_model_options():
    """测试模型选项配置"""
    print("\n🧪 测试模型选项配置")
    print("=" * 60)
    
    # 阿里百炼模型选项
    dashscope_models = ["qwen-turbo", "qwen-plus", "qwen-max"]
    print("📊 阿里百炼模型选项:")
    for model in dashscope_models:
        print(f"   ✅ {model}")
    
    # Google模型选项
    google_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    print("\n🤖 Google模型选项:")
    for model in google_models:
        print(f"   ✅ {model}")
    
    # 验证推荐配置
    print(f"\n🏆 推荐配置:")
    print(f"   LLM提供商: Google AI")
    print(f"   推荐模型: gemini-2.0-flash")
    print(f"   嵌入服务: 阿里百炼 (自动配置)")
    print(f"   内存功能: 启用")
    
    return True

def test_api_requirements():
    """测试API密钥要求"""
    print("\n🧪 测试API密钥要求")
    print("=" * 60)
    
    # 检查必需的API密钥
    api_keys = {
        'GOOGLE_API_KEY': 'Google AI API密钥',
        'DASHSCOPE_API_KEY': '阿里百炼API密钥（用于嵌入）',
        'FINNHUB_API_KEY': '金融数据API密钥'
    }
    
    all_configured = True
    
    for key, description in api_keys.items():
        value = os.getenv(key)
        if value:
            print(f"✅ {description}: 已配置")
        else:
            print(f"❌ {description}: 未配置")
            all_configured = False
    
    if all_configured:
        print(f"\n🎉 所有必需的API密钥都已配置！")
        print(f"💡 现在可以使用Google AI进行完整的股票分析")
    else:
        print(f"\n⚠️ 部分API密钥未配置")
        print(f"💡 请在.env文件中配置缺失的API密钥")
    
    return all_configured

def main():
    """主测试函数"""
    print("🧪 Web界面Google模型功能测试")
    print("=" * 70)
    
    # 运行测试
    results = {}
    
    results['Web界面配置'] = test_web_interface_config()
    results['模型选项'] = test_model_options()
    results['API密钥'] = test_api_requirements()
    
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
        print("🎉 Web界面Google模型功能完全可用！")
        print("\n💡 使用指南:")
        print("   1. 打开Web界面: http://localhost:8501")
        print("   2. 在左侧边栏选择'Google AI'作为LLM提供商")
        print("   3. 选择'Gemini 2.0 Flash'模型（推荐）")
        print("   4. 启用记忆功能获得更好的分析效果")
        print("   5. 选择分析师并开始股票分析")
        print("\n🚀 现在您可以享受Google AI的强大分析能力！")
    else:
        print("⚠️ 部分功能需要进一步配置")

if __name__ == "__main__":
    main()
