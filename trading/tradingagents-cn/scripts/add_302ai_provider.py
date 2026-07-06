#!/usr/bin/env python3
"""
添加 302.AI 供应商到数据库
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import init_db, get_mongo_db

async def add_302ai_provider():
    """添加 302.AI 供应商"""
    print("🚀 开始添加 302.AI 供应商...")
    
    # 初始化数据库连接
    await init_db()
    db = get_mongo_db()
    providers_collection = db.llm_providers
    
    # 检查是否已存在
    existing = await providers_collection.find_one({"name": "302ai"})
    if existing:
        print("⚠️  302.AI 供应商已存在，跳过添加")
        print(f"   ID: {existing['_id']}")
        print(f"   名称: {existing.get('display_name')}")
        return
    
    # 302.AI 供应商数据
    provider_data = {
        "name": "302ai",
        "display_name": "302.AI",
        "description": "302.AI是企业级AI聚合平台，提供多种主流大模型的统一接口",
        "website": "https://302.ai",
        "api_doc_url": "https://doc.302.ai",
        "default_base_url": "https://api.302.ai/v1",
        "is_active": True,
        "supported_features": ["chat", "completion", "embedding", "image", "vision", "function_calling", "streaming"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # 插入数据
    result = await providers_collection.insert_one(provider_data)
    print(f"✅ 成功添加 302.AI 供应商")
    print(f"   ID: {result.inserted_id}")
    print(f"   名称: {provider_data['display_name']}")
    print(f"   Base URL: {provider_data['default_base_url']}")
    print(f"   支持功能: {', '.join(provider_data['supported_features'])}")

if __name__ == "__main__":
    asyncio.run(add_302ai_provider())

