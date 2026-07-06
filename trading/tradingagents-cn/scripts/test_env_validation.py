"""
测试 .env 文件中的 API Key 验证

验证占位符是否被正确识别为"未配置"
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from app.core.startup_validator import StartupValidator


def test_env_validation():
    """测试 .env 文件中的 API Key 验证"""
    
    print("\n" + "=" * 80)
    print("🧪 .env 文件 API Key 验证测试")
    print("=" * 80)
    
    # 检查 .env 文件中的 API Key
    api_keys_to_check = [
        ("DASHSCOPE_API_KEY", "通义千问 API"),
        ("DEEPSEEK_API_KEY", "DeepSeek API"),
        ("OPENAI_API_KEY", "OpenAI API"),
        ("ANTHROPIC_API_KEY", "Anthropic API"),
        ("GOOGLE_API_KEY", "Google API"),
        ("QIANFAN_API_KEY", "千帆 API"),
        ("OPENROUTER_API_KEY", "OpenRouter API"),
        ("TUSHARE_TOKEN", "Tushare Token"),
    ]
    
    validator = StartupValidator()
    
    print("\n📋 环境变量中的 API Key 状态:")
    print("-" * 80)
    
    for env_key, display_name in api_keys_to_check:
        value = os.getenv(env_key, "")
        
        if not value:
            status = "❌ 未设置"
            validation = "N/A"
        else:
            is_valid = validator._is_valid_api_key(value)
            status = "✅ 已设置" if value else "❌ 未设置"
            validation = "✅ 有效" if is_valid else "❌ 占位符/无效"
            
            # 显示前 30 个字符
            display_value = value[:30] + "..." if len(value) > 30 else value
        
        print(f"{display_name:20s} | {status:10s} | 验证: {validation:15s}", end="")
        if value:
            print(f" | 值: {display_value}")
        else:
            print()
    
    print("-" * 80)
    
    # 运行完整验证
    print("\n🔍 运行完整配置验证...")
    print("-" * 80)
    
    result = validator.validate()
    
    print("\n📊 验证结果摘要:")
    print("-" * 80)
    print(f"✅ 验证通过: {result.success}")
    print(f"❌ 缺少必需配置: {len(result.missing_required)}")
    print(f"⚠️  缺少推荐配置: {len(result.missing_recommended)}")
    print(f"❌ 无效配置: {len(result.invalid_configs)}")
    print(f"⚠️  警告: {len(result.warnings)}")
    
    if result.missing_recommended:
        print("\n⚠️  缺少的推荐配置:")
        for config in result.missing_recommended:
            print(f"  - {config.key}: {config.description}")
    
    if result.warnings:
        print("\n⚠️  警告信息:")
        for warning in result.warnings:
            print(f"  - {warning}")
    
    print("=" * 80)
    
    # 验证占位符是否被正确识别
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    placeholder_detected = False
    
    if openai_key and not validator._is_valid_api_key(openai_key):
        print(f"\n✅ 正确识别 OPENAI_API_KEY 为占位符: {openai_key}")
        placeholder_detected = True
    
    if anthropic_key and not validator._is_valid_api_key(anthropic_key):
        print(f"✅ 正确识别 ANTHROPIC_API_KEY 为占位符: {anthropic_key}")
        placeholder_detected = True
    
    if placeholder_detected:
        print("\n🎉 占位符检测功能正常工作！")
    else:
        print("\n⚠️  未检测到占位符（可能所有 API Key 都是有效的）")
    
    print("=" * 80)


if __name__ == "__main__":
    test_env_validation()

