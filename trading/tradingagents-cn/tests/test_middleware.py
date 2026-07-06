#!/usr/bin/env python3
"""
测试操作日志中间件
"""

import asyncio
import sys
import os
import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_middleware():
    """测试中间件是否正常工作"""
    print("🧪 测试操作日志中间件...")
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # 测试1: 登录请求
            print("\n🔐 测试1: 登录请求")
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = await client.post(f"{base_url}/api/auth/login", json=login_data)
            print(f"登录响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data["data"]["access_token"]
                print("✅ 登录成功，获取到token")
                
                # 测试2: 使用token进行认证请求
                print("\n📊 测试2: 获取操作日志列表")
                headers = {"Authorization": f"Bearer {token}"}
                
                logs_response = await client.get(
                    f"{base_url}/api/system/logs/list", 
                    headers=headers
                )
                print(f"获取日志响应状态: {logs_response.status_code}")
                
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    total_logs = logs_data["data"]["total"]
                    print(f"✅ 获取日志成功，总数: {total_logs}")
                    
                    # 显示最近的几条日志
                    logs = logs_data["data"]["logs"]
                    print("📝 最近的日志:")
                    for log in logs[:5]:
                        print(f"  - {log['timestamp']} | {log['username']} | {log['action']} | {'✅' if log['success'] else '❌'}")
                else:
                    print(f"❌ 获取日志失败: {logs_response.text}")
                
                # 测试3: 登出请求
                print("\n🚪 测试3: 登出请求")
                logout_response = await client.post(
                    f"{base_url}/api/auth/logout",
                    headers=headers
                )
                print(f"登出响应状态: {logout_response.status_code}")
                
                if logout_response.status_code == 200:
                    print("✅ 登出成功")
                else:
                    print(f"❌ 登出失败: {logout_response.text}")
                
            else:
                print(f"❌ 登录失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_middleware())
