#!/usr/bin/env python3
"""
快速登录修复脚本
专门用于解决新机器部署后的登录问题
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def fix_admin_password():
    """修复管理员密码配置"""
    print("🔐 修复管理员密码配置...")
    
    try:
        config_file = project_root / "config" / "admin_password.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取当前配置
        current_password = "admin123"  # 默认密码
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    current_password = config.get("password", "admin123")
                print(f"✓ 当前管理员密码: {current_password}")
            except Exception as e:
                print(f"⚠️ 读取密码配置失败: {e}")
        
        # 如果密码不是默认密码，询问是否重置
        if current_password != "admin123":
            print(f"\n当前管理员密码是: {current_password}")
            reset = input("是否重置为默认密码 'admin123'? (y/N): ").strip().lower()
            if reset == 'y':
                config = {"password": "admin123"}
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                print("✅ 管理员密码已重置为: admin123")
                current_password = "admin123"
            else:
                print("✓ 保持当前密码不变")
        else:
            # 确保配置文件存在
            config = {"password": "admin123"}
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print("✅ 管理员密码配置已确认: admin123")
        
        return current_password
        
    except Exception as e:
        print(f"❌ 修复管理员密码配置失败: {e}")
        return "admin123"

def create_web_users_config():
    """创建 Web 应用用户配置"""
    print("👤 创建 Web 应用用户配置...")
    
    try:
        users_file = project_root / "web" / "config" / "users.json"
        users_file.parent.mkdir(parents=True, exist_ok=True)
        
        if users_file.exists():
            print("✓ Web 用户配置文件已存在")
            return True
        
        # 创建默认用户配置
        import hashlib
        
        def hash_password(password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()
        
        default_users = {
            "admin": {
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "permissions": ["analysis", "config", "admin"],
                "created_at": time.time()
            },
            "user": {
                "password_hash": hash_password("user123"),
                "role": "user", 
                "permissions": ["analysis"],
                "created_at": time.time()
            }
        }
        
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2, ensure_ascii=False)
        
        print("✅ Web 用户配置创建成功")
        print("   - admin / admin123 (管理员)")
        print("   - user / user123 (普通用户)")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建 Web 用户配置失败: {e}")
        return False

def check_mongodb_connection():
    """检查 MongoDB 连接"""
    print("🗄️ 检查 MongoDB 连接...")

    try:
        from pymongo import MongoClient
        import os

        # 检查是否在Docker容器内
        is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'

        if is_docker:
            # Docker环境：使用服务名和认证
            mongo_host = os.getenv('MONGODB_HOST', 'mongodb')
            mongo_port = int(os.getenv('MONGODB_PORT', '27017'))
            mongo_username = os.getenv('MONGODB_USERNAME', '')
            mongo_password = os.getenv('MONGODB_PASSWORD', '')
            mongo_database = os.getenv('MONGODB_DATABASE', 'tradingagents')
            mongo_auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')

            if mongo_username and mongo_password:
                # 带认证的连接
                mongo_url = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_database}?authSource={mongo_auth_source}"
            else:
                # 无认证的连接
                mongo_url = f"mongodb://{mongo_host}:{mongo_port}/"
        else:
            # 本地环境：使用localhost
            mongo_url = "mongodb://localhost:27017/"

        print(f"   连接地址: {mongo_url}")

        # 尝试连接 MongoDB
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        client.server_info()

        print("✅ MongoDB 连接成功")
        return client
        
    except Exception as e:
        print(f"⚠️ MongoDB 连接失败: {e}")
        print("   请确保 MongoDB 服务正在运行")
        return None

def create_basic_mongodb_data(client):
    """创建基础 MongoDB 数据"""
    print("📝 创建基础 MongoDB 数据...")
    
    try:
        db = client["tradingagents"]
        
        # 检查是否已存在管理员用户
        users_collection = db["users"]
        existing_admin = users_collection.find_one({"username": "admin"})
        
        if existing_admin:
            print("✓ 管理员用户已存在")
        else:
            # 读取管理员密码
            config_file = project_root / "config" / "admin_password.json"
            admin_password = "admin123"
            
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        admin_password = config.get("password", "admin123")
                except:
                    pass
            
            # 创建管理员用户
            admin_user = {
                "username": "admin",
                "email": "admin@tradingagents.cn",
                "password": admin_password,  # 开源版使用明文密码
                "full_name": "系统管理员",
                "role": "admin",
                "is_active": True,
                "is_superuser": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "settings": {
                    "default_research_depth": 2,
                    "enable_notifications": True,
                    "theme": "light"
                }
            }
            
            users_collection.insert_one(admin_user)
            print(f"✅ 创建管理员用户成功 (密码: {admin_password})")
        
        # 创建基础系统配置
        system_config_collection = db["system_config"]
        basic_configs = [
            {
                "key": "system_version",
                "value": "v1.0.0-preview",
                "description": "系统版本号",
                "updated_at": datetime.utcnow()
            },
            {
                "key": "max_concurrent_tasks",
                "value": 3,
                "description": "最大并发分析任务数",
                "updated_at": datetime.utcnow()
            }
        ]
        
        for config in basic_configs:
            system_config_collection.replace_one(
                {"key": config["key"]},
                config,
                upsert=True
            )
        
        print("✅ 基础系统配置创建完成")
        return True
        
    except Exception as e:
        print(f"❌ 创建基础 MongoDB 数据失败: {e}")
        return False

def check_env_file():
    """检查 .env 文件"""
    print("📄 检查 .env 文件...")
    
    try:
        env_file = project_root / ".env"
        env_example = project_root / ".env.example"
        
        if env_file.exists():
            print("✅ .env 文件已存在")
            return True
        elif env_example.exists():
            print("⚠️ .env 文件不存在，但找到 .env.example")
            create = input("是否从 .env.example 创建 .env 文件? (y/N): ").strip().lower()
            if create == 'y':
                import shutil
                shutil.copy2(env_example, env_file)
                print("✅ .env 文件创建成功")
                print("⚠️  请根据实际情况修改 .env 文件中的配置")
                return True
            else:
                print("⚠️ 跳过 .env 文件创建")
                return False
        else:
            print("⚠️ 未找到 .env 和 .env.example 文件")
            return False
            
    except Exception as e:
        print(f"❌ 检查 .env 文件失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 TradingAgents-CN 快速登录修复工具")
    print("=" * 50)
    print("此工具将帮助您解决新机器部署后的登录问题")
    print()
    
    try:
        # 1. 修复管理员密码配置
        admin_password = fix_admin_password()
        
        # 2. 创建 Web 用户配置
        create_web_users_config()
        
        # 3. 检查 .env 文件
        check_env_file()
        
        # 4. 检查并初始化 MongoDB
        mongo_client = check_mongodb_connection()
        if mongo_client:
            create_basic_mongodb_data(mongo_client)
            mongo_client.close()
        
        print("\n" + "=" * 50)
        print("✅ 快速登录修复完成！")
        print("=" * 50)
        
        print(f"\n🔐 登录信息:")
        print(f"- 后端 API 用户名: admin")
        print(f"- 后端 API 密码: {admin_password}")
        print(f"- Web 应用用户名: admin")
        print(f"- Web 应用密码: admin123")
        
        print(f"\n🌐 访问地址:")
        print(f"- 前端应用: http://localhost:80")
        print(f"- 后端 API: http://localhost:8000")
        print(f"- API 文档: http://localhost:8000/docs")
        
        print(f"\n📋 下一步:")
        print("1. 尝试使用上述账号密码登录系统")
        print("2. 登录成功后立即修改密码")
        print("3. 配置必要的 API 密钥（.env 文件）")
        print("4. 如仍有问题，请运行完整初始化脚本:")
        print("   python scripts/docker_deployment_init.py")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
