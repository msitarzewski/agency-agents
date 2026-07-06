#!/usr/bin/env python3
"""
清理测试数据
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'web'))

def cleanup_test_files():
    """清理测试文件"""
    print("🧹 清理测试文件...")
    
    # 清理详细报告目录
    project_root = Path(__file__).parent
    test_dir = project_root / "data" / "analysis_results" / "TEST123"
    
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print(f"✅ 已删除测试目录: {test_dir}")
    else:
        print(f"⚠️ 测试目录不存在: {test_dir}")

def cleanup_mongodb_test_data():
    """清理MongoDB测试数据"""
    print("🗄️ 清理MongoDB测试数据...")
    
    try:
        from web.utils.mongodb_report_manager import mongodb_report_manager
        
        if not mongodb_report_manager.connected:
            print("❌ MongoDB未连接")
            return
        
        # 删除测试数据
        collection = mongodb_report_manager.collection
        result = collection.delete_many({"stock_symbol": "TEST123"})
        
        print(f"✅ 已删除 {result.deleted_count} 条TEST123相关记录")
        
        # 删除其他测试数据
        result2 = collection.delete_many({"stock_symbol": "TEST001"})
        print(f"✅ 已删除 {result2.deleted_count} 条TEST001相关记录")
        
    except Exception as e:
        print(f"❌ MongoDB清理失败: {e}")

def main():
    """主函数"""
    print("🧹 清理测试数据")
    print("=" * 30)
    
    cleanup_test_files()
    cleanup_mongodb_test_data()
    
    print("\n🎉 清理完成")

if __name__ == "__main__":
    main()
