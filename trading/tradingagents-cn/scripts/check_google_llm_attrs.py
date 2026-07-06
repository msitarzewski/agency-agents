"""
检查 ChatGoogleOpenAI 的属性
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['GOOGLE_API_KEY'] = 'test-key'

from tradingagents.llm_adapters import ChatGoogleOpenAI

# 创建实例
llm = ChatGoogleOpenAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=4000
)

print("=" * 80)
print("ChatGoogleOpenAI 实例属性")
print("=" * 80)

# 检查常见的模型名称属性
attrs_to_check = [
    'model',
    'model_name',
    'model_id',
    '_model',
    '__class__.__name__'
]

for attr in attrs_to_check:
    if '.' in attr:
        # 处理嵌套属性
        parts = attr.split('.')
        obj = llm
        try:
            for part in parts:
                obj = getattr(obj, part)
            print(f"✅ {attr}: {obj}")
        except AttributeError:
            print(f"❌ {attr}: 不存在")
    else:
        value = getattr(llm, attr, 'NOT_FOUND')
        if value != 'NOT_FOUND':
            print(f"✅ {attr}: {value}")
        else:
            print(f"❌ {attr}: 不存在")

print("\n" + "=" * 80)
print("测试日志代码")
print("=" * 80)

# 模拟日志代码
model_name_for_log = getattr(llm, 'model_name', 'unknown')
print(f"日志中显示的模型名称: {model_name_for_log}")

print("\n" + "=" * 80)
print("所有属性（前20个）")
print("=" * 80)

all_attrs = [a for a in dir(llm) if not a.startswith('_')]
for i, attr in enumerate(all_attrs[:20]):
    try:
        value = getattr(llm, attr)
        if not callable(value):
            print(f"{attr}: {value}")
    except:
        pass

