#!/usr/bin/env python3
"""
许可证检查脚本
License Check Script

检查项目中各个组件的许可证状态
Check the license status of various components in the project
"""

import os
import sys
from pathlib import Path

def check_license_file(file_path: Path, component_name: str) -> bool:
    """检查许可证文件是否存在并包含必要信息"""
    if not file_path.exists():
        print(f"❌ {component_name}: 许可证文件不存在 - {file_path}")
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # 检查是否包含版权声明
        if "Copyright" not in content and "版权所有" not in content:
            print(f"⚠️  {component_name}: 缺少版权声明")
            return False
            
        # 检查是否包含联系信息
        if "hsliup@163.com" not in content:
            print(f"⚠️  {component_name}: 缺少联系信息")
            return False
            
        print(f"✅ {component_name}: 许可证文件正常")
        return True
        
    except Exception as e:
        print(f"❌ {component_name}: 读取许可证文件失败 - {e}")
        return False

def main():
    """主函数"""
    print("🔍 TradingAgents-CN 许可证检查")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    all_good = True
    
    # 检查主许可证文件
    main_license = project_root / "LICENSE"
    if not check_license_file(main_license, "主许可证 (Main License)"):
        all_good = False
    
    # 检查 app 目录许可证
    app_license = project_root / "app" / "LICENSE"
    if not check_license_file(app_license, "后端应用 (Backend App)"):
        all_good = False
    
    # 检查 frontend 目录许可证
    frontend_license = project_root / "frontend" / "LICENSE"
    if not check_license_file(frontend_license, "前端应用 (Frontend App)"):
        all_good = False
    
    # 检查许可证说明文档
    licensing_doc = project_root / "LICENSING.md"
    if not licensing_doc.exists():
        print("❌ 许可证说明文档不存在 - LICENSING.md")
        all_good = False
    else:
        print("✅ 许可证说明文档存在")
    
    # 检查商业许可证模板
    commercial_template = project_root / "COMMERCIAL_LICENSE_TEMPLATE.md"
    if not commercial_template.exists():
        print("❌ 商业许可证模板不存在 - COMMERCIAL_LICENSE_TEMPLATE.md")
        all_good = False
    else:
        print("✅ 商业许可证模板存在")
    
    print("=" * 50)
    
    if all_good:
        print("🎉 所有许可证文件检查通过！")
        print("🎉 All license files passed the check!")
        return 0
    else:
        print("⚠️  发现许可证问题，请检查上述错误")
        print("⚠️  License issues found, please check the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
