#!/usr/bin/env python3
"""
修复所有路由文件中的 auth 导入
将 from app.routers.auth import 替换为 from app.routers.auth_db import
"""

import os
from pathlib import Path

# 需要修改的文件列表
files_to_fix = [
    "app/routers/akshare_init.py",
    "app/routers/analysis.py",
    "app/routers/cache.py",
    "app/routers/config.py",
    "app/routers/database.py",
    "app/routers/favorites.py",
    "app/routers/news_data.py",
    "app/routers/notifications.py",
    "app/routers/operation_logs.py",
    "app/routers/paper.py",
    "app/routers/queue.py",
    "app/routers/scheduler.py",
    "app/routers/screening.py",
    "app/routers/sse.py",
    "app/routers/stocks.py",
    "app/routers/stock_data.py",
    "app/routers/system_config.py",
    "app/routers/tags.py",
    "app/routers/tushare_init.py",
    "app/routers/usage_statistics.py",
    "app/routers/baostock_init.py",
    "app/routers/financial_data.py",
    "app/routers/historical_data.py",
    "app/routers/internal_messages.py",
    "app/routers/model_capabilities.py",
    "app/routers/multi_period_sync.py",
    "app/routers/reports.py",
    "app/routers/social_media.py",
    "tests/test_tradingagents_runtime_settings.py",
]

def fix_file(filepath: str) -> bool:
    """修复单个文件的导入"""
    path = Path(filepath)
    
    if not path.exists():
        print(f"⚠️  文件不存在: {filepath}")
        return False
    
    try:
        # 读取文件内容（使用 UTF-8 编码）
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要替换
        if 'from app.routers.auth import' not in content:
            print(f"⏭️  跳过（无需修改）: {filepath}")
            return False
        
        # 执行替换
        new_content = content.replace(
            'from app.routers.auth import',
            'from app.routers.auth_db import'
        )
        
        # 写回文件（保持 UTF-8 编码）
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        
        print(f"✅ 已修复: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {filepath} - {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 开始修复 auth 导入")
    print("=" * 60)
    print()
    
    fixed_count = 0
    skipped_count = 0
    failed_count = 0
    
    for filepath in files_to_fix:
        result = fix_file(filepath)
        if result is True:
            fixed_count += 1
        elif result is False:
            skipped_count += 1
        else:
            failed_count += 1
    
    print()
    print("=" * 60)
    print("📊 修复完成")
    print("=" * 60)
    print(f"✅ 已修复: {fixed_count} 个文件")
    print(f"⏭️  已跳过: {skipped_count} 个文件")
    print(f"❌ 失败: {failed_count} 个文件")
    print()

if __name__ == "__main__":
    main()

