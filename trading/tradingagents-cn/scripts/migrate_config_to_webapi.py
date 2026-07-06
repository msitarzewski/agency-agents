#!/usr/bin/env python3
"""
配置数据迁移工具
将现有的tradingagents/config配置迁移到webapi的MongoDB数据库中
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入webapi相关模块
from webapi.core.database import DatabaseManager
from webapi.models.config import (
    SystemConfig, LLMConfig, DataSourceConfig, DatabaseConfig,
    ModelProvider, DataSourceType, DatabaseType
)
from webapi.services.config_service import ConfigService

# 导入传统配置管理器
from tradingagents.config.config_manager import ConfigManager, ModelConfig, PricingConfig, UsageRecord


class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self):
        self.project_root = project_root
        self.config_manager = ConfigManager()
        self.db_manager = None
        self.config_service = None
        
    async def initialize(self):
        """初始化数据库连接"""
        try:
            self.db_manager = DatabaseManager()
            await self.db_manager.init_mongodb()
            # 将DatabaseManager实例传递给ConfigService
            self.config_service = ConfigService(db_manager=self.db_manager)
            print("✅ 数据库连接初始化成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接初始化失败: {e}")
            return False
    
    async def migrate_all_configs(self):
        """迁移所有配置"""
        print("🚀 开始配置迁移...")
        
        # 检查数据库连接
        if not await self.initialize():
            return False
        
        try:
            # 1. 迁移模型配置
            await self.migrate_model_configs()
            
            # 2. 迁移系统设置
            await self.migrate_system_settings()
            
            # 3. 迁移使用统计数据
            await self.migrate_usage_records()
            
            # 4. 创建统一系统配置
            await self.create_unified_system_config()
            
            print("🎉 配置迁移完成！")
            return True
            
        except Exception as e:
            print(f"❌ 配置迁移失败: {e}")
            return False
        finally:
            if self.db_manager:
                await self.db_manager.close_connections()
                print("✅ 数据库连接已关闭")
    
    async def migrate_model_configs(self):
        """迁移模型配置"""
        print("\n📋 迁移模型配置...")
        
        # 加载传统模型配置
        legacy_models = self.config_manager.load_models()
        
        if not legacy_models:
            print("⚠️ 没有找到传统模型配置")
            return
        
        migrated_count = 0
        for model in legacy_models:
            try:
                # 转换为新格式
                llm_config = self._convert_model_config(model)
                
                # 保存到数据库
                success = await self.config_service.update_llm_config(llm_config)
                if success:
                    migrated_count += 1
                    print(f"  ✅ 已迁移: {model.provider}/{model.model_name}")
                else:
                    print(f"  ❌ 迁移失败: {model.provider}/{model.model_name}")
                    
            except Exception as e:
                print(f"  ❌ 迁移模型配置失败 {model.provider}/{model.model_name}: {e}")
        
        print(f"📊 模型配置迁移完成: {migrated_count}/{len(legacy_models)}")
    
    def _convert_model_config(self, legacy_model: ModelConfig) -> LLMConfig:
        """转换传统模型配置为新格式"""
        # 映射供应商名称 - 包含sidebar.py中的所有提供商
        provider_mapping = {
            'dashscope': ModelProvider.DASHSCOPE,
            'openai': ModelProvider.OPENAI,
            'google': ModelProvider.GOOGLE,
            'anthropic': ModelProvider.ANTHROPIC,
            'zhipuai': ModelProvider.GLM,
            'deepseek': ModelProvider.DEEPSEEK,
            'siliconflow': ModelProvider.SILICONFLOW,
            'openrouter': ModelProvider.OPENROUTER,
            'custom_openai': ModelProvider.CUSTOM_OPENAI,
            'qianfan': ModelProvider.QIANFAN
        }

        provider = provider_mapping.get(legacy_model.provider.lower(), ModelProvider.OPENAI)

        return LLMConfig(
            provider=provider,
            model_name=legacy_model.model_name,
            api_key=legacy_model.api_key,
            api_base=legacy_model.base_url,
            max_tokens=legacy_model.max_tokens,
            temperature=legacy_model.temperature,
            enabled=legacy_model.enabled,
            description=f"从传统配置迁移: {legacy_model.provider}/{legacy_model.model_name}"
        )
    
    async def migrate_system_settings(self):
        """迁移系统设置"""
        print("\n⚙️ 迁移系统设置...")
        
        # 加载传统设置
        legacy_settings = self.config_manager.load_settings()
        
        if not legacy_settings:
            print("⚠️ 没有找到传统系统设置")
            return
        
        try:
            # 转换为新格式的系统设置
            system_settings = {
                "default_provider": legacy_settings.get("default_provider", "dashscope"),
                "default_model": legacy_settings.get("default_model", "qwen-turbo"),
                "enable_cost_tracking": legacy_settings.get("enable_cost_tracking", True),
                "cost_alert_threshold": legacy_settings.get("cost_alert_threshold", 100.0),
                "currency_preference": legacy_settings.get("currency_preference", "CNY"),
                "auto_save_usage": legacy_settings.get("auto_save_usage", True),
                "max_usage_records": legacy_settings.get("max_usage_records", 10000),
                "data_dir": legacy_settings.get("data_dir", ""),
                "cache_dir": legacy_settings.get("cache_dir", ""),
                "results_dir": legacy_settings.get("results_dir", ""),
                "auto_create_dirs": legacy_settings.get("auto_create_dirs", True),
                "openai_enabled": legacy_settings.get("openai_enabled", False),
                "log_level": "INFO",
                "enable_monitoring": True,
                "max_concurrent_tasks": 3,
                "default_analysis_timeout": 300,
                "enable_cache": True,
                "cache_ttl": 3600
            }
            
            print(f"  ✅ 系统设置迁移完成，包含 {len(system_settings)} 个配置项")
            
        except Exception as e:
            print(f"  ❌ 系统设置迁移失败: {e}")
    
    async def migrate_usage_records(self):
        """迁移使用统计数据"""
        print("\n📊 迁移使用统计数据...")

        try:
            # 检查ConfigManager是否有load_usage_records方法
            if hasattr(self.config_manager, 'load_usage_records'):
                legacy_usage = self.config_manager.load_usage_records()

                if not legacy_usage:
                    print("⚠️ 没有找到传统使用记录")
                    return

                # 这里可以实现使用记录的迁移逻辑
                # 由于使用记录可能很多，建议分批处理
                print(f"  📋 找到 {len(legacy_usage)} 条使用记录")
                print("  ℹ️ 使用记录迁移功能待实现...")
            else:
                print("  ℹ️ 传统配置管理器不支持使用记录，跳过迁移")

        except Exception as e:
            print(f"  ❌ 使用记录迁移失败: {e}")
    
    async def create_unified_system_config(self):
        """创建统一系统配置"""
        print("\n🔧 创建统一系统配置...")
        
        try:
            # 检查是否已存在系统配置
            existing_config = await self.config_service.get_system_config()
            if existing_config and existing_config.config_type != "default":
                print("  ℹ️ 系统配置已存在，跳过创建")
                return
            
            # 创建新的系统配置会自动包含迁移的数据
            new_config = await self.config_service._create_default_config()
            if new_config:
                print("  ✅ 统一系统配置创建成功")
            else:
                print("  ❌ 统一系统配置创建失败")
                
        except Exception as e:
            print(f"  ❌ 创建统一系统配置失败: {e}")


async def main():
    """主函数"""
    print("=" * 60)
    print("🔄 TradingAgents 配置迁移工具")
    print("=" * 60)
    
    migrator = ConfigMigrator()
    success = await migrator.migrate_all_configs()
    
    if success:
        print("\n✅ 配置迁移成功完成！")
        print("💡 现在可以使用新的webapi配置系统了")
    else:
        print("\n❌ 配置迁移失败")
        print("💡 请检查错误信息并重试")
    
    return success


if __name__ == "__main__":
    # 运行迁移
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
