#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态检查 Python 文件的导入错误
排除 tests 目录
"""

import os
import sys
import ast
from pathlib import Path
from typing import List, Tuple, Set, Dict


class ImportChecker:
    """导入检查器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors: List[Tuple[Path, int, str, str]] = []
        self.checked_files = 0
        self.total_imports = 0
        
    def find_python_files(self, exclude_dirs: Set[str] = None) -> List[Path]:
        """查找所有 Python 文件（排除指定目录）"""
        if exclude_dirs is None:
            exclude_dirs = {
                '.git', '__pycache__', '.venv', 'env', 'venv',
                'node_modules', '.pytest_cache', 'tests',  # 排除 tests 目录
                'build', 'dist', '*.egg-info',
                'release', 'examples', 'scripts'  # 排除 release、examples 和 scripts 目录
            }
        
        python_files = []
        
        for py_file in self.project_root.rglob('*.py'):
            # 检查是否在排除目录中
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            python_files.append(py_file)
        
        return sorted(python_files)
    
    def extract_imports(self, file_path: Path) -> List[Tuple[str, int, str]]:
        """
        提取文件中的所有导入语句
        返回: [(module_name, line_no, import_type), ...]
        import_type: 'import' 或 'from'
        """
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno, 'import'))
                elif isinstance(node, ast.ImportFrom):
                    # 跳过相对导入（如 from .module import ...）
                    # node.level > 0 表示相对导入（. 或 .. 等）
                    if node.module and node.level == 0:
                        imports.append((node.module, node.lineno, 'from'))
        
        except SyntaxError as e:
            self.errors.append((file_path, e.lineno or 0, 'SYNTAX_ERROR', str(e.msg)))
        except Exception as e:
            self.errors.append((file_path, 0, 'PARSE_ERROR', str(e)))
        
        return imports
    
    def check_module_path(self, module_name: str) -> Tuple[bool, str]:
        """
        检查模块路径是否存在
        返回: (是否存在, 错误信息)
        """
        # 跳过标准库和第三方库（只检查项目内部模块）
        if not (module_name.startswith('tradingagents') or 
                module_name.startswith('app') or 
                module_name.startswith('web')):
            return True, ""
        
        # 将模块名转换为文件路径
        parts = module_name.split('.')
        
        # 检查是否是包（目录 + __init__.py）
        package_path = self.project_root / Path(*parts)
        if package_path.is_dir():
            init_file = package_path / '__init__.py'
            if init_file.exists():
                return True, ""
            else:
                return False, f"目录存在但缺少 __init__.py: {package_path.relative_to(self.project_root)}"
        
        # 检查是否是模块文件（.py）
        module_file = self.project_root / Path(*parts[:-1]) / f"{parts[-1]}.py"
        if module_file.exists():
            return True, ""
        
        # 检查父包是否存在
        if len(parts) > 1:
            parent_path = self.project_root / Path(*parts[:-1])
            if not parent_path.exists():
                return False, f"父目录不存在: {parent_path.relative_to(self.project_root)}"
            if not (parent_path / '__init__.py').exists():
                return False, f"父目录缺少 __init__.py: {parent_path.relative_to(self.project_root)}"
        
        return False, f"模块不存在: {module_name}"
    
    def check_file(self, file_path: Path) -> int:
        """检查单个文件的导入，返回错误数量"""
        imports = self.extract_imports(file_path)
        error_count = 0
        
        for module_name, line_no, import_type in imports:
            self.total_imports += 1
            
            # 跳过相对导入
            if module_name.startswith('.'):
                continue
            
            exists, error_msg = self.check_module_path(module_name)
            
            if not exists:
                self.errors.append((file_path, line_no, module_name, error_msg))
                error_count += 1
        
        return error_count
    
    def check_all(self) -> int:
        """检查所有文件，返回总错误数"""
        print(f"📂 项目根目录: {self.project_root}")
        print(f"🔍 开始检查核心代码的导入错误（排除 tests、scripts、examples、release 目录）...\n")
        
        python_files = self.find_python_files()
        print(f"📊 找到 {len(python_files)} 个 Python 文件\n")
        
        for py_file in python_files:
            self.checked_files += 1
            self.check_file(py_file)
        
        return len(self.errors)
    
    def print_report(self):
        """打印检查报告"""
        print("\n" + "=" * 80)
        print("📋 检查报告")
        print("=" * 80)
        print(f"✅ 已检查文件: {self.checked_files}")
        print(f"📦 已检查导入: {self.total_imports}")
        print(f"❌ 发现错误: {len(self.errors)}")
        print("=" * 80)
        
        if self.errors:
            print("\n❌ 导入错误详情:\n")
            
            # 按文件分组
            errors_by_file: Dict[Path, List[Tuple[int, str, str]]] = {}
            for file_path, line_no, module_name, error_msg in self.errors:
                if file_path not in errors_by_file:
                    errors_by_file[file_path] = []
                errors_by_file[file_path].append((line_no, module_name, error_msg))
            
            # 输出每个文件的错误
            for file_path, errors in sorted(errors_by_file.items()):
                rel_path = file_path.relative_to(self.project_root)
                print(f"📄 {rel_path}")
                
                for line_no, module_name, error_msg in sorted(errors, key=lambda x: x[0]):
                    if module_name in ['SYNTAX_ERROR', 'PARSE_ERROR']:
                        print(f"   ❌ 第 {line_no} 行: {module_name} - {error_msg}")
                    else:
                        print(f"   ❌ 第 {line_no} 行: import {module_name}")
                        print(f"      {error_msg}")
                print()
        else:
            print("\n✅ 没有发现导入错误！")


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # 创建检查器并执行检查
    checker = ImportChecker(project_root)
    error_count = checker.check_all()
    
    # 打印报告
    checker.print_report()
    
    # 返回错误码
    return 1 if error_count > 0 else 0


if __name__ == '__main__':
    sys.exit(main())

