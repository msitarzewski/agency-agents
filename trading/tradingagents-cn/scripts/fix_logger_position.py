#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复logger变量位置脚本 (改进版)
Fix logger variable position script (improved version)

将错误位置的logger初始化移动到文件头部import语句下面
Move misplaced logger initialization to the correct position after import statements
"""

import os
import re
import sys
from typing import List, Tuple, Optional
from collections import defaultdict

class LoggerPositionFixer:
    """
    Logger位置修复器
    Logger position fixer
    """
    
    def __init__(self):
        self.fixed_files = []
        self.skipped_files = []
        self.error_files = []
        
    def find_python_files(self, directory: str) -> List[str]:
        """
        查找所有Python文件
        Find all Python files
        """
        python_files = []
        
        for root, dirs, files in os.walk(directory):
            # 跳过虚拟环境目录
            if 'env' in dirs:
                dirs.remove('env')
            if 'venv' in dirs:
                dirs.remove('venv')
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            if '.git' in dirs:
                dirs.remove('.git')
                
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
                    
        return python_files
    
    def analyze_file_structure(self, content: str) -> dict:
        """
        分析文件结构
        Analyze file structure
        """
        lines = content.split('\n')
        structure = {
            'docstring_end': 0,
            'last_import': 0,
            'logger_positions': [],
            'has_logging_import': False,
            'logging_import_line': -1,
            'proper_logger_exists': False
        }
        
        in_docstring = False
        docstring_quotes = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检查文档字符串
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                docstring_quotes = stripped[:3]
                in_docstring = True
                if stripped.count(docstring_quotes) >= 2:  # 单行文档字符串
                    in_docstring = False
                    structure['docstring_end'] = i + 1
                continue
            elif in_docstring and docstring_quotes in stripped:
                in_docstring = False
                structure['docstring_end'] = i + 1
                continue
            elif in_docstring:
                continue
                
            # 跳过注释和空行
            if not stripped or stripped.startswith('#'):
                continue
                
            # 检查import语句
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                ('import ' in stripped and not stripped.startswith('logger'))):
                structure['last_import'] = i + 1
                
                # 检查是否有日志相关的import
                if ('logging_manager' in stripped or 
                    'get_logger' in stripped):
                    structure['has_logging_import'] = True
                    structure['logging_import_line'] = i
                continue
                
            # 检查logger初始化
            if re.match(r'^\s*logger\s*=\s*get_logger\s*\(', stripped):
                structure['logger_positions'].append(i)
                
                # 检查是否在合适位置（import后不久）
                if i <= structure['last_import'] + 10:  # 允许在import后10行内
                    structure['proper_logger_exists'] = True
                
        return structure
    
    def fix_logger_position(self, file_path: str) -> bool:
        """
        修复单个文件的logger位置
        Fix logger position in a single file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            structure = self.analyze_file_structure(content)
            
            # 如果没有logger初始化或没有日志import，跳过
            if not structure['logger_positions'] or not structure['has_logging_import']:
                return False
                
            # 如果只有一个logger且在正确位置，跳过
            if (len(structure['logger_positions']) == 1 and 
                structure['proper_logger_exists']):
                return False
                
            # 检查是否需要修复
            needs_fix = False
            correct_position = max(structure['docstring_end'], structure['last_import'])
            
            # 查找错误位置的logger（在函数内部或文件末尾）
            misplaced_loggers = []
            for pos in structure['logger_positions']:
                # 如果logger在import后很远的位置，认为是错误位置
                if pos > correct_position + 20:
                    misplaced_loggers.append(pos)
                    needs_fix = True
                    
            if not needs_fix:
                return False
                
            # 提取logger初始化语句
            logger_statements = []
            lines_to_remove = []
            
            for pos in misplaced_loggers:
                logger_line = lines[pos].strip()
                if logger_line:
                    logger_statements.append(logger_line)
                    lines_to_remove.append(pos)
                    
            # 移除原位置的logger语句
            for pos in sorted(lines_to_remove, reverse=True):
                lines.pop(pos)
                
            # 如果已经有正确位置的logger，不重复添加
            if not structure['proper_logger_exists'] and logger_statements:
                # 找到插入位置
                insert_position = correct_position
                
                # 确保插入位置后有空行
                while (insert_position < len(lines) and 
                       lines[insert_position].strip() == ''):
                    insert_position += 1
                    
                # 插入第一个logger语句（通常只需要一个）
                lines.insert(insert_position, logger_statements[0])
                
                # 确保logger语句后有空行
                if (insert_position + 1 < len(lines) and
                    lines[insert_position + 1].strip() != ''):
                    lines.insert(insert_position + 1, '')
                
            # 写回文件
            new_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return True
            
        except Exception as e:
            print(f"修复文件 {file_path} 时出错: {e}")
            return False
    
    def fix_all_files(self, directory: str) -> dict:
        """
        修复所有文件的logger位置
        Fix logger position in all files
        """
        python_files = self.find_python_files(directory)
        
        print(f"找到 {len(python_files)} 个Python文件")
        
        for file_path in python_files:
            relative_path = os.path.relpath(file_path, directory)
            
            try:
                if self.fix_logger_position(file_path):
                    self.fixed_files.append(relative_path)
                    print(f"✅ 修复: {relative_path}")
                else:
                    self.skipped_files.append(relative_path)
                    
            except Exception as e:
                self.error_files.append((relative_path, str(e)))
                print(f"❌ 错误: {relative_path} - {e}")
                
        return {
            'fixed': len(self.fixed_files),
            'skipped': len(self.skipped_files),
            'errors': len(self.error_files)
        }
    
    def generate_report(self, output_file: str = 'logger_position_fix_report.md'):
        """
        生成修复报告
        Generate fix report
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Logger位置修复报告\n")
            f.write("# Logger Position Fix Report\n\n")
            f.write(f"生成时间: {__import__('datetime').datetime.now()}\n\n")
            
            f.write("## 修复统计 | Fix Statistics\n\n")
            f.write(f"- 修复文件数: {len(self.fixed_files)}\n")
            f.write(f"- 跳过文件数: {len(self.skipped_files)}\n")
            f.write(f"- 错误文件数: {len(self.error_files)}\n\n")
            
            if self.fixed_files:
                f.write("## 修复的文件 | Fixed Files\n\n")
                for file_path in sorted(self.fixed_files):
                    f.write(f"- {file_path}\n")
                f.write("\n")
                
            if self.error_files:
                f.write("## 错误文件 | Error Files\n\n")
                for file_path, error in self.error_files:
                    f.write(f"- {file_path}: {error}\n")
                f.write("\n")

def main():
    """
    主函数
    Main function
    """
    print("🔧 开始修复logger位置问题...")
    
    current_dir = os.getcwd()
    fixer = LoggerPositionFixer()
    
    # 修复所有文件
    results = fixer.fix_all_files(current_dir)
    
    # 生成报告
    fixer.generate_report()
    
    print(f"\n📊 修复完成:")
    print(f"✅ 修复文件: {results['fixed']}")
    print(f"⏭️  跳过文件: {results['skipped']}")
    print(f"❌ 错误文件: {results['errors']}")
    print(f"\n📄 详细报告: logger_position_fix_report.md")
    
    return results['errors']

if __name__ == "__main__":
    error_count = main()
    sys.exit(0 if error_count == 0 else 1)