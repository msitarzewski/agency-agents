"""
简单测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.model_capability_service import ModelCapabilityService

service = ModelCapabilityService()

# 测试 gemini-2.5-flash 配置
print("=" * 80)
print("测试：gemini-2.5-flash 配置")
print("=" * 80)

config = service.get_model_config('gemini-2.5-flash')

print(f"\nfeatures: {config['features']}")
print(f"suitable_roles: {config['suitable_roles']}")

# 测试模型验证
print("\n" + "=" * 80)
print("测试：模型对验证")
print("=" * 80)

result = service.validate_model_pair(
    quick_model="gemini-2.5-flash",
    deep_model="qwen-plus",
    research_depth="标准"
)

print(f"\n验证结果:")
print(f"  - valid: {result['valid']}")
print(f"  - warnings: {len(result['warnings'])} 条")
if result['warnings']:
    for i, warning in enumerate(result['warnings'], 1):
        print(f"    {i}. {warning}")

if result['valid']:
    print(f"\n✅ 验证通过！模型对可以使用")
else:
    print(f"\n❌ 验证失败！模型对不适合使用")

