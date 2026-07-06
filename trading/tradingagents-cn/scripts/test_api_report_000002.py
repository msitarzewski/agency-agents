#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通过 API 测试 000002 报告生成"""

import requests
import time

# API 基础 URL
BASE_URL = "http://127.0.0.1:8000"

def test_report_generation():
    print("🔍 测试通过 API 生成 000002 的报告...")
    
    # 1. 发起分析请求
    print("\n1️⃣ 发起分析请求...")
    response = requests.post(
        f"{BASE_URL}/api/analysis/",
        json={
            "stock_code": "000002",
            "analysis_type": "fundamentals"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    task_id = result.get('data', {}).get('task_id')
    print(f"✅ 任务已创建: {task_id}")
    
    # 2. 等待任务完成
    print("\n2️⃣ 等待任务完成...")
    max_wait = 120  # 最多等待2分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/analysis/status/{task_id}")
        if response.status_code != 200:
            print(f"❌ 查询失败: {response.status_code}")
            break
        
        status_data = response.json()
        status = status_data.get('data', {}).get('status')
        progress = status_data.get('data', {}).get('progress', 0)
        
        print(f"   状态: {status}, 进度: {progress}%")
        
        if status == 'completed':
            print("✅ 任务完成!")
            report_id = status_data.get('data', {}).get('report_id')
            
            # 3. 获取报告内容
            print(f"\n3️⃣ 获取报告内容 (ID: {report_id})...")
            response = requests.get(f"{BASE_URL}/api/reports/{report_id}")
            if response.status_code != 200:
                print(f"❌ 获取报告失败: {response.status_code}")
                return
            
            report_data = response.json()
            report_content = report_data.get('data', {}).get('content', '')
            
            # 检查是否包含"估算数据"警告
            if '估算数据' in report_content:
                print("❌ 报告中仍然包含'估算数据'警告")
                # 找到警告位置
                lines = report_content.split('\n')
                for i, line in enumerate(lines):
                    if '估算数据' in line:
                        print(f"  第 {i+1} 行: {line}")
            else:
                print("✅ 报告中没有'估算数据'警告")
            
            # 显示报告前500字符
            print("\n📄 报告前500字符:")
            print(report_content[:500])
            return
        
        elif status == 'failed':
            print(f"❌ 任务失败: {status_data.get('data', {}).get('error')}")
            return
        
        time.sleep(2)
    
    print("⏱️ 等待超时")

if __name__ == '__main__':
    test_report_generation()

