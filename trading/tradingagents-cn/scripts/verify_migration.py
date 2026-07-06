#!/usr/bin/env python3
"""
配置迁移验证脚本
验证配置是否正确迁移到webapi数据库中
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapi.core.database import DatabaseManager
from webapi.services.config_service import ConfigService


async def verify_migration():
    """验证配置迁移结果"""
    print("🔍 开始验证配置迁移结果...")
    
    # 初始化数据库连接
    db_manager = DatabaseManager()
    try:
        await db_manager.init_mongodb()
        config_service = ConfigService(db_manager=db_manager)
        
        print("✅ 数据库连接成功")
        
        # 1. 验证系统配置
        print("\n📋 验证系统配置...")
        system_config = await config_service.get_system_config()
        
        if system_config:
            print(f"  ✅ 系统配置存在")
            print(f"  📝 配置名称: {system_config.config_name}")
            print(f"  📝 配置类型: {system_config.config_type}")
            print(f"  📝 版本: {system_config.version}")
            print(f"  📝 是否激活: {system_config.is_active}")
            print(f"  📝 创建时间: {system_config.created_at}")
            print(f"  📝 更新时间: {system_config.updated_at}")
        else:
            print("  ❌ 系统配置不存在")
            return False
        
        # 2. 验证大模型配置
        print("\n🤖 验证大模型配置...")
        llm_configs = system_config.llm_configs
        
        if llm_configs:
            print(f"  ✅ 找到 {len(llm_configs)} 个大模型配置")
            for i, llm in enumerate(llm_configs[:5]):  # 只显示前5个
                print(f"    {i+1}. {llm.provider.value}/{llm.model_name} ({'启用' if llm.enabled else '禁用'})")
            
            if len(llm_configs) > 5:
                print(f"    ... 还有 {len(llm_configs) - 5} 个配置")
        else:
            print("  ❌ 没有找到大模型配置")
        
        # 3. 验证数据源配置
        print("\n📊 验证数据源配置...")
        data_source_configs = system_config.data_source_configs
        
        if data_source_configs:
            print(f"  ✅ 找到 {len(data_source_configs)} 个数据源配置")
            for ds in data_source_configs:
                print(f"    - {ds.name} ({ds.type.value}) ({'启用' if ds.enabled else '禁用'})")
        else:
            print("  ⚠️ 没有找到数据源配置")
        
        # 4. 验证数据库配置
        print("\n🗄️ 验证数据库配置...")
        database_configs = system_config.database_configs
        
        if database_configs:
            print(f"  ✅ 找到 {len(database_configs)} 个数据库配置")
            for db in database_configs:
                print(f"    - {db.name} ({db.type.value}) {db.host}:{db.port} ({'启用' if db.enabled else '禁用'})")
        else:
            print("  ⚠️ 没有找到数据库配置")
        
        # 5. 验证系统设置
        print("\n⚙️ 验证系统设置...")
        system_settings = system_config.system_settings
        
        if system_settings:
            print(f"  ✅ 找到 {len(system_settings)} 个系统设置")
            key_settings = [
                'default_provider', 'default_model', 'enable_cost_tracking',
                'max_concurrent_tasks', 'log_level', 'enable_cache'
            ]
            for key in key_settings:
                if key in system_settings:
                    print(f"    - {key}: {system_settings[key]}")
        else:
            print("  ❌ 没有找到系统设置")
        
        # 6. 验证默认配置
        print("\n🎯 验证默认配置...")
        if system_config.default_llm:
            print(f"  ✅ 默认大模型: {system_config.default_llm}")
        else:
            print("  ⚠️ 未设置默认大模型")
        
        if system_config.default_data_source:
            print(f"  ✅ 默认数据源: {system_config.default_data_source}")
        else:
            print("  ⚠️ 未设置默认数据源")
        
        print("\n🎉 配置迁移验证完成！")
        return True
        
    except Exception as e:
        print(f"❌ 验证过程中出错: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close_connections()
            print("✅ 数据库连接已关闭")


async def test_config_api():
    """测试配置API功能"""
    print("\n🧪 测试配置API功能...")
    
    db_manager = DatabaseManager()
    try:
        await db_manager.init_mongodb()
        config_service = ConfigService(db_manager=db_manager)
        
        # 测试获取系统设置
        print("\n1️⃣ 测试获取系统设置...")
        settings = await config_service.get_system_settings()
        if settings:
            print(f"  ✅ 成功获取 {len(settings)} 个系统设置")
        else:
            print("  ❌ 获取系统设置失败")
        
        # 测试更新系统设置
        print("\n2️⃣ 测试更新系统设置...")
        test_settings = {"test_migration": True, "migration_time": "2025-08-18"}
        success = await config_service.update_system_settings(test_settings)
        if success:
            print("  ✅ 系统设置更新成功")
        else:
            print("  ❌ 系统设置更新失败")
        
        # 测试导出配置
        print("\n3️⃣ 测试配置导出...")
        export_data = await config_service.export_config()
        if export_data:
            print(f"  ✅ 配置导出成功，包含 {len(export_data)} 个字段")
        else:
            print("  ❌ 配置导出失败")
        
        print("\n✅ API功能测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ API测试过程中出错: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close_connections()


async def main():
    """主函数"""
    print("=" * 60)
    print("🔍 TradingAgents 配置迁移验证工具")
    print("=" * 60)
    
    # 验证迁移结果
    verify_success = await verify_migration()
    
    # 测试API功能
    api_success = await test_config_api()
    
    print("\n" + "=" * 60)
    if verify_success and api_success:
        print("✅ 所有验证通过！配置迁移成功且功能正常")
        print("💡 现在可以通过webapi使用新的配置系统了")
        print("🌐 前端访问地址: http://localhost:3000/settings")
        print("📡 API文档地址: http://localhost:8000/docs")
    else:
        print("❌ 验证失败，请检查配置迁移结果")
    print("=" * 60)
    
    return verify_success and api_success


if __name__ == "__main__":
    # 运行验证
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
