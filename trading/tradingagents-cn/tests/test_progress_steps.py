"""
测试进度跟踪和步骤状态更新
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

async def login() -> str:
    """登录并获取token"""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        async with session.post(f"{BASE_URL}/api/auth/login", json=login_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"📋 登录响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

                # 尝试不同的数据结构
                if "data" in result and "token" in result["data"]:
                    token = result["data"]["token"]
                elif "data" in result and "access_token" in result["data"]:
                    token = result["data"]["access_token"]
                elif "token" in result:
                    token = result["token"]
                elif "access_token" in result:
                    token = result["access_token"]
                else:
                    print(f"❌ 无法从响应中提取token")
                    return None

                print(f"✅ 登录成功，token: {token[:20]}...")
                return token
            else:
                error = await response.text()
                print(f"❌ 登录失败: {error}")
                return None

async def start_analysis(token: str) -> str:
    """发起分析任务"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    analysis_data = {
        "stock_code": "601398",
        "parameters": {
            "analysts": ["market", "fundamentals"],
            "research_depth": "快速",
            "custom_requirements": "测试步骤状态更新"
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/analysis/single",
            headers=headers,
            json=analysis_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"📋 分析响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                task_id = result["data"]["task_id"]
                print(f"✅ 分析任务已提交: {task_id}")
                return task_id
            else:
                error = await response.text()
                print(f"❌ 提交分析失败 (状态码: {response.status}): {error}")
                return None

async def get_task_status(token: str, task_id: str) -> dict:
    """获取任务状态"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/api/analysis/tasks/{task_id}/status",
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result["data"]
            else:
                error = await response.text()
                print(f"❌ 获取状态失败: {error}")
                return None

def print_progress_info(status_data: dict, iteration: int):
    """打印进度信息"""
    print(f"\n{'='*80}")
    print(f"📊 第 {iteration} 次查询 - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    
    # 基本信息
    print(f"📋 任务ID: {status_data.get('task_id', 'N/A')}")
    print(f"📈 状态: {status_data.get('status', 'N/A')}")
    print(f"📊 进度: {status_data.get('progress', 0)}%")
    print(f"💬 消息: {status_data.get('message', 'N/A')}")
    
    # 当前步骤信息
    current_step = status_data.get('current_step')
    current_step_name = status_data.get('current_step_name', 'N/A')
    current_step_description = status_data.get('current_step_description', 'N/A')
    
    print(f"\n🎯 当前步骤:")
    print(f"   索引: {current_step}")
    print(f"   名称: {current_step_name}")
    print(f"   描述: {current_step_description}")
    
    # 时间信息
    elapsed = status_data.get('elapsed_time', 0)
    remaining = status_data.get('remaining_time', 0)
    estimated = status_data.get('estimated_total_time', 0)
    
    print(f"\n⏱️ 时间信息:")
    print(f"   已用时间: {elapsed:.1f}秒")
    print(f"   预计剩余: {remaining:.1f}秒")
    print(f"   预计总时长: {estimated:.1f}秒")
    
    # 步骤详情
    steps = status_data.get('steps', [])
    if steps:
        print(f"\n📝 步骤详情 (共 {len(steps)} 个):")
        print(f"{'序号':<6} {'状态':<12} {'名称':<30} {'权重':<8}")
        print(f"{'-'*80}")
        
        for i, step in enumerate(steps):
            status_icon = {
                'pending': '⏳',
                'current': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(step.get('status', 'pending'), '❓')
            
            print(f"{i:<6} {status_icon} {step.get('status', 'N/A'):<10} {step.get('name', 'N/A'):<30} {step.get('weight', 0):.2%}")
        
        # 统计步骤状态
        status_count = {}
        for step in steps:
            s = step.get('status', 'pending')
            status_count[s] = status_count.get(s, 0) + 1
        
        print(f"\n📊 步骤状态统计:")
        for status, count in status_count.items():
            print(f"   {status}: {count}")
    else:
        print(f"\n⚠️ 没有步骤信息")
    
    print(f"{'='*80}\n")

async def monitor_task_progress(token: str, task_id: str, max_iterations: int = 60, interval: int = 3):
    """监控任务进度"""
    print(f"\n🔄 开始监控任务进度...")
    print(f"   任务ID: {task_id}")
    print(f"   最大查询次数: {max_iterations}")
    print(f"   查询间隔: {interval}秒")
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # 获取状态
        status_data = await get_task_status(token, task_id)
        
        if not status_data:
            print(f"❌ 无法获取任务状态")
            break
        
        # 打印进度信息
        print_progress_info(status_data, iteration)
        
        # 检查是否完成
        status = status_data.get('status')
        if status == 'completed':
            print(f"✅ 任务已完成！")
            break
        elif status == 'failed':
            print(f"❌ 任务失败！")
            break
        
        # 等待下一次查询
        await asyncio.sleep(interval)
    
    if iteration >= max_iterations:
        print(f"⏰ 达到最大查询次数，停止监控")

async def main():
    """主函数"""
    print(f"{'='*80}")
    print(f"🧪 测试进度跟踪和步骤状态更新")
    print(f"{'='*80}\n")
    
    # 1. 登录
    print(f"1️⃣ 登录系统...")
    token = await login()
    if not token:
        print(f"❌ 登录失败，退出测试")
        return
    
    # 2. 发起分析
    print(f"\n2️⃣ 发起分析任务...")
    task_id = await start_analysis(token)
    if not task_id:
        print(f"❌ 发起分析失败，退出测试")
        return
    
    # 3. 监控进度
    print(f"\n3️⃣ 监控任务进度...")
    await monitor_task_progress(token, task_id, max_iterations=100, interval=3)
    
    print(f"\n{'='*80}")
    print(f"✅ 测试完成")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())

