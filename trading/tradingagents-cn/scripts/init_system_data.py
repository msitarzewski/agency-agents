#!/usr/bin/env python3
"""
系统初始化数据脚本 - TradingAgents-CN v1.0.0-preview
用于初始化系统所需的基础数据
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_mongo_db
from app.models.user import User, UserRole
from app.utils.security import get_password_hash
from app.utils.timezone import now_tz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_default_users(db):
    """创建默认用户"""
    logger.info("创建默认用户...")
    
    users_collection = db["users"]
    
    # 检查是否已存在管理员用户
    existing_admin = await users_collection.find_one({"username": "admin"})
    if existing_admin:
        logger.info("✓ 管理员用户已存在，跳过创建")
        return
    
    # 创建默认管理员用户
    admin_user = {
        "username": "admin",
        "email": "admin@tradingagents.cn",
        "hashed_password": get_password_hash("admin123"),
        "full_name": "系统管理员",
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "is_superuser": True,
        "created_at": now_tz(),
        "updated_at": now_tz(),
        "settings": {
            "default_research_depth": 2,
            "enable_notifications": True,
            "theme": "light"
        }
    }
    
    await users_collection.insert_one(admin_user)
    logger.info("✓ 创建管理员用户成功")
    logger.info("  用户名: admin")
    logger.info("  密码: admin123")
    logger.info("  ⚠️  请在首次登录后立即修改密码！")
    
    # 创建默认测试用户
    test_user = {
        "username": "test",
        "email": "test@tradingagents.cn",
        "hashed_password": get_password_hash("test123"),
        "full_name": "测试用户",
        "role": UserRole.USER.value,
        "is_active": True,
        "is_superuser": False,
        "created_at": now_tz(),
        "updated_at": now_tz(),
        "settings": {
            "default_research_depth": 2,
            "enable_notifications": True,
            "theme": "light"
        }
    }
    
    await users_collection.insert_one(test_user)
    logger.info("✓ 创建测试用户成功")
    logger.info("  用户名: test")
    logger.info("  密码: test123")


async def create_system_config(db):
    """创建系统配置"""
    logger.info("\n创建系统配置...")
    
    config_collection = db["system_config"]
    
    # 检查是否已存在配置
    existing_config = await config_collection.find_one({"key": "system_version"})
    if existing_config:
        logger.info("✓ 系统配置已存在，跳过创建")
        return
    
    # 系统配置
    configs = [
        {
            "key": "system_version",
            "value": "v1.0.0-preview",
            "description": "系统版本号",
            "category": "system",
            "updated_at": now_tz()
        },
        {
            "key": "max_concurrent_tasks",
            "value": 3,
            "description": "最大并发分析任务数",
            "category": "performance",
            "updated_at": now_tz()
        },
        {
            "key": "default_research_depth",
            "value": 2,
            "description": "默认分析深度（1-5）",
            "category": "analysis",
            "updated_at": now_tz()
        },
        {
            "key": "enable_realtime_pe_pb",
            "value": True,
            "description": "启用实时PE/PB计算",
            "category": "features",
            "updated_at": now_tz()
        },
        {
            "key": "quotes_update_interval",
            "value": 30,
            "description": "行情更新间隔（秒）",
            "category": "data",
            "updated_at": now_tz()
        },
        {
            "key": "cache_ttl",
            "value": 300,
            "description": "缓存过期时间（秒）",
            "category": "performance",
            "updated_at": now_tz()
        },
        {
            "key": "enable_batch_analysis",
            "value": True,
            "description": "启用批量分析功能",
            "category": "features",
            "updated_at": now_tz()
        },
        {
            "key": "max_batch_size",
            "value": 50,
            "description": "批量分析最大股票数",
            "category": "limits",
            "updated_at": now_tz()
        }
    ]
    
    await config_collection.insert_many(configs)
    logger.info(f"✓ 创建 {len(configs)} 个系统配置")


async def create_model_config(db):
    """创建模型配置"""
    logger.info("\n创建模型配置...")
    
    model_collection = db["model_config"]
    
    # 检查是否已存在配置
    existing_model = await model_collection.find_one({"provider": "deepseek"})
    if existing_model:
        logger.info("✓ 模型配置已存在，跳过创建")
        return
    
    # 模型配置
    models = [
        {
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "display_name": "DeepSeek Chat",
            "description": "DeepSeek通用对话模型",
            "enabled": True,
            "priority": 1,
            "capabilities": ["chat", "analysis", "reasoning"],
            "pricing": {
                "input_price_per_1k": 0.001,
                "output_price_per_1k": 0.002,
                "currency": "CNY"
            },
            "limits": {
                "max_tokens": 4096,
                "rate_limit_per_minute": 60
            },
            "created_at": now_tz(),
            "updated_at": now_tz()
        },
        {
            "provider": "dashscope",
            "model_name": "qwen-max",
            "display_name": "通义千问 Max",
            "description": "阿里云通义千问最强模型",
            "enabled": True,
            "priority": 2,
            "capabilities": ["chat", "analysis", "reasoning"],
            "pricing": {
                "input_price_per_1k": 0.02,
                "output_price_per_1k": 0.06,
                "currency": "CNY"
            },
            "limits": {
                "max_tokens": 8192,
                "rate_limit_per_minute": 60
            },
            "created_at": now_tz(),
            "updated_at": now_tz()
        },
        {
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "GPT-4",
            "description": "OpenAI GPT-4模型",
            "enabled": False,
            "priority": 3,
            "capabilities": ["chat", "analysis", "reasoning", "code"],
            "pricing": {
                "input_price_per_1k": 0.03,
                "output_price_per_1k": 0.06,
                "currency": "USD"
            },
            "limits": {
                "max_tokens": 8192,
                "rate_limit_per_minute": 60
            },
            "created_at": now_tz(),
            "updated_at": now_tz()
        }
    ]
    
    await model_collection.insert_many(models)
    logger.info(f"✓ 创建 {len(models)} 个模型配置")


async def create_sync_status(db):
    """创建数据同步状态"""
    logger.info("\n创建数据同步状态...")
    
    sync_collection = db["sync_status"]
    
    # 检查是否已存在状态
    existing_sync = await sync_collection.find_one({"data_type": "stock_basics"})
    if existing_sync:
        logger.info("✓ 同步状态已存在，跳过创建")
        return
    
    # 同步状态
    sync_statuses = [
        {
            "data_type": "stock_basics",
            "description": "股票基础信息",
            "last_sync_at": None,
            "next_sync_at": None,
            "status": "pending",
            "total_count": 0,
            "success_count": 0,
            "error_count": 0,
            "created_at": now_tz(),
            "updated_at": now_tz()
        },
        {
            "data_type": "market_quotes",
            "description": "实时行情数据",
            "last_sync_at": None,
            "next_sync_at": None,
            "status": "pending",
            "total_count": 0,
            "success_count": 0,
            "error_count": 0,
            "created_at": now_tz(),
            "updated_at": now_tz()
        },
        {
            "data_type": "financial_data",
            "description": "财务数据",
            "last_sync_at": None,
            "next_sync_at": None,
            "status": "pending",
            "total_count": 0,
            "success_count": 0,
            "error_count": 0,
            "created_at": now_tz(),
            "updated_at": now_tz()
        }
    ]
    
    await sync_collection.insert_many(sync_statuses)
    logger.info(f"✓ 创建 {len(sync_statuses)} 个同步状态")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("TradingAgents-CN v1.0.0-preview 系统初始化")
    logger.info("=" * 60)
    
    try:
        # 获取数据库连接
        db = get_mongo_db()
        
        # 创建默认用户
        await create_default_users(db.client[db.database_name])
        
        # 创建系统配置
        await create_system_config(db.client[db.database_name])
        
        # 创建模型配置
        await create_model_config(db.client[db.database_name])
        
        # 创建同步状态
        await create_sync_status(db.client[db.database_name])
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 系统初始化完成！")
        logger.info("=" * 60)
        logger.info("\n下一步:")
        logger.info("1. 启动后端服务: python -m uvicorn app.main:app --reload")
        logger.info("2. 启动前端服务: cd frontend && npm run dev")
        logger.info("3. 访问应用: http://localhost:5173")
        logger.info("4. 使用管理员账号登录: admin / admin123")
        logger.info("\n⚠️  重要: 请在首次登录后立即修改管理员密码！")
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

