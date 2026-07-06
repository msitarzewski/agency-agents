#!/usr/bin/env python3
"""
测试新的异步分析实现
验证 BackgroundTasks + 内存状态管理 + WebSocket 的完整流程
"""

import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime

async def test_async_analysis():
    """测试异步分析功能"""
    
    base_url = "http://localhost:8000"
    ws_url = "ws://localhost:8000"
    
    print("🧪 开始测试新的异步分析实现")
    print("=" * 50)
    
    # 1. 登录获取token
    print("🔐 正在登录...")
    async with aiohttp.ClientSession() as session:
        login_response = await session.post(f"{base_url}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status != 200:
            print(f"❌ 登录失败: {login_response.status}")
            return
        
        login_data = await login_response.json()
        token = login_data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        
        # 2. 提交分析任务（应该立即返回）
        print("\n📊 提交分析任务...")
        submit_start = time.time()
        
        analysis_response = await session.post(f"{base_url}/api/analysis/single", 
                                             json={
                                                 "stock_code": "000001",
                                                 "parameters": {
                                                     "research_depth": 1,  # 快速分析
                                                     "selected_analysts": ["market"]
                                                 }
                                             }, 
                                             headers=headers)
        
        submit_time = time.time() - submit_start
        print(f"⏱️ 任务提交耗时: {submit_time:.2f}秒")
        
        if analysis_response.status != 200:
            print(f"❌ 任务提交失败: {analysis_response.status}")
            response_text = await analysis_response.text()
            print(f"错误信息: {response_text}")
            return
        
        analysis_data = await analysis_response.json()
        task_id = analysis_data["data"]["task_id"]
        print(f"✅ 任务提交成功: {task_id}")
        
        # 验证API响应速度
        if submit_time < 2.0:
            print("🎉 API响应迅速，非阻塞实现成功！")
        else:
            print("⚠️ API响应较慢，可能仍有阻塞问题")
        
        # 3. 立即测试其他API（验证非阻塞）
        print("\n🔍 测试其他API响应性...")
        
        # 健康检查
        health_start = time.time()
        health_response = await session.get(f"{base_url}/api/health")
        health_time = time.time() - health_start
        print(f"🏥 健康检查: {health_response.status} - {health_time:.2f}秒")
        
        # 任务状态查询
        status_start = time.time()
        status_response = await session.get(f"{base_url}/api/analysis/task/{task_id}", 
                                          headers=headers)
        status_time = time.time() - status_start
        print(f"📋 任务状态查询: {status_response.status} - {status_time:.2f}秒")
        
        if status_response.status == 200:
            status_data = await status_response.json()
            print(f"📊 当前状态: {status_data['data']['status']} ({status_data['data']['progress']}%)")
        
        # 4. 测试 WebSocket 实时进度
        print(f"\n🔌 测试 WebSocket 实时进度...")
        try:
            await test_websocket_progress(task_id, ws_url)
        except Exception as e:
            print(f"⚠️ WebSocket 测试失败: {e}")
        
        # 5. 轮询任务状态直到完成
        print(f"\n⏳ 等待任务完成...")
        max_wait_time = 300  # 最多等待5分钟
        start_wait = time.time()
        
        while time.time() - start_wait < max_wait_time:
            status_response = await session.get(f"{base_url}/api/analysis/task/{task_id}", 
                                              headers=headers)
            
            if status_response.status == 200:
                status_data = await status_response.json()
                task_status = status_data['data']['status']
                progress = status_data['data']['progress']
                message = status_data['data'].get('message', '')
                
                print(f"📊 状态: {task_status} ({progress}%) - {message}")
                
                if task_status in ['completed', 'failed', 'cancelled']:
                    break
            
            await asyncio.sleep(5)  # 每5秒查询一次
        
        # 6. 获取最终结果
        final_response = await session.get(f"{base_url}/api/analysis/task/{task_id}", 
                                         headers=headers)
        
        if final_response.status == 200:
            final_data = await final_response.json()
            task_data = final_data['data']
            
            print(f"\n📈 最终结果:")
            print(f"  状态: {task_data['status']}")
            print(f"  进度: {task_data['progress']}%")
            print(f"  执行时间: {task_data.get('execution_time', 'N/A')}秒")
            
            if task_data['status'] == 'completed' and task_data.get('result_data'):
                result = task_data['result_data']
                print(f"  股票代码: {result.get('stock_code', 'N/A')}")
                print(f"  推荐: {result.get('recommendation', 'N/A')}")
                print(f"  置信度: {result.get('confidence_score', 'N/A')}")
        
        # 7. 测试任务列表
        print(f"\n📋 测试任务列表...")
        tasks_response = await session.get(f"{base_url}/api/analysis/tasks", 
                                         headers=headers)
        
        if tasks_response.status == 200:
            tasks_data = await tasks_response.json()
            tasks = tasks_data['data']['tasks']
            print(f"✅ 获取到 {len(tasks)} 个任务")
            for task in tasks[:3]:  # 显示前3个任务
                print(f"  - {task['task_id'][:8]}... : {task['status']} ({task['progress']}%)")

async def test_websocket_progress(task_id: str, ws_url: str):
    """测试 WebSocket 实时进度"""
    try:
        uri = f"{ws_url}/api/analysis/ws/task/{task_id}"
        print(f"🔌 连接 WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功")
            
            # 接收消息，最多等待30秒
            timeout = 30
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "connection_established":
                        print("🔗 WebSocket 连接确认")
                    elif data.get("type") == "progress_update":
                        print(f"📡 实时进度: {data.get('status')} ({data.get('progress')}%) - {data.get('message')}")
                    
                    # 如果任务完成，退出
                    if data.get("status") in ["completed", "failed", "cancelled"]:
                        break
                        
                except asyncio.TimeoutError:
                    # 发送心跳
                    await websocket.send("ping")
                    continue
                except Exception as e:
                    print(f"⚠️ WebSocket 消息处理错误: {e}")
                    break
            
            print("🔌 WebSocket 测试完成")
            
    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")

async def test_concurrent_requests():
    """测试并发请求能力"""
    print("\n🔄 测试并发请求能力...")
    
    base_url = "http://localhost:8000"
    
    async def make_health_check():
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            async with session.get(f"{base_url}/api/health") as resp:
                duration = time.time() - start_time
                return resp.status, duration
    
    # 并发发送10个健康检查请求
    tasks = [make_health_check() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    print("🏥 并发健康检查结果:")
    for i, (status, duration) in enumerate(results):
        print(f"  请求 {i+1}: 状态 {status}, 耗时 {duration:.3f}秒")
    
    avg_time = sum(duration for _, duration in results) / len(results)
    max_time = max(duration for _, duration in results)
    
    print(f"📊 性能统计:")
    print(f"  平均响应时间: {avg_time:.3f}秒")
    print(f"  最大响应时间: {max_time:.3f}秒")
    
    if max_time < 1.0:
        print("🎉 并发性能良好！")
    else:
        print("⚠️ 并发性能需要优化")

if __name__ == "__main__":
    print(f"🚀 开始测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    asyncio.run(test_async_analysis())
    asyncio.run(test_concurrent_requests())
    
    print(f"\n✅ 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
