"""
修复分析深度值

将分析深度从 "5" 改为 "4"（4级 - 深度分析）
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_depth_value():
    """修复分析深度值"""
    try:
        # 获取同步数据库连接
        db = get_mongo_db_sync()
        users_collection = db["users"]
        
        # 查找所有用户
        users = users_collection.find({})
        updated_count = 0
        
        for user in users:
            username = user.get("username", "unknown")
            preferences = user.get("preferences", {})
            
            current_depth = preferences.get("default_depth")
            logger.info(f"用户 {username} 当前分析深度: {current_depth}")
            
            # 如果深度为 "5"，改为 "4"
            if current_depth == "5":
                preferences["default_depth"] = "4"
                
                # 更新用户
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"preferences": preferences}}
                )
                updated_count += 1
                logger.info(f"✅ 用户 {username} 分析深度已修复: 5 → 4")
        
        logger.info(f"🎉 修复完成！共更新 {updated_count} 个用户的分析深度")
        
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🚀 开始修复分析深度值...")
    fix_depth_value()
    logger.info("✅ 修复完成")

