#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法检查脚本 - 检查除env目录外的所有Python文件
Syntax Check Script - Check all Python files except env directory
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple

def find_python_files(root_dir: str, exclude_dirs: List[str] = None) -> List[str]:
    """
    查找所有Python文件，排除指定目录
    Find all Python files, excluding specified directories
    """
    if exclude_dirs is None:
        exclude_dirs = ['env', '.env', 'venv', '.venv', '__pycache__', '.git', 'node_modules']
    
    python_files = []
    root_path = Path(root_dir)
    
    for file_path in root_path.rglob('*.py'):
        # 检查是否在排除目录中
        should_exclude = False
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path.parts:
                should_exclude = True
                break
        
        if not should_exclude:
            python_files.append(str(file_path))
    
    return sorted(python_files)

def check_syntax(file_path: str) -> Tuple[bool, str]:
    """
    检查单个Python文件的语法
    Check syntax of a single Python file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析AST
        ast.parse(content, filename=file_path)
        return True, "OK"
    
    except SyntaxError as e:
        error_msg = f"语法错误 | Syntax Error: Line {e.lineno}, Column {e.offset}: {e.msg}"
        return False, error_msg
    
    except UnicodeDecodeError as e:
        error_msg = f"编码错误 | Encoding Error: {e}"
        return False, error_msg
    
    except Exception as e:
        error_msg = f"其他错误 | Other Error: {e}"
        return False, error_msg

def main():
    """
    主函数
    Main function
    """
    print("\n🔍 开始语法检查 | Starting syntax check...")
    
    # 获取当前目录
    current_dir = os.getcwd()
    print(f"📁 检查目录 | Checking directory: {current_dir}")
    
    # 查找所有Python文件
    python_files = find_python_files(current_dir)
    print(f"📄 找到 {len(python_files)} 个Python文件 | Found {len(python_files)} Python files")
    
    # 检查语法
    success_count = 0
    error_count = 0
    error_files = []
    
    for file_path in python_files:
        relative_path = os.path.relpath(file_path, current_dir)
        is_valid, message = check_syntax(file_path)
        
        if is_valid:
            success_count += 1
            print(f"✅ {relative_path}: {message}")
        else:
            error_count += 1
            error_files.append((relative_path, message))
            print(f"❌ {relative_path}: {message}")
    
    # 输出总结
    print(f"\n📊 检查完成 | Check completed:")
    print(f"✅ 成功文件 | Successful files: {success_count}")
    print(f"❌ 错误文件 | Error files: {error_count}")
    
    if error_files:
        print(f"\n🚨 错误详情 | Error details:")
        for file_path, error_msg in error_files:
            print(f"  {file_path}: {error_msg}")
        
        # 返回错误代码
        sys.exit(1)
    else:
        print(f"\n🎉 所有文件语法检查通过！| All files passed syntax check!")
        sys.exit(0)

if __name__ == "__main__":
    main()