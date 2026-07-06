#!/usr/bin/env python3
"""
配置迁移工具
将现有的配置文件迁移到统一配置管理系统
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapi.core.unified_config import unified_config
from webapi.models.config import SystemConfig


def check_existing_configs():
    """检查现有配置文件"""
    print("🔍 检查现有配置文件...")
    
    config_files = [
        "config/models.json",
        "config/settings.json", 
        "config/pricing.json",
        "config/verified_models.json",
        "tradingagents/config/config_manager.py"
    ]
    
    existing_files = []
    for file_path in config_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"  ✅ 找到: {file_path}")
        else:
            print(f"  ❌ 缺失: {file_path}")
    
    return existing_files


def migrate_models_config():
    """迁移模型配置"""
    print("\n📦 迁移模型配置...")
    
    try:
        llm_configs = unified_config.get_llm_configs()
        print(f"  发现 {len(llm_configs)} 个模型配置:")
        
        for config in llm_configs:
            print(f"    - {config.provider.value}: {config.model_name}")
            print(f"      API Base: {config.api_base}")
            print(f"      启用状态: {'✅' if config.enabled else '❌'}")
        
        return llm_configs
    except Exception as e:
        print(f"  ❌ 迁移模型配置失败: {e}")
        return []


def migrate_system_settings():
    """迁移系统设置"""
    print("\n⚙️ 迁移系统设置...")
    
    try:
        settings = unified_config.get_system_settings()
        print(f"  发现 {len(settings)} 个系统设置:")
        
        for key, value in settings.items():
            print(f"    - {key}: {value}")
        
        return settings
    except Exception as e:
        print(f"  ❌ 迁移系统设置失败: {e}")
        return {}


def migrate_data_sources():
    """迁移数据源配置"""
    print("\n🔌 迁移数据源配置...")
    
    try:
        data_sources = unified_config.get_data_source_configs()
        print(f"  发现 {len(data_sources)} 个数据源:")
        
        for ds in data_sources:
            print(f"    - {ds.name} ({ds.type.value})")
            print(f"      端点: {ds.endpoint}")
            print(f"      启用状态: {'✅' if ds.enabled else '❌'}")
        
        return data_sources
    except Exception as e:
        print(f"  ❌ 迁移数据源配置失败: {e}")
        return []


def migrate_database_configs():
    """迁移数据库配置"""
    print("\n🗄️ 迁移数据库配置...")
    
    try:
        databases = unified_config.get_database_configs()
        print(f"  发现 {len(databases)} 个数据库配置:")
        
        for db in databases:
            print(f"    - {db.name} ({db.type.value})")
            print(f"      地址: {db.host}:{db.port}")
            print(f"      启用状态: {'✅' if db.enabled else '❌'}")
        
        return databases
    except Exception as e:
        print(f"  ❌ 迁移数据库配置失败: {e}")
        return []


async def create_unified_config():
    """创建统一配置"""
    print("\n🔧 创建统一配置...")
    
    try:
        unified_system_config = await unified_config.get_unified_system_config()
        
        print("  ✅ 统一配置创建成功:")
        print(f"    - 配置名称: {unified_system_config.config_name}")
        print(f"    - LLM配置数量: {len(unified_system_config.llm_configs)}")
        print(f"    - 数据源数量: {len(unified_system_config.data_source_configs)}")
        print(f"    - 数据库数量: {len(unified_system_config.database_configs)}")
        print(f"    - 默认LLM: {unified_system_config.default_llm}")
        print(f"    - 默认数据源: {unified_system_config.default_data_source}")
        
        return unified_system_config
    except Exception as e:
        print(f"  ❌ 创建统一配置失败: {e}")
        return None


def backup_existing_configs():
    """备份现有配置"""
    print("\n💾 备份现有配置...")
    
    backup_dir = Path("config_backup")
    backup_dir.mkdir(exist_ok=True)
    
    config_files = [
        "config/models.json",
        "config/settings.json",
        "config/pricing.json",
        "config/verified_models.json"
    ]
    
    for file_path in config_files:
        src = Path(file_path)
        if src.exists():
            dst = backup_dir / src.name
            import shutil
            shutil.copy2(src, dst)
            print(f"  ✅ 备份: {file_path} -> {dst}")


def test_unified_config():
    """测试统一配置"""
    print("\n🧪 测试统一配置...")
    
    try:
        # 测试获取模型配置
        models = unified_config.get_llm_configs()
        print(f"  ✅ 模型配置测试通过: {len(models)} 个模型")
        
        # 测试获取系统设置
        settings = unified_config.get_system_settings()
        print(f"  ✅ 系统设置测试通过: {len(settings)} 个设置")
        
        # 测试获取默认模型
        default_model = unified_config.get_default_model()
        print(f"  ✅ 默认模型测试通过: {default_model}")
        
        return True
    except Exception as e:
        print(f"  ❌ 统一配置测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 开始配置迁移...")
    print("=" * 50)
    
    # 1. 检查现有配置
    existing_files = check_existing_configs()
    if not existing_files:
        print("\n❌ 没有找到现有配置文件，退出迁移")
        return
    
    # 2. 备份现有配置
    backup_existing_configs()
    
    # 3. 迁移各类配置
    llm_configs = migrate_models_config()
    settings = migrate_system_settings()
    data_sources = migrate_data_sources()
    databases = migrate_database_configs()
    
    # 4. 创建统一配置
    unified_system_config = await create_unified_config()
    if not unified_system_config:
        print("\n❌ 统一配置创建失败，退出迁移")
        return
    
    # 5. 测试统一配置
    if not test_unified_config():
        print("\n❌ 统一配置测试失败，请检查配置")
        return
    
    print("\n" + "=" * 50)
    print("🎉 配置迁移完成!")
    print("\n📋 迁移摘要:")
    print(f"  - LLM配置: {len(llm_configs)} 个")
    print(f"  - 系统设置: {len(settings)} 个")
    print(f"  - 数据源: {len(data_sources)} 个")
    print(f"  - 数据库: {len(databases)} 个")
    print(f"  - 默认LLM: {unified_system_config.default_llm}")
    print(f"  - 配置备份: config_backup/ 目录")
    
    print("\n💡 使用建议:")
    print("  1. 现有配置文件已备份到 config_backup/ 目录")
    print("  2. 统一配置管理器会自动读取现有配置文件")
    print("  3. 通过 WebAPI 修改的配置会同步到传统格式")
    print("  4. 可以继续使用原有的配置文件格式")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
