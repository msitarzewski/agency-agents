#!/usr/bin/env python3
"""
测试decision数据是否正确保存和获取
"""
import requests
import json
from datetime import datetime

def test_decision_data():
    """测试decision数据的完整流程"""
    base_url = "http://localhost:8000"
    
    # 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(
        f"{base_url}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code}")
        return
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ 登录失败: {result.get('message')}")
        return
    
    token = result["data"]["access_token"]
    print(f"✅ 登录成功")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print(f"\n🧪 测试decision数据流程")
        print("=" * 50)
        
        # 1. 启动一个新的分析任务
        print(f"\n1. 启动新的分析任务...")
        analysis_request = {
            "stock_code": "000001",
            "parameters": {
                "research_depth": "快速",
                "selected_analysts": ["market", "fundamentals"]
            }
        }
        
        start_response = requests.post(
            f"{base_url}/api/analysis/single",
            json=analysis_request,
            headers=headers
        )
        
        if start_response.status_code != 200:
            print(f"❌ 启动分析失败: {start_response.status_code}")
            print(f"   错误信息: {start_response.text}")
            return
        
        start_data = start_response.json()
        if not start_data.get("success"):
            print(f"❌ 启动分析失败: {start_data.get('message')}")
            return
        
        task_id = start_data["data"]["task_id"]
        print(f"✅ 分析任务启动成功: {task_id}")
        
        # 2. 等待任务完成
        print(f"\n2. 等待任务完成...")
        import time
        max_wait = 300  # 最多等待5分钟
        wait_time = 0
        
        while wait_time < max_wait:
            status_response = requests.get(
                f"{base_url}/api/analysis/tasks/{task_id}/status",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("success"):
                    status = status_data["data"]["status"]
                    print(f"   任务状态: {status}")
                    
                    if status == "completed":
                        print(f"✅ 任务完成!")
                        break
                    elif status == "failed":
                        print(f"❌ 任务失败!")
                        return
            
            time.sleep(10)
            wait_time += 10
        
        if wait_time >= max_wait:
            print(f"❌ 任务超时!")
            return
        
        # 3. 获取完整结果
        print(f"\n3. 获取完整分析结果...")
        result_response = requests.get(
            f"{base_url}/api/analysis/tasks/{task_id}/result",
            headers=headers
        )
        
        if result_response.status_code != 200:
            print(f"❌ 获取结果失败: {result_response.status_code}")
            print(f"   错误信息: {result_response.text}")
            return
        
        result_data = result_response.json()
        if not result_data.get("success"):
            print(f"❌ 获取结果失败: {result_data.get('message')}")
            return
        
        analysis_result = result_data["data"]
        
        # 4. 检查decision字段
        print(f"\n4. 检查decision数据...")
        print(f"   有decision字段: {bool(analysis_result.get('decision'))}")
        
        if analysis_result.get('decision'):
            decision = analysis_result['decision']
            print(f"   Decision数据结构:")
            print(f"     action: {decision.get('action', '无')}")
            print(f"     target_price: {decision.get('target_price', '无')}")
            print(f"     confidence: {decision.get('confidence', '无')}")
            print(f"     risk_score: {decision.get('risk_score', '无')}")
            print(f"     reasoning: {len(str(decision.get('reasoning', '')))} 字符")
            
            # 保存decision数据用于检查
            with open('decision_sample.json', 'w', encoding='utf-8') as f:
                json.dump(decision, f, ensure_ascii=False, indent=2, default=str)
            print(f"   Decision数据已保存到 decision_sample.json")
        else:
            print(f"   ❌ 没有找到decision字段!")
            print(f"   可用字段: {list(analysis_result.keys())}")
        
        # 5. 检查MongoDB中的数据
        print(f"\n5. 检查MongoDB中的数据...")
        reports_response = requests.get(
            f"{base_url}/api/reports/list?search_keyword={task_id}",
            headers=headers
        )
        
        if reports_response.status_code == 200:
            reports_data = reports_response.json()
            if reports_data.get("success") and reports_data["data"]["reports"]:
                report = reports_data["data"]["reports"][0]
                report_id = report["id"]
                
                # 获取报告详情
                detail_response = requests.get(
                    f"{base_url}/api/reports/{report_id}/detail",
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get("success"):
                        report_detail = detail_data["data"]
                        print(f"   MongoDB中有decision字段: {bool(report_detail.get('decision'))}")
                        
                        if report_detail.get('decision'):
                            mongo_decision = report_detail['decision']
                            print(f"   MongoDB Decision数据:")
                            print(f"     action: {mongo_decision.get('action', '无')}")
                            print(f"     target_price: {mongo_decision.get('target_price', '无')}")
                            print(f"     confidence: {mongo_decision.get('confidence', '无')}")
                        else:
                            print(f"   ❌ MongoDB中没有decision字段!")
                            print(f"   MongoDB可用字段: {list(report_detail.keys())}")
        
        print(f"\n🎉 Decision数据测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    test_decision_data()
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
