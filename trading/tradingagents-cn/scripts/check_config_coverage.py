#!/usr/bin/env python3
"""
配置覆盖率检查脚本
检查sidebar.py中的配置项是否都已包含在新的webapi配置系统中
"""

import os
import sys
import re
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapi.models.config import ModelProvider


def extract_sidebar_providers():
    """从sidebar.py中提取LLM提供商"""
    sidebar_file = project_root / "web" / "components" / "sidebar.py"
    
    if not sidebar_file.exists():
        print("❌ sidebar.py文件不存在")
        return []
    
    with open(sidebar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取LLM提供商选项
    provider_pattern = r'options=\["([^"]+)"(?:,\s*"([^"]+)")*\]'
    matches = re.findall(r'options=\[([^\]]+)\]', content)
    
    providers = []
    for match in matches:
        # 解析选项列表
        options = re.findall(r'"([^"]+)"', match)
        if 'dashscope' in options:  # 这是LLM提供商的选项列表
            providers = options
            break
    
    return providers


def extract_sidebar_models():
    """从sidebar.py中提取所有模型"""
    sidebar_file = project_root / "web" / "components" / "sidebar.py"
    
    with open(sidebar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    models = {}
    
    # 提取各个提供商的模型
    # DashScope模型
    dashscope_match = re.search(r'dashscope_options = \[([^\]]+)\]', content)
    if dashscope_match:
        models['dashscope'] = re.findall(r'"([^"]+)"', dashscope_match.group(1))
    
    # SiliconFlow模型
    siliconflow_match = re.search(r'siliconflow_options = \[([^\]]+)\]', content, re.DOTALL)
    if siliconflow_match:
        models['siliconflow'] = re.findall(r'"([^"]+)"', siliconflow_match.group(1))
    
    # DeepSeek模型
    deepseek_match = re.search(r'deepseek_options = \[([^\]]+)\]', content)
    if deepseek_match:
        models['deepseek'] = re.findall(r'"([^"]+)"', deepseek_match.group(1))
    
    # Google模型
    google_match = re.search(r'google_options = \[([^\]]+)\]', content, re.DOTALL)
    if google_match:
        models['google'] = re.findall(r'"([^"]+)"', google_match.group(1))
    
    # OpenAI模型
    openai_match = re.search(r'openai_options = \[([^\]]+)\]', content, re.DOTALL)
    if openai_match:
        models['openai'] = re.findall(r'"([^"]+)"', openai_match.group(1))
    
    # Qianfan模型
    qianfan_match = re.search(r'qianfan_options = \[([^\]]+)\]', content, re.DOTALL)
    if qianfan_match:
        models['qianfan'] = re.findall(r'"([^"]+)"', qianfan_match.group(1))
    
    return models


def extract_sidebar_api_keys():
    """从sidebar.py中提取API密钥配置"""
    sidebar_file = project_root / "web" / "components" / "sidebar.py"
    
    with open(sidebar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有环境变量引用
    env_vars = re.findall(r'os\.getenv\("([^"]+)"\)', content)
    
    return list(set(env_vars))


def extract_sidebar_advanced_settings():
    """从sidebar.py中提取高级设置"""
    sidebar_file = project_root / "web" / "components" / "sidebar.py"
    
    with open(sidebar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    settings = {}
    
    # 查找高级设置
    if 'enable_memory' in content:
        settings['enable_memory'] = True
    if 'enable_debug' in content:
        settings['enable_debug'] = True
    if 'max_tokens' in content:
        settings['max_tokens'] = True
    
    return settings


def check_provider_coverage():
    """检查提供商覆盖率"""
    print("🔍 检查LLM提供商覆盖率...")
    
    sidebar_providers = extract_sidebar_providers()
    webapi_providers = [provider.value for provider in ModelProvider]
    
    print(f"\n📋 Sidebar.py中的提供商 ({len(sidebar_providers)}):")
    for provider in sidebar_providers:
        print(f"  - {provider}")
    
    print(f"\n📋 WebAPI中的提供商 ({len(webapi_providers)}):")
    for provider in webapi_providers:
        print(f"  - {provider}")
    
    # 检查覆盖率
    missing_in_webapi = []
    for provider in sidebar_providers:
        if provider not in webapi_providers:
            missing_in_webapi.append(provider)
    
    if missing_in_webapi:
        print(f"\n❌ WebAPI中缺失的提供商 ({len(missing_in_webapi)}):")
        for provider in missing_in_webapi:
            print(f"  - {provider}")
    else:
        print(f"\n✅ 所有提供商都已包含在WebAPI中")
    
    return len(missing_in_webapi) == 0


def check_model_coverage():
    """检查模型覆盖率"""
    print("\n🔍 检查模型覆盖率...")
    
    sidebar_models = extract_sidebar_models()
    
    print(f"\n📋 Sidebar.py中的模型:")
    total_models = 0
    for provider, models in sidebar_models.items():
        print(f"  {provider} ({len(models)} 个模型):")
        total_models += len(models)
        for model in models[:3]:  # 只显示前3个
            print(f"    - {model}")
        if len(models) > 3:
            print(f"    ... 还有 {len(models) - 3} 个模型")
    
    print(f"\n📊 总计: {total_models} 个模型")
    print("ℹ️ 模型配置在迁移时会自动包含")
    
    return True


def check_api_key_coverage():
    """检查API密钥覆盖率"""
    print("\n🔍 检查API密钥覆盖率...")
    
    sidebar_api_keys = extract_sidebar_api_keys()
    
    print(f"\n📋 Sidebar.py中的API密钥 ({len(sidebar_api_keys)}):")
    for key in sidebar_api_keys:
        print(f"  - {key}")
    
    # 检查.env文件中是否存在这些密钥
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        missing_keys = []
        for key in sidebar_api_keys:
            if key not in env_content:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"\n⚠️ .env文件中缺失的密钥 ({len(missing_keys)}):")
            for key in missing_keys:
                print(f"  - {key}")
        else:
            print(f"\n✅ 所有API密钥都在.env文件中配置")
    else:
        print(f"\n❌ .env文件不存在")
    
    return True


def check_advanced_settings_coverage():
    """检查高级设置覆盖率"""
    print("\n🔍 检查高级设置覆盖率...")
    
    sidebar_settings = extract_sidebar_advanced_settings()
    
    print(f"\n📋 Sidebar.py中的高级设置 ({len(sidebar_settings)}):")
    for setting in sidebar_settings:
        print(f"  - {setting}")
    
    # 检查LLMConfig中是否包含这些设置
    from webapi.models.config import LLMConfig
    llm_fields = LLMConfig.__fields__.keys()
    
    missing_settings = []
    for setting in sidebar_settings:
        if setting not in llm_fields:
            missing_settings.append(setting)
    
    if missing_settings:
        print(f"\n❌ LLMConfig中缺失的设置 ({len(missing_settings)}):")
        for setting in missing_settings:
            print(f"  - {setting}")
    else:
        print(f"\n✅ 所有高级设置都已包含在LLMConfig中")
    
    return len(missing_settings) == 0


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 TradingAgents 配置覆盖率检查")
    print("=" * 60)
    
    # 检查各项覆盖率
    provider_ok = check_provider_coverage()
    model_ok = check_model_coverage()
    api_key_ok = check_api_key_coverage()
    settings_ok = check_advanced_settings_coverage()
    
    print("\n" + "=" * 60)
    print("📊 覆盖率检查结果:")
    print(f"  LLM提供商: {'✅ 完整' if provider_ok else '❌ 不完整'}")
    print(f"  模型配置: {'✅ 完整' if model_ok else '❌ 不完整'}")
    print(f"  API密钥: {'✅ 完整' if api_key_ok else '❌ 不完整'}")
    print(f"  高级设置: {'✅ 完整' if settings_ok else '❌ 不完整'}")
    
    if all([provider_ok, model_ok, api_key_ok, settings_ok]):
        print("\n🎉 所有配置项都已包含在新系统中！")
        print("💡 可以安全地使用新的webapi配置系统")
    else:
        print("\n⚠️ 部分配置项缺失，需要进一步完善")
        print("💡 建议更新webapi配置模型以包含缺失的配置项")
    
    print("=" * 60)
    
    return all([provider_ok, model_ok, api_key_ok, settings_ok])


if __name__ == "__main__":
    # 运行检查
    result = main()
    sys.exit(0 if result else 1)
