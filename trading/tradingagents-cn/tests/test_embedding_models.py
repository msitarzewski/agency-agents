#!/usr/bin/env python3
"""
测试不同嵌入模型的使用场景
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

def test_embedding_selection():
    """测试不同配置下的嵌入模型选择"""
    print("🧪 测试嵌入模型选择逻辑")
    print("=" * 60)
    
    from tradingagents.agents.utils.memory import FinancialSituationMemory
    from tradingagents.default_config import DEFAULT_CONFIG
    
    # 测试场景1: 阿里百炼
    print("📊 场景1: 阿里百炼配置")
    config1 = DEFAULT_CONFIG.copy()
    config1["llm_provider"] = "dashscope"
    config1["backend_url"] = "https://dashscope.aliyuncs.com/api/v1"
    
    try:
        memory1 = FinancialSituationMemory("test_dashscope", config1)
        print(f"✅ 嵌入模型: {memory1.embedding}")
        print(f"   LLM提供商: {memory1.llm_provider}")
        print(f"   客户端: {type(memory1.client)}")
    except Exception as e:
        print(f"❌ 阿里百炼配置失败: {e}")
    
    print()
    
    # 测试场景2: 本地Ollama
    print("📊 场景2: 本地Ollama配置")
    config2 = DEFAULT_CONFIG.copy()
    config2["llm_provider"] = "ollama"
    config2["backend_url"] = "http://localhost:11434/v1"
    
    try:
        memory2 = FinancialSituationMemory("test_ollama", config2)
        print(f"✅ 嵌入模型: {memory2.embedding}")
        print(f"   LLM提供商: {memory2.llm_provider}")
        print(f"   客户端: {type(memory2.client)}")
        print(f"   后端URL: {config2['backend_url']}")
    except Exception as e:
        print(f"❌ 本地Ollama配置失败: {e}")
    
    print()
    
    # 测试场景3: Google AI (问题场景)
    print("📊 场景3: Google AI配置 (问题场景)")
    config3 = DEFAULT_CONFIG.copy()
    config3["llm_provider"] = "google"
    config3["backend_url"] = "https://api.openai.com/v1"  # 默认还是OpenAI URL
    
    try:
        memory3 = FinancialSituationMemory("test_google", config3)
        print(f"⚠️ 嵌入模型: {memory3.embedding}")
        print(f"   LLM提供商: {memory3.llm_provider}")
        print(f"   客户端: {type(memory3.client)}")
        print(f"   问题: Google AI没有专门的嵌入配置，默认使用OpenAI")
    except Exception as e:
        print(f"❌ Google AI配置失败: {e}")
    
    print()
    
    # 测试场景4: OpenAI
    print("📊 场景4: OpenAI配置")
    config4 = DEFAULT_CONFIG.copy()
    config4["llm_provider"] = "openai"
    config4["backend_url"] = "https://api.openai.com/v1"
    
    try:
        memory4 = FinancialSituationMemory("test_openai", config4)
        print(f"✅ 嵌入模型: {memory4.embedding}")
        print(f"   LLM提供商: {memory4.llm_provider}")
        print(f"   客户端: {type(memory4.client)}")
    except Exception as e:
        print(f"❌ OpenAI配置失败: {e}")

def test_embedding_functionality():
    """测试嵌入功能是否正常工作"""
    print("\n🧪 测试嵌入功能")
    print("=" * 60)
    
    from tradingagents.agents.utils.memory import FinancialSituationMemory
    from tradingagents.default_config import DEFAULT_CONFIG
    
    # 测试阿里百炼嵌入
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    if dashscope_key:
        print("📊 测试阿里百炼嵌入功能")
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "dashscope"
        
        try:
            memory = FinancialSituationMemory("test_embedding", config)
            embedding = memory.get_embedding("苹果公司股票分析")
            print(f"✅ 阿里百炼嵌入成功")
            print(f"   嵌入维度: {len(embedding)}")
            print(f"   嵌入预览: {embedding[:5]}...")
        except Exception as e:
            print(f"❌ 阿里百炼嵌入失败: {e}")
    else:
        print("⚠️ 阿里百炼API密钥未配置，跳过测试")
    
    print()
    
    # 测试Google AI嵌入（会失败）
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print("📊 测试Google AI嵌入功能（预期失败）")
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        
        try:
            memory = FinancialSituationMemory("test_google_embedding", config)
            embedding = memory.get_embedding("Apple stock analysis")
            print(f"✅ Google AI嵌入成功（意外）")
            print(f"   嵌入维度: {len(embedding)}")
        except Exception as e:
            print(f"❌ Google AI嵌入失败（预期）: {e}")
            print("   原因: Google AI没有专门的嵌入配置，尝试使用OpenAI API")
    else:
        print("⚠️ Google API密钥未配置，跳过测试")

def show_solutions():
    """显示解决方案"""
    print("\n💡 解决方案")
    print("=" * 60)
    
    print("🔧 方案1: 为Google AI添加专门的嵌入配置")
    print("   - 使用Google的嵌入API（如果有）")
    print("   - 或者使用其他兼容的嵌入服务")
    
    print("\n🔧 方案2: 禁用内存功能")
    print("   - 设置 memory_enabled = False")
    print("   - 修复代码中的None检查")
    
    print("\n🔧 方案3: 使用阿里百炼嵌入")
    print("   - 即使LLM使用Google AI")
    print("   - 嵌入仍然使用阿里百炼")
    
    print("\n🔧 方案4: 使用本地嵌入")
    print("   - 安装Ollama")
    print("   - 下载nomic-embed-text模型")
    print("   - 完全本地运行")
    
    print("\n📋 各方案对比:")
    print("   方案1: 最理想，但需要Google嵌入API")
    print("   方案2: 最简单，但失去记忆功能")
    print("   方案3: 实用，混合使用不同服务")
    print("   方案4: 隐私最佳，但需要本地资源")

def main():
    """主测试函数"""
    print("🧪 嵌入模型使用场景分析")
    print("=" * 70)
    
    test_embedding_selection()
    test_embedding_functionality()
    show_solutions()
    
    print(f"\n📊 总结:")
    print("=" * 50)
    print("1. nomic-embed-text 是本地Ollama使用的嵌入模型")
    print("2. Google AI没有专门的嵌入配置，默认尝试使用OpenAI")
    print("3. 这就是为什么测试Google AI时内存功能不可用")
    print("4. 需要为Google AI添加合适的嵌入解决方案")

if __name__ == "__main__":
    main()
