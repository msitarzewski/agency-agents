"""
调试前端API调用
检查前端调用的API是否返回正确的数据
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def debug_frontend_api():
    """调试前端API调用"""
    
    print("=" * 80)
    print("🔍 调试前端API调用")
    print("=" * 80)
    
    # 1. 登录
    print("\n[步骤1] 登录...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    token_data = login_response.json()
    access_token = token_data["data"]["access_token"]
    print(f"✅ 登录成功")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 测试不同的股票代码
    test_codes = ["002475", "000001", "600519"]
    
    for stock_code in test_codes:
        print(f"\n{'=' * 80}")
        print(f"📊 测试股票代码: {stock_code}")
        print(f"{'=' * 80}")
        
        # 调用前端使用的API
        print(f"\n[API调用] GET /api/analysis/user/history")
        print(f"   参数: stock_code={stock_code}, page=1, page_size=1, status=completed")
        
        response = requests.get(
            f"{BASE_URL}/api/analysis/user/history",
            headers=headers,
            params={
                "stock_code": stock_code,
                "page": 1,
                "page_size": 1,
                "status": "completed"
            }
        )
        
        if response.status_code != 200:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"   响应: {response.text}")
            continue
        
        data = response.json()
        print(f"✅ API调用成功")
        
        # 检查响应结构
        if not data.get("success"):
            print(f"❌ success=False")
            continue
        
        response_data = data.get("data", {})
        tasks = response_data.get("tasks", [])
        total = response_data.get("total", 0)
        
        print(f"\n📋 响应数据:")
        print(f"   total: {total}")
        print(f"   tasks数量: {len(tasks)}")
        
        if len(tasks) > 0:
            print(f"\n✅ 找到 {len(tasks)} 个任务")
            
            for i, task in enumerate(tasks):
                print(f"\n   任务 {i+1}:")
                print(f"      task_id: {task.get('task_id')}")
                print(f"      stock_code: {task.get('stock_code')}")
                print(f"      status: {task.get('status')}")
                print(f"      created_at: {task.get('created_at')}")
                
                # 检查result_data字段
                if 'result_data' in task:
                    result_data = task['result_data']
                    print(f"      ✅ 有 result_data 字段")
                    print(f"         键: {list(result_data.keys())}")
                    
                    if 'reports' in result_data:
                        reports = result_data['reports']
                        print(f"         ✅ 有 reports 字段")
                        print(f"            类型: {type(reports)}")
                        if isinstance(reports, dict):
                            print(f"            报告数量: {len(reports)}")
                            print(f"            报告列表: {list(reports.keys())}")
                        else:
                            print(f"            ⚠️ reports不是字典类型")
                    else:
                        print(f"         ❌ 没有 reports 字段")
                else:
                    print(f"      ❌ 没有 result_data 字段")
                    
                    # 检查是否有result字段
                    if 'result' in task:
                        print(f"      ⚠️ 有 result 字段（旧格式）")
        else:
            print(f"\n❌ 该股票没有历史分析记录")
            print(f"   这就是为什么前端显示'该股票暂无历史分析报告'")
    
    print(f"\n{'=' * 80}")
    print(f"✅ 调试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    try:
        debug_frontend_api()
    except Exception as e:
        print(f"\n❌ 调试异常: {e}")
        import traceback
        traceback.print_exc()

