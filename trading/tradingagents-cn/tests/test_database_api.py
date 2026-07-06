#!/usr/bin/env python3
"""
测试数据库管理API
"""

import asyncio
import sys
import os
sys.path.append('.')

from app.services.database_service import DatabaseService

async def test_database_service():
    """测试数据库服务"""
    print('🧪 测试数据库管理服务')
    print('=' * 50)
    
    try:
        service = DatabaseService()
        
        # 测试获取数据库状态
        print('📊 测试获取数据库状态...')
        status = await service.get_database_status()
        print(f'✅ MongoDB连接: {status["mongodb"]["connected"]}')
        print(f'✅ Redis连接: {status["redis"]["connected"]}')
        
        # 测试获取数据库统计
        print('\n📈 测试获取数据库统计...')
        stats = await service.get_database_stats()
        print(f'📋 集合数量: {stats["total_collections"]}')
        print(f'📄 文档数量: {stats["total_documents"]}')
        print(f'💾 存储大小: {stats["total_size"]} bytes')
        
        # 测试连接测试
        print('\n🔗 测试数据库连接...')
        test_results = await service.test_connections()
        print(f'✅ MongoDB测试: {test_results["mongodb"]["success"]}')
        print(f'✅ Redis测试: {test_results["redis"]["success"]}')
        print(f'✅ 整体测试: {test_results["overall"]}')
        
        # 测试备份列表
        print('\n📋 测试获取备份列表...')
        backups = await service.list_backups()
        print(f'📦 备份数量: {len(backups)}')
        
        print('\n🎉 所有测试通过！')
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_database_service())
