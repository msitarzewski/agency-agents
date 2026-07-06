#!/usr/bin/env python3
"""
检查MongoDB中保存的数据结构
"""

from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

def check_mongodb_data():
    """检查MongoDB中保存的数据结构"""
    print("🔍 检查MongoDB中保存的数据结构")
    print("=" * 60)

    try:
        # 加载环境变量
        load_dotenv()

        # 从环境变量获取MongoDB配置
        mongodb_host = os.getenv("MONGODB_HOST", "localhost")
        mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongodb_username = os.getenv("MONGODB_USERNAME")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_database = os.getenv("MONGODB_DATABASE", "tradingagents")
        mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")

        print(f"📡 连接MongoDB: {mongodb_host}:{mongodb_port}")
        print(f"📊 数据库: {mongodb_database}")
        print(f"👤 用户: {mongodb_username}")

        # 构建连接参数
        connect_kwargs = {
            "host": mongodb_host,
            "port": mongodb_port,
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000
        }

        # 如果有用户名和密码，添加认证信息
        if mongodb_username and mongodb_password:
            connect_kwargs.update({
                "username": mongodb_username,
                "password": mongodb_password,
                "authSource": mongodb_auth_source
            })

        # 连接MongoDB
        client = MongoClient(**connect_kwargs)

        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB连接成功")

        # 选择数据库和集合
        db = client[mongodb_database]
        collection = db['analysis_reports']
        
        # 获取最新的几条记录
        latest_records = collection.find().sort("created_at", -1).limit(3)
        
        for i, record in enumerate(latest_records, 1):
            print(f"\n📋 记录 {i}:")
            print(f"   analysis_id: {record.get('analysis_id')}")
            print(f"   stock_symbol: {record.get('stock_symbol')}")
            print(f"   analysts: {record.get('analysts', [])}")
            print(f"   research_depth: {record.get('research_depth')}")
            print(f"   source: {record.get('source')}")
            
            # 检查reports字段的详细结构
            reports = record.get('reports', {})
            print(f"\n   📊 reports字段包含 {len(reports)} 个报告:")
            
            if reports:
                for report_type, content in reports.items():
                    if isinstance(content, str):
                        content_preview = content[:100].replace('\n', ' ') + "..." if len(content) > 100 else content
                        print(f"      - {report_type}: {len(content)} 字符")
                        print(f"        预览: {content_preview}")
                    else:
                        print(f"      - {report_type}: {type(content)} - {content}")
            else:
                print(f"      ❌ reports字段为空")
            
            print(f"   " + "="*50)
        
        # 统计所有reports字段中的键
        print(f"\n📊 统计所有reports字段中的键:")
        all_report_keys = set()
        
        all_records = collection.find({}, {"reports": 1})
        for record in all_records:
            reports = record.get('reports', {})
            if isinstance(reports, dict):
                all_report_keys.update(reports.keys())
        
        print(f"   发现的所有报告类型: {sorted(all_report_keys)}")
        
        # 检查前端期望的字段
        expected_fields = [
            'market_report',
            'fundamentals_report', 
            'sentiment_report',
            'news_report',
            'investment_plan',
            'trader_investment_plan',
            'final_trade_decision',
            'investment_debate_state',
            'risk_debate_state',
            'research_team_decision',
            'risk_management_decision'
        ]
        
        print(f"\n🎯 前端期望的字段:")
        for field in expected_fields:
            if field in all_report_keys:
                print(f"   ✅ {field} - 存在")
            else:
                print(f"   ❌ {field} - 缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    check_mongodb_data()
