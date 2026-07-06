#!/usr/bin/env python3
"""
简化版认证系统迁移脚本
将基于配置文件的认证迁移到基于数据库的认证
"""

import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_auth_to_db():
    """迁移认证系统到数据库"""
    print("🔄 开始认证系统迁移...")
    print("=" * 60)
    
    try:
        # 1. 导入必要的模块
        from pymongo import MongoClient
        from app.core.config import Settings
        
        settings = Settings()
        
        # 2. 连接数据库
        print("🗄️ 连接数据库...")
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        users_collection = db.users
        
        # 3. 读取现有的配置文件密码
        config_file = project_root / "config" / "admin_password.json"
        admin_password = "admin123"  # 默认密码
        
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    admin_password = config.get("password", "admin123")
                print(f"✅ 从配置文件读取管理员密码")
            except Exception as e:
                print(f"⚠️ 读取配置文件失败，使用默认密码: {e}")
        else:
            print("⚠️ 配置文件不存在，使用默认密码")
        
        # 4. 检查是否已存在管理员用户
        existing_admin = users_collection.find_one({"username": "admin"})
        if existing_admin:
            print("✓ 管理员用户已存在，更新密码...")
            # 更新密码
            users_collection.update_one(
                {"username": "admin"},
                {
                    "$set": {
                        "hashed_password": hash_password(admin_password),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            print("👤 创建管理员用户...")
            # 创建管理员用户
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
                "preferences": {
                    "default_market": "A股",
                    "default_depth": "深度",
                    "ui_theme": "light",
                    "language": "zh-CN",
                    "notifications_enabled": True,
                    "email_notifications": False
                },
                "daily_quota": 10000,  # 管理员更高配额
                "concurrent_limit": 10,
                "total_analyses": 0,
                "successful_analyses": 0,
                "failed_analyses": 0,
                "favorite_stocks": []
            }
            
            users_collection.insert_one(admin_user)
        
        # 5. 迁移 Web 应用用户配置
        print("👤 迁移 Web 应用用户配置...")
        web_users_file = project_root / "web" / "config" / "users.json"
        
        if web_users_file.exists():
            try:
                with open(web_users_file, "r", encoding="utf-8") as f:
                    web_users = json.load(f)
                
                for username, user_info in web_users.items():
                    if username == "admin":
                        continue  # 管理员已处理
                    
                    # 检查用户是否已存在
                    existing_user = users_collection.find_one({"username": username})
                    if existing_user:
                        print(f"✓ 用户 {username} 已存在，跳过")
                        continue
                    
                    # 创建用户（使用默认密码）
                    default_password = f"{username}123"
                    
                    user_doc = {
                        "username": username,
                        "email": f"{username}@tradingagents.cn",
                        "hashed_password": hash_password(default_password),
                        "is_active": True,
                        "is_verified": False,
                        "is_admin": False,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "last_login": None,
                        "preferences": {
                            "default_market": "A股",
                            "default_depth": "深度",
                            "ui_theme": "light",
                            "language": "zh-CN",
                            "notifications_enabled": True,
                            "email_notifications": False
                        },
                        "daily_quota": 1000,
                        "concurrent_limit": 3,
                        "total_analyses": 0,
                        "successful_analyses": 0,
                        "failed_analyses": 0,
                        "favorite_stocks": []
                    }
                    
                    users_collection.insert_one(user_doc)
                    print(f"✅ 用户 {username} 迁移成功，默认密码: {default_password}")
                    
            except Exception as e:
                print(f"⚠️ Web 用户配置迁移失败: {e}")
        else:
            print("⚠️ Web 用户配置文件不存在，跳过迁移")
        
        # 6. 备份原配置文件
        print("💾 备份原配置文件...")
        backup_dir = project_root / "config" / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if config_file.exists():
            backup_file = backup_dir / f"admin_password_{timestamp}.json"
            import shutil
            shutil.copy2(config_file, backup_file)
            print(f"✅ 备份管理员密码配置: {backup_file}")
        
        if web_users_file.exists():
            backup_file = backup_dir / f"web_users_{timestamp}.json"
            import shutil
            shutil.copy2(web_users_file, backup_file)
            print(f"✅ 备份 Web 用户配置: {backup_file}")
        
        # 7. 验证迁移结果
        print("🔍 验证迁移结果...")
        
        # 验证管理员用户
        admin_user = users_collection.find_one({"username": "admin"})
        if admin_user:
            print("✅ 管理员用户验证成功")
            print(f"   用户名: {admin_user['username']}")
            print(f"   邮箱: {admin_user['email']}")
            print(f"   是否管理员: {admin_user['is_admin']}")
            print(f"   是否激活: {admin_user['is_active']}")
        else:
            print("❌ 管理员用户验证失败")
            return False
        
        # 测试认证
        stored_hash = admin_user["hashed_password"]
        test_hash = hash_password(admin_password)
        if stored_hash == test_hash:
            print("✅ 管理员密码验证成功")
        else:
            print("❌ 管理员密码验证失败")
            return False
        
        # 获取用户列表
        users = list(users_collection.find())
        print(f"✅ 数据库中共有 {len(users)} 个用户")
        for user in users:
            role = "管理员" if user.get("is_admin", False) else "普通用户"
            print(f"   - {user['username']} ({user['email']}) - {role}")
        
        # 关闭数据库连接
        client.close()
        
        print("\n" + "=" * 60)
        print("✅ 认证系统迁移成功完成！")
        print("=" * 60)
        
        print(f"\n📋 迁移后的登录信息:")
        print(f"- 用户名: admin")
        print(f"- 密码: {admin_password}")
        
        print(f"\n⚠️  重要提醒:")
        print("1. 原配置文件已备份到 config/backup/ 目录")
        print("2. 现在可以使用新的基于数据库的认证 API")
        print("3. 建议立即修改默认密码")
        print("4. 可以通过 API 创建更多用户")
        print("5. 前端需要更新 API 端点到 /api/auth-db/")
        
        print(f"\n📖 详细说明:")
        print("- 查看迁移指南: docs/auth_system_improvement.md")
        print("- 新的认证 API 端点: /api/auth-db/")
        print("- 用户管理功能已启用")
        
        return True
        
    except Exception as e:
        print(f"❌ 认证系统迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 TradingAgents-CN 认证系统迁移工具")
    print("=" * 60)
    print("此工具将把基于配置文件的认证迁移到基于数据库的认证")
    print()
    
    try:
        success = migrate_auth_to_db()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 迁移过程中出现错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
