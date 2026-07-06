#!/usr/bin/env python3
"""
检查股票300750的MongoDB数据
"""

import pymongo
from tradingagents.config.database_manager import get_database_manager

print('=== 检查股票300750的MongoDB数据 ===')

try:
    db_manager = get_database_manager()
    
    if not db_manager.is_mongodb_available():
        print('❌ MongoDB不可用')
        exit(1)
    
    client = db_manager.get_mongodb_client()
    db = client['tradingagents']
    collection = db['stock_financial_data']
    
    doc = collection.find_one({'code': '300750'})
    
    if doc:
        print('✅ 找到300750的财务数据')
        print(f'数据字段数量: {len(doc.keys())}')
        
        # 查找估值相关字段
        valuation_keywords = ['pe', 'pb', 'ps', 'eps', 'bps', 'price', 'market', 'cap']
        
        print('\n🔍 估值相关字段:')
        found_fields = []
        for key, value in doc.items():
            if any(keyword in key.lower() for keyword in valuation_keywords):
                found_fields.append(key)
                print(f'  {key}: {value}')
        
        if not found_fields:
            print('  ❌ 未找到估值指标字段')
        
        print('\n📊 前20个字段:')
        for i, key in enumerate(list(doc.keys())[:20], 1):
            print(f'  {i:2d}. {key}')
                
    else:
        print('❌ 未找到300750的财务数据')
        sample_docs = list(collection.find().limit(3))
        if sample_docs:
            print('\n📋 样本股票代码:')
            for doc in sample_docs:
                print(f'  - {doc.get("code", "未知")}')
    
    client.close()
    
except Exception as e:
    print(f'检查数据时出错: {e}')
    import traceback
    traceback.print_exc()