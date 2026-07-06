#!/usr/bin/env python3
"""
Streamlit文件监控错误修复脚本

这个脚本用于修复Streamlit应用中的文件监控错误：
FileNotFoundError: [WinError 2] 系统找不到指定的文件。: '__pycache__\\*.pyc.*'

使用方法:
python scripts/fix_streamlit_watcher.py
"""

import os
import sys
import shutil
from pathlib import Path

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('scripts')


def clean_pycache_files():
    """清理所有__pycache__目录和.pyc文件"""
    
    project_root = Path(__file__).parent.parent
    logger.debug(f"🔍 扫描项目目录: {project_root}")
    
    # 查找所有__pycache__目录
    cache_dirs = list(project_root.rglob("__pycache__"))
    pyc_files = list(project_root.rglob("*.pyc"))
    pyo_files = list(project_root.rglob("*.pyo"))
    
    total_cleaned = 0
    
    # 清理__pycache__目录
    if cache_dirs:
        logger.info(f"\n🧹 发现 {len(cache_dirs)} 个__pycache__目录")
        for cache_dir in cache_dirs:
            try:
                shutil.rmtree(cache_dir)
                logger.info(f"  ✅ 已删除: {cache_dir.relative_to(project_root)}")
                total_cleaned += 1
            except Exception as e:
                logger.error(f"  ❌ 删除失败: {cache_dir.relative_to(project_root)} - {e}")
    
    # 清理单独的.pyc文件
    if pyc_files:
        logger.info(f"\n🧹 发现 {len(pyc_files)} 个.pyc文件")
        for pyc_file in pyc_files:
            try:
                pyc_file.unlink()
                logger.info(f"  ✅ 已删除: {pyc_file.relative_to(project_root)}")
                total_cleaned += 1
            except Exception as e:
                logger.error(f"  ❌ 删除失败: {pyc_file.relative_to(project_root)} - {e}")
    
    # 清理.pyo文件
    if pyo_files:
        logger.info(f"\n🧹 发现 {len(pyo_files)} 个.pyo文件")
        for pyo_file in pyo_files:
            try:
                pyo_file.unlink()
                logger.info(f"  ✅ 已删除: {pyo_file.relative_to(project_root)}")
                total_cleaned += 1
            except Exception as e:
                logger.error(f"  ❌ 删除失败: {pyo_file.relative_to(project_root)} - {e}")
    
    if total_cleaned == 0:
        logger.info(f"\n✅ 没有发现需要清理的缓存文件")
    else:
        logger.info(f"\n✅ 总共清理了 {total_cleaned} 个文件/目录")

def check_streamlit_config():
    """检查Streamlit配置文件"""
    
    project_root = Path(__file__).parent.parent
    config_file = project_root / ".streamlit" / "config.toml"
    
    logger.debug(f"\n🔍 检查Streamlit配置文件: {config_file}")
    
    if config_file.exists():
        logger.info(f"  ✅ 配置文件存在")
        
        # 检查配置内容
        try:
            content = config_file.read_text(encoding='utf-8')
            if "excludePatterns" in content and "__pycache__" in content:
                logger.info(f"  ✅ 配置文件包含__pycache__排除规则")
            else:
                logger.warning(f"  ⚠️ 配置文件可能缺少__pycache__排除规则")
        except Exception as e:
            logger.error(f"  ❌ 读取配置文件失败: {e}")
    else:
        logger.error(f"  ❌ 配置文件不存在")
        logger.info(f"  💡 建议运行: python web/run_web.py 来创建配置文件")

def set_environment_variables():
    """设置环境变量禁用字节码生成"""
    
    logger.info(f"\n🔧 设置环境变量...")
    
    # 设置当前会话的环境变量
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    logger.info(f"  ✅ 已设置 PYTHONDONTWRITEBYTECODE=1")
    
    # 检查.env文件
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        if 'PYTHONDONTWRITEBYTECODE' not in content:
            logger.info(f"  💡 建议在.env文件中添加: PYTHONDONTWRITEBYTECODE=1")
        else:
            logger.info(f"  ✅ .env文件已包含PYTHONDONTWRITEBYTECODE设置")
    else:
        logger.info(f"  💡 建议创建.env文件并添加: PYTHONDONTWRITEBYTECODE=1")

def main():
    """主函数"""
    
    logger.error(f"🔧 Streamlit文件监控错误修复工具")
    logger.info(f"=")
    
    logger.info(f"\n📋 此工具将执行以下操作:")
    logger.info(f"  1. 清理所有Python缓存文件(__pycache__, *.pyc, *.pyo)")
    logger.info(f"  2. 检查Streamlit配置文件")
    logger.info(f"  3. 设置环境变量禁用字节码生成")
    
    response = input("\n是否继续? (y/n): ").lower().strip()
    if response != 'y':
        logger.error(f"❌ 操作已取消")
        return
    
    try:
        # 步骤1: 清理缓存文件
        logger.info(f"\n")
        logger.info(f"步骤1: 清理Python缓存文件")
        logger.info(f"=")
        clean_pycache_files()
        
        # 步骤2: 检查配置文件
        logger.info(f"\n")
        logger.info(f"步骤2: 检查Streamlit配置")
        logger.info(f"=")
        check_streamlit_config()
        
        # 步骤3: 设置环境变量
        logger.info(f"\n")
        logger.info(f"步骤3: 设置环境变量")
        logger.info(f"=")
        set_environment_variables()
        
        logger.info(f"\n")
        logger.info(f"🎉 修复完成!")
        logger.info(f"\n📝 建议:")
        logger.info(f"  1. 重启Streamlit应用")
        logger.info(f"  2. 如果问题仍然存在，请查看文档:")
        logger.info(f"     docs/troubleshooting/streamlit-file-watcher-fix.md")
        logger.info(f"  3. 考虑使用虚拟环境隔离Python包")
        
    except Exception as e:
        logger.error(f"\n❌ 修复过程中出现错误: {e}")
        logger.info(f"请手动执行以下操作:")
        logger.info(f"  1. 删除所有__pycache__目录")
        logger.info(f"  2. 检查.streamlit/config.toml配置文件")
        logger.info(f"  3. 设置环境变量 PYTHONDONTWRITEBYTECODE=1")

if __name__ == "__main__":
    main()