#!/usr/bin/env python3
"""
直接从.env文件迁移API密钥到数据库
"""

import asyncio
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env文件已加载")
except ImportError:
    print("❌ python-dotenv未安装，手动加载.env")
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ 手动加载.env文件完成")

from app.core.database import init_db, get_mongo_db

async def migrate_env_direct():
    """直接从.env迁移API密钥到数据库"""
    print("🚀 开始直接迁移.env中的API密钥到数据库...")
    
    # 初始化数据库连接
    await init_db()
    db = get_mongo_db()
    providers_collection = db.llm_providers
    
    # API密钥映射表
    api_key_mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "zhipu": "ZHIPU_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
        "qianfan": "QIANFAN_API_KEY",  # 修正为QIANFAN_API_KEY
        "azure": "AZURE_OPENAI_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    
    updated_count = 0
    created_count = 0
    skipped_count = 0
    
    print("\n📋 处理API密钥:")
    print("-" * 60)
    
    for provider_name, env_var in api_key_mapping.items():
        api_key = os.getenv(env_var)
        
        # 跳过空值和占位符
        if not api_key or api_key.startswith('your_'):
            print(f"⏭️ 跳过 {provider_name}: 无有效API密钥")
            skipped_count += 1
            continue
        
        print(f"🔑 处理 {provider_name}: {api_key[:10]}...")
        
        # 查找现有厂家配置
        existing = await providers_collection.find_one({"name": provider_name})
        
        if existing:
            # 更新现有厂家的API密钥
            update_data = {
                "api_key": api_key,
                "is_active": True,  # 有API密钥的自动启用
                "extra_config": {"source": "environment", "migrated_at": datetime.utcnow().isoformat()},
                "updated_at": datetime.utcnow()
            }
            
            await providers_collection.update_one(
                {"name": provider_name},
                {"$set": update_data}
            )
            
            print(f"✅ 更新厂家 {existing.get('display_name', provider_name)} 的API密钥")
            updated_count += 1
        else:
            # 创建新厂家配置
            # 厂家基本信息映射
            provider_info = {
                "openai": {
                    "display_name": "OpenAI",
                    "description": "OpenAI是人工智能领域的领先公司，提供GPT系列模型",
                    "website": "https://openai.com",
                    "api_doc_url": "https://platform.openai.com/docs",
                    "default_base_url": "https://api.openai.com/v1",
                    "supported_features": ["chat", "completion", "embedding", "image", "vision", "function_calling", "streaming"]
                },
                "anthropic": {
                    "display_name": "Anthropic",
                    "description": "Anthropic专注于AI安全研究，提供Claude系列模型",
                    "website": "https://anthropic.com",
                    "api_doc_url": "https://docs.anthropic.com",
                    "default_base_url": "https://api.anthropic.com",
                    "supported_features": ["chat", "completion", "function_calling", "streaming"]
                },
                "google": {
                    "display_name": "Google AI",
                    "description": "Google的人工智能平台，提供Gemini系列模型",
                    "website": "https://ai.google.dev",
                    "api_doc_url": "https://ai.google.dev/docs",
                    "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
                    "supported_features": ["chat", "completion", "embedding", "vision", "function_calling", "streaming"]
                },
                "deepseek": {
                    "display_name": "DeepSeek",
                    "description": "DeepSeek提供高性能的AI推理服务",
                    "website": "https://www.deepseek.com",
                    "api_doc_url": "https://platform.deepseek.com/api-docs",
                    "default_base_url": "https://api.deepseek.com",
                    "supported_features": ["chat", "completion", "function_calling", "streaming"]
                },
                "dashscope": {
                    "display_name": "阿里云百炼",
                    "description": "阿里云百炼大模型服务平台，提供通义千问等模型",
                    "website": "https://bailian.console.aliyun.com",
                    "api_doc_url": "https://help.aliyun.com/zh/dashscope/",
                    "default_base_url": "https://dashscope.aliyuncs.com/api/v1",
                    "supported_features": ["chat", "completion", "embedding", "function_calling", "streaming"]
                },
                "openrouter": {
                    "display_name": "OpenRouter",
                    "description": "OpenRouter提供多种AI模型的统一API接口",
                    "website": "https://openrouter.ai",
                    "api_doc_url": "https://openrouter.ai/docs",
                    "default_base_url": "https://openrouter.ai/api/v1",
                    "supported_features": ["chat", "completion", "function_calling", "streaming"]
                },
                "qianfan": {
                    "display_name": "百度千帆",
                    "description": "百度千帆大模型平台，提供文心一言等模型",
                    "website": "https://qianfan.cloud.baidu.com",
                    "api_doc_url": "https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html",
                    "default_base_url": "https://qianfan.baidubce.com/v2",
                    "supported_features": ["chat", "completion", "function_calling", "streaming"]
                }
            }
            
            info = provider_info.get(provider_name, {
                "display_name": provider_name.title(),
                "description": f"{provider_name} AI服务",
                "supported_features": ["chat", "completion"]
            })
            
            provider_data = {
                "name": provider_name,
                "api_key": api_key,
                "is_active": True,
                "extra_config": {"source": "environment", "migrated_at": datetime.utcnow().isoformat()},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **info
            }
            
            await providers_collection.insert_one(provider_data)
            print(f"✅ 创建新厂家 {info['display_name']} 并设置API密钥")
            created_count += 1
    
    print(f"\n🎉 迁移完成!")
    print(f"📊 统计:")
    print(f"   - 创建新厂家: {created_count}")
    print(f"   - 更新现有厂家: {updated_count}")
    print(f"   - 跳过: {skipped_count}")
    
    total_changes = created_count + updated_count
    if total_changes > 0:
        print(f"\n✅ 总共处理了 {total_changes} 个厂家的API密钥")
        print("🔄 请刷新前端页面查看更新结果")
    else:
        print("\n⏭️ 没有找到有效的API密钥需要迁移")

if __name__ == "__main__":
    asyncio.run(migrate_env_direct())
