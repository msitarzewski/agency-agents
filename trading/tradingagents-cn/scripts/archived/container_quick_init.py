#!/usr/bin/env python3
"""
TradingAgents-CN 容器内快速初始化脚本
直接在容器内执行，无需挂载外部文件
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

def print_status(message, status="info"):
    """打印状态信息"""
    colors = {
        "info": "\033[0;34m",      # 蓝色
        "success": "\033[0;32m",   # 绿色
        "warning": "\033[1;33m",   # 黄色
        "error": "\033[0;31m",     # 红色
        "reset": "\033[0m"         # 重置
    }
    
    symbols = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    color = colors.get(status, colors["info"])
    symbol = symbols.get(status, "")
    reset = colors["reset"]
    
    print(f"{color}{symbol} {message}{reset}")

def check_mongodb_connection():
    """检查MongoDB连接"""
    try:
        from pymongo import MongoClient
        
        # 从环境变量获取MongoDB配置
        mongo_host = os.getenv('MONGODB_HOST', 'mongodb')
        mongo_port = int(os.getenv('MONGODB_PORT', '27017'))
        
        print_status(f"连接MongoDB: {mongo_host}:{mongo_port}")
        
        client = MongoClient(mongo_host, mongo_port, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        print_status("MongoDB连接成功", "success")
        return client
        
    except ImportError:
        print_status("pymongo模块未安装", "error")
        return None
    except Exception as e:
        print_status(f"MongoDB连接失败: {e}", "error")
        return None

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin_user(client):
    """创建管理员用户"""
    try:
        db = client.tradingagents
        users_collection = db.users
        
        # 检查是否已存在管理员用户
        existing_admin = users_collection.find_one({"username": "admin"})
        
        admin_password = "admin123"
        
        if existing_admin:
            # 更新现有管理员用户
            users_collection.update_one(
                {"username": "admin"},
                {
                    "$set": {
                        "hashed_password": hash_password(admin_password),
                        "updated_at": datetime.utcnow(),
                        "is_active": True,
                        "is_verified": True,
                        "is_admin": True
                    }
                }
            )
            print_status("管理员用户已更新", "success")
        else:
            # 创建新的管理员用户
            admin_user = {
                "username": "admin",
                "email": "admin@tradingagents.cn",
                "hashed_password": hash_password(admin_password),
                "is_active": True,
                "is_verified": True,
                "is_admin": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "profile": {
                    "display_name": "系统管理员",
                    "bio": "TradingAgents-CN 系统管理员",
                    "avatar_url": None
                },
                "preferences": {
                    "theme": "light",
                    "language": "zh-CN",
                    "timezone": "Asia/Shanghai",
                    "notifications": {
                        "email": True,
                        "push": True,
                        "analysis_complete": True,
                        "system_alerts": True
                    }
                },
                "usage_stats": {
                    "total_analyses": 0,
                    "total_tokens_used": 0,
                    "last_analysis_date": None,
                    "favorite_models": []
                }
            }
            
            result = users_collection.insert_one(admin_user)
            print_status(f"管理员用户已创建，ID: {result.inserted_id}", "success")
        
        # 验证用户创建
        admin_user = users_collection.find_one({"username": "admin"})
        if admin_user and admin_user.get("hashed_password") == hash_password(admin_password):
            print_status("管理员用户验证成功", "success")
            return True
        else:
            print_status("管理员用户验证失败", "error")
            return False
            
    except Exception as e:
        print_status(f"创建管理员用户失败: {e}", "error")
        return False

def create_web_user_config():
    """创建Web应用用户配置"""
    try:
        # 创建web/config目录
        web_config_dir = Path("/app/web/config")
        web_config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建用户配置文件
        users_config = {
            "admin": {
                "password": hash_password("admin123"),
                "role": "admin",
                "name": "管理员",
                "email": "admin@tradingagents.cn"
            },
            "user": {
                "password": hash_password("user123"),
                "role": "user", 
                "name": "普通用户",
                "email": "user@tradingagents.cn"
            }
        }
        
        users_file = web_config_dir / "users.json"
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(users_config, f, ensure_ascii=False, indent=2)
        
        print_status(f"Web用户配置已创建: {users_file}", "success")
        return True
        
    except Exception as e:
        print_status(f"创建Web用户配置失败: {e}", "error")
        return False

def create_admin_password_config():
    """创建管理员密码配置"""
    try:
        # 创建config目录
        config_dir = Path("/app/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建管理员密码配置
        admin_config = {
            "password": "admin123",
            "created_at": datetime.utcnow().isoformat(),
            "description": "系统管理员默认密码，请登录后立即修改"
        }
        
        admin_file = config_dir / "admin_password.json"
        with open(admin_file, "w", encoding="utf-8") as f:
            json.dump(admin_config, f, ensure_ascii=False, indent=2)
        
        print_status(f"管理员密码配置已创建: {admin_file}", "success")
        return True
        
    except Exception as e:
        print_status(f"创建管理员密码配置失败: {e}", "error")
        return False

def main():
    """主函数"""
    print("🔧 TradingAgents-CN 容器内快速初始化")
    print("=" * 50)
    
    # 检查是否在容器内
    if not os.path.exists("/.dockerenv"):
        print_status("此脚本应在Docker容器内执行", "warning")
    
    # 步骤1: 检查MongoDB连接
    print_status("检查MongoDB连接...")
    client = check_mongodb_connection()
    if not client:
        print_status("MongoDB连接失败，无法继续", "error")
        sys.exit(1)
    
    # 步骤2: 创建管理员用户
    print_status("创建管理员用户...")
    if not create_admin_user(client):
        print_status("创建管理员用户失败", "error")
        sys.exit(1)
    
    # 步骤3: 创建Web用户配置
    print_status("创建Web用户配置...")
    create_web_user_config()
    
    # 步骤4: 创建管理员密码配置
    print_status("创建管理员密码配置...")
    create_admin_password_config()
    
    # 完成
    print("\n" + "=" * 50)
    print_status("初始化完成！", "success")
    print("=" * 50)
    
    print("\n🔐 登录信息:")
    print("  用户名: admin")
    print("  密码: admin123")
    
    print("\n🌐 访问地址:")
    print("  前端: http://your-server-ip:80")
    print("  后端API: http://your-server-ip:8000")
    print("  API文档: http://your-server-ip:8000/docs")
    
    print("\n📋 建议:")
    print("  1. 立即登录并修改默认密码")
    print("  2. 检查 .env 文件中的API密钥配置")
    print("  3. 验证系统功能是否正常")

if __name__ == "__main__":
    main()
