#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速语法检查器 - 只显示有语法错误的文件
Quick Syntax Checker - Only show files with syntax errors
"""

import os
import py_compile
import sys
from pathlib import Path
from typing import List, Tuple

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')



def find_python_files(root_dir: str, exclude_dirs: List[str] = None) -> List[str]:
    """查找项目中所有Python文件，排除指定目录"""
    if exclude_dirs is None:
        exclude_dirs = ['env', 'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache']
    
    python_files = []
    root_path = Path(root_dir)
    
    for file_path in root_path.rglob('*.py'):
        if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
            continue
        python_files.append(str(file_path))
    
    return sorted(python_files)


def check_syntax(file_path: str) -> Tuple[bool, str]:
    """检查单个Python文件的语法"""
    try:
        py_compile.compile(file_path, doraise=True)
        return False, ""
    except py_compile.PyCompileError as e:
        return True, str(e)
    except Exception as e:
        return True, f"Unexpected error: {str(e)}"


def main():
    """主函数 - 执行语法检查"""
    logger.error(f"🔍 快速语法检查 - 查找有错误的文件...\n")
    
    current_dir = os.getcwd()
    python_files = find_python_files(current_dir)
    
    logger.info(f"📊 总共找到 {len(python_files)} 个Python文件")
    logger.error(f"🔍 正在检查语法错误...\n")
    
    error_files = []
    
    for file_path in python_files:
        relative_path = os.path.relpath(file_path, current_dir)
        has_error, error_msg = check_syntax(file_path)
        
        if has_error:
            error_files.append((relative_path, error_msg))
            logger.error(f"❌ {relative_path}")
    
    logger.info(f"\n📋 检查完成!")
    logger.info(f"✅ 语法正确: {len(python_files) - len(error_files)} 个文件")
    logger.error(f"❌ 语法错误: {len(error_files)} 个文件")
    
    if error_files:
        logger.error(f"\n🚨 有语法错误的文件列表:")
        logger.info(f"-")
        for i, (file_path, _) in enumerate(error_files, 1):
            logger.info(f"{i:2d}. {file_path}")
        
        logger.error(f"\n💡 使用详细检查脚本查看具体错误信息:")
        logger.info(f"   python syntax_checker.py")
    else:
        logger.info(f"\n🎉 所有文件语法检查通过!")


if __name__ == "__main__":
    main()