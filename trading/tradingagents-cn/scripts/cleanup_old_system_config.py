"""
清理脚本：删除旧的 system_config 集合

这个脚本会：
1. 检查 system_config 集合是否存在
2. 检查集合中是否有数据
3. 如果没有数据或数据已过时，删除集合
4. 确认 system_configs 集合正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from app.core.config import settings
import json
from datetime import datetime


def check_and_cleanup():
    """检查并清理旧的 system_config 集合"""
    
    print("=" * 80)
    print("🔍 MongoDB 集合清理脚本")
    print("=" * 80)
    
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    
    # 列出所有集合
    print(f"\n📋 数据库中的集合：")
    collections = db.list_collection_names()
    for coll in sorted(collections):
        print(f"  - {coll}")
    
    # 检查 system_config 集合（旧版本，单数）
    print(f"\n" + "=" * 80)
    print(f"检查：system_config 集合（旧版本，单数）")
    print("=" * 80)
    
    if "system_config" in collections:
        print(f"✅ system_config 集合存在")
        
        collection = db.system_config
        
        # 查询所有文档
        docs = list(collection.find())
        count = len(docs)
        print(f"📊 system_config 集合中的文档数量: {count}")
        
        if count > 0:
            print(f"\n📄 文档内容：")
            for i, doc in enumerate(docs, 1):
                print(f"\n  文档 {i}:")
                print(f"    _id: {doc.get('_id')}")
                print(f"    key: {doc.get('key')}")
                print(f"    value: {doc.get('value')}")
                print(f"    description: {doc.get('description')}")
                print(f"    updated_at: {doc.get('updated_at')}")
            
            # 询问是否删除
            print(f"\n⚠️  system_config 集合中有 {count} 条数据")
            print(f"⚠️  这些数据可能已经过时，新系统使用 system_configs 集合")
            response = input(f"\n是否删除 system_config 集合？(yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                collection.drop()
                print(f"✅ 已删除 system_config 集合")
            else:
                print(f"⏭️  跳过删除")
        else:
            print(f"\n✅ system_config 集合为空")
            response = input(f"是否删除空集合？(yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                collection.drop()
                print(f"✅ 已删除 system_config 集合")
            else:
                print(f"⏭️  跳过删除")
    else:
        print(f"✅ system_config 集合不存在（已清理）")
    
    # 检查 system_configs 集合（新版本，复数）
    print(f"\n" + "=" * 80)
    print(f"检查：system_configs 集合（新版本，复数）")
    print("=" * 80)
    
    if "system_configs" in collections:
        print(f"✅ system_configs 集合存在")
        
        collection = db.system_configs
        
        # 查询激活的配置
        active_config = collection.find_one({"is_active": True}, sort=[("version", -1)])
        
        if active_config:
            print(f"\n📊 激活的配置：")
            print(f"  _id: {active_config.get('_id')}")
            print(f"  config_name: {active_config.get('config_name')}")
            print(f"  config_type: {active_config.get('config_type')}")
            print(f"  version: {active_config.get('version')}")
            print(f"  is_active: {active_config.get('is_active')}")
            print(f"  created_at: {active_config.get('created_at')}")
            print(f"  updated_at: {active_config.get('updated_at')}")
            
            # 统计配置数量
            llm_configs = active_config.get('llm_configs', [])
            data_source_configs = active_config.get('data_source_configs', [])
            database_configs = active_config.get('database_configs', [])
            system_settings = active_config.get('system_settings', {})
            
            print(f"\n📋 配置统计：")
            print(f"  LLM 配置: {len(llm_configs)} 个")
            print(f"  数据源配置: {len(data_source_configs)} 个")
            print(f"  数据库配置: {len(database_configs)} 个")
            print(f"  系统设置: {len(system_settings)} 项")
            
            # 显示启用的 LLM
            enabled_llms = [llm for llm in llm_configs if llm.get('enabled', False)]
            if enabled_llms:
                print(f"\n✅ 启用的 LLM：")
                for llm in enabled_llms:
                    print(f"  - {llm.get('provider')}: {llm.get('model_name')}")
            
            # 显示启用的数据源
            enabled_data_sources = [ds for ds in data_source_configs if ds.get('enabled', False)]
            if enabled_data_sources:
                print(f"\n✅ 启用的数据源：")
                for ds in enabled_data_sources:
                    print(f"  - {ds.get('type')}: {ds.get('name')}")
            
            print(f"\n✅ system_configs 集合正常工作")
        else:
            print(f"\n⚠️  未找到激活的配置")
            print(f"⚠️  请检查配置是否正确初始化")
    else:
        print(f"❌ system_configs 集合不存在")
        print(f"❌ 请检查应用是否正确初始化")
    
    # 检查 model_config 集合（也是旧版本）
    print(f"\n" + "=" * 80)
    print(f"检查：model_config 集合（旧版本，单数）")
    print("=" * 80)
    
    if "model_config" in collections:
        print(f"✅ model_config 集合存在")
        
        collection = db.model_config
        count = collection.count_documents({})
        print(f"📊 model_config 集合中的文档数量: {count}")
        
        if count > 0:
            print(f"\n⚠️  model_config 集合中有 {count} 条数据")
            print(f"⚠️  这些数据可能已经过时，新系统使用 system_configs.llm_configs")
            response = input(f"\n是否删除 model_config 集合？(yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                collection.drop()
                print(f"✅ 已删除 model_config 集合")
            else:
                print(f"⏭️  跳过删除")
        else:
            print(f"\n✅ model_config 集合为空")
            response = input(f"是否删除空集合？(yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                collection.drop()
                print(f"✅ 已删除 model_config 集合")
            else:
                print(f"⏭️  跳过删除")
    else:
        print(f"✅ model_config 集合不存在（已清理）")
    
    # 最终总结
    print(f"\n" + "=" * 80)
    print(f"✅ 清理完成")
    print("=" * 80)
    
    # 再次列出所有集合
    print(f"\n📋 清理后的集合：")
    collections = db.list_collection_names()
    for coll in sorted(collections):
        print(f"  - {coll}")
    
    client.close()
    
    print(f"\n" + "=" * 80)
    print(f"🎉 脚本执行完成")
    print("=" * 80)


if __name__ == "__main__":
    try:
        check_and_cleanup()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

