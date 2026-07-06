#!/usr/bin/env python3
"""
手动触发数据同步脚本
用于手动启动各种数据同步任务
"""

import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """获取认证token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def trigger_historical_data_sync():
    """触发历史数据同步"""
    print("🔄 启动历史数据同步（最近30天）...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/multi-period-sync/start-incremental?days_back=30"
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 历史数据同步启动成功: {result.get('message', '')}")
            return True
        else:
            print(f"❌ 历史数据同步启动失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 历史数据同步异常: {e}")
        return False

def trigger_financial_data_sync():
    """触发财务数据同步"""
    print("🔄 启动财务数据同步...")
    try:
        # 同步几只主要股票的财务数据
        payload = {
            "symbols": ["000001", "000002", "000858", "600000", "600036", "600519", "000858"],
            "data_sources": ["tushare"],
            "batch_size": 5,
            "delay_seconds": 2.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/financial-data/sync/start",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 财务数据同步启动成功: {result.get('message', '')}")
            return True
        else:
            print(f"❌ 财务数据同步启动失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 财务数据同步异常: {e}")
        return False

def trigger_news_data_sync(token):
    """触发新闻数据同步"""
    print("🔄 启动新闻数据同步...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "data_sources": ["tushare", "akshare"],
            "hours_back": 48,
            "max_news_per_source": 50
        }
        
        response = requests.post(
            f"{BASE_URL}/api/news-data/sync/start",
            json=payload,
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 新闻数据同步启动成功: {result.get('message', '')}")
            return True
        else:
            print(f"❌ 新闻数据同步启动失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 新闻数据同步异常: {e}")
        return False

def trigger_stock_news_sync(token, symbol="000001"):
    """触发单只股票新闻同步"""
    print(f"🔄 启动股票 {symbol} 新闻同步...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "symbol": symbol,
            "data_sources": ["tushare", "akshare"],
            "hours_back": 24,
            "max_news_per_source": 20
        }
        
        response = requests.post(
            f"{BASE_URL}/api/news-data/sync/start",
            json=payload,
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 股票 {symbol} 新闻同步启动成功: {result.get('message', '')}")
            return True
        else:
            print(f"❌ 股票 {symbol} 新闻同步启动失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 股票 {symbol} 新闻同步异常: {e}")
        return False

def check_sync_status():
    """检查同步状态"""
    print("🔍 检查同步状态...")
    
    # 检查多数据源同步状态
    try:
        response = requests.get(f"{BASE_URL}/api/sync/multi-source/status")
        if response.status_code == 200:
            result = response.json()
            print(f"📊 多数据源同步状态: {result.get('message', '')}")
        else:
            print(f"⚠️ 无法获取多数据源同步状态: {response.text}")
    except Exception as e:
        print(f"⚠️ 多数据源同步状态查询异常: {e}")
    
    # 检查基础信息同步状态
    try:
        response = requests.get(f"{BASE_URL}/api/sync/stock_basics/status")
        if response.status_code == 200:
            result = response.json()
            print(f"📊 基础信息同步状态: {result.get('message', '')}")
        else:
            print(f"⚠️ 无法获取基础信息同步状态: {response.text}")
    except Exception as e:
        print(f"⚠️ 基础信息同步状态查询异常: {e}")

def main():
    """主函数"""
    print("🚀 手动数据同步触发器")
    print("=" * 50)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 获取认证token
    print("🔑 获取认证token...")
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token，部分功能将无法使用")
    else:
        print("✅ 认证token获取成功")
    print()
    
    # 1. 触发历史数据同步
    success_count = 0
    if trigger_historical_data_sync():
        success_count += 1
    print()
    
    # 2. 触发财务数据同步
    if trigger_financial_data_sync():
        success_count += 1
    print()
    
    # 3. 触发新闻数据同步（需要token）
    if token:
        if trigger_news_data_sync(token):
            success_count += 1
        print()
        
        # 4. 触发单只股票新闻同步
        if trigger_stock_news_sync(token, "000001"):
            success_count += 1
        print()
    else:
        print("⚠️ 跳过新闻数据同步（需要认证）")
        print()
    
    # 5. 检查同步状态
    check_sync_status()
    print()
    
    # 总结
    print("=" * 50)
    print(f"✅ 同步任务启动完成: {success_count} 个任务成功启动")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 后续步骤:")
    print("1. 等待同步任务完成（可能需要几分钟到几十分钟）")
    print("2. 运行测试脚本验证数据: python examples/test_enhanced_data_integration.py")
    print("3. 查看后端日志了解同步进度")

if __name__ == "__main__":
    main()
