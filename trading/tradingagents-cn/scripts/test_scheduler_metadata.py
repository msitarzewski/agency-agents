"""
测试定时任务元数据功能
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"


def login() -> str:
    """登录并获取 token"""
    print("🔐 正在登录...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            token = data["data"]["access_token"]
            print(f"✅ 登录成功")
            return token
    
    print(f"❌ 登录失败")
    return None


def test_list_jobs(token: str):
    """测试获取任务列表"""
    print("\n📋 测试获取任务列表...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/api/scheduler/jobs", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取成功，共 {len(data['data'])} 个任务")
        
        # 显示第一个任务的信息
        if data['data']:
            job = data['data'][0]
            print(f"\n第一个任务:")
            print(f"  - ID: {job['id']}")
            print(f"  - 名称: {job['name']}")
            print(f"  - 触发器名称: {job.get('display_name', '(未设置)')}")
            print(f"  - 备注: {job.get('description', '(未设置)')}")
            return job['id']
    else:
        print(f"❌ 获取失败: {response.text}")
    
    return None


def test_update_metadata(token: str, job_id: str):
    """测试更新任务元数据"""
    print(f"\n✏️ 测试更新任务元数据: {job_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 更新元数据
    data = {
        "display_name": "测试任务名称",
        "description": "这是一个测试任务的备注说明，用于验证元数据功能是否正常工作。"
    }
    
    response = requests.put(
        f"{BASE_URL}/api/scheduler/jobs/{job_id}/metadata",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 更新成功: {result['message']}")
        return True
    else:
        print(f"❌ 更新失败: {response.text}")
        return False


def test_get_job_detail(token: str, job_id: str):
    """测试获取任务详情"""
    print(f"\n🔍 测试获取任务详情: {job_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/scheduler/jobs/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        job = data['data']
        print(f"✅ 获取成功")
        print(f"  - ID: {job['id']}")
        print(f"  - 名称: {job['name']}")
        print(f"  - 触发器名称: {job.get('display_name', '(未设置)')}")
        print(f"  - 备注: {job.get('description', '(未设置)')}")
        print(f"  - 触发器: {job['trigger']}")
        print(f"  - 下次执行: {job.get('next_run_time', '(已暂停)')}")
    else:
        print(f"❌ 获取失败: {response.text}")


def test_clear_metadata(token: str, job_id: str):
    """测试清除任务元数据"""
    print(f"\n🧹 测试清除任务元数据: {job_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 清除元数据（设置为空字符串）
    data = {
        "display_name": "",
        "description": ""
    }
    
    response = requests.put(
        f"{BASE_URL}/api/scheduler/jobs/{job_id}/metadata",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 清除成功: {result['message']}")
        return True
    else:
        print(f"❌ 清除失败: {response.text}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 定时任务元数据功能测试")
    print("=" * 60)
    
    # 1. 登录
    token = login()
    if not token:
        print("\n❌ 登录失败，无法继续测试")
        return
    
    # 2. 获取任务列表
    job_id = test_list_jobs(token)
    if not job_id:
        print("\n❌ 没有可用的任务，无法继续测试")
        return
    
    # 3. 更新任务元数据
    if test_update_metadata(token, job_id):
        # 4. 获取任务详情（验证更新）
        test_get_job_detail(token, job_id)
        
        # 5. 清除任务元数据
        if test_clear_metadata(token, job_id):
            # 6. 再次获取任务详情（验证清除）
            test_get_job_detail(token, job_id)
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

