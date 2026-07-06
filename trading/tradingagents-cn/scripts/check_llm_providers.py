"""
检查 llm_providers 集合的数据结构
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from app.core.config import settings
import json

# 连接 MongoDB
client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

print("=" * 80)
print("检查 llm_providers 集合")
print("=" * 80)

providers_collection = db.llm_providers
providers = list(providers_collection.find())

print(f"\n总共有 {len(providers)} 个厂家配置\n")

for provider in providers:
    print(f"厂家: {provider.get('name')}")
    print(f"  display_name: {provider.get('display_name')}")
    print(f"  default_base_url: {provider.get('default_base_url')}")
    print(f"  api_key_env: {provider.get('api_key_env')}")
    print(f"  enabled: {provider.get('enabled')}")
    print()

print("=" * 80)
print("检查 system_configs.llm_configs")
print("=" * 80)

configs_collection = db.system_configs
doc = configs_collection.find_one({"is_active": True}, sort=[("version", -1)])

if doc and "llm_configs" in doc:
    llm_configs = doc["llm_configs"]
    print(f"\n总共有 {len(llm_configs)} 个模型配置\n")
    
    # 查找 gemini-2.5-flash
    for config in llm_configs:
        if config.get('model_name') == 'gemini-2.5-flash':
            print(f"gemini-2.5-flash 配置:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            break

client.close()

