#!/usr/bin/env python3
"""
快速测试异步分析实现
验证API是否不再阻塞
"""

import requests
import time
import json

def test_api_non_blocking():
    """测试API非阻塞功能"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 快速测试API非阻塞功能")
    print("=" * 40)
    
    # 1. 登录
    print("🔐 登录中...")
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False
    
    # 2. 提交分析任务（关键测试：应该立即返回）
    print("\n📊 提交分析任务...")
    start_time = time.time()
    
    try:
        analysis_response = requests.post(f"{base_url}/api/analysis/single", 
                                        json={
                                            "stock_code": "000001",
                                            "parameters": {
                                                "research_depth": 1,  # 快速分析
                                                "selected_analysts": ["market"]
                                            }
                                        }, 
                                        headers=headers,
                                        timeout=10)  # 10秒超时
        
        submit_time = time.time() - start_time
        print(f"⏱️ 任务提交耗时: {submit_time:.2f}秒")
        
        if analysis_response.status_code == 200:
            task_data = analysis_response.json()
            task_id = task_data["data"]["task_id"]
            print(f"✅ 任务提交成功: {task_id}")
            
            # 关键判断：如果提交时间很短，说明API没有阻塞
            if submit_time < 3.0:
                print("🎉 API响应迅速，非阻塞实现成功！")
                success = True
            else:
                print("⚠️ API响应较慢，可能仍有阻塞问题")
                success = False
                
        else:
            print(f"❌ 任务提交失败: {analysis_response.status_code}")
            print(f"错误信息: {analysis_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时！API可能仍然阻塞")
        return False
    except Exception as e:
        print(f"❌ 提交任务异常: {e}")
        return False
    
    # 3. 立即测试其他API（验证服务器没有被阻塞）
    print("\n🔍 测试其他API响应性...")
    
    # 健康检查
    try:
        health_start = time.time()
        health_response = requests.get(f"{base_url}/api/health", timeout=5)
        health_time = time.time() - health_start
        print(f"🏥 健康检查: {health_response.status_code} - {health_time:.2f}秒")
        
        if health_time > 2.0:
            print("⚠️ 健康检查响应慢，服务器可能被阻塞")
            success = False
            
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        success = False
    
    # 任务状态查询
    try:
        status_start = time.time()
        status_response = requests.get(f"{base_url}/api/analysis/task/{task_id}", 
                                     headers=headers, timeout=5)
        status_time = time.time() - status_start
        print(f"📋 任务状态查询: {status_response.status_code} - {status_time:.2f}秒")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            task_status = status_data['data']['status']
            progress = status_data['data']['progress']
            print(f"📊 当前状态: {task_status} ({progress}%)")
            
        if status_time > 2.0:
            print("⚠️ 状态查询响应慢")
            success = False
            
    except Exception as e:
        print(f"❌ 状态查询失败: {e}")
        success = False
    
    # 4. 总结
    print(f"\n📈 测试总结:")
    print(f"  - 任务提交时间: {submit_time:.2f}秒")
    print(f"  - 健康检查时间: {health_time:.2f}秒")
    print(f"  - 状态查询时间: {status_time:.2f}秒")
    
    if success:
        print("🎉 异步实现成功！API不再阻塞")
    else:
        print("❌ 仍有阻塞问题，需要进一步优化")
    
    return success

def test_multiple_concurrent_requests():
    """测试多个并发请求"""
    print("\n🔄 测试并发请求...")
    
    base_url = "http://localhost:8000"
    
    import threading
    import queue
    
    results = queue.Queue()
    
    def make_health_request():
        try:
            start = time.time()
            response = requests.get(f"{base_url}/api/health", timeout=5)
            duration = time.time() - start
            results.put((response.status_code, duration))
        except Exception as e:
            results.put((0, 999))
    
    # 启动5个并发请求
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_health_request)
        threads.append(thread)
        thread.start()
    
    # 等待所有请求完成
    for thread in threads:
        thread.join()
    
    # 收集结果
    response_times = []
    while not results.empty():
        status, duration = results.get()
        response_times.append(duration)
        print(f"  并发请求: 状态 {status}, 耗时 {duration:.3f}秒")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        print(f"📊 并发性能: 平均 {avg_time:.3f}秒, 最大 {max_time:.3f}秒")
        
        if max_time < 1.0:
            print("🎉 并发性能良好")
        else:
            print("⚠️ 并发性能需要优化")

if __name__ == "__main__":
    print(f"🚀 开始测试: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_api_non_blocking()
    test_multiple_concurrent_requests()
    
    print(f"\n✅ 测试完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("🎊 恭喜！异步分析实现成功")
    else:
        print("🔧 需要进一步调试和优化")
