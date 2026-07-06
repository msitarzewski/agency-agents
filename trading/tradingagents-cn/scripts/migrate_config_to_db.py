"""
配置迁移脚本：JSON → MongoDB

将旧的 JSON 配置文件迁移到 MongoDB 数据库中。

使用方法：
    python scripts/migrate_config_to_db.py [--dry-run] [--backup] [--force]

参数：
    --dry-run   仅显示将要迁移的内容，不实际执行
    --backup    迁移前备份现有配置
    --force     强制覆盖已存在的配置
"""

import sys
import os
import json
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.config import ModelProvider, DataSourceType


class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self, dry_run: bool = False, backup: bool = True, force: bool = False):
        self.dry_run = dry_run
        self.backup = backup
        self.force = force
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
        # 配置文件路径
        self.config_dir = Path("config")
        self.models_file = self.config_dir / "models.json"
        self.settings_file = self.config_dir / "settings.json"
        self.pricing_file = self.config_dir / "pricing.json"
        self.usage_file = self.config_dir / "usage.json"
        
        # 备份目录
        self.backup_dir = self.config_dir / "backup"
        
    async def connect_db(self):
        """连接数据库"""
        print("📡 连接数据库...")
        
        # 构建 MongoDB URI
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            uri = f"mongodb://{settings.MONGODB_USERNAME}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DATABASE}?authSource={settings.MONGODB_AUTH_SOURCE}"
        else:
            uri = f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DATABASE}"
        
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[settings.MONGODB_DATABASE]
        
        # 测试连接
        try:
            await self.client.admin.command('ping')
            print(f"✅ 数据库连接成功: {settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DATABASE}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise
    
    async def close_db(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            print("📡 数据库连接已关闭")
    
    def backup_configs(self):
        """备份现有配置文件"""
        if not self.backup:
            return
        
        print("\n📦 备份配置文件...")
        
        # 创建备份目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 备份 JSON 文件
        files_to_backup = [
            self.models_file,
            self.settings_file,
            self.pricing_file,
            self.usage_file
        ]
        
        backed_up = 0
        for file_path in files_to_backup:
            if file_path.exists():
                dest = backup_path / file_path.name
                shutil.copy2(file_path, dest)
                print(f"  ✅ {file_path.name} → {dest}")
                backed_up += 1
        
        print(f"✅ 备份完成: {backed_up} 个文件 → {backup_path}")
    
    def load_json_file(self, file_path: Path) -> Optional[Any]:
        """加载 JSON 文件"""
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path}: {e}")
            return None
    
    async def migrate_llm_configs(self):
        """迁移大模型配置"""
        print("\n🤖 迁移大模型配置...")
        
        # 加载 models.json
        models_data = self.load_json_file(self.models_file)
        if not models_data:
            print("⚠️  跳过大模型配置迁移")
            return
        
        # 加载 pricing.json
        pricing_data = self.load_json_file(self.pricing_file)
        pricing_map = {}
        if pricing_data:
            for item in pricing_data:
                key = f"{item['provider']}:{item['model_name']}"
                pricing_map[key] = item
        
        print(f"  发现 {len(models_data)} 个模型配置")
        
        if self.dry_run:
            print("  [DRY RUN] 将要迁移的模型:")
            for model in models_data:
                print(f"    • {model['provider']}: {model['model_name']} (enabled={model.get('enabled', False)})")
            return
        
        # 获取或创建系统配置
        system_config = await self.db.system_configs.find_one({"config_type": "system"})
        
        if not system_config:
            # 创建新的系统配置
            system_config = {
                "config_type": "system",
                "llm_configs": [],
                "data_source_configs": [],
                "database_config": {},
                "system_settings": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        
        # 转换模型配置
        llm_configs = []
        for model in models_data:
            provider = model.get('provider', '')
            model_name = model.get('model_name', '')
            
            # 获取定价信息
            pricing_key = f"{provider}:{model_name}"
            pricing = pricing_map.get(pricing_key, {})
            
            # 从环境变量获取 API 密钥
            api_key = model.get('api_key', '')
            if not api_key:
                # 尝试从环境变量获取
                env_key_map = {
                    'openai': 'OPENAI_API_KEY',
                    'dashscope': 'DASHSCOPE_API_KEY',
                    'deepseek': 'DEEPSEEK_API_KEY',
                    'google': 'GOOGLE_API_KEY',
                    'zhipu': 'ZHIPU_API_KEY',
                }
                env_key = env_key_map.get(provider)
                if env_key:
                    api_key = os.getenv(env_key, '')
            
            llm_config = {
                "provider": provider,
                "model_name": model_name,
                "api_key": api_key,
                "base_url": model.get('base_url'),
                "max_tokens": model.get('max_tokens', 4000),
                "temperature": model.get('temperature', 0.7),
                "enabled": model.get('enabled', False),
                "is_default": False,  # 第一个启用的模型设为默认
                "input_price_per_1k": pricing.get('input_price_per_1k', 0.0),
                "output_price_per_1k": pricing.get('output_price_per_1k', 0.0),
                "currency": pricing.get('currency', 'USD'),
                "extra_params": {}
            }
            
            llm_configs.append(llm_config)
            print(f"  ✅ {provider}: {model_name}")
        
        # 设置第一个启用的模型为默认
        for config in llm_configs:
            if config['enabled']:
                config['is_default'] = True
                break
        
        # 更新或插入系统配置
        system_config['llm_configs'] = llm_configs
        system_config['updated_at'] = datetime.utcnow()
        
        if self.force or not await self.db.system_configs.find_one({"config_type": "system"}):
            await self.db.system_configs.replace_one(
                {"config_type": "system"},
                system_config,
                upsert=True
            )
            print(f"✅ 成功迁移 {len(llm_configs)} 个大模型配置")
        else:
            print("⚠️  系统配置已存在，使用 --force 强制覆盖")
    
    async def migrate_system_settings(self):
        """迁移系统设置"""
        print("\n⚙️  迁移系统设置...")
        
        # 加载 settings.json
        settings_data = self.load_json_file(self.settings_file)
        if not settings_data:
            print("⚠️  跳过系统设置迁移")
            return
        
        print(f"  发现 {len(settings_data)} 个系统设置")
        
        if self.dry_run:
            print("  [DRY RUN] 将要迁移的设置:")
            for key, value in settings_data.items():
                print(f"    • {key}: {value}")
            return
        
        # 获取或创建系统配置
        system_config = await self.db.system_configs.find_one({"config_type": "system"})
        
        if not system_config:
            system_config = {
                "config_type": "system",
                "llm_configs": [],
                "data_source_configs": [],
                "database_config": {},
                "system_settings": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        
        # 转换系统设置
        system_settings = {
            "max_concurrent_tasks": 5,
            "cache_ttl": 3600,
            "log_level": "INFO",
            "enable_monitoring": True,
            "worker_heartbeat_interval": 30,
            "sse_poll_timeout": 30,
            # 从 settings.json 迁移的设置
            "max_debate_rounds": settings_data.get('max_debate_rounds', 1),
            "max_risk_discuss_rounds": settings_data.get('max_risk_discuss_rounds', 1),
            "online_tools": settings_data.get('online_tools', True),
            "online_news": settings_data.get('online_news', True),
            "realtime_data": settings_data.get('realtime_data', False),
            "memory_enabled": settings_data.get('memory_enabled', True),
        }
        
        # 更新系统配置
        system_config['system_settings'] = system_settings
        system_config['updated_at'] = datetime.utcnow()
        
        if self.force or not await self.db.system_configs.find_one({"config_type": "system"}):
            await self.db.system_configs.replace_one(
                {"config_type": "system"},
                system_config,
                upsert=True
            )
            print(f"✅ 成功迁移 {len(system_settings)} 个系统设置")
        else:
            print("⚠️  系统配置已存在，使用 --force 强制覆盖")
    
    async def verify_migration(self):
        """验证迁移结果"""
        print("\n🔍 验证迁移结果...")
        
        # 检查系统配置
        system_config = await self.db.system_configs.find_one({"config_type": "system"})
        
        if not system_config:
            print("❌ 未找到系统配置")
            return False
        
        llm_count = len(system_config.get('llm_configs', []))
        settings_count = len(system_config.get('system_settings', {}))
        
        print(f"  ✅ 大模型配置: {llm_count} 个")
        print(f"  ✅ 系统设置: {settings_count} 个")
        
        # 显示启用的模型
        enabled_llms = [llm for llm in system_config.get('llm_configs', []) if llm.get('enabled')]
        if enabled_llms:
            print(f"\n  已启用的大模型 ({len(enabled_llms)}):")
            for llm in enabled_llms:
                default_mark = " [默认]" if llm.get('is_default') else ""
                print(f"    • {llm['provider']}: {llm['model_name']}{default_mark}")
        
        return True
    
    async def run(self):
        """执行迁移"""
        print("=" * 70)
        print("📦 配置迁移工具: JSON → MongoDB")
        print("=" * 70)
        
        if self.dry_run:
            print("\n⚠️  DRY RUN 模式：仅显示将要迁移的内容，不实际执行\n")
        
        try:
            # 备份配置文件
            if not self.dry_run:
                self.backup_configs()
            
            # 连接数据库
            await self.connect_db()
            
            # 迁移配置
            await self.migrate_llm_configs()
            await self.migrate_system_settings()
            
            # 验证迁移结果
            if not self.dry_run:
                success = await self.verify_migration()
                
                if success:
                    print("\n" + "=" * 70)
                    print("✅ 配置迁移完成！")
                    print("=" * 70)
                    print("\n💡 后续步骤:")
                    print("  1. 启动后端服务，验证配置是否正常加载")
                    print("  2. 在 Web 界面检查配置是否正确")
                    print("  3. 如果一切正常，可以考虑删除旧的 JSON 配置文件")
                    print(f"  4. 备份文件位置: {self.backup_dir}")
                else:
                    print("\n❌ 配置迁移验证失败")
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            await self.close_db()
        
        return 0


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="配置迁移工具: JSON → MongoDB")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要迁移的内容，不实际执行")
    parser.add_argument("--backup", action="store_true", default=True, help="迁移前备份现有配置（默认启用）")
    parser.add_argument("--no-backup", action="store_true", help="不备份现有配置")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的配置")
    
    args = parser.parse_args()
    
    # 处理备份参数
    backup = args.backup and not args.no_backup
    
    migrator = ConfigMigrator(
        dry_run=args.dry_run,
        backup=backup,
        force=args.force
    )
    
    return await migrator.run()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

