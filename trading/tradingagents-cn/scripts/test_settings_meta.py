#!/usr/bin/env python3
"""
测试系统设置元数据 API
"""

import requests
import json

def main():
    """主函数"""
    print("=" * 60)
    print("📊 测试系统设置元数据 API")
    print("=" * 60)
    
    try:
        # 登录获取 token
        login_response = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return
        
        token = login_response.json().get("data", {}).get("access_token")
        if not token:
            print(f"❌ 无法获取 token")
            return
        
        # 获取元数据
        response = requests.get(
            "http://127.0.0.1:8000/api/config/settings/meta",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            meta_response = response.json()
            items = meta_response.get("data", {}).get("items", [])
            
            print(f"\n✅ 获取到 {len(items)} 个设置的元数据\n")
            
            # 查找模型相关的元数据
            print("模型相关的元数据:")
            for item in items:
                key = item.get("key")
                if "model" in key.lower():
                    print(f"\n  {key}:")
                    print(f"    editable: {item.get('editable')}")
                    print(f"    sensitive: {item.get('sensitive')}")
                    print(f"    source: {item.get('source')}")
                    print(f"    has_value: {item.get('has_value')}")
            
            # 检查是否有 quick_analysis_model 和 deep_analysis_model
            quick_meta = next((item for item in items if item.get("key") == "quick_analysis_model"), None)
            deep_meta = next((item for item in items if item.get("key") == "deep_analysis_model"), None)
            
            print(f"\n\n检查关键字段:")
            print(f"  quick_analysis_model 元数据: {quick_meta}")
            print(f"  deep_analysis_model 元数据: {deep_meta}")
            
        else:
            print(f"\n❌ API 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

