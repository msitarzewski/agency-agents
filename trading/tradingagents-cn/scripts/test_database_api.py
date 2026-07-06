#!/usr/bin/env python3
"""
测试数据库管理 API 接口
"""
import asyncio
import httpx
import json
from typing import Dict, Any


BASE_URL = "http://127.0.0.1:8000"
TOKEN = None  # 将在登录后设置


async def login() -> str:
    """登录并获取 token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.text}\n")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("access_token")
        else:
            raise Exception(f"登录失败: {response.text}")


async def test_database_status(token: str):
    """测试数据库状态接口"""
    print("=" * 80)
    print("测试: GET /api/system/database/status")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/system/database/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()


async def test_database_stats(token: str):
    """测试数据库统计接口"""
    print("=" * 80)
    print("测试: GET /api/system/database/stats")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        import time
        start_time = time.time()
        
        response = await client.get(
            f"{BASE_URL}/api/system/database/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"耗时: {elapsed_time:.2f} 秒")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容:")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 验证数据结构
            print("\n" + "=" * 80)
            print("数据结构验证:")
            print("=" * 80)
            
            if "success" in data:
                print(f"✅ 包含 'success' 字段: {data['success']}")
            else:
                print("❌ 缺少 'success' 字段")
            
            if "data" in data:
                print(f"✅ 包含 'data' 字段")
                stats_data = data["data"]
                
                if "total_collections" in stats_data:
                    print(f"  - total_collections: {stats_data['total_collections']}")
                else:
                    print("  ❌ 缺少 'total_collections' 字段")
                
                if "total_documents" in stats_data:
                    print(f"  - total_documents: {stats_data['total_documents']}")
                else:
                    print("  ❌ 缺少 'total_documents' 字段")
                
                if "total_size" in stats_data:
                    print(f"  - total_size: {stats_data['total_size']}")
                else:
                    print("  ❌ 缺少 'total_size' 字段")
                
                if "collections" in stats_data:
                    print(f"  - collections: {len(stats_data['collections'])} 个集合")
                    if stats_data['collections']:
                        print(f"    第一个集合示例: {stats_data['collections'][0]}")
                else:
                    print("  ❌ 缺少 'collections' 字段")
            else:
                print("❌ 缺少 'data' 字段")
            
            if "message" in data:
                print(f"✅ 包含 'message' 字段: {data['message']}")
            else:
                print("❌ 缺少 'message' 字段")
        else:
            print(response.text)
        
        print()


async def test_database_test_connection(token: str):
    """测试数据库连接测试接口"""
    print("=" * 80)
    print("测试: POST /api/system/database/test")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/system/database/test",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print()


async def main():
    """主函数"""
    try:
        # 1. 登录
        print("🔐 正在登录...")
        token = await login()
        print(f"✅ 登录成功，Token: {token[:20]}...\n")
        
        # 2. 测试数据库状态接口
        await test_database_status(token)
        
        # 3. 测试数据库统计接口
        await test_database_stats(token)
        
        # 4. 测试数据库连接测试接口
        await test_database_test_connection(token)
        
        print("=" * 80)
        print("✅ 所有测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

