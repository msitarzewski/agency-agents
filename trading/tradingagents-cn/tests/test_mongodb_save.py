#!/usr/bin/env python3
"""
测试MongoDB保存功能
"""

import requests
import time
import json
from pymongo import MongoClient

def check_mongodb_before_after():
    """检查MongoDB保存前后的数据"""
    print("🔍 测试MongoDB保存功能")
    print("=" * 60)
    
    # 连接MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['tradingagents']
        collection = db['analysis_reports']
        
        # 检查保存前的记录数
        before_count = collection.count_documents({})
        print(f"📊 保存前analysis_reports记录数: {before_count}")
        
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        return False
    
    # API基础URL
    base_url = "http://localhost:8000"
    
    try:
        # 1. 登录获取token
        print("\n1. 登录获取token...")
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
            "stock_code": "000005",  # 使用新的股票代码
            "parameters": {
                "market_type": "A股",
                "analysis_date": "2025-08-20",
                "research_depth": "快速",
                "selected_analysts": ["market"],
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
                
                if status == "completed":
                    print("✅ 分析任务完成!")
                    break
                elif status == "failed":
                    print(f"❌ 分析任务失败")
                    return False
            
            time.sleep(5)
        else:
            print(f"⏰ 任务执行超时")
            return False
        
        # 4. 检查MongoDB保存结果
        print(f"\n4. 检查MongoDB保存结果...")
        
        # 检查保存后的记录数
        after_count = collection.count_documents({})
        print(f"📊 保存后analysis_reports记录数: {after_count}")
        
        if after_count > before_count:
            print(f"✅ MongoDB记录增加了 {after_count - before_count} 条")
            
            # 获取最新的记录
            latest_record = collection.find().sort("created_at", -1).limit(1)
            for record in latest_record:
                print(f"\n📋 最新记录详情:")
                print(f"   analysis_id: {record.get('analysis_id')}")
                print(f"   stock_symbol: {record.get('stock_symbol')}")
                print(f"   analysis_date: {record.get('analysis_date')}")
                print(f"   status: {record.get('status')}")
                print(f"   source: {record.get('source')}")
                
                # 检查reports字段
                reports = record.get('reports', {})
                if reports:
                    print(f"✅ 找到reports字段，包含 {len(reports)} 个报告:")
                    for report_type, content in reports.items():
                        if isinstance(content, str):
                            print(f"   - {report_type}: {len(content)} 字符")
                        else:
                            print(f"   - {report_type}: {type(content)}")
                else:
                    print(f"❌ 未找到reports字段或为空")
                
                return True
        else:
            print(f"❌ MongoDB记录数未增加")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    success = check_mongodb_before_after()
    if success:
        print("\n🎉 MongoDB保存测试成功!")
    else:
        print("\n💥 MongoDB保存测试失败!")
