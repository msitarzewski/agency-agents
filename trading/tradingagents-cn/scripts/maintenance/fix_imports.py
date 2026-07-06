#!/usr/bin/env python3
"""
批量修复app目录中的import语句
将所有 webapi 引用改为 app
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """修复单个文件中的import语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换import语句
        patterns = [
            (r'from webapi\.', 'from app.'),
            (r'import webapi\.', 'import app.'),
            (r'from webapi import', 'from app import'),
            (r'import webapi', 'import app'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 处理文件 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    print("🔧 批量修复app目录中的import语句")
    print("=" * 50)
    
    app_dir = Path("app")
    if not app_dir.exists():
        print("❌ app目录不存在")
        return
    
    # 查找所有Python文件
    python_files = list(app_dir.rglob("*.py"))
    print(f"📁 找到 {len(python_files)} 个Python文件")
    
    fixed_count = 0
    
    for file_path in python_files:
        # 跳过__pycache__目录
        if "__pycache__" in str(file_path):
            continue
            
        print(f"🔍 检查: {file_path}")
        
        if fix_imports_in_file(file_path):
            print(f"✅ 修复: {file_path}")
            fixed_count += 1
        else:
            print(f"⏭️  跳过: {file_path}")
    
    print("=" * 50)
    print(f"🎉 修复完成！共修复 {fixed_count} 个文件")
    
    if fixed_count > 0:
        print("\n📋 修复的内容:")
        print("- webapi. → app.")
        print("- import webapi → import app")
        print("- from webapi import → from app import")


if __name__ == "__main__":
    main()
