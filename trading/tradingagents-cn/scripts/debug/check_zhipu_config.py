#!/usr/bin/env python3
"""检查智谱AI配置"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient('mongodb://admin:tradingagents123@localhost:27017/')
    db = client['tradingagents']
    
    provider = await db.llm_providers.find_one({'name': 'zhipu'})
    
    if provider:
        print(f"✅ 找到智谱AI配置:")
        print(f"   ID: {provider['_id']}")
        print(f"   名称: {provider.get('display_name')}")
        print(f"   base_url: {provider.get('default_base_url')}")
        print(f"   API密钥: {'已配置' if provider.get('api_key') else '未配置'}")
    else:
        print("❌ 未找到智谱AI配置")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())

