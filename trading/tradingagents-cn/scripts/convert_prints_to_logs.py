#!/usr/bin/env python3
"""
将项目中的print语句转换为日志输出
排除tests和env目录
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class PrintToLogConverter:
    """Print语句到日志转换器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.converted_files = []
        self.errors = []
        
        # 需要排除的目录
        self.exclude_dirs = {'tests', 'env', '.env', '__pycache__', '.git', '.github'}
        
        # 需要排除的文件模式
        self.exclude_patterns = {
            'test_*.py',
            '*_test.py', 
            'conftest.py',
            'setup.py',
            'convert_prints_to_logs.py'  # 排除自己
        }
    
    def should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        # 检查是否在排除目录中
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return True
        
        # 检查文件名模式
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        
        return False
    
    def get_log_level_from_message(self, message: str) -> str:
        """根据消息内容确定日志级别"""
        message_lower = message.lower()
        
        # 错误级别
        if any(indicator in message for indicator in ['❌', '错误', 'ERROR', 'Error', '失败', 'Failed', 'Exception']):
            return 'error'
        
        # 警告级别
        elif any(indicator in message for indicator in ['⚠️', '警告', 'WARNING', 'Warning', '注意']):
            return 'warning'
        
        # 调试级别
        elif any(indicator in message for indicator in ['🔍', 'DEBUG', 'Debug', '[DEBUG]']):
            return 'debug'
        
        # 成功/完成信息
        elif any(indicator in message for indicator in ['✅', '成功', '完成', 'Success', 'Complete']):
            return 'info'
        
        # 默认信息级别
        else:
            return 'info'
    
    def add_logging_import(self, content: str, file_path: Path) -> str:
        """添加日志导入"""
        # 检查是否已经有日志导入
        if 'from tradingagents.utils.logging_manager import get_logger' in content:
            return content
        
        lines = content.split('\n')
        insert_pos = 0
        in_docstring = False
        docstring_char = None
        
        # 找到所有import语句的结束位置
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 处理文档字符串
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_char = stripped[:3]
                    if not stripped.endswith(docstring_char) or len(stripped) == 3:
                        in_docstring = True
                    continue
            else:
                if stripped.endswith(docstring_char):
                    in_docstring = False
                continue
            
            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                continue
            
            # 如果是import语句，更新插入位置
            if stripped.startswith(('import ', 'from ')) and 'logging_manager' not in line:
                insert_pos = i + 1
            # 如果遇到非import语句，停止搜索
            elif insert_pos > 0:
                break
        
        # 确定日志器名称
        relative_path = file_path.relative_to(self.project_root)
        if 'web' in str(relative_path):
            logger_name = 'web'
        elif 'tradingagents' in str(relative_path):
            if 'agents' in str(relative_path):
                logger_name = 'agents'
            elif 'dataflows' in str(relative_path):
                logger_name = 'dataflows'
            elif 'llm_adapters' in str(relative_path):
                logger_name = 'llm_adapters'
            elif 'utils' in str(relative_path):
                logger_name = 'utils'
            else:
                logger_name = 'tradingagents'
        elif 'cli' in str(relative_path):
            logger_name = 'cli'
        elif 'scripts' in str(relative_path):
            logger_name = 'scripts'
        else:
            logger_name = 'default'
        
        # 插入日志导入
        lines.insert(insert_pos, "")
        lines.insert(insert_pos + 1, "# 导入日志模块")
        lines.insert(insert_pos + 2, "from tradingagents.utils.logging_manager import get_logger")
        lines.insert(insert_pos + 3, f"logger = get_logger('{logger_name}')")
        
        return '\n'.join(lines)
    
    def convert_print_statements(self, content: str) -> str:
        """转换print语句为日志调用"""
        lines = content.split('\n')
        modified_lines = []
        
        for line in lines:
            # 跳过注释行
            if line.strip().startswith('#'):
                modified_lines.append(line)
                continue
            
            # 查找print语句
            # 匹配各种print格式：print("..."), print(f"..."), print('...'), print(f'...')
            print_patterns = [
                r'print\s*\(\s*f?"([^"]*?)"([^)]*)\)',  # print("...")
                r"print\s*\(\s*f?'([^']*?)'([^)]*)\)",   # print('...')
                r'print\s*\(\s*f?"""([^"]*?)"""([^)]*)\)',  # print("""...""")
                r"print\s*\(\s*f?'''([^']*?)'''([^)]*)\)",   # print('''...''')
            ]
            
            line_modified = False
            for pattern in print_patterns:
                match = re.search(pattern, line, re.DOTALL)
                if match:
                    message = match.group(1)
                    rest = match.group(2).strip()
                    
                    # 确定日志级别
                    log_level = self.get_log_level_from_message(message)
                    
                    # 获取缩进
                    indent = len(line) - len(line.lstrip())
                    
                    # 构建新的日志语句
                    if rest and rest.startswith(','):
                        # 有额外参数
                        new_line = f"{' ' * indent}logger.{log_level}(f\"{message}\"{rest})"
                    else:
                        # 没有额外参数
                        new_line = f"{' ' * indent}logger.{log_level}(f\"{message}\")"
                    
                    line = new_line
                    line_modified = True
                    break
            
            modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def convert_file(self, file_path: Path) -> bool:
        """转换单个文件"""
        try:
            print(f"🔄 转换文件: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含print语句
            if 'print(' not in content:
                print(f"⏭️ 跳过文件（无print语句）: {file_path}")
                return False
            
            original_content = content
            
            # 添加日志导入
            content = self.add_logging_import(content, file_path)
            
            # 转换print语句
            content = self.convert_print_statements(content)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.converted_files.append(str(file_path))
                print(f"✅ 转换完成: {file_path}")
                return True
            else:
                print(f"⏭️ 无需修改: {file_path}")
                return False
                
        except Exception as e:
            error_msg = f"❌ 转换失败 {file_path}: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
    
    def convert_project(self) -> Dict[str, int]:
        """转换整个项目"""
        stats = {'converted': 0, 'skipped': 0, 'errors': 0}
        
        # 查找所有Python文件
        for py_file in self.project_root.rglob('*.py'):
            if self.should_skip_file(py_file):
                continue
            
            if self.convert_file(py_file):
                stats['converted'] += 1
            else:
                if str(py_file) in [error.split(':')[0] for error in self.errors]:
                    stats['errors'] += 1
                else:
                    stats['skipped'] += 1
        
        return stats
    
    def generate_report(self) -> str:
        """生成转换报告"""
        report = f"""
# Print语句转换报告

## 转换统计
- 成功转换文件: {len(self.converted_files)}
- 错误数量: {len(self.errors)}

## 转换的文件
"""
        for file_path in self.converted_files:
            report += f"- {file_path}\n"
        
        if self.errors:
            report += "\n## 错误列表\n"
            for error in self.errors:
                report += f"- {error}\n"
        
        return report


def main():
    """主函数"""
    print("🚀 开始将print语句转换为日志输出")
    print("=" * 50)
    
    # 确定项目根目录
    project_root = Path(__file__).parent
    
    # 创建转换器
    converter = PrintToLogConverter(project_root)
    
    # 执行转换
    stats = converter.convert_project()
    
    # 显示结果
    print("\n" + "=" * 50)
    print("📊 转换结果汇总:")
    print(f"   转换文件: {stats['converted']}")
    print(f"   跳过文件: {stats['skipped']}")
    print(f"   错误文件: {stats['errors']}")
    
    if stats['converted'] > 0:
        print(f"\n🎉 成功转换 {stats['converted']} 个文件的print语句为日志输出！")
    
    if converter.errors:
        print(f"\n⚠️ 有 {len(converter.errors)} 个文件转换失败")
        for error in converter.errors:
            print(f"   {error}")
    
    # 生成报告
    report = converter.generate_report()
    report_file = project_root / 'print_to_log_conversion_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 详细报告已保存到: {report_file}")


if __name__ == '__main__':
    main()