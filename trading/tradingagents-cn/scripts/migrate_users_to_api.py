#!/usr/bin/env python3
"""
用户数据迁移脚本
将老web系统的用户数据迁移到新的API系统
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapi.core.database import init_database, get_mongo_db
from webapi.models.user import User, UserPreferences
from webapi.services.auth_service import AuthService

# 简单的密码哈希（避免依赖passlib）
import hashlib
import bcrypt

# 简单的密码哈希函数
def hash_password(password: str) -> str:
    """使用bcrypt哈希密码"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def load_old_users():
    """加载老系统的用户数据"""
    users_file = project_root / "web" / "config" / "users.json"
    
    if not users_file.exists():
        print("❌ 老用户文件不存在，创建默认用户")
        return {
            "admin": {
                "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123的SHA256
                "role": "admin",
                "permissions": ["analysis", "config", "admin"],
                "created_at": datetime.now().timestamp()
            },
            "user": {
                "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # user123的SHA256
                "role": "user",
                "permissions": ["analysis"],
                "created_at": datetime.now().timestamp()
            }
        }
    
    with open(users_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def sha256_to_bcrypt(sha256_hash: str, original_password: str) -> str:
    """将SHA256哈希转换为bcrypt哈希"""
    # 由于无法从SHA256逆向得到原密码，我们使用已知的默认密码
    return hash_password(original_password)

async def migrate_users():
    """迁移用户数据"""
    print("🔄 开始用户数据迁移...")
    
    # 初始化数据库
    await init_database()
    db = get_mongo_db()
    users_collection = db.users
    
    # 加载老用户数据
    old_users = await load_old_users()
    
    # 已知的默认密码映射
    default_passwords = {
        "admin": "admin123",
        "user": "user123"
    }
    
    migrated_count = 0
    
    for username, user_data in old_users.items():
        try:
            # 检查用户是否已存在
            existing_user = await users_collection.find_one({"username": username})
            if existing_user:
                print(f"⚠️ 用户 {username} 已存在，跳过")
                continue
            
            # 获取原密码（仅对默认用户有效）
            original_password = default_passwords.get(username, "defaultpass123")
            
            # 创建新用户模型
            new_user = User(
                username=username,
                email=f"{username}@tradingagents.cn",  # 默认邮箱
                hashed_password=hash_password(original_password),
                is_active=True,
                is_verified=True,
                is_admin=(user_data.get("role") == "admin"),
                created_at=datetime.fromtimestamp(user_data.get("created_at", datetime.now().timestamp())),
                preferences=UserPreferences(
                    default_market="A股",
                    default_depth="标准",
                    ui_theme="light",
                    language="zh-CN"
                )
            )
            
            # 插入到数据库
            result = await users_collection.insert_one(new_user.model_dump(by_alias=True))
            
            print(f"✅ 用户 {username} 迁移成功 (ID: {result.inserted_id})")
            print(f"   邮箱: {new_user.email}")
            print(f"   角色: {'管理员' if new_user.is_admin else '普通用户'}")
            print(f"   密码: {original_password}")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ 用户 {username} 迁移失败: {e}")
    
    print(f"\n🎉 用户迁移完成！共迁移 {migrated_count} 个用户")
    print("\n📋 迁移后的用户信息:")
    print("   - admin / admin123 (管理员)")
    print("   - user / user123 (普通用户)")
    print("\n💡 提示: 用户可以在前端修改邮箱和密码")

async def main():
    """主函数"""
    try:
        await migrate_users()
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
