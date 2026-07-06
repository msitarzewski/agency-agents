#!/usr/bin/env python3
"""
测试已有的分析结果
"""

import requests
import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

def get_existing_task_ids():
    """从MongoDB获取已有的任务ID"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 从环境变量获取MongoDB配置
        mongodb_host = os.getenv("MONGODB_HOST", "localhost")
        mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongodb_username = os.getenv("MONGODB_USERNAME")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_database = os.getenv("MONGODB_DATABASE", "tradingagents")
        mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
        
        # 构建连接参数
        connect_kwargs = {
            "host": mongodb_host,
            "port": mongodb_port,
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000
        }

        # 如果有用户名和密码，添加认证信息
        if mongodb_username and mongodb_password:
            connect_kwargs.update({
                "username": mongodb_username,
                "password": mongodb_password,
                "authSource": mongodb_auth_source
            })
        
        # 连接MongoDB
        client = MongoClient(**connect_kwargs)
        db = client[mongodb_database]
        
        # 从analysis_reports集合获取最近的任务
        reports_collection = db['analysis_reports']
        recent_reports = reports_collection.find(
            {"source": "api", "task_id": {"$exists": True}},
            {"task_id": 1, "analysis_id": 1, "stock_symbol": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5)
        
        task_ids = []
        for report in recent_reports:
            task_ids.append({
                "task_id": report.get("task_id"),
                "analysis_id": report.get("analysis_id"),
                "stock_symbol": report.get("stock_symbol"),
                "created_at": report.get("created_at")
            })
        
        client.close()
        return task_ids
        
    except Exception as e:
        print(f"❌ 获取任务ID失败: {e}")
        return []

def test_existing_result(task_id, stock_symbol):
    """测试已有的分析结果"""
    print(f"\n🔍 测试已有结果: {task_id} ({stock_symbol})")
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
            print("✅ 登录成功")
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # 2. 检查任务状态
        print(f"\n2. 检查任务状态...")
        status_response = requests.get(
            f"{base_url}/api/analysis/tasks/{task_id}/status",
            headers=headers
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data["data"]["status"]
            print(f"   任务状态: {status}")
            
            if status != "completed":
                print(f"   ⚠️ 任务未完成，跳过")
                return False
        else:
            print(f"   ❌ 获取状态失败: {status_response.status_code}")
            return False
        
        # 3. 获取分析结果
        print(f"\n3. 获取分析结果...")
        result_response = requests.get(
            f"{base_url}/api/analysis/tasks/{task_id}/result",
            headers=headers
        )
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            data = result_data["data"]
            
            print(f"✅ 成功获取分析结果")
            print(f"   stock_symbol: {data.get('stock_symbol')}")
            print(f"   analysts: {data.get('analysts', [])}")
            print(f"   research_depth: {data.get('research_depth')}")
            
            # 检查reports字段的数据类型
            reports = data.get('reports', {})
            if reports:
                print(f"✅ API返回包含 {len(reports)} 个报告:")
                for report_type, content in reports.items():
                    content_type = type(content).__name__
                    if isinstance(content, str):
                        print(f"   ✅ {report_type}: {content_type} ({len(content)} 字符)")
                        # 检查内容是否包含有效的文本
                        if len(content.strip()) > 10:
                            preview = content[:100].replace('\n', ' ').replace('\r', ' ')
                            print(f"      预览: {preview}...")
                        else:
                            print(f"      ⚠️ 内容过短: '{content}'")
                    else:
                        print(f"   ❌ {report_type}: {content_type} (应该是str)")
                        print(f"      值: {content}")
                
                # 验证前端期望的字段
                expected_fields = ['market_report', 'fundamentals_report', 'investment_plan', 'final_trade_decision']
                print(f"\n🎯 检查前端期望的字段:")
                for field in expected_fields:
                    if field in reports:
                        content = reports[field]
                        if isinstance(content, str) and len(content.strip()) > 10:
                            print(f"   ✅ {field}: 有效字符串内容")
                        else:
                            print(f"   ⚠️ {field}: 内容无效或过短")
                    else:
                        print(f"   ❌ {field}: 缺失")
                
                return True
            else:
                print(f"❌ API返回未包含reports字段")
                
                # 显示完整的数据结构用于调试
                print(f"\n🔍 完整数据结构:")
                for key, value in data.items():
                    print(f"   {key}: {type(value).__name__}")
                    if isinstance(value, dict) and len(value) > 0:
                        print(f"      子字段: {list(value.keys())}")
                
                return False
        else:
            print(f"❌ 获取API结果失败: {result_response.status_code}")
            print(f"   响应: {result_response.text}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 测试已有的分析结果")
    print("=" * 80)
    
    # 获取已有的任务ID
    print("📋 获取已有的任务ID...")
    task_ids = get_existing_task_ids()
    
    if not task_ids:
        print("❌ 没有找到已有的任务")
        return
    
    print(f"✅ 找到 {len(task_ids)} 个任务:")
    for i, task_info in enumerate(task_ids, 1):
        print(f"   {i}. {task_info['task_id']} - {task_info['stock_symbol']} ({task_info['created_at']})")
    
    # 测试最新的任务
    latest_task = task_ids[0]
    success = test_existing_result(latest_task['task_id'], latest_task['stock_symbol'])
    
    if success:
        print(f"\n🎉 测试成功! 任务 {latest_task['task_id']} 的API返回格式正确")
    else:
        print(f"\n💥 测试失败! 任务 {latest_task['task_id']} 的API返回格式有问题")

if __name__ == "__main__":
    main()
