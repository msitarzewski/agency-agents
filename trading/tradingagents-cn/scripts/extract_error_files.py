#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取语法错误文件列表脚本
Extract syntax error files list script
"""

import os
import sys
import subprocess
import re
from collections import defaultdict

def run_syntax_check():
    """
    运行语法检查并捕获输出
    Run syntax check and capture output
    """
    try:
        result = subprocess.run(
            [sys.executable, 'syntax_test_script.py'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        print(f"运行语法检查时出错 | Error running syntax check: {e}")
        return "", str(e), 1

def extract_error_files(output):
    """
    从输出中提取错误文件列表
    Extract error files list from output
    """
    error_files = defaultdict(list)
    
    # 匹配错误行的正则表达式
    error_pattern = r'❌\s+([^:]+):\s*(.+)'
    
    lines = output.split('\n')
    for line in lines:
        match = re.match(error_pattern, line.strip())
        if match:
            file_path = match.group(1).strip()
            error_msg = match.group(2).strip()
            error_files[file_path].append(error_msg)
    
    return error_files

def generate_report(error_files):
    """
    生成错误报告
    Generate error report
    """
    if not error_files:
        print("🎉 没有发现语法错误文件！| No syntax error files found!")
        return
    
    print(f"\n🚨 发现 {len(error_files)} 个文件存在语法错误 | Found {len(error_files)} files with syntax errors:\n")
    
    # 按文件路径排序
    sorted_files = sorted(error_files.items())
    
    for i, (file_path, errors) in enumerate(sorted_files, 1):
        print(f"{i:2d}. {file_path}")
        for error in errors:
            print(f"    - {error}")
        print()
    
    # 生成简洁的文件列表
    print("\n📋 错误文件列表 | Error files list:")
    print("=" * 50)
    for file_path in sorted(error_files.keys()):
        print(file_path)
    
    # 保存到文件
    report_file = "syntax_error_files_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"语法错误文件报告 | Syntax Error Files Report\n")
        f.write(f"生成时间 | Generated at: {__import__('datetime').datetime.now()}\n")
        f.write(f"错误文件数量 | Error files count: {len(error_files)}\n\n")
        
        f.write("详细错误信息 | Detailed error information:\n")
        f.write("=" * 60 + "\n")
        for file_path, errors in sorted_files:
            f.write(f"\n{file_path}:\n")
            for error in errors:
                f.write(f"  - {error}\n")
        
        f.write("\n\n错误文件列表 | Error files list:\n")
        f.write("=" * 30 + "\n")
        for file_path in sorted(error_files.keys()):
            f.write(f"{file_path}\n")
    
    print(f"\n📄 详细报告已保存到 | Detailed report saved to: {report_file}")

def main():
    """
    主函数
    Main function
    """
    print("🔍 开始提取语法错误文件列表 | Starting to extract syntax error files list...")
    
    # 运行语法检查
    stdout, stderr, returncode = run_syntax_check()
    
    if stderr:
        print(f"⚠️  语法检查过程中有警告 | Warnings during syntax check: {stderr}")
    
    # 提取错误文件
    error_files = extract_error_files(stdout)
    
    # 生成报告
    generate_report(error_files)
    
    return len(error_files)

if __name__ == "__main__":
    error_count = main()
    sys.exit(0 if error_count == 0 else 1)