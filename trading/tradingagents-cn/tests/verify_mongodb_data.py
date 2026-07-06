#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB数据验证脚本
验证A股股票基础信息是否正确同步到MongoDB
"""

import os
from typing import Dict, Any, List
from datetime import datetime

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("❌ pymongo未安装，请运行: pip install pymongo")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv未安装，将使用系统环境变量")

def get_mongodb_config() -> Dict[str, Any]:
    """获取MongoDB配置"""
    return {
        'host': os.getenv('MONGODB_HOST', 'localhost'),
        'port': int(os.getenv('MONGODB_PORT', 27018)),
        'username': os.getenv('MONGODB_USERNAME'),
        'password': os.getenv('MONGODB_PASSWORD'),
        'database': os.getenv('MONGODB_DATABASE', 'tradingagents'),
        'auth_source': os.getenv('MONGODB_AUTH_SOURCE', 'admin')
    }

def connect_mongodb():
    """连接MongoDB"""
    if not MONGODB_AVAILABLE:
        return None, None
    
    config = get_mongodb_config()
    
    try:
        # 构建连接字符串
        if config.get('username') and config.get('password'):
            connection_string = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['auth_source']}"
        else:
            connection_string = f"mongodb://{config['host']}:{config['port']}/"
        
        # 创建客户端
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000
        )
        
        # 测试连接
        client.admin.command('ping')
        
        # 选择数据库
        db = client[config['database']]
        
        print(f"✅ MongoDB连接成功: {config['host']}:{config['port']}")
        return client, db
        
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        return None, None

def verify_stock_data(db):
    """验证股票数据"""
    if db is None:
        return
    
    collection = db['stock_basic_info']
    
    print("\n" + "="*60)
    print("📊 MongoDB中的A股基础信息验证")
    print("="*60)
    
    # 1. 总记录数
    total_count = collection.count_documents({})
    print(f"📈 总记录数: {total_count:,}")
    
    # 2. 按市场统计
    print("\n🏢 市场分布:")
    market_pipeline = [
        {'$group': {
            '_id': '$sse',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]
    
    for market in collection.aggregate(market_pipeline):
        market_name = '上海' if market['_id'] == 'sh' else '深圳'
        print(f"  {market_name}市场 ({market['_id']}): {market['count']:,} 条")
    
    # 3. 按分类统计
    print("\n📊 分类分布:")
    category_pipeline = [
        {'$group': {
            '_id': '$sec',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]
    
    for category in collection.aggregate(category_pipeline):
        category_name = {
            'stock_cn': '股票',
            'etf_cn': 'ETF基金',
            'index_cn': '指数',
            'bond_cn': '债券'
        }.get(category['_id'], category['_id'])
        print(f"  {category_name}: {category['count']:,} 条")
    
    # 4. 数据样本
    print("\n📋 数据样本 (前10条):")
    samples = collection.find({}).limit(10)
    
    for i, stock in enumerate(samples, 1):
        market_name = '上海' if stock['sse'] == 'sh' else '深圳'
        print(f"  {i:2d}. {stock['code']} - {stock['name']} ({market_name})")
    
    # 5. 最近更新时间
    latest = collection.find_one({}, sort=[('updated_at', -1)])
    if latest and 'updated_at' in latest:
        print(f"\n🕒 最近更新时间: {latest['updated_at']}")
    
    # 6. 数据完整性检查
    print("\n🔍 数据完整性检查:")
    
    # 检查必需字段
    required_fields = ['code', 'name', 'sse']
    for field in required_fields:
        missing_count = collection.count_documents({field: {'$exists': False}})
        null_count = collection.count_documents({field: None})
        empty_count = collection.count_documents({field: ''})
        
        if missing_count + null_count + empty_count == 0:
            print(f"  ✅ {field}: 完整")
        else:
            print(f"  ⚠️ {field}: 缺失{missing_count}, 空值{null_count}, 空字符串{empty_count}")
    
    # 7. 查询示例
    print("\n🔍 查询示例:")
    
    # 查找平安相关股票
    ping_an_stocks = list(collection.find(
        {'name': {'$regex': '平安', '$options': 'i'}}
    ).limit(5))
    
    if ping_an_stocks:
        print("  平安相关股票:")
        for stock in ping_an_stocks:
            market_name = '上海' if stock['sse'] == 'sh' else '深圳'
            print(f"    {stock['code']} - {stock['name']} ({market_name})")
    
    # 查找ETF
    etf_count = collection.count_documents({'sec': 'etf_cn'})
    print(f"  ETF基金总数: {etf_count:,}")
    
    # 查找指数
    index_count = collection.count_documents({'sec': 'index_cn'})
    print(f"  指数总数: {index_count:,}")

def main():
    """主函数"""
    print("🔍 正在验证MongoDB中的A股基础信息...")
    
    # 连接MongoDB
    client, db = connect_mongodb()
    
    if client is None or db is None:
        print("❌ 无法连接到MongoDB，验证失败")
        return
    
    try:
        # 验证数据
        verify_stock_data(db)
        
        print("\n✅ 数据验证完成")
        
    except Exception as e:
        print(f"❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭连接
        if client:
            client.close()
            print("🔒 MongoDB连接已关闭")

if __name__ == "__main__":
    main()