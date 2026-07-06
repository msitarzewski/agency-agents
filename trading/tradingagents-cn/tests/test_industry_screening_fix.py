#!/usr/bin/env python3
"""
测试行业筛选修复
验证前端发送行业筛选条件，后端正确处理并返回银行股
"""

import asyncio
import requests
import json
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

async def test_industry_screening():
    """测试行业筛选功能"""
    print("🧪 测试行业筛选修复")
    print("=" * 50)
    
    # 1. 获取访问令牌
    print("\n1. 获取访问令牌...")
    auth_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print(f"❌ 登录失败: {auth_response.status_code}")
        return False
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")
    
    # 2. 测试只有市值条件的筛选（原始问题场景）
    print("\n2. 测试只有市值条件的筛选...")
    market_cap_only_payload = {
        "market": "CN",
        "conditions": {
            "logic": "AND",
            "children": [
                {"field": "market_cap", "op": "between", "value": [5000000, 9007199254740991]}
            ]
        },
        "order_by": [{"field": "market_cap", "direction": "desc"}],
        "limit": 10,
        "offset": 0
    }
    
    response = requests.post(
        f"{BASE_URL}/api/screening/run",
        json=market_cap_only_payload,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"✅ 市值筛选成功，返回 {len(items)} 只股票")
        
        # 显示前3只股票的行业分布
        industries = {}
        for item in items[:3]:
            industry = item.get("industry", "未知")
            industries[industry] = industries.get(industry, 0) + 1
            print(f"   {item['code']} - {item['name']} - {industry}")
        
        print(f"   行业分布: {industries}")
    else:
        print(f"❌ 市值筛选失败: {response.status_code}")
        return False
    
    # 3. 测试加入行业条件的筛选（修复后应该工作）
    print("\n3. 测试加入银行行业条件的筛选...")
    industry_payload = {
        "market": "CN", 
        "conditions": {
            "logic": "AND",
            "children": [
                {"field": "market_cap", "op": "between", "value": [5000000, 9007199254740991]},
                {"field": "industry", "op": "in", "value": ["银行"]}
            ]
        },
        "order_by": [{"field": "market_cap", "direction": "desc"}],
        "limit": 10,
        "offset": 0
    }
    
    response = requests.post(
        f"{BASE_URL}/api/screening/run",
        json=industry_payload,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"✅ 银行行业筛选成功，返回 {len(items)} 只股票")
        
        # 验证所有返回的股票都是银行股
        all_banks = True
        for item in items:
            industry = item.get("industry", "")
            is_bank = "银行" in industry
            print(f"   {item['code']} - {item['name']} - {industry} {'✅' if is_bank else '❌'}")
            if not is_bank:
                all_banks = False
        
        if all_banks and len(items) > 0:
            print("🎉 修复成功！所有返回的股票都是银行股")
            return True
        elif len(items) == 0:
            print("⚠️  没有找到银行股，可能数据库中没有银行行业数据")
            return False
        else:
            print("❌ 修复失败！返回了非银行股")
            return False
    else:
        print(f"❌ 银行行业筛选失败: {response.status_code}")
        print(f"   响应内容: {response.text}")
        return False

def test_frontend_payload():
    """测试前端修复后会发送的payload格式"""
    print("\n4. 测试前端修复后的payload格式...")
    
    # 模拟前端修复后发送的请求
    frontend_payload = {
        "market": "CN",
        "conditions": {
            "logic": "AND", 
            "children": [
                {"field": "market_cap", "op": "between", "value": [500 * 10000, 9007199254740991]},  # 大盘股
                {"field": "industry", "op": "in", "value": ["银行"]}  # 银行行业
            ]
        },
        "order_by": [{"field": "market_cap", "direction": "desc"}],
        "limit": 50,
        "offset": 0
    }
    
    print("前端修复后会发送的payload:")
    print(json.dumps(frontend_payload, indent=2, ensure_ascii=False))
    
    return frontend_payload

if __name__ == "__main__":
    # 测试前端payload格式
    test_frontend_payload()
    
    # 测试后端API
    success = asyncio.run(test_industry_screening())
    
    if success:
        print("\n🎉 行业筛选修复验证成功！")
        print("现在用户选择银行行业时，应该只返回银行股了。")
    else:
        print("\n❌ 行业筛选修复验证失败！")
        print("需要进一步检查数据库数据或后端逻辑。")
