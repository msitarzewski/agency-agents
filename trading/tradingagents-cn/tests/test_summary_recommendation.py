#!/usr/bin/env python3
"""
测试summary和recommendation字段
"""
import requests
import json

def test_summary_recommendation():
    """测试summary和recommendation字段"""
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
    
    # 使用最新的任务ID
    task_id = "b407e811-e593-416f-8e7f-3e75d37e8b8b"
    
    print(f"\n🔍 检查任务 {task_id} 的summary和recommendation字段")
    
    # 获取完整结果
    result_response = requests.get(
        f"{base_url}/api/analysis/tasks/{task_id}/result",
        headers=headers
    )
    
    if result_response.status_code != 200:
        print(f"❌ 获取结果失败: {result_response.status_code}")
        return
    
    result_data = result_response.json()
    if not result_data.get("success"):
        print(f"❌ 获取结果失败: {result_data.get('message')}")
        return
    
    analysis_result = result_data["data"]
    
    print(f"\n📊 字段检查:")
    print(f"   summary存在: {bool(analysis_result.get('summary'))}")
    print(f"   summary长度: {len(analysis_result.get('summary', ''))}")
    print(f"   summary内容: {analysis_result.get('summary', '无')[:100]}...")
    
    print(f"\n   recommendation存在: {bool(analysis_result.get('recommendation'))}")
    print(f"   recommendation长度: {len(analysis_result.get('recommendation', ''))}")
    print(f"   recommendation内容: {analysis_result.get('recommendation', '无')[:100]}...")
    
    print(f"\n   decision存在: {bool(analysis_result.get('decision'))}")
    if analysis_result.get('decision'):
        decision = analysis_result['decision']
        print(f"   decision.action: {decision.get('action')}")
        print(f"   decision.target_price: {decision.get('target_price')}")
        print(f"   decision.reasoning: {decision.get('reasoning', '')[:50]}...")
    
    print(f"\n   reports存在: {bool(analysis_result.get('reports'))}")
    if analysis_result.get('reports'):
        reports = analysis_result['reports']
        print(f"   reports键: {list(reports.keys())}")
        if 'final_trade_decision' in reports:
            final_decision = reports['final_trade_decision']
            print(f"   final_trade_decision长度: {len(final_decision)}")
            print(f"   final_trade_decision前100字符: {final_decision[:100]}...")
    
    # 保存完整数据用于检查
    with open('full_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 完整分析结果已保存到 full_analysis_result.json")

if __name__ == "__main__":
    test_summary_recommendation()
