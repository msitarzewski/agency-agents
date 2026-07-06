#!/usr/bin/env python3
"""
通过API创建默认用户
"""

import requests
import json
import time

# API基础URL
API_BASE = "http://localhost:8000/api"

def create_user_via_api(username: str, email: str, password: str):
    """通过API创建用户"""
    try:
        # 注册用户
        register_data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        
        if response.status_code == 200:
            print(f"✅ 用户 {username} 创建成功")
            return True
        else:
            error_detail = response.json().get('detail', '未知错误')
            print(f"❌ 用户 {username} 创建失败: {error_detail}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 创建用户 {username} 时出错: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始创建默认用户...")
    print("📍 API地址:", API_BASE)
    
    # 检查API服务是否运行
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code != 200:
            print("❌ API服务未正常运行")
            return
        print("✅ API服务运行正常")
    except:
        print("❌ 无法连接到API服务，请先启动后端服务:")
        print("   python -m uvicorn webapi.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # 创建默认用户
    users_to_create = [
        {
            "username": "admin",
            "email": "admin@tradingagents.cn",
            "password": "admin123"
        },
        {
            "username": "user",
            "email": "user@tradingagents.cn", 
            "password": "user123"
        }
    ]
    
    created_count = 0
    for user_data in users_to_create:
        if create_user_via_api(**user_data):
            created_count += 1
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n🎉 用户创建完成！成功创建 {created_count} 个用户")
    
    if created_count > 0:
        print("\n📋 默认用户信息:")
        print("   - admin / admin123 (管理员)")
        print("   - user / user123 (普通用户)")
        print("\n💡 提示: 现在可以使用这些账号登录前端系统")
    else:
        print("\n⚠️ 没有创建任何用户，可能用户已存在或API有问题")

if __name__ == "__main__":
    main()
