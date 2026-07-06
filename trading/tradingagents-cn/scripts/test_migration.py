#!/usr/bin/env python3
"""
配置迁移测试脚本
测试配置迁移工具的功能
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.migrate_config_to_webapi import ConfigMigrator
from tradingagents.config.config_manager import ConfigManager


async def test_migration():
    """测试配置迁移功能"""
    print("🧪 开始测试配置迁移功能...")
    
    # 1. 检查传统配置是否存在
    print("\n1️⃣ 检查传统配置...")
    config_manager = ConfigManager()
    
    # 检查模型配置
    models = config_manager.load_models()
    print(f"   📋 找到 {len(models)} 个模型配置")
    for model in models[:3]:  # 只显示前3个
        print(f"      - {model.provider}/{model.model_name} ({'启用' if model.enabled else '禁用'})")
    
    # 检查系统设置
    settings = config_manager.load_settings()
    print(f"   ⚙️ 找到 {len(settings)} 个系统设置")
    key_settings = ['default_provider', 'default_model', 'enable_cost_tracking']
    for key in key_settings:
        if key in settings:
            print(f"      - {key}: {settings[key]}")
    
    # 检查使用记录
    usage = config_manager.load_usage()
    print(f"   📊 找到 {len(usage)} 条使用记录")
    
    # 2. 测试迁移器初始化
    print("\n2️⃣ 测试迁移器初始化...")
    migrator = ConfigMigrator()
    
    # 检查数据库连接（如果可用）
    try:
        init_success = await migrator.initialize()
        if init_success:
            print("   ✅ 迁移器初始化成功")
        else:
            print("   ❌ 迁移器初始化失败（可能是数据库未启动）")
            return False
    except Exception as e:
        print(f"   ❌ 迁移器初始化异常: {e}")
        return False
    
    # 3. 测试配置转换
    print("\n3️⃣ 测试配置转换...")
    if models:
        test_model = models[0]
        try:
            converted = migrator._convert_model_config(test_model)
            print(f"   ✅ 模型配置转换成功: {test_model.provider}/{test_model.model_name}")
            print(f"      转换后: {converted.provider.value}/{converted.model_name}")
        except Exception as e:
            print(f"   ❌ 模型配置转换失败: {e}")
    
    # 4. 执行完整迁移（如果数据库可用）
    print("\n4️⃣ 执行配置迁移...")
    try:
        success = await migrator.migrate_all_configs()
        if success:
            print("   ✅ 配置迁移测试成功")
        else:
            print("   ❌ 配置迁移测试失败")
        return success
    except Exception as e:
        print(f"   ❌ 配置迁移测试异常: {e}")
        return False


def test_config_files():
    """测试配置文件的存在性"""
    print("\n📁 检查配置文件...")
    
    config_dir = project_root / "config"
    files_to_check = ["models.json", "pricing.json", "settings.json", "usage.json"]
    
    for file_name in files_to_check:
        file_path = config_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name} 存在")
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"      包含 {len(data) if isinstance(data, list) else '1'} 项数据")
            except Exception as e:
                print(f"      ⚠️ 读取失败: {e}")
        else:
            print(f"   ❌ {file_name} 不存在")


def test_env_file():
    """测试.env文件"""
    print("\n🔐 检查环境变量文件...")
    
    env_file = project_root / ".env"
    if env_file.exists():
        print("   ✅ .env 文件存在")
        
        # 检查关键环境变量
        key_vars = [
            "DASHSCOPE_API_KEY",
            "OPENAI_API_KEY", 
            "MONGODB_CONNECTION_STRING",
            "MONGODB_DATABASE_NAME"
        ]
        
        for var in key_vars:
            value = os.getenv(var)
            if value:
                # 隐藏敏感信息
                display_value = value[:8] + "..." if len(value) > 8 else "***"
                print(f"      ✅ {var}: {display_value}")
            else:
                print(f"      ❌ {var}: 未设置")
    else:
        print("   ❌ .env 文件不存在")


async def main():
    """主函数"""
    print("=" * 60)
    print("🔬 TradingAgents 配置迁移测试")
    print("=" * 60)
    
    # 测试配置文件
    test_config_files()
    
    # 测试环境变量
    test_env_file()
    
    # 测试迁移功能
    success = await test_migration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！配置迁移功能正常")
    else:
        print("❌ 测试失败，请检查配置和数据库连接")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
