"""
迁移用户偏好设置脚本

将旧的分析深度值（"快速"、"标准"、"深度"）迁移到新的值（"1"、"2"、"3"、"4"、"5"）
将旧的默认分析师值迁移到新的值
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_user_preferences():
    """迁移用户偏好设置"""
    try:
        # 获取同步数据库连接
        db = get_mongo_db_sync()
        users_collection = db["users"]
        
        # 深度值映射
        depth_mapping = {
            "快速": "1",
            "标准": "3",
            "深度": "4",  # 深度分析对应4级
            # 保留新值
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "4",
            "5": "5"
        }
        
        # 分析师映射
        old_analysts = ["基本面分析师", "技术分析师", "情绪分析师", "量化分析师"]
        new_analysts = ["市场分析师", "基本面分析师", "新闻分析师", "社媒分析师"]
        
        # 查找所有用户
        users = users_collection.find({})
        updated_count = 0
        
        for user in users:
            username = user.get("username", "unknown")
            preferences = user.get("preferences", {})
            updated = False
            
            # 迁移分析深度
            old_depth = preferences.get("default_depth")
            if old_depth in depth_mapping:
                new_depth = depth_mapping[old_depth]
                if new_depth != old_depth:
                    preferences["default_depth"] = new_depth
                    updated = True
                    logger.info(f"用户 {username}: 分析深度 {old_depth} → {new_depth}")
            
            # 迁移默认分析师（只迁移旧的分析师名称，保留用户的选择）
            old_analysts_list = preferences.get("default_analysts", [])

            # 分析师名称映射
            analyst_mapping = {
                "技术分析师": "市场分析师",  # 旧名称 → 新名称
                "情绪分析师": "社媒分析师",
                "量化分析师": "新闻分析师"
            }

            if old_analysts_list:
                # 检查是否包含旧的分析师名称
                has_old_analysts = any(analyst in analyst_mapping for analyst in old_analysts_list)
                if has_old_analysts:
                    # 迁移旧的分析师名称到新名称
                    new_analysts_list = []
                    for analyst in old_analysts_list:
                        if analyst in analyst_mapping:
                            new_analysts_list.append(analyst_mapping[analyst])
                        else:
                            new_analysts_list.append(analyst)

                    # 去重
                    new_analysts_list = list(dict.fromkeys(new_analysts_list))

                    preferences["default_analysts"] = new_analysts_list
                    updated = True
                    logger.info(f"用户 {username}: 默认分析师 {old_analysts_list} → {new_analysts_list}")
            else:
                # 如果没有设置，使用新的默认值
                preferences["default_analysts"] = ["市场分析师", "基本面分析师"]
                updated = True
                logger.info(f"用户 {username}: 设置默认分析师 → ['市场分析师', '基本面分析师']")
            
            # 更新用户
            if updated:
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"preferences": preferences}}
                )
                updated_count += 1
                logger.info(f"✅ 用户 {username} 偏好设置已更新")
        
        logger.info(f"🎉 迁移完成！共更新 {updated_count} 个用户的偏好设置")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🚀 开始迁移用户偏好设置...")
    migrate_user_preferences()
    logger.info("✅ 迁移完成")

