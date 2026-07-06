#!/usr/bin/env python3
"""
数据目录重新组织迁移脚本
Data Directory Reorganization Migration Script

此脚本将项目中分散的数据目录重新组织为统一的结构
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime

# 设置日志
os.makedirs(os.path.join('data', 'logs'), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('data', 'logs', 'data_migration.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataDirectoryMigrator:
    """数据目录迁移器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.backup_dir = self.project_root / f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 新的目录结构
        self.new_structure = {
            'data': {
                'cache': ['stock_data', 'news_data', 'fundamentals', 'metadata'],
                'analysis_results': ['summary', 'detailed', 'exports'],
                'databases': ['mongodb', 'redis'],
                'sessions': ['web_sessions', 'cli_sessions'],
                'logs': ['application', 'operations', 'user_activities'],
                'config': ['user_configs', 'system_configs'],
                'temp': ['downloads', 'processing']
            }
        }
        
        # 迁移映射：(源路径, 目标路径)
        self.migration_map = [
            # 缓存数据迁移
            ('tradingagents/dataflows/data_cache', 'data/cache'),
            
            # 分析结果迁移
            ('results', 'data/analysis_results/detailed'),
            ('web/data/analysis_results', 'data/analysis_results/summary'),
            
            # 数据库数据迁移
            ('data/mongodb', 'data/databases/mongodb'),
            ('data/redis', 'data/databases/redis'),
            
            # 会话数据迁移
            ('data/sessions', 'data/sessions/cli_sessions'),
            ('web/data/sessions', 'data/sessions/web_sessions'),
            
            # 日志数据迁移
            ('web/data/operation_logs', 'data/logs/operations'),
            ('web/data/user_activities', 'data/logs/user_activities'),
            
            # 报告数据迁移（如果存在）
            ('data/reports', 'data/analysis_results/exports'),
        ]
    
    def create_backup(self) -> bool:
        """创建数据备份"""
        try:
            logger.info(f"🔄 开始创建数据备份到: {self.backup_dir}")
            self.backup_dir.mkdir(exist_ok=True)
            
            # 备份现有数据目录
            backup_paths = ['data', 'web/data', 'results', 'tradingagents/dataflows/data_cache']
            
            for path in backup_paths:
                source = self.project_root / path
                if source.exists():
                    target = self.backup_dir / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source.is_dir():
                        shutil.copytree(source, target, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, target)
                    
                    logger.info(f"  ✅ 已备份: {path}")
            
            logger.info(f"✅ 数据备份完成: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 备份失败: {e}")
            return False
    
    def create_new_structure(self) -> bool:
        """创建新的目录结构"""
        try:
            logger.info("🔄 创建新的目录结构...")
            
            for root_dir, subdirs in self.new_structure.items():
                root_path = self.project_root / root_dir
                root_path.mkdir(exist_ok=True)
                
                if isinstance(subdirs, dict):
                    for subdir, sub_subdirs in subdirs.items():
                        subdir_path = root_path / subdir
                        subdir_path.mkdir(exist_ok=True)
                        
                        for sub_subdir in sub_subdirs:
                            (subdir_path / sub_subdir).mkdir(exist_ok=True)
                            
                        logger.info(f"  ✅ 创建目录: {subdir_path.relative_to(self.project_root)}")
                elif isinstance(subdirs, list):
                    for subdir in subdirs:
                        subdir_path = root_path / subdir
                        subdir_path.mkdir(exist_ok=True)
                        logger.info(f"  ✅ 创建目录: {subdir_path.relative_to(self.project_root)}")
            
            logger.info("✅ 新目录结构创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建目录结构失败: {e}")
            return False
    
    def migrate_data(self) -> bool:
        """迁移数据"""
        try:
            logger.info("🔄 开始数据迁移...")
            
            for source_path, target_path in self.migration_map:
                source = self.project_root / source_path
                target = self.project_root / target_path
                
                if not source.exists():
                    logger.info(f"  ⏭️ 跳过不存在的路径: {source_path}")
                    continue
                
                # 确保目标目录存在
                target.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    if source.is_dir():
                        # 如果目标已存在，合并内容
                        if target.exists():
                            self._merge_directories(source, target)
                        else:
                            shutil.copytree(source, target)
                    else:
                        shutil.copy2(source, target)
                    
                    logger.info(f"  ✅ 迁移完成: {source_path} → {target_path}")
                    
                except Exception as e:
                    logger.error(f"  ❌ 迁移失败: {source_path} → {target_path}, 错误: {e}")
            
            logger.info("✅ 数据迁移完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据迁移失败: {e}")
            return False
    
    def _merge_directories(self, source: Path, target: Path):
        """合并目录内容"""
        for item in source.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(source)
                target_file = target / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 如果目标文件已存在，重命名
                if target_file.exists():
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    target_file = target_file.with_name(f"{target_file.stem}_{timestamp}{target_file.suffix}")
                
                shutil.copy2(item, target_file)
    
    def update_env_file(self) -> bool:
        """更新.env文件"""
        try:
            logger.info("🔄 更新.env文件...")
            
            env_file = self.project_root / '.env'
            if not env_file.exists():
                logger.warning("⚠️ .env文件不存在，跳过更新")
                return True
            
            # 读取现有内容
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加新的环境变量配置
            new_config = """
# ===== 数据目录配置 (重新组织后) =====
# 统一数据根目录
TRADINGAGENTS_DATA_DIR=./data

# 子目录配置（可选，使用默认值）
TRADINGAGENTS_CACHE_DIR=${TRADINGAGENTS_DATA_DIR}/cache
TRADINGAGENTS_SESSIONS_DIR=${TRADINGAGENTS_DATA_DIR}/sessions
TRADINGAGENTS_LOGS_DIR=${TRADINGAGENTS_DATA_DIR}/logs
TRADINGAGENTS_CONFIG_DIR=${TRADINGAGENTS_DATA_DIR}/config
TRADINGAGENTS_TEMP_DIR=${TRADINGAGENTS_DATA_DIR}/temp

# 更新结果目录配置
TRADINGAGENTS_RESULTS_DIR=${TRADINGAGENTS_DATA_DIR}/analysis_results
"""
            
            # 如果还没有这些配置，则添加
            if 'TRADINGAGENTS_DATA_DIR' not in content:
                content += new_config
                
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("✅ .env文件更新完成")
            else:
                logger.info("ℹ️ .env文件已包含数据目录配置")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新.env文件失败: {e}")
            return False
    
    def create_migration_report(self) -> bool:
        """创建迁移报告"""
        try:
            report = {
                'migration_date': datetime.now().isoformat(),
                'project_root': str(self.project_root),
                'backup_location': str(self.backup_dir),
                'new_structure': self.new_structure,
                'migration_map': self.migration_map,
                'status': 'completed'
            }
            
            report_file = self.project_root / 'data_migration_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 迁移报告已保存: {report_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建迁移报告失败: {e}")
            return False
    
    def cleanup_old_directories(self, confirm: bool = False) -> bool:
        """清理旧目录（可选）"""
        if not confirm:
            logger.info("⚠️ 跳过清理旧目录（需要手动确认）")
            return True
        
        try:
            logger.info("🔄 清理旧目录...")
            
            # 要清理的旧目录
            old_dirs = [
                'web/data',
                'tradingagents/dataflows/data_cache'
            ]
            
            for old_dir in old_dirs:
                old_path = self.project_root / old_dir
                if old_path.exists():
                    shutil.rmtree(old_path)
                    logger.info(f"  ✅ 已删除: {old_dir}")
            
            logger.info("✅ 旧目录清理完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清理旧目录失败: {e}")
            return False
    
    def run_migration(self, cleanup_old: bool = False) -> bool:
        """运行完整的迁移流程"""
        logger.info("🚀 开始数据目录重新组织迁移...")
        
        steps = [
            ("创建备份", self.create_backup),
            ("创建新目录结构", self.create_new_structure),
            ("迁移数据", self.migrate_data),
            ("更新环境变量", self.update_env_file),
            ("创建迁移报告", self.create_migration_report),
        ]
        
        if cleanup_old:
            steps.append(("清理旧目录", lambda: self.cleanup_old_directories(True)))
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 执行步骤: {step_name}")
            if not step_func():
                logger.error(f"❌ 步骤失败: {step_name}")
                return False
        
        logger.info("\n🎉 数据目录重新组织完成！")
        logger.info(f"📁 备份位置: {self.backup_dir}")
        logger.info(f"📊 新数据目录: {self.project_root / 'data'}")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据目录重新组织迁移脚本')
    parser.add_argument('--project-root', help='项目根目录路径')
    parser.add_argument('--cleanup-old', action='store_true', help='迁移后清理旧目录')
    parser.add_argument('--dry-run', action='store_true', help='仅显示迁移计划，不执行实际迁移')
    
    args = parser.parse_args()
    
    migrator = DataDirectoryMigrator(args.project_root)
    
    if args.dry_run:
        logger.info("🔍 迁移计划预览:")
        logger.info(f"📁 项目根目录: {migrator.project_root}")
        logger.info(f"📁 备份目录: {migrator.backup_dir}")
        logger.info("\n📋 迁移映射:")
        for source, target in migrator.migration_map:
            logger.info(f"  {source} → {target}")
        return
    
    # 执行迁移
    success = migrator.run_migration(cleanup_old=args.cleanup_old)
    
    if success:
        logger.info("\n✅ 迁移成功完成！")
        logger.info("\n📝 后续步骤:")
        logger.info("1. 验证新目录结构是否正确")
        logger.info("2. 测试应用程序功能")
        logger.info("3. 确认无误后可删除备份目录")
    else:
        logger.error("\n❌ 迁移失败！请检查日志并从备份恢复")


if __name__ == '__main__':
    main()