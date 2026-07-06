#!/usr/bin/env python3
"""
配置兼容性测试脚本
测试统一配置管理系统与现有系统的兼容性
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapi.core.unified_config import unified_config
from webapi.models.config import LLMConfig, ModelProvider


async def test_read_legacy_configs():
    """测试读取传统配置"""
    print("🔍 测试读取传统配置...")
    
    try:
        # 测试读取模型配置
        legacy_models = unified_config.get_legacy_models()
        print(f"  ✅ 读取传统模型配置: {len(legacy_models)} 个")
        
        # 测试转换为标准格式
        llm_configs = unified_config.get_llm_configs()
        print(f"  ✅ 转换为标准LLM配置: {len(llm_configs)} 个")
        
        # 测试读取系统设置
        settings = unified_config.get_system_settings()
        print(f"  ✅ 读取系统设置: {len(settings)} 个")
        
        return True
    except Exception as e:
        print(f"  ❌ 读取传统配置失败: {e}")
        return False


async def test_write_legacy_configs():
    """测试写入传统配置"""
    print("\n💾 测试写入传统配置...")
    
    try:
        # 创建测试LLM配置
        test_llm_config = LLMConfig(
            provider=ModelProvider.OPENAI,
            model_name="test-gpt-3.5-turbo",
            api_key="test-api-key",
            api_base="https://api.openai.com/v1",
            max_tokens=4000,
            temperature=0.7,
            enabled=True,
            description="测试配置"
        )
        
        # 保存到传统格式
        success = unified_config.save_llm_config(test_llm_config)
        if success:
            print("  ✅ 保存LLM配置到传统格式成功")
        else:
            print("  ❌ 保存LLM配置到传统格式失败")
            return False
        
        # 验证保存结果
        legacy_models = unified_config.get_legacy_models()
        test_model_found = any(
            model.get("model_name") == "test-gpt-3.5-turbo" 
            for model in legacy_models
        )
        
        if test_model_found:
            print("  ✅ 验证保存结果成功")
        else:
            print("  ❌ 验证保存结果失败")
            return False
        
        # 清理测试数据
        legacy_models = [
            model for model in legacy_models 
            if model.get("model_name") != "test-gpt-3.5-turbo"
        ]
        unified_config._save_json_file(
            unified_config.paths.models_json, 
            legacy_models, 
            "models"
        )
        print("  ✅ 清理测试数据完成")
        
        return True
    except Exception as e:
        print(f"  ❌ 写入传统配置失败: {e}")
        return False


async def test_unified_system_config():
    """测试统一系统配置"""
    print("\n🔧 测试统一系统配置...")
    
    try:
        # 获取统一配置
        system_config = await unified_config.get_unified_system_config()
        
        print(f"  ✅ 配置名称: {system_config.config_name}")
        print(f"  ✅ LLM配置数量: {len(system_config.llm_configs)}")
        print(f"  ✅ 数据源数量: {len(system_config.data_source_configs)}")
        print(f"  ✅ 数据库数量: {len(system_config.database_configs)}")
        print(f"  ✅ 默认LLM: {system_config.default_llm}")
        
        return True
    except Exception as e:
        print(f"  ❌ 统一系统配置测试失败: {e}")
        return False


async def test_config_sync():
    """测试配置同步"""
    print("\n🔄 测试配置同步...")
    
    try:
        # 获取统一配置
        system_config = await unified_config.get_unified_system_config()
        
        # 测试同步到传统格式
        success = unified_config.sync_to_legacy_format(system_config)
        if success:
            print("  ✅ 同步到传统格式成功")
        else:
            print("  ❌ 同步到传统格式失败")
            return False
        
        # 验证同步结果
        legacy_models = unified_config.get_legacy_models()
        settings = unified_config.get_system_settings()
        
        print(f"  ✅ 同步后模型数量: {len(legacy_models)}")
        print(f"  ✅ 同步后设置数量: {len(settings)}")
        
        return True
    except Exception as e:
        print(f"  ❌ 配置同步测试失败: {e}")
        return False


async def test_default_model_management():
    """测试默认模型管理"""
    print("\n🎯 测试默认模型管理...")
    
    try:
        # 获取当前默认模型
        current_default = unified_config.get_default_model()
        print(f"  ✅ 当前默认模型: {current_default}")
        
        # 测试设置默认模型
        test_model = "test-model"
        success = unified_config.set_default_model(test_model)
        if success:
            print(f"  ✅ 设置默认模型成功: {test_model}")
        else:
            print("  ❌ 设置默认模型失败")
            return False
        
        # 验证设置结果
        new_default = unified_config.get_default_model()
        if new_default == test_model:
            print("  ✅ 验证默认模型设置成功")
        else:
            print("  ❌ 验证默认模型设置失败")
            return False
        
        # 恢复原始默认模型
        unified_config.set_default_model(current_default)
        print(f"  ✅ 恢复原始默认模型: {current_default}")
        
        return True
    except Exception as e:
        print(f"  ❌ 默认模型管理测试失败: {e}")
        return False


async def test_data_source_configs():
    """测试数据源配置"""
    print("\n🔌 测试数据源配置...")
    
    try:
        data_sources = unified_config.get_data_source_configs()
        
        print(f"  ✅ 数据源数量: {len(data_sources)}")
        for ds in data_sources:
            print(f"    - {ds.name}: {ds.type.value} ({'启用' if ds.enabled else '禁用'})")
        
        return True
    except Exception as e:
        print(f"  ❌ 数据源配置测试失败: {e}")
        return False


async def test_database_configs():
    """测试数据库配置"""
    print("\n🗄️ 测试数据库配置...")
    
    try:
        databases = unified_config.get_database_configs()
        
        print(f"  ✅ 数据库数量: {len(databases)}")
        for db in databases:
            print(f"    - {db.name}: {db.type.value} ({db.host}:{db.port})")
        
        return True
    except Exception as e:
        print(f"  ❌ 数据库配置测试失败: {e}")
        return False


async def test_cache_functionality():
    """测试缓存功能"""
    print("\n⚡ 测试缓存功能...")
    
    try:
        # 清空缓存
        unified_config._cache.clear()
        unified_config._last_modified.clear()
        
        # 第一次读取（应该从文件读取）
        models1 = unified_config.get_legacy_models()
        print(f"  ✅ 第一次读取: {len(models1)} 个模型")
        
        # 第二次读取（应该从缓存读取）
        models2 = unified_config.get_legacy_models()
        print(f"  ✅ 第二次读取: {len(models2)} 个模型")
        
        # 验证缓存是否生效
        if "models" in unified_config._cache:
            print("  ✅ 缓存功能正常")
        else:
            print("  ❌ 缓存功能异常")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ 缓存功能测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🧪 开始配置兼容性测试...")
    print("=" * 50)
    
    tests = [
        ("读取传统配置", test_read_legacy_configs),
        ("写入传统配置", test_write_legacy_configs),
        ("统一系统配置", test_unified_system_config),
        ("配置同步", test_config_sync),
        ("默认模型管理", test_default_model_management),
        ("数据源配置", test_data_source_configs),
        ("数据库配置", test_database_configs),
        ("缓存功能", test_cache_functionality),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                failed += 1
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试结果摘要:")
    print(f"  ✅ 通过: {passed} 个测试")
    print(f"  ❌ 失败: {failed} 个测试")
    print(f"  📊 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 所有测试通过！配置兼容性良好。")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查配置系统。")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
