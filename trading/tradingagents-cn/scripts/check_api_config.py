#!/usr/bin/env python3
"""
API配置检查工具
检查各种API密钥的配置状态和可用性
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_env_file():
    """检查.env文件是否存在"""
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ .env文件存在")
        load_dotenv(env_file)
        return True
    else:
        print("❌ .env文件不存在")
        print("💡 请复制.env_example为.env并配置API密钥")
        return False

def check_dashscope_config():
    """检查DashScope配置"""
    print("\n🔍 检查DashScope配置...")
    
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("❌ DASHSCOPE_API_KEY未配置")
        print("💡 影响: 记忆功能将被禁用，但系统可以正常运行")
        return False
    
    print(f"✅ DASHSCOPE_API_KEY已配置: {api_key[:12]}...{api_key[-4:]}")
    
    # 测试API可用性
    try:
        import dashscope
        from dashscope import TextEmbedding
        
        dashscope.api_key = api_key
        
        response = TextEmbedding.call(
            model="text-embedding-v3",
            input="测试文本"
        )
        
        if response.status_code == 200:
            print("✅ DashScope API测试成功")
            return True
        else:
            print(f"❌ DashScope API测试失败: {response.code} - {response.message}")
            return False
            
    except ImportError:
        print("⚠️ dashscope包未安装，无法测试API")
        return False
    except Exception as e:
        print(f"❌ DashScope API测试异常: {e}")
        return False

def check_other_apis():
    """检查其他API配置"""
    print("\n🔍 检查其他API配置...")
    
    apis = {
        'OPENAI_API_KEY': 'OpenAI API',
        'GOOGLE_API_KEY': 'Google AI API', 
        'DEEPSEEK_API_KEY': 'DeepSeek API',
        'TUSHARE_TOKEN': 'Tushare数据源',
        'FINNHUB_API_KEY': 'FinnHub数据源'
    }
    
    configured_apis = []
    missing_apis = []
    
    for env_var, name in apis.items():
        value = os.getenv(env_var)
        if value:
            print(f"✅ {name}: 已配置")
            configured_apis.append(name)
        else:
            print(f"❌ {name}: 未配置")
            missing_apis.append(name)
    
    return configured_apis, missing_apis

def check_memory_functionality():
    """检查记忆功能是否可用"""
    print("\n🧠 检查记忆功能...")
    
    try:
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        from tradingagents.default_config import DEFAULT_CONFIG
        
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "dashscope"
        
        memory = FinancialSituationMemory("test_memory", config)
        
        # 测试embedding
        embedding = memory.get_embedding("测试文本")
        
        if all(x == 0.0 for x in embedding):
            print("⚠️ 记忆功能已禁用（返回空向量）")
            print("💡 原因: DashScope API密钥未配置或无效")
            return False
        else:
            print(f"✅ 记忆功能正常（向量维度: {len(embedding)}）")
            return True
            
    except Exception as e:
        print(f"❌ 记忆功能测试失败: {e}")
        return False

def provide_recommendations(dashscope_ok, configured_apis, missing_apis):
    """提供配置建议"""
    print("\n💡 配置建议:")
    print("=" * 50)
    
    if not dashscope_ok:
        print("🔴 DashScope配置问题:")
        print("   - 记忆功能将被禁用")
        print("   - 看涨/看跌研究员无法使用历史经验")
        print("   - 系统仍可正常进行股票分析")
        print("   - 建议配置DASHSCOPE_API_KEY以获得完整功能")
        print()
    
    if 'Tushare数据源' not in configured_apis:
        print("🟡 Tushare未配置:")
        print("   - A股数据将使用AKShare备用源")
        print("   - 建议配置TUSHARE_TOKEN以获得更好的数据质量")
        print()
    
    if len(configured_apis) == 0:
        print("🔴 严重警告:")
        print("   - 没有配置任何API密钥")
        print("   - 系统可能无法正常工作")
        print("   - 请至少配置一个LLM API密钥")
        print()
    
    print("📋 最小配置建议:")
    print("   1. 配置至少一个LLM API密钥（DASHSCOPE_API_KEY推荐）")
    print("   2. 配置TUSHARE_TOKEN以获得A股数据")
    print("   3. 其他API密钥可选配置")
    print()
    
    print("🚀 完整配置建议:")
    print("   - DASHSCOPE_API_KEY: 阿里百炼（推荐，中文优化）")
    print("   - TUSHARE_TOKEN: A股专业数据")
    print("   - OPENAI_API_KEY: 备用LLM")
    print("   - FINNHUB_API_KEY: 美股数据")

def main():
    """主函数"""
    print("🔍 TradingAgents API配置检查工具")
    print("=" * 60)
    
    # 检查.env文件
    if not check_env_file():
        return
    
    # 检查DashScope
    dashscope_ok = check_dashscope_config()
    
    # 检查其他API
    configured_apis, missing_apis = check_other_apis()
    
    # 检查记忆功能
    memory_ok = check_memory_functionality()
    
    # 总结
    print("\n📊 配置总结:")
    print("=" * 30)
    print(f"DashScope API: {'✅ 正常' if dashscope_ok else '❌ 异常'}")
    print(f"记忆功能: {'✅ 可用' if memory_ok else '❌ 禁用'}")
    print(f"已配置API: {len(configured_apis)}个")
    print(f"缺失API: {len(missing_apis)}个")
    
    # 提供建议
    provide_recommendations(dashscope_ok, configured_apis, missing_apis)
    
    # 系统状态评估
    if dashscope_ok and len(configured_apis) >= 2:
        print("\n🎉 系统配置良好，可以正常使用所有功能！")
    elif len(configured_apis) >= 1:
        print("\n⚠️ 系统可以基本运行，但建议完善配置以获得更好体验。")
    else:
        print("\n🚨 系统配置不足，可能无法正常工作，请配置必要的API密钥。")

if __name__ == "__main__":
    main()
