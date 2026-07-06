"""
检查数据库中 gemini-2.5-flash 的 provider 配置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from app.core.config import settings

# 连接 MongoDB
client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]
collection = db.system_configs

# 查询最新的活跃配置
doc = collection.find_one({"is_active": True}, sort=[("version", -1)])

if not doc:
    print("❌ 未找到活跃的系统配置")
    sys.exit(1)

print(f"✅ 找到系统配置，版本: {doc.get('version')}")
print(f"   is_active: {doc.get('is_active')}")
print(f"   llm_configs 数量: {len(doc.get('llm_configs', []))}")

# 查找 gemini-2.5-flash
llm_configs = doc.get('llm_configs', [])
gemini_flash = None

for config in llm_configs:
    if config.get('model_name') == 'gemini-2.5-flash':
        gemini_flash = config
        break

if gemini_flash:
    print(f"\n✅ 找到 gemini-2.5-flash 配置:")
    print(f"   provider: {gemini_flash.get('provider')}")
    print(f"   model_name: {gemini_flash.get('model_name')}")
    print(f"   api_base: {gemini_flash.get('api_base')}")
    print(f"   enabled: {gemini_flash.get('enabled')}")
    print(f"   features: {gemini_flash.get('features')}")
else:
    print(f"\n❌ 未找到 gemini-2.5-flash 配置")
    print(f"\n所有模型列表:")
    for config in llm_configs:
        print(f"   - {config.get('provider')}: {config.get('model_name')}")

client.close()

