"""
测试供应商查找功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.simple_analysis_service import get_provider_and_url_by_model_sync

def test_provider_lookup():
    """测试供应商和 URL 查找（同步版本）"""

    test_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "qwen-plus",
        "gpt-4o",
        "deepseek-chat",
        "unknown-model"  # 测试未知模型
    ]

    print("=" * 80)
    print("测试：供应商和 URL 查找功能（同步版本）")
    print("=" * 80)

    for model in test_models:
        info = get_provider_and_url_by_model_sync(model)
        print(f"\n模型: {model}")
        print(f"  -> 供应商: {info['provider']}")
        print(f"  -> API URL: {info['backend_url']}")

if __name__ == "__main__":
    test_provider_lookup()

