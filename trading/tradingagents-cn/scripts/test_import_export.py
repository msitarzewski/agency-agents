#!/usr/bin/env python3
"""
测试数据库导入导出功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from app.core.database import get_mongo_db_sync

async def test_export_import():
    """测试导出和导入功能"""
    print("=" * 80)
    print("📊 测试数据库导入导出功能")
    print("=" * 80)
    
    # 获取数据库连接
    db = get_mongo_db_sync()
    
    # 1. 导出测试数据
    print("\n1️⃣ 导出测试数据")
    print("-" * 80)
    
    # 导出 system_configs 集合
    configs = list(db.system_configs.find({"is_active": True}).limit(1))
    
    if not configs:
        print("❌ 没有找到激活的配置")
        return
    
    config = configs[0]
    print(f"✅ 找到激活的配置（版本 {config.get('version')}）")
    
    # 序列化为 JSON
    def serialize_doc(doc):
        """序列化文档"""
        from bson import ObjectId
        from datetime import datetime
        
        if isinstance(doc, dict):
            return {k: serialize_doc(v) for k, v in doc.items()}
        elif isinstance(doc, list):
            return [serialize_doc(item) for item in doc]
        elif isinstance(doc, ObjectId):
            return str(doc)
        elif isinstance(doc, datetime):
            return doc.isoformat()
        else:
            return doc
    
    serialized_config = serialize_doc(config)
    
    # 保存到文件
    export_file = Path("data/test_export.json")
    export_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(export_file, 'w', encoding='utf-8') as f:
        json.dump({"system_configs": [serialized_config]}, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 导出数据到文件: {export_file}")
    print(f"   文件大小: {export_file.stat().st_size / 1024:.2f} KB")
    
    # 2. 测试导入
    print("\n2️⃣ 测试导入数据")
    print("-" * 80)
    
    # 读取导出的文件
    with open(export_file, 'r', encoding='utf-8') as f:
        import_data = json.load(f)
    
    print(f"✅ 读取导入文件成功")
    print(f"   包含集合: {list(import_data.keys())}")
    print(f"   system_configs 文档数: {len(import_data['system_configs'])}")
    
    # 3. 验证导入数据格式
    print("\n3️⃣ 验证导入数据格式")
    print("-" * 80)
    
    # 检测是否为多集合导出格式
    is_multi_collection = isinstance(import_data, dict) and all(
        isinstance(k, str) and isinstance(v, list) 
        for k, v in import_data.items()
    )
    
    if is_multi_collection:
        print("✅ 检测到多集合导出格式")
        for coll_name, documents in import_data.items():
            print(f"   - {coll_name}: {len(documents)} 条文档")
    else:
        print("❌ 不是多集合导出格式")
    
    # 4. 检查数据源配置
    print("\n4️⃣ 检查数据源配置")
    print("-" * 80)
    
    if 'system_configs' in import_data:
        config_doc = import_data['system_configs'][0]
        data_source_configs = config_doc.get('data_source_configs', [])
        
        print(f"✅ 数据源配置数量: {len(data_source_configs)}")
        
        for ds in data_source_configs:
            name = ds.get('name', 'N/A')
            ds_type = ds.get('type', 'N/A')
            enabled = ds.get('enabled', False)
            has_api_key = bool(ds.get('api_key'))
            
            status = "✅" if enabled else "❌"
            api_key_status = "🔑" if has_api_key else "🔓"
            
            print(f"   {status} {api_key_status} {name} ({ds_type})")
    
    # 5. 检查市场分类配置
    print("\n5️⃣ 检查市场分类配置")
    print("-" * 80)
    
    if 'system_configs' in import_data:
        config_doc = import_data['system_configs'][0]
        market_categories = config_doc.get('market_categories', [])
        
        print(f"✅ 市场分类数量: {len(market_categories)}")
        
        for cat in market_categories:
            cat_id = cat.get('id', 'N/A')
            name = cat.get('name', 'N/A')
            enabled = cat.get('enabled', False)
            
            status = "✅" if enabled else "❌"
            print(f"   {status} {name} ({cat_id})")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_export_import())

