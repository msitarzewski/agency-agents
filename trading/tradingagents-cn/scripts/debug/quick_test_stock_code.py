#!/usr/bin/env python3
"""
快速测试股票代码传递问题
"""

import requests
import time
import json

def quick_test():
    """快速测试股票代码传递"""
    print("🔍 快速测试股票代码传递")
    print("=" * 60)
    
    # API基础URL
    base_url = "http://localhost:8000"
    
    try:
        # 1. 检查API健康状态
        print("1. 检查API健康状态...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常运行")
        else:
            print(f"❌ API服务异常: {response.status_code}")
            return False
        
        # 2. 提交分析请求
        print("\n2. 提交分析请求...")
        analysis_request = {
            "stock_code": "000003",  # 使用新的股票代码
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
            "Authorization": "Bearer admin_token"
        }
        
        response = requests.post(
            f"{base_url}/api/analysis/single",
            json=analysis_request,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
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
                status = status_data.get("status")
                
                if status == "completed":
                    print("✅ 分析任务完成!")
                    
                    # 获取结果并检查股票代码
                    result_response = requests.get(
                        f"{base_url}/api/analysis/tasks/{task_id}/result",
                        headers=headers
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        print(f"\n📊 结果检查:")
                        print(f"   stock_code: {result_data.get('stock_code', 'NOT_FOUND')}")
                        print(f"   stock_symbol: {result_data.get('stock_symbol', 'NOT_FOUND')}")
                        
                        # 检查保存的文件路径
                        from pathlib import Path
                        
                        # 检查是否保存到正确的目录
                        correct_dir = Path(f"data/analysis_results/000003/2025-08-20")
                        unknown_dir = Path(f"data/analysis_results/UNKNOWN/2025-08-20")
                        
                        if correct_dir.exists():
                            print(f"✅ 文件保存到正确目录: {correct_dir}")
                        elif unknown_dir.exists():
                            print(f"❌ 文件仍保存到UNKNOWN目录: {unknown_dir}")
                        else:
                            print(f"❌ 找不到保存的文件")
                        
                        return True
                    else:
                        print(f"❌ 获取结果失败: {result_response.status_code}")
                        return False
                        
                elif status == "failed":
                    print(f"❌ 分析任务失败")
                    return False
            
            time.sleep(5)
        
        print(f"⏰ 任务执行超时")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 股票代码传递测试成功!")
    else:
        print("\n💥 股票代码传递测试失败!")
