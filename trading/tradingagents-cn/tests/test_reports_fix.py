#!/usr/bin/env python3
"""
测试reports和analysts字段修复
"""

import requests
import time
import json
from pymongo import MongoClient

def test_reports_and_analysts_fix():
    """测试reports和analysts字段修复"""
    print("🔍 测试reports和analysts字段修复")
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
        
        # 2. 提交分析请求（包含多个分析师）
        print("\n2. 提交分析请求...")
        analysis_request = {
            "stock_code": "000006",  # 使用新的股票代码
            "parameters": {
                "market_type": "A股",
                "analysis_date": "2025-08-20",
                "research_depth": "深度",  # 使用深度分析
                "selected_analysts": ["market", "fundamentals", "sentiment"],  # 选择多个分析师
                "include_sentiment": True,
                "include_risk": True,
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
            print(f"📋 选择的分析师: {analysis_request['parameters']['selected_analysts']}")
        else:
            print(f"❌ 提交分析请求失败: {response.status_code}")
            return False
        
        # 3. 等待任务完成
        print(f"\n3. 等待任务完成...")
        for i in range(120):  # 最多等待10分钟（深度分析需要更长时间）
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
                    break
                elif status == "failed":
                    print(f"❌ 分析任务失败")
                    return False
            
            time.sleep(5)
        else:
            print(f"⏰ 任务执行超时")
            return False
        
        # 4. 检查API返回的结果
        print(f"\n4. 检查API返回的结果...")
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
            
            # 检查reports字段
            reports = data.get('reports', {})
            if reports:
                print(f"✅ API返回包含 {len(reports)} 个报告:")
                for report_type, content in reports.items():
                    if isinstance(content, str):
                        print(f"   - {report_type}: {len(content)} 字符")
                    else:
                        print(f"   - {report_type}: {type(content)}")
            else:
                print(f"❌ API返回未包含reports字段")
        else:
            print(f"❌ 获取API结果失败: {result_response.status_code}")
        
        # 5. 检查MongoDB保存的数据
        print(f"\n5. 检查MongoDB保存的数据...")
        
        try:
            client = MongoClient('mongodb://localhost:27017/')
            db = client['tradingagents']
            collection = db['analysis_reports']
            
            # 查找最新的记录
            latest_record = collection.find({"stock_symbol": "000006"}).sort("created_at", -1).limit(1)
            
            for record in latest_record:
                print(f"📋 MongoDB记录详情:")
                print(f"   analysis_id: {record.get('analysis_id')}")
                print(f"   stock_symbol: {record.get('stock_symbol')}")
                print(f"   analysts: {record.get('analysts', [])}")
                print(f"   research_depth: {record.get('research_depth')}")
                
                # 检查reports字段
                reports = record.get('reports', {})
                if reports:
                    print(f"✅ MongoDB包含 {len(reports)} 个报告:")
                    for report_type, content in reports.items():
                        if isinstance(content, str):
                            print(f"   - {report_type}: {len(content)} 字符")
                            # 显示报告内容的前100个字符作为预览
                            preview = content[:100].replace('\n', ' ')
                            print(f"     预览: {preview}...")
                        else:
                            print(f"   - {report_type}: {type(content)}")
                    
                    return True
                else:
                    print(f"❌ MongoDB未包含reports字段或为空")
                    return False
            
            print(f"❌ 未找到MongoDB记录")
            return False
            
        except Exception as e:
            print(f"❌ MongoDB检查失败: {e}")
            return False
        finally:
            if 'client' in locals():
                client.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_reports_and_analysts_fix()
    if success:
        print("\n🎉 reports和analysts字段修复测试成功!")
    else:
        print("\n💥 reports和analysts字段修复测试失败!")
