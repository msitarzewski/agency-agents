#!/usr/bin/env python3
"""
快速测试修复效果
"""

import requests
import time
import json

def quick_test():
    """快速测试修复效果"""
    print("🔍 快速测试修复效果")
    print("=" * 60)
    
    # API基础URL
    base_url = "http://localhost:8000"
    
    try:
        # 1. 登录获取token
        print("1. 登录获取token...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result["data"]["access_token"]
            print("✅ 登录成功，获取到token")
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        # 2. 提交分析请求
        print("\n2. 提交分析请求...")
        analysis_request = {
            "stock_code": "000007",  # 使用新的股票代码
            "parameters": {
                "market_type": "A股",
                "analysis_date": "2025-08-20",
                "research_depth": "快速",
                "selected_analysts": ["market"],  # 只选择一个分析师进行快速测试
                "include_sentiment": False,
                "include_risk": False,
                "language": "zh-CN",
                "quick_analysis_model": "qwen-turbo",
                "deep_analysis_model": "qwen-max"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(
            f"{base_url}/api/analysis/single",
            json=analysis_request,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["data"]["task_id"]
            print(f"✅ 分析任务已提交: {task_id}")
        else:
            print(f"❌ 提交分析请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
        
        # 3. 等待任务完成
        print(f"\n3. 等待任务完成...")
        for i in range(60):  # 最多等待5分钟
            status_response = requests.get(
                f"{base_url}/api/analysis/tasks/{task_id}/status",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data["data"]["status"]
                progress = status_data["data"].get("progress", 0)
                message = status_data["data"].get("message", "")
                
                print(f"   状态: {status}, 进度: {progress}%, 消息: {message}")
                
                if status == "completed":
                    print("✅ 分析任务完成!")
                    return True
                elif status == "failed":
                    print(f"❌ 分析任务失败: {message}")
                    return False
            
            time.sleep(5)
        
        print(f"⏰ 任务执行超时")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 快速测试成功!")
    else:
        print("\n💥 快速测试失败!")
