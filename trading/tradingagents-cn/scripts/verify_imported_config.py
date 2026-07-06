#!/usr/bin/env python3
"""
验证导入后的配置数据

使用方法：
    # 在测试服务器的 Docker 容器内运行
    docker exec tradingagents-backend python /tmp/verify_imported_config.py
"""

import sys
from pymongo import MongoClient

# MongoDB 连接配置（Docker 容器内）
MONGO_URI = "mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin"
DB_NAME = "tradingagents"


def main():
    """主函数"""
    print("=" * 80)
    print("验证导入后的配置数据")
    print("=" * 80)
    
    # 连接数据库
    print(f"\n🔌 连接到 MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"✅ MongoDB 连接成功")
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        return 1
    
    db = client[DB_NAME]
    
    # 检查 system_configs
    print(f"\n📋 检查 system_configs 集合:")
    system_configs = db.system_configs.find_one()
    
    if not system_configs:
        print(f"❌ system_configs 集合为空！")
        return 1
    
    print(f"   配置名称: {system_configs.get('config_name')}")
    print(f"   配置类型: {system_configs.get('config_type')}")
    print(f"   默认 LLM: {system_configs.get('default_llm')}")
    print(f"   默认数据源: {system_configs.get('default_data_source')}")
    
    # 检查 LLM 配置数量
    llm_configs = system_configs.get('llm_configs', [])
    print(f"\n   📊 LLM 配置数量: {len(llm_configs)}")
    
    if len(llm_configs) == 0:
        print(f"   ❌ 错误：LLM 配置为空！")
        return 1
    elif len(llm_configs) < 17:
        print(f"   ⚠️  警告：LLM 配置数量不足（期望 17 个，实际 {len(llm_configs)} 个）")
    else:
        print(f"   ✅ LLM 配置数量正确")
    
    # 显示所有 LLM 配置
    print(f"\n   📝 LLM 配置列表:")
    for i, llm in enumerate(llm_configs, 1):
        provider = llm.get('provider', 'N/A')
        model_name = llm.get('model_name', 'N/A')
        enabled = llm.get('enabled', False)
        max_tokens = llm.get('max_tokens', 'N/A')
        print(f"      {i:2d}. {provider:15s} / {model_name:35s} "
              f"[{'启用' if enabled else '禁用'}] "
              f"max_tokens={max_tokens}")
    
    # 检查数据源配置
    data_source_configs = system_configs.get('data_source_configs', [])
    print(f"\n   📊 数据源配置数量: {len(data_source_configs)}")
    if data_source_configs:
        print(f"   📝 数据源列表:")
        for ds in data_source_configs:
            print(f"      - {ds.get('name')} ({ds.get('type')}): "
                  f"{'启用' if ds.get('enabled') else '禁用'}")
    
    # 检查 llm_providers
    print(f"\n📋 检查 llm_providers 集合:")
    providers_count = db.llm_providers.count_documents({})
    print(f"   文档数量: {providers_count}")
    
    if providers_count > 0:
        providers = db.llm_providers.find({}, {"name": 1, "display_name": 1, "is_active": 1})
        print(f"   📝 Provider 列表:")
        for p in providers:
            print(f"      - {p.get('name'):15s} ({p.get('display_name'):20s}): "
                  f"{'启用' if p.get('is_active') else '禁用'}")
    
    # 检查 model_catalog
    print(f"\n📋 检查 model_catalog 集合:")
    catalog_count = db.model_catalog.count_documents({})
    print(f"   文档数量: {catalog_count}")
    
    if catalog_count > 0:
        catalogs = db.model_catalog.find({}, {"provider": 1, "provider_name": 1, "models": 1})
        print(f"   📝 Catalog 列表:")
        for c in catalogs:
            models_count = len(c.get('models', []))
            print(f"      - {c.get('provider'):15s} ({c.get('provider_name'):20s}): "
                  f"{models_count} 个模型")
    
    # 关闭连接
    client.close()
    
    print("\n" + "=" * 80)
    if len(llm_configs) >= 17:
        print("✅ 验证通过！配置数据完整")
        print("=" * 80)
        return 0
    else:
        print("❌ 验证失败！配置数据不完整")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

